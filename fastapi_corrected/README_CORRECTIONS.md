# FastAPI — corrected training exercise (12 November 2026)

This is a **small fix of your instructor's original exercise**, not a new application. It retains the same three default users and the same GET `/users`, GET `/users/{id}`, and POST `/user` endpoints. It adds GET `/` for a simple health/landing response.

## What was wrong

1. `from models import UserCreate` could not find `models` at project root. The Pydantic model is now imported from `datas.models`.
2. `from datas import users` previously resolved to the `datas.users` **module**, not the list. `datas/__init__.py` now explicitly exports the `users` list.
3. The user ID check `len(users) > id or id < 0` was reversed. Fixed to `id < 0 or id >= len(users)`.
4. `users.index(user.name)` returned the wrong ID for duplicate names. Replaced with `len(users) - 1` after appending.
5. Removed duplicate Pydantic models and an incomplete `create_user` class. Only the request model actually used by the exercise remains.
6. Enabled `/`, avoiding an unnecessary 404 while learning.
7. Added simple validation: an empty name returns HTTP 422.

## Run on your Ubuntu machine — no new Python installation

Your existing environment is at `~/formation/fastapi/.venv`.

**Safest: try this corrected project alongside the original.** Extract the ZIP into `~/formation/`, giving `~/formation/fastapi_corrected/`. Then:

```bash
cd ~/formation/fastapi_corrected
source ~/formation/fastapi/.venv/bin/activate
fastapi dev main.py --port 8001
```

Use **port 8001** so you do not collide with the original server on 8000.

Open: `http://127.0.0.1:8001/docs`

In Bruno, send these requests:

| Method | URL | Expected |
| --- | --- | --- |
| GET | `http://127.0.0.1:8001/` | 200, welcome JSON |
| GET | `http://127.0.0.1:8001/users` | 200, array of names |
| GET | `http://127.0.0.1:8001/users/1` | 200, `"Jane Smith"` |
| GET | `http://127.0.0.1:8001/users/9` | 404, `User not found` |
| POST | `http://127.0.0.1:8001/user` | 201; JSON body `{"name":"Ana"}`, returns index `3` |

To run local tests (with the same virtual environment activated):

```bash
python -m unittest discover -s tests -v
```

## Two important concepts

- **ID is a list position** starting at 0, not a persistent database ID. Names and indices are suitable only for this demonstration.
- **Data is in memory.** New users disappear when the server is fully restarted. Production applications need persistent storage.

## What was intentionally not added

No database, no authentication, no BLL/DAL layers, no extra endpoints: those belong to later lessons. The goal is to understand GET, POST, validation, and 404 responses first.
