"""Modèles Pydantic : données entrantes, publiques et internes."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def clean_name(value: str) -> str:
    """Accepte les espaces, accents, apostrophes et traits d'union."""
    value = value.strip()
    if len(value) < 2 or not all(
        char.isalpha() or char in " -'’" for char in value
    ):
        raise ValueError("Name must contain at least two letters and valid separators")
    if not any(char.isalpha() for char in value):
        raise ValueError("Name must contain letters")
    return value


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=8, max_length=128)
    validation: str = Field(min_length=8, max_length=128)
    birthdate: date

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return clean_name(value)

    @field_validator("birthdate")
    @classmethod
    def validate_birthdate(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("Birthdate cannot be in the future")
        return value

    @model_validator(mode="after")
    def check_confirmation(self):
        if self.password != self.validation:
            raise ValueError("Password and confirmation do not match")
        return self


class UserRead(BaseModel):
    """Ce modèle est renvoyé par GET/PATCH : aucun mot de passe."""

    model_config = ConfigDict(from_attributes=True)
    name: str
    birthdate: date


class User(BaseModel):
    """Modèle interne : seul le hash est conservé en mémoire."""

    name: str
    birthdate: date
    password_hash: str


class UserUpdateName(BaseModel):
    name: str = Field(min_length=2, max_length=100)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        return clean_name(value)


class UserUpdatePassword(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8, max_length=128)
    validation: str = Field(min_length=8, max_length=128)

    @model_validator(mode="after")
    def check_confirmation(self):
        if self.new_password != self.validation:
            raise ValueError("New password and confirmation do not match")
        return self
