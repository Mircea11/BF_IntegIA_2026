# UpperCamelCase | PascalCase : convention de noammage
# sans espace 
# chaque mot commence par une majuscule
class Voiture:
    # attribut lié à la classe
    dernier_id = 1

    # constructeur de la classe: 
    # définir les valeurs des attributs de l'instance
    def __init__(self, nb_roue, couleur = 'blanc'):
        # attribut lié à une instance propre
        self.id = Voiture.dernier_id
        Voiture.dernier_id += 1

        self.nb_roue = nb_roue
        self.couleur = couleur
        self.vitesse = 0

    # mon_instance.accelerer(50) ou mon_instance.accelerer()
    def accelerer(self, acceleration = 50):
        self.vitesse += acceleration

    def deccelerer(self, decceleration = 50):
        self.vitesse -= decceleration

    def klaxoner (self):
        print("Tut tut")



print(f"depuis Voiture : {__name__}")
# permet l'éxécution de ce bloc uniquement 
# si ce fichier est le fichier de lancement
# __name__ est un attribut fixé lors du lancement du fichier
#  si ce fichier est lancé, __name__ vaudra __main__
if __name__ == "__main__":
    # instance
    # fstring | interpolation : format de texte à afficher
    voiture_blanche = Voiture(4)
    voiture_blanche.klaxoner()
    print(Voiture.dernier_id, voiture_blanche.dernier_id)
    print(f"voiture {voiture_blanche.id} {voiture_blanche.couleur} {voiture_blanche.nb_roue}")
    print("voiture "+str(voiture_blanche.id)+" "+voiture_blanche.couleur+" "+str(voiture_blanche.nb_roue))

    voiture_rouge = Voiture(4, 'rouge')
    print(Voiture.dernier_id, voiture_blanche.dernier_id, voiture_rouge.dernier_id)
    print(f"voiture {voiture_rouge.id} {voiture_rouge.couleur} {voiture_rouge.nb_roue}")