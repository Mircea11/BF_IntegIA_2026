class  SoldeInsuffisantException (Exception):
    def __init__(self, solde):
        super().__init__(f"Solde de {solde} eur est insuffisant")