from abc import abstractmethod

class Animal(ABC):
    def __init__(self, nom):
        self.__nom = nom

@abstractmethod
def crier(self):
    pass


if __name__ == "__main__":
    animal = Animal ("Medor")
    print(animal.nom)

 