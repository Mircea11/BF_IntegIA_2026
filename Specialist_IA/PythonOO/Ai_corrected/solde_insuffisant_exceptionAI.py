class SoldeInsuffisantException(Exception):
    def __init__(self, solde):
        super().__init__(f"Solde insuffisant. Solde actuel : {solde} EUR")
        self.solde = solde
