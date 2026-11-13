from datas.models import UserRead
from typing import cast
from models import UserRead, UserCreate, UserUpdate, UserUpdatePassword

"""Simple in-memory dataset for the instructor's exercise."""

users : list[UserRead]= cast(list[UserRead],
[
   {"name": "John Doe"},
   {"name": "Jane Smith"},
   {"name": "Bob Johnson"},
]
)