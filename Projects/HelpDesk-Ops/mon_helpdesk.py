"""Étape 0 : une chaîne de tri, tracée dans Langfuse.            (carte : étape 0 · vu le 04/11, J1-01 §1 à 5)

Le point de départ de HelpDesk-Ops : un ticket entre, la chaîne LCEL `prompt | llm | parser` renvoie une
catégorie, deux règles métier fixent la priorité et la file d'attente. Le CallbackHandler envoie la trace.

Lancer (depuis la racine du cours) :
    uv run --project infrastructure python construction/etape_00_chaine_tri.py "Mon VPN ne marche plus"

À observer :
    - le terminal : catégorie brute renvoyée par le modèle, puis catégorie normalisée, priorité, file ;
    - Langfuse › Tracing : une trace « tri-ticket » (CHAIN → ChatPromptTemplate, ChatOpenAI, StrOutputParser) ;
    - l'adresse e-mail du ticket apparaît <EMAIL> dans la trace : le masque est posé à la création du client.
"""
import sys

from traitlets import observe

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langfuse import observe, Langfuse, propagate_attributes

from helpdesk_ops.config import creer_llm
from helpdesk_ops.donnees import CATEGORIES
from helpdesk_ops.observabilite import init_observabilite
from helpdesk_ops.texte import normaliser

TICKETS = sys.argv[1:] if len(sys.argv) > 1 else [
    "Bonjour, le VPN est bloqué depuis ce matin, c'est urgent. Jean (jean.dupont@nordtech.example)",
    "Mon imprimante laser couleur du 2eme ne fonctionne plus",
]

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



# --------------------------------------------------------------------------- exécuter


#Observation
@observe(name="traiter-ticket")
def traiter_ticket(ticket: str)-> dict:
    brute=tri.invoke(
        #parrametres
        {
            "ticket": ticket,
            "categories": ", ".join(CATEGORIES)
        },
    #configuration
        config=
        {
            "callbacks": [handler],
            "run_name": "tri-ticket"
        }
    )
    categorie = normaliser_categorie(brute)
    priorite = estimer_priorite(ticket)
    file = file_attente(categorie)
    return { "categorie": categorie, "priorite": priorite, "file": file}

# --------------------------------------------------------------------------- exécuter
#Ajuter une session, utilisateur, des tg ==> heerite pour toue ce qui se retrouveera dans mon BlockingIOError
with propagate_attributes(session_id="construction-etape-1", user_id="mb", tags=["construction", "Etape-1"]):
    for TICKET in TICKETS:
        decision = traiter_ticket(TICKET)
        print(f"🎫 Ticket      : {TICKET}")
        print(f"🏷️ Resultat     : {decision}")
        print(f" -> {decision['categorie']}  -{decision['priorite']} - file_attente: {decision['file']}")


# --------------------------------------------------------------------------- exécuter
# brute = tri.invoke({"ticket": TICKET, "categories": ", ".join(CATEGORIES)},
#                    config={"callbacks": [handler], "run_name": "tri-ticket"})
# categorie = normaliser_categorie(brute)
# priorite = estimer_priorite(TICKET)

# print(f"🎫 Ticket      : {TICKETS}")
# print(f"🏷️  Catégorie   : {categorie}   (le modèle a répondu {brute!r})")
# print(f"🚦 Priorité    : {priorite}")
# print(f"📥 File        : {file_attente(categorie)}")

langfuse.flush()                                 # l'envoi est asynchrone : sans flush, la trace peut se perdre
print("🔭 Trace envoyée : Langfuse › Tracing › tri-ticket")
