from animal import Animal
from abc import abstractmethod

class Chien(Animal):
    def crier(self):
        return "aboyer"

    @abstractmethod
    def promener(self)
    
    pass


if __name__ == "__main__":
    chien = Chien ("Medor")
    print(chien.nom)
    