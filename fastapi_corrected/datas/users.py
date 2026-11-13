"""20 utilisateurs fictifs fournis pour l'exercice du formateur.

Dates et mots de passe sont des données de démonstration, jamais de vraies
informations personnelles. Les mots de passe sont hachés en mémoire.
"""

from datetime import date

from .models import User
from .security import hash_password


_EXAMPLES = [
    ("Gustave", "Password123!", date(1990, 5, 14)),
    ("Patoche", "Patoche2024#", date(1985, 11, 2)),
    ("Gontrand", "Gontrand_99", date(1992, 3, 21)),
    ("Anastasia", "Ana$tasia88", date(1998, 7, 30)),
    ("Barnabé", "B@rnabe1979", date(1979, 1, 12)),
    ("Clotilde", "CloTilde*42", date(1995, 9, 8)),
    ("Hypolite", "Hypo_Lite77", date(2001, 12, 19)),
    ("Cunégonde", "CuneGonde!1", date(1988, 4, 3)),
    ("Théodule", "TheoDule#65", date(1993, 8, 25)),
    ("Gertrude", "GertRude_00", date(1975, 6, 17)),
    ("Philémon", "PhileMon2023$", date(1999, 2, 14)),
    ("Zéphirin", "ZephiRin*91", date(1991, 10, 29)),
    ("Pétronille", "PetroNille!8", date(1983, 7, 11)),
    ("Archibald", "ArchiBald#34", date(1996, 11, 5)),
    ("Bérénice", "BereNice_56", date(2000, 3, 28)),
    ("Léopold", "LeoPold2022!", date(1987, 9, 16)),
    ("Séraphine", "SeraPhine$12", date(1994, 5, 22)),
    ("Balthazar", "BalthaZar*78", date(1981, 12, 4)),
    ("Apolline", "ApolLine_33", date(2002, 8, 9)),
    ("Maximilien", "MaxiMilien!9", date(1989, 1, 27)),
]

users: list[User] = [
    User(name=name, birthdate=birthdate, password_hash=hash_password(password))
    for name, password, birthdate in _EXAMPLES
]
