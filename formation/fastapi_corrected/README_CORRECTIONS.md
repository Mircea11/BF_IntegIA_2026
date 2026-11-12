# FastAPI — corrected training exercise (12 November 2026)

This is a small correction of the instructor's original exercise, not a new application. It keeps three default users and the GET `/users`, GET `/users/{id}` and POST `/user` endpoints. GET `/` was added as a simple home/health response.

## Corrections

1. Replaced `from models import UserCreate` with `from datas.models import UserCreate` so the Pydantic model can be imported.
2. `datas/__init__.py` now exports the shared `users` list instead of leaving the module/list import ambiguous.
3. Fixed the reversed range check to `id < 0 or id >= len(users)` to return HTTP 404 for missing users.
4. Return `len(users) - 1` after appending a user, rather than using `users.index(user.name)`, which fails for duplicate names.
5. Removed unused/incomplete model definitions, keeping one valid Pydantic request model.
6. Added GET `/` so visiting the root does not return 404.
7. Empty names are rejected with HTTP 422 through Pydantic validation.

## Run on Ubuntu

The **local** working folder is `~/formation/fastapi_corrected` and its dedicated virtual environment is `~/formation/fastapi_corrected/.venv`. The virtual environment is **not committed to Git**.

```bash
cd ~/formation/fastapi_corrected
source .venv/bin/activate
python -m pip install -r requirements.txt   # only if dependencies are not already installed
fastapi dev main.py
```

Open `http://127.0.0.1:8000/docs`. If 8000 is already used, start with `fastapi dev main.py --port 8001` and use port 8001 below.

### Exercises

| Method | Path | Expected response |
| --- | --- | --- |
| GET | `/` | 200; home message |
| GET | `/users` | 200; array of names |
| GET | `/users/1` | 200; `"Jane Smith"` |
| GET | `/users/9` | 404; user not found |
| POST | `/user` | 201; JSON body `{"name":"Ana"}` returns index 3 |

Run local tests:

```bash
python -m unittest discover -s tests -v
```

## Important boundaries

- Here, `id` means a zero-based position in a Python list, **not** a durable database identifier.
- Data is stored in memory; restarting the server resets changes.
- No database, authentication, BLL/DAL, or TECHREG-specific logic has been added. This exercise is intended to teach GET, POST, validation and HTTP errors.

## GitHub placement

The project is archived in `Mircea11/BF_IntegIA_2026/formation/fastapi_corrected/`, alongside other training exercises. The code was uploaded from the previously shared corrected archive; subsequent changes made only on the Ubuntu workstation will require a separate local Git sync.
