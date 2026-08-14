class NombreRoueException (Exception):
    def __init__(self, nombre_roue):
        super().__init__(f"{nombre_roue} n'est pas un nombre de roue valide!")
        
