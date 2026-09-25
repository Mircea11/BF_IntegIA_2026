class Personne:
    def __init__(self, id: int, nom: str, prenom: str):
        self.id = id
        self.nom = nom
        self.prenom = prenom

if __name__ == "__main__":
    john_doe = Personne(1, "Doe", "John")
    print(john_doe.prenom)