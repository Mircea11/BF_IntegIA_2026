class  SoldeInsuffisantException (Exception):
    def __init__(self, sold):
        super().__init__(f"Solde de {solde} eur est insuffisant")