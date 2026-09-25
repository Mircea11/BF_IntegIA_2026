from Specialist_IA.PythonOO.Car_class.bateau import Bateau
from Specialist_IA.PythonOO.Car_class.voiture import Voiture

class VoitureAmphibie(Voiture, Bateau):
    def __init__(self, nb_roue, couleur, tirant_eau):
        print(VoitureAmphibie.__mro__)
        super().__init__(nb_roue, couleur)
        Voiture.__init__(self,nb_roue,couleur)
        Bateau.__init__(self, couleur, tirant_eau)
        self.vitesse = 0
        # self.couleur = couleur
        # self.nb_roue = nb_roue
        self.tirant_eau = tirant_eau

    def accelerer(self, est_sur_eau, acceleration=50):
        if est_sur_eau:
            Bateau.accelerer(self,self.acceleration)
                        #Methode d'aceleration du bateau
        else: 
            Voiture.accelerer(self,self.acceleration)
            return super().accelerer(acceleration)
    def __str__(self):
         return Voiture.__str__(self)

    
if __name__ == "__main__":
    voiture_amphibie = VoitureAmphibie(4,"bleu",0.5)
def __str__(self):
        print(f"C'est un bateau :{voiture_amphibie}")
print("_"*50)
print("_"*50)
print(voiture_amphibie.couleur)
print("_"*50)
print(VoitureAmphibie.__mro__)
print("_"*50)
print(voiture_amphibie)