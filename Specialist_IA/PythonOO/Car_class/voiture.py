# UpperCamelCase : sans espace
# et chaque mot commence par une majuscule
#fishier une minuscule san charactere spciale
from Specialist_IA.PythonOO.Car_class.nombre_roue_exception import NombreRoueException

class Voiture:
    # atttribut lié a la class 
    dernier_id=1
    # constructeur de la claae: definir les valeurs des attributs de l'instance
    def __init__(self, nb_roue, couleur='blanc'):
        self.id = Voiture.dernier_id
        Voiture.dernier_id +=1
        self.nb_roue = nb_roue
        self.couleur = couleur
        self.vitesse = 20

    @property
    def nb_roue(self):
         return self.__nb_roue


    @nb_roue.setter
    def nb_roue(self, nb_roue):
        print(nb_roue, "ici")
        if nb_roue < 0:
            raise NombreRoueException(nb_roue)
        else:
             self.__nb_roue = nb_roue


#mon_instance.accelerer(50)
    def accelerer(self, acceleration = 50):
            if acceleration < 0:
                 print( "pas d'acceleration négative")
            self.vitesse += acceleration

    def deccelerer(self, decceleration = 50):
            self.vitesse -= decceleration

    def klaxoner (self):
        print("Tut tut")

    def __str__(self):
     return f"voiture {self.id} {self.couleur} {self.nb_roue} {self.vitesse}"

    #resultat = voiture - other
    def __sub__(self, other:int):
        print(other, "depui sub")
        try:
            self.nb_roue -= other
        except NombreRoueException as exception:
             raise exception
        #finally:
        return self.nb_roue

    def __isup__(self, other):
         pass
         



print(f"depuit Voiture Python : {__name__}")
# permet l'execution de ce bloc uniquement 
# si ce fichier est le fichier de lancement
#__name__ est un attribut fixé lors du lancement du fichier
#si ce fichier est lancé

if __name__ == "__main__":

    #instance
    voiture_blanche = Voiture(4)
    # fstring | interpolation : format de texte a afficher
    print(Voiture.dernier_id, voiture_blanche.dernier_id)
    print(f"voiture {voiture_blanche.vitesse} {voiture_blanche.id} {voiture_blanche.couleur} {voiture_blanche.nb_roue}")
    #voiture_blanche = Voiture(3)
    print("voiture "+str(voiture_blanche.id) +" "+voiture_blanche.couleur+" "+str(voiture_blanche.nb_roue))
    voiture_rouge = Voiture(4, "rouge")
    voiture_rouge.vitesse = 30
    print(voiture_rouge.vitesse)
    #voiture_rouge.couleur = "rouge" pas ecessair du moment que il est dans la cosntructin de class
    print(Voiture.dernier_id,voiture_blanche.dernier_id, voiture_rouge.dernier_id)
    print(f"voiture {voiture_rouge.id} {voiture_rouge.couleur} {voiture_rouge.nb_roue} {voiture_rouge.vitesse}")
    print("_"*50)
    print(voiture_rouge)
    print(voiture_blanche)
    try:
        print(voiture_blanche-2)
        #voiture_bleue.nb_roue
    except NombreRoueException as exception:
         print(exception)
    print(f"depuis main : {__name__}")
    


     