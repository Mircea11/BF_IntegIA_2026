


"""FastAPI training application: GET, POST, PUT and error handling."""

from fastapi import FastAPI, HTTPException, status

from datas import users
from datas.models import UserCreate, UserRead, UserUpdate, UserUpdatePassword

app = FastAPI(title="FastAPI Formation")


# 1. HOME
@app.get("/")
def home():
    return {
        "message": "FastAPI is running",
        "documentation": "/docs"
    }


# 2. GET ALL USERS
@app.get("/users", response_model=list[UserRead])
def get_all_users(limit: int = 3, offset: int = 0):
    """Return users with pagination."""
    return users[offset:offset + limit]


# 3. GET ONE USER
@app.get("/users/{id}", response_model=UserRead)
def get_user(id: int):
    """Find a user by ID."""

    if id < 0 or id >= len(users):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return users[id]


# 4. CREATE USER
@app.post("/user", status_code=201, response_model=int)
def create_user(user: UserCreate):
    """Create a new user."""

    new_user = UserRead(name=user.name)

    users.append(new_user)

    return len(users) - 1


# 5. UPDATE USER
@app.put("/users/{id}", response_model=UserRead)
def update_user(id: int, user: UserCreate):
    """Update an existing user by ID."""

    if id < 0 or id >= len(users):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    users[id] = UserRead(name=user.name)

    return users[id]

@app.delete("/users/{id}", status_code=204)
def delete_user(id: int):
    """Delete a user by ID."""

    if id < 0 or id >= len(users):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    users.pop(id) 
    return {"message": "User deleted successfully"}


@app.post("/chat")
async def chat(prompt: str):
    async with httpx.AsyncClient(timeout=120) as client:
        r= await client.post(
            "https://api.openai.com/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": prompt}]
            })
     return {"reply": r.json()["choices"][0]["message"]["content"]
         
     }   
        
                # lancer dans dockers, 
                # une modalite de verifie si auqune informations sensible n'est pas envoyee,
                #  et que le prompt est comforme a la politique de l'entreprise,
                