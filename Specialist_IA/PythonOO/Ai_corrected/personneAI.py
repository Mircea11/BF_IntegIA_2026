class Personne:
    def __init__(self, id: int, nom: str, prenom: str):
        self.id = id
        self.nom = nom
        self.prenom = prenom

    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"

    def __str__(self):
        return self.nom_complet
