from Specialist_IA.PythonOO.Car_class.voiture import Voiture

#def test (param1, param2, param3:int = 0, param4:str = "blanc", param5 = True):
#    print(param1, param2, param3, param4, param5)

voiture_bleue = Voiture(4)
voiture_bleue.couleur = 'bleu'
print(f"voiture {voiture_bleue.couleur} {voiture_bleue.nb_roue}")
print(voiture_bleue.vitesse)
voiture_bleue.accelerer()
print(voiture_bleue.vitesse)

print(f"depuit main : {__name__}")

#test("John", "Doe", param4="rouge")
voiture_bleue.klaxoner()