"""Hachage et vérification de mots de passe avec Argon2."""

from pwdlib import PasswordHash

password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, stored_hash: str) -> bool:
    return password_hasher.verify(password, stored_hash)
