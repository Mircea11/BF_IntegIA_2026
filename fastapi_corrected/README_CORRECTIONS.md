# FastAPI — exercice utilisateurs (version corrigée)

Cette version adapte ton projet `fastapi_corrected/` au ZIP du formateur du
13 novembre 2026, en conservant son emplacement `datas/models/`.

## Installation sous Ubuntu

Depuis `~/formation/fastapi_corrected` :

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
fastapi dev main.py
```

Si `.venv` existe déjà, saute la première commande. Sur Windows uniquement,
l'activation est `.venv\\Scripts\\activate`.

Ouvre http://127.0.0.1:8000/docs, puis teste :

| Méthode | Route | Corps JSON | Résultat |
| --- | --- | --- | --- |
| GET | `/users?limit=5&offset=0` | aucun | 5 utilisateurs sans mot de passe |
| GET | `/user/0` | aucun | Gustave et sa date de naissance |
| POST | `/user` | `{"name":"Ana","password":"TestPassword123!","validation":"TestPassword123!","birthdate":"1990-01-01"}` | 201, nouvel ID |
| PATCH | `/user/0` | `{"name":"Gustave Martin"}` | 200, nom modifié |
| PATCH | `/user/0/password` | `{"old_password":"Password123!","new_password":"OtherPassword123!","validation":"OtherPassword123!"}` | 204, sans corps |
| DELETE | `/user/0` | aucun | 204, sans corps |

L'ancien `GET /users/{id}` fonctionne aussi, mais n'apparaît plus dans Swagger.
L'ancien `PUT /users/{id}` est remplacé par les deux routes PATCH du cours.

Pour tester le programme :

```bash
python -m unittest discover -s tests -v
```

## Notes

- Les 20 utilisateurs sont fictifs et correspondent aux exemples du formateur.
- Le mot de passe n'est jamais envoyé dans les réponses GET/PATCH.
- Les mots de passe sont stockés sous forme de hash Argon2 dans la liste mémoire.
- Le fichier source contient des mots de passe **de démonstration**. Ne jamais
  y placer de véritables identifiants ou mots de passe.
- Un redémarrage complet réinitialise la liste.
- Comme l'ID est l'index de liste, DELETE déplace les IDs des utilisateurs suivants.
- `POST /chat?prompt=Bonjour` appelle un LLM local : URL par défaut
  `http://127.0.0.1:8080/v1`, modèle par défaut `local`. Il faut lancer le LLM
  séparément. Les variables `LLM_BASE_URL` et `LLM_MODEL` permettent de changer
  ces valeurs. Ce chatbot n'est **pas** une chaîne RAG et n'a pas de contrôle
  d'accès : utiliser uniquement des prompts fictifs pour cet exercice.
