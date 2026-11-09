"""Mini-défi P1 + étape 4 : mémoire SQLite des conversations (J2-01).

Conserve le routage du mini-défi : P1 → escalader → END ; P3 → agent ⇄ tools → END.
Ajoute la mémoire : checkpoints SQLite, --thread par conversation, --oublier.

Lancer depuis ~/helpdesk-ops :
    uv run --project infrastructure python construction/atelier/defi_escalade.py --thread demo-42 "srv-erp-02 est-il en ligne ?"
    uv run --project infrastructure python construction/atelier/defi_escalade.py --thread demo-42 "Et que dois-je faire maintenant ?"
    uv run --project infrastructure python construction/atelier/defi_escalade.py --thread demo-p1 "Le VPN est bloqué, urgent"
    uv run --project infrastructure python construction/atelier/defi_escalade.py --thread demo-42 --oublier

Note : --oublier efface ce thread de SQLite, pas ses traces Langfuse.
"""
import argparse
from pathlib import Path
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langfuse import propagate_attributes
from langgraph.checkpoint.sqlite import SqliteSaver  # ═══ NOUVEAU (étape 4)
from langgraph.graph import END, START, MessagesState, StateGraph      # ═══ NOUVEAU (étape 3)
from langgraph.prebuilt import ToolNode, tools_condition              # ═══ NOUVEAU (étape 3)

from helpdesk_ops.config import creer_llm
from helpdesk_ops.donnees import CATEGORIES, INVENTAIRE, KB
from helpdesk_ops.observabilite import init_observabilite
from helpdesk_ops.texte import mots_cles, normaliser

# ═══ NOUVEAU (étape 4) : une conversation est identifiée par --thread ═══
parser = argparse.ArgumentParser(description="HelpDesk-Ops : défi P1 avec mémoire SQLite")
parser.add_argument("message", nargs="?", default="srv-erp-02 est-il en ligne ?")
parser.add_argument("--thread", default="defi-demo", help="identifiant de conversation réutilisable")
parser.add_argument("--oublier", action="store_true", help="effacer le thread de la base SQLite")
args = parser.parse_args()

RACINE = next(p for p in Path(__file__).resolve().parents if (p / "infrastructure").is_dir())
SORTIE = Path(__file__).resolve().parent / "sortie"
# Base distincte de l'exemple du formateur pour ne pas mélanger leurs checkpoints.
BASE = RACINE / "data" / "checkpoints" / "defi_escalade.sqlite"  # ═══ NOUVEAU (étape 4)

llm = creer_llm("agent")                         # le modèle désigné par infrastructure/.env
langfuse, handler = init_observabilite()         # client Langfuse avec masque PII + CallbackHandler

# --------------------------------------------------------------------------- la chaîne de tri (LCEL)
PROMPT_TRI = ChatPromptTemplate.from_messages([
    ("system",
     "Tu es l'agent de tri N1 du help-desk de NordTech SA. "
     "Classe le ticket dans UNE catégorie parmi : {categories}. "
     "Réponds uniquement par le nom de la catégorie, en minuscules, sans ponctuation."),
    ("human", "Ticket : {ticket}"),
])
tri = PROMPT_TRI | llm | StrOutputParser()


# --------------------------------------------------------------------------- les règles métier (sans LLM)
def normaliser_categorie(brute: str) -> str:
    """'Réseau.' ou 'catégorie : reseau' -> 'reseau' ; une réponse inattendue -> 'autre' (repli sûr)."""
    nettoyee = normaliser(brute).rstrip(".")
    return next((c for c in CATEGORIES if c in nettoyee), "autre")


def estimer_priorite(ticket: str) -> str:
    """P1 si un mot d'urgence apparaît, sinon P3 : simple, donc explicable."""
    texte = normaliser(ticket)
    return "P1" if any(m in texte for m in ("bloque", "urgent", "production", "tous les utilisateurs")) else "P3"


def file_attente(categorie: str) -> str:
    return "N2-infra" if categorie in ("reseau", "materiel") else "N1"


# --------------------------------------------------------------------------- les outils
@tool(parse_docstring=True)
def statut_serveur(nom: str) -> str:
    """Retourne le statut (en ligne, hors ligne, dégradé) d'un serveur de l'inventaire NordTech.

    Args:
        nom: nom d'hôte exact en minuscules, par exemple 'srv-vpn-01'
    """
    return INVENTAIRE.get(nom.strip().lower(), f"inconnu : '{nom}' n'est pas dans l'inventaire")


@tool(parse_docstring=True)
def chercher_kb(question: str) -> str:
    """Cherche dans la base de connaissances NordTech les procédures utiles pour un problème.

    Args:
        question: description courte du problème, par exemple 'configurer le VPN'
    """
    mots = mots_cles(question)
    trouves = [a for a in KB if mots & mots_cles(a["titre"] + " " + a["contenu"])]
    if not trouves:
        return "Aucun article trouvé. Proposer d'ouvrir un ticket."
    return "\n".join(f"[{a['id']}] {a['titre']} : {a['contenu']}" for a in trouves[:2])


OUTILS = [statut_serveur, chercher_kb]
SYSTEME = SystemMessage(
    "Tu es l'agent support N1 du help-desk de NordTech SA. Réponds en français, en 3 phrases maximum. "
    "Utilise statut_serveur pour l'état d'un serveur et chercher_kb pour une procédure. "
    "N'invente jamais de procédure ni de nom de serveur : si les outils ne donnent rien, propose d'ouvrir un ticket.")
llm_outils = llm.bind_tools(OUTILS)                  # ═══ NOUVEAU (étape 3) : le modèle connaît les outils


# ═══ NOUVEAU (étape 3) : l'état partagé. MessagesState apporte `messages` et son reducer add_messages ═══
class EtatTicket(MessagesState):
    ticket: str
    categorie: str
    priorite: str
    file: str


# ═══ NOUVEAU (étape 3) : les nœuds. Chacun lit l'état et renvoie une MISE À JOUR PARTIELLE ═══
def trier(state: EtatTicket) -> dict:
    brute = tri.invoke({"ticket": state["ticket"], "categories": ", ".join(CATEGORIES)})
    categorie = normaliser_categorie(brute)
    priorite = estimer_priorite(state["ticket"])
    return {"categorie": categorie, "priorite": priorite, "file": file_attente(categorie),
            "messages": [HumanMessage(f"[{categorie} · {priorite}] {state['ticket']}")]}


def agent(state: EtatTicket) -> dict:
    return {"messages": [llm_outils.invoke([SYSTEME] + state["messages"])]}


# ═══ NOUVEAU (mini-défi) : un P1 est escaladé, sans appel à l’agent ni à ses outils ═══
def escalader(state: EtatTicket) -> dict:
    """Renvoyer une confirmation d’escalade pour le ticket prioritaire (simulation)."""
    return {"messages": [AIMessage(
        content=f"Ticket P1 transmis à l'astreinte : {state['ticket']}"
    )]}


# ═══ NOUVEAU (mini-défi) : ce routeur retourne un NOM DE NŒUD, pas une réponse ═══
def apres_tri(state: EtatTicket) -> Literal["escalader", "agent"]:
    """Choisir la branche selon la priorité calculée par trier()."""
    if state["priorite"] == "P1":
        return "escalader"
    return "agent"


# ═══ NOUVEAU (mini-défi) : le graphe bifurque après le tri ═══
builder = StateGraph(EtatTicket)
builder.add_node("trier", trier)
builder.add_node("agent", agent)
builder.add_node("tools", ToolNode(OUTILS))
builder.add_node("escalader", escalader)

builder.add_edge(START, "trier")
builder.add_conditional_edges("trier", apres_tri)    # P1 → escalader ; P3 → agent
builder.add_edge("escalader", END)                 # ne passe jamais par l’agent
builder.add_conditional_edges("agent", tools_condition)
builder.add_edge("tools", "agent")                # boucle normale de l’agent

# Le graphe sera compilé avec son checkpointer SQLite dans le bloc `with` ci-dessous.


# ═══ NOUVEAU (étape 3) : dessiner le graphe, sans service en ligne ═══
def dessiner(graphe, nom: str) -> None:
    SORTIE.mkdir(exist_ok=True)
    (SORTIE / f"{nom}.md").write_text(f"```mermaid\n{graphe.get_graph().draw_mermaid()}\n```\n", encoding="utf-8")
    try:
        print(graphe.get_graph().draw_ascii())       # grandalf, installé par uv sync
    except ImportError:
        print("(dessin ASCII indisponible : grandalf absent)")
    print(f"🗺️  Schéma Mermaid : {(SORTIE / (nom + '.md')).relative_to(RACINE)}\n")


# ═══ NOUVEAU (étape 4) : mémoire persistante par conversation ═══
BASE.parent.mkdir(parents=True, exist_ok=True)
with SqliteSaver.from_conn_string(str(BASE)) as memoire:
    graphe = builder.compile(checkpointer=memoire)
    config = {
        "configurable": {"thread_id": args.thread},
        "callbacks": [handler],
        "run_name": "helpdesk",
        "recursion_limit": 10,
    }

    if args.oublier:
        memoire.delete_thread(args.thread)
        print(f"🧹 Thread {args.thread} effacé de {BASE.relative_to(RACINE)}.")
        raise SystemExit(0)

    # Lire les messages enregistrés AVANT ce nouvel appel.
    avant = len(graphe.get_state(config).values.get("messages", []))
    if avant == 0:
        dessiner(graphe, "defi_escalade_graphe")
    print(f"💾 Thread {args.thread} : {avant} message(s) en mémoire avant l'appel")
    print(f"🎫 {args.message}")

    with propagate_attributes(session_id=args.thread, user_id="agent-n1-042",
                              tags=["construction", "etape-4", "defi-p1"]):
        for etape in graphe.stream({"ticket": args.message}, config=config, stream_mode="updates"):
            for noeud, maj in etape.items():
                if noeud == "trier":
                    print(f"   ▶ trier    : {maj['categorie']} · {maj['priorite']} · file {maj['file']}")
                elif noeud == "agent":
                    msg = maj["messages"][-1]
                    if msg.tool_calls:
                        appels = ", ".join(f"{a['name']}({a['args']})" for a in msg.tool_calls)
                        print(f"   ▶ agent    : demande {appels}")
                    else:
                        print(f"   ▶ agent    : répond « {msg.content} »")
                else:
                    print(f"   ▶ {noeud:<8} : {maj['messages'][-1].content[:90]}")

    etat = graphe.get_state(config).values
    historique = list(graphe.get_state_history(config))
    print(f"💾 Thread {args.thread} : {len(etat.get('messages', []))} message(s), "
          f"{len(historique)} checkpoint(s) dans {BASE.relative_to(RACINE)}")

langfuse.flush()
print(f"🔭 Langfuse › Sessions › {args.thread}")
