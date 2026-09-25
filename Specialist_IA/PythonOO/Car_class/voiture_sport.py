from Specialist_IA.PythonOO.Car_class.voiture import Voiture

class VoitureSport(Voiture):
    def __init__(self, nb_roue, couleur='blanc', a_turbo = False):
        self.a_turbo = a_turbo
        # on appel l'init du parent 
        super().__init__(nb_roue, couleur)
        #super.___init__()
    def accelerer(self, acceleration=100):
        if acceleration <= 50:
            acceleration = 50
        #return 
        super().accelerer(acceleration)

    
if __name__ == "__main__":
    voiture_sport = VoitureSport(4)
    print(voiture_sport.id, voiture_sport.nb_roue)
    print("_"*50)

    print(voiture_sport)
    print("_"*50)
    voiture_sport.accelerer(5)
    print("_"*50)
    print(voiture_sport)
    print("_"*50)
    print("_"*50)

    print(voiture_sport)
    print("_"*50)
#methode de parante
    voiture_sport.deccelerer(55)
    print("_"*50)
    print(voiture_sport)