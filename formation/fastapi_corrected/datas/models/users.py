"""Pydantic model for the POST /user JSON request."""
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=1)
