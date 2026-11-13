"""Pydantic model for the POST /user JSON request."""
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import date


class UserCreate(BaseModel):
    name: str | None= Field(min_length=2, pattern="^[a-zA-Z]+$", description="User name must contain only letters and be at least 2 characters long.")
    password: str
    validation: str
    birthday: date

    @field_validator("password")
    def check_password(cls, v: str):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long.")
        return v

    @model_validator(mode="after")
    def check_confirmation(self):
        if self.password != self.validation:
            raise ValueError("Password and validation do not match.")
        return self;

class UserRead(BaseModel):
    name: str
    password: str
    birthday: date

class UserUpdate(BaseModel):
    name: str = Field(min_length=1)


class User(BaseModel):
    name: str
    password: str
    birthday: date


class UserUpdatePassword(BaseModel):
    old_password: str = Field(min_length=8)
    password: str = Field(min_length=8)     
    validation: str = Field(min_length=8)

    @model_validator(mode="after")
    def check_confirmation(self):
        if self.password != self.validation:
            raise ValueError("Password and validation do not match.")
        return self