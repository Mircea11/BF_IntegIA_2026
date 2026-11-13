"""Exercice FastAPI : utilisateurs, mots de passe et appel à un LLM local."""

import os

import httpx
from fastapi import FastAPI, HTTPException, Query, status

from datas import users
from datas.models import User, UserCreate, UserRead, UserUpdateName, UserUpdatePassword
from datas.security import hash_password, verify_password

app = FastAPI(title="FastAPI Formation")


def existing_user(id: int) -> User:
    """Ici, l'ID est une position dans la liste (0, 1, 2, ...)."""
    if id < 0 or id >= len(users):
        raise HTTPException(status_code=404, detail="User not found")
    return users[id]


@app.get("/")
def home():
    return {"message": "FastAPI is running", "documentation": "/docs"}


@app.get("/users", response_model=list[UserRead])
def get_all_users(limit: int = Query(5, ge=0, le=100), offset: int = Query(0, ge=0)):
    """Renvoie seulement les champs de UserRead (jamais les mots de passe)."""
    return users[offset : offset + limit]


@app.get("/users/{id}", response_model=UserRead, include_in_schema=False)
@app.get("/user/{id}", response_model=UserRead)
def get_user(id: int):
    """GET /users/{id} reste utilisable avec les anciennes requêtes Bruno."""
    return existing_user(id)


@app.post("/user", status_code=status.HTTP_201_CREATED, response_model=int)
def create_user(user: UserCreate):
    new_user = User(
        name=user.name,
        birthdate=user.birthdate,
        password_hash=hash_password(user.password),
    )
    users.append(new_user)
    return len(users) - 1


@app.patch("/user/{id}", response_model=UserRead)
def update_user_name(id: int, update: UserUpdateName):
    user = existing_user(id)
    user.name = update.name
    return user


@app.patch("/user/{id}/password", status_code=status.HTTP_204_NO_CONTENT)
def update_user_password(id: int, update: UserUpdatePassword):
    user = existing_user(id)
    if not verify_password(update.old_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Ancien password incorrect")
    user.password_hash = hash_password(update.new_password)
    return None


@app.delete("/user/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(id: int):
    existing_user(id)
    users.pop(id)
    return None


@app.post("/chat")
async def chat(prompt: str = Query(min_length=1)):
    """Appel à un LLM local, sans RAG. Le modèle doit déjà tourner sur le port 8080."""
    base_url = os.getenv("LLM_BASE_URL", "http://127.0.0.1:8080/v1").rstrip("/")
    model = os.getenv("LLM_MODEL", "local")
    try:
        async with httpx.AsyncClient(timeout=120, trust_env=False) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Local LLM unavailable") from exc

    try:
        reply = response.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail="Invalid local LLM response") from exc
    return {"reply": reply}
