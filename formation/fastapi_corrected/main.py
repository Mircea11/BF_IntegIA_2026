"""A minimal FastAPI training app: GET, POST, validation, and 404 errors."""

from fastapi import FastAPI, HTTPException, status

from datas import users
from datas.models import UserCreate

app = FastAPI(title="FastAPI Formation")


@app.get("/")
def home():
    """A helpful landing endpoint so GET / does not return 404."""
    return {"message": "FastAPI is running", "documentation": "/docs"}


@app.get("/users", response_model=list[str])
def get_all_users():
    """Return the list of names."""
    return users


@app.get("/users/{id}", response_model=str)
def get_user(id: int):
    """Read a user by zero-based list position (0, 1, 2, ...)."""
    if id < 0 or id >= len(users):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return users[id]


@app.post("/user", status_code=status.HTTP_201_CREATED, response_model=int)
def create_user(user: UserCreate):
    """Append a name and return its new zero-based position.

    /user is intentionally kept singular to match the original exercise.
    """
    users.append(user.name)
    return len(users) - 1
