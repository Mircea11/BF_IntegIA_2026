import psycopg
from psycopg.types.json import Jsonb

from rag_hopital.config import settings


def init_db():
    """Create the experiment evaluation tables."""

    statements = [
        """
        CREATE TABLE IF NOT EXISTS experiments (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            config JSONB NOT NULL,
            started_at TIMESTAMPTZ DEFAULT NOW(),
            duration_s REAL,
            status TEXT NOT NULL DEFAULT 'running'
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS answers (
            experiment_id INTEGER NOT NULL
                REFERENCES experiments(id),
            question_id TEXT NOT NULL,
            question_text TEXT NOT NULL,
            expected_answer TEXT,
            chunks JSONB NOT NULL,
            answer TEXT,
            latency_ms REAL,
            PRIMARY KEY (experiment_id, question_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS scores (
            experiment_id INTEGER NOT NULL
                REFERENCES experiments(id),
            question_id TEXT NOT NULL,
            question_type TEXT NOT NULL,
            metric TEXT NOT NULL,
            value REAL,
            reason TEXT,
            PRIMARY KEY (
                experiment_id,
                question_id,
                metric
            )
        )
        """,
    ]

    with psycopg.connect(settings.postgres_url) as conn:
        for statement in statements:
            conn.execute(statement)


def save_retrieval_run(question, points, latency_ms, config):
    """Save a real retrieval execution and its ranked results."""

    chunks = []

    for rank, point in enumerate(points, 1):
        payload = point.payload or {}

        chunks.append({
            "rank": rank,
            "chunk_id": payload.get("chunk_id"),
            "document": payload.get("document"),
            "chunk_index": payload.get("chunk_index"),
            "patient_ipp": payload.get("patient_ipp"),
            "score": float(point.score),
        })

    with psycopg.connect(settings.postgres_url) as conn:

        experiment_id = conn.execute(
            """
            INSERT INTO experiments (name, config)
            VALUES (%s, %s)
            RETURNING id
            """,
            (
                config["name"],
                Jsonb(config),
            ),
        ).fetchone()[0]

        conn.execute(
            """
            INSERT INTO answers (
                experiment_id,
                question_id,
                question_text,
                expected_answer,
                chunks,
                answer,
                latency_ms
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                experiment_id,
                question["id"],
                question["question"],
                question.get("answer"),
                Jsonb(chunks),
                None,
                latency_ms,
            ),
        )

        conn.execute(
            """
            UPDATE experiments
            SET status = 'done',
                duration_s = %s
            WHERE id = %s
            """,
            (latency_ms / 1000, experiment_id),
        )

    return experiment_id


def get_results(experiment_id):
    """Retrieve an experiment from PostgreSQL."""

    with psycopg.connect(settings.postgres_url) as conn:
        return conn.execute(
            """
            SELECT
                e.name,
                a.question_id,
                a.question_text,
                a.expected_answer,
                a.latency_ms,
                a.chunks
            FROM experiments e
            JOIN answers a
                ON e.id = a.experiment_id
            WHERE e.id = %s
            """,
            (experiment_id,),
        ).fetchone()
# ============================================================
# [E09.5-A] CRÉER UNE EXPÉRIENCE POUR PLUSIEURS QUESTIONS
# ============================================================

def create_experiment(config: dict) -> int:
    """
    Créer une expérience dans PostgreSQL.

    ENTRÉE
    -------
    config : dictionnaire décrivant la configuration
             de la recherche.

    SORTIE
    ------
    experiment_id : identifiant attribué par PostgreSQL.

    IMPORTANT
    ---------
    Cette fonction crée UNE expérience.

    Plusieurs questions pourront ensuite être enregistrées
    sous le même experiment_id.
    """

    # Ouvrir une connexion PostgreSQL.
    # settings.postgres_url contient les paramètres de connexion.
    with psycopg.connect(settings.postgres_url) as conn:

        # Envoyer une requête SQL pour créer l'expérience.
        #
        # INSERT INTO : ajouter une ligne.
        #
        # Jsonb(config) : convertir le dictionnaire Python
        # en JSONB, le format JSON utilisé dans PostgreSQL.
        #
        # RETURNING id : demander à PostgreSQL de retourner
        # l'identifiant de la nouvelle expérience.
        result = conn.execute(
            """
            INSERT INTO experiments (
                name,
                config,
                status
            )
            VALUES (%s, %s, 'running')
            RETURNING id
            """,
            (
                config["name"],
                Jsonb(config),
            ),
        )

        # fetchone() récupère la première ligne retournée.
        #
        # [0] sélectionne la première colonne : id.
        experiment_id = result.fetchone()[0]

    # La connexion est fermée après validation
    # de la transaction.

    # Renvoyer l'identifiant au programme appelant.
    return experiment_id
# ============================================================
# [E09.5-B1] ENREGISTRER UNE QUESTION DANS UNE EXPÉRIENCE
# ============================================================

def save_question_result(
    experiment_id: int,
    question: dict,
    points: list,
    latency_ms: float,
) -> None:
    """
    Enregistrer les résultats d'une recherche dans PostgreSQL.

    ENTRÉES
    -------
    experiment_id :
        Identifiant d'une expérience déjà créée.

    question :
        Dictionnaire contenant la question du golden dataset.

    points :
        Liste des chunks retrouvés dans Qdrant.

    latency_ms :
        Durée de la recherche en millisecondes.

    SORTIE
    ------
    None : la fonction enregistre les données,
           mais ne retourne pas de valeur.
    """

    # --------------------------------------------------------
    # [E09.5-B1.1] PRÉPARER LES CHUNKS
    # --------------------------------------------------------

    # Créer une liste vide pour les résultats.
    chunks = []

    # Parcourir les points retournés par Qdrant.
    #
    # enumerate() fournit le rang et le point.
    # start=1 signifie que le premier résultat est au rang 1.
    for rank, point in enumerate(points, start=1):

        # Le payload est un dictionnaire de métadonnées.
        #
        # Si le payload est absent, utiliser un dictionnaire vide.
        payload = point.payload or {}

        # Construire un dictionnaire pour ce chunk.
        #
        # get() récupère la valeur d'une clé.
        # Si la clé est absente, il retourne None.
        chunk = {
            "rank": rank,
            "chunk_id": payload.get("chunk_id"),
            "document": payload.get("document"),
            "chunk_index": payload.get("chunk_index"),
            "patient_ipp": payload.get("patient_ipp"),
            "score": float(point.score),
        }

        # Ajouter ce dictionnaire à notre liste.
        chunks.append(chunk)

    # --------------------------------------------------------
    # [E09.5-B1.2] ENREGISTRER DANS POSTGRESQL
    # --------------------------------------------------------

    # Ouvrir une connexion PostgreSQL.
    #
    # Le bloc with valide la transaction si tout réussit.
    with psycopg.connect(settings.postgres_url) as conn:

        # Insérer la question et ses résultats dans answers.
        #
        # experiment_id rattache la question à l'expérience.
        #
        # Jsonb(chunks) convertit la liste Python en JSONB.
        #
        # answer = NULL :
        # Nous n'avons pas encore généré de réponse avec un LLM.
        #
        # ON CONFLICT :
        # Si cette question existe déjà dans cette expérience,
        # mettre à jour ses résultats plutôt que créer un doublon.
        conn.execute(
            """
            INSERT INTO answers (
                experiment_id,
                question_id,
                question_text,
                expected_answer,
                chunks,
                answer,
                latency_ms
            )
            VALUES (%s, %s, %s, %s, %s, NULL, %s)

            ON CONFLICT (experiment_id, question_id)

            DO UPDATE SET
                question_text = EXCLUDED.question_text,
                expected_answer = EXCLUDED.expected_answer,
                chunks = EXCLUDED.chunks,
                latency_ms = EXCLUDED.latency_ms
            """,
            (
                experiment_id,
                question["id"],
                question["question"],
                question.get("answer"),
                Jsonb(chunks),
                latency_ms,
            ),
        )

    # --------------------------------------------------------
    # [E09.5-B1.3] CONFIRMER L'ENREGISTREMENT
    # --------------------------------------------------------

    # Afficher une confirmation dans le terminal.
    #
    # Cela permet de suivre la progression pendant
    # l'exécution des expériences.
    print(
        f"Experiment {experiment_id} | "
        f"Question {question['id']} | "
        f"{len(chunks)} chunks saved"
    )
# ============================================================
# [E09.5-C1] TERMINER UNE EXPÉRIENCE
# ============================================================

def finish_experiment(experiment_id: int, duration_s: float) -> None:
    """
    Marquer une expérience PostgreSQL comme terminée.

    ENTRÉES
    -------
    experiment_id : identifiant de l'expérience.
    duration_s    : durée totale en secondes.

    SORTIE
    ------
    None : la fonction modifie la base de données.
    """

    # Ouvrir une connexion PostgreSQL.
    with psycopg.connect(settings.postgres_url) as conn:

        # UPDATE modifie une ligne existante.
        #
        # status = 'done' indique que l'exécution est terminée.
        #
        # WHERE id = %s limite la modification
        # à l'expérience concernée.
        conn.execute(
            """
            UPDATE experiments
            SET status = 'done',
                duration_s = %s
            WHERE id = %s
            """,
            (duration_s, experiment_id),
        )
# ============================================================
# [E09.5-D1] LIRE TOUTES LES QUESTIONS D'UNE EXPÉRIENCE
# ============================================================

def get_experiment_questions(experiment_id: int) -> list:
    """
    Lire toutes les questions enregistrées dans une expérience.

    ENTRÉE
    ------
    experiment_id :
        Identifiant de l'expérience PostgreSQL.

    SORTIE
    ------
    Liste de résultats contenant :
        - question_id : identifiant de la question ;
        - chunks      : liste des chunks récupérés par Qdrant.

    Exemple pour l'expérience 2 :
        Q001 -> 5 chunks
        Q002 -> 5 chunks
        Q003 -> 5 chunks
    """

    # [D1.1] Ouvrir la connexion à PostgreSQL.
    #
    # Les paramètres de connexion viennent de settings.
    with psycopg.connect(settings.postgres_url) as conn:

        # [D1.2] Rechercher les questions de l'expérience.
        #
        # SELECT indique les colonnes à récupérer.
        # FROM désigne la table PostgreSQL.
        # WHERE limite la recherche à une expérience.
        # ORDER BY classe les questions par identifiant.
        result = conn.execute(
            """
            SELECT
                question_id,
                chunks
            FROM answers
            WHERE experiment_id = %s
            ORDER BY question_id
            """,
            (experiment_id,),
        )

        # [D1.3] Récupérer toutes les lignes.
        #
        # fetchall() retourne une liste.
        # Chaque élément contient :
        # (question_id, chunks).
        questions = result.fetchall()

    # [D1.4] Renvoyer les résultats au programme.
    return questions


# ============================================================
# [E09.5-D2-A] SAVE EVALUATION SCORES
# ============================================================

def save_question_scores(
    experiment_id: int,
    question: dict,
    metrics: dict,
    reason: str,
) -> None:
    """
    Save the evaluation metrics for one question in PostgreSQL.

    INPUTS
    ------
    experiment_id : ID of an existing experiment.
    question      : Question from hopital_eval.json.
    metrics       : Dictionary containing metric names and values.
    reason        : Explanation of the evaluation results.

    OUTPUT
    ------
    None. The function writes data into PostgreSQL.
    """

    # [D2-A1] Open a PostgreSQL connection.
    #
    # The connection parameters are stored in settings.
    with psycopg.connect(settings.postgres_url) as conn:

        # [D2-A2] Process each metric separately.
        #
        # Example:
        # metric = "fact_recall@5"
        # value  = 1.0
        for metric, value in metrics.items():

            # [D2-A3] Insert the metric into the scores table.
            #
            # ON CONFLICT updates an existing metric.
            # This prevents duplicate records when rerunning
            # the evaluation of the same experiment.
            conn.execute(
                """
                INSERT INTO scores (
                    experiment_id,
                    question_id,
                    question_type,
                    metric,
                    value,
                    reason
                )
                VALUES (%s, %s, %s, %s, %s, %s)

                ON CONFLICT (
                    experiment_id,
                    question_id,
                    metric
                )

                DO UPDATE SET
                    value = EXCLUDED.value,
                    reason = EXCLUDED.reason
                """,
                (
                    experiment_id,
                    question["id"],
                    question["type"],
                    metric,
                    float(value),
                    reason,
                ),
            )