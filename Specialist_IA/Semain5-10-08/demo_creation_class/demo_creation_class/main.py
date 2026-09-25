from voiture import Voiture

voiture_bleue = Voiture(4,'bleu')

print(f"voiture {voiture_bleue.id} {voiture_bleue.couleur} {voiture_bleue.nb_roue}")
print(voiture_bleue.klaxoner)

print(voiture_bleue.vitesse)
voiture_bleue.accelerer()
print(voiture_bleue.vitesse)

print(f"depuis main : {__name__}")


