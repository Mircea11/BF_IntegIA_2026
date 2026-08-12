class Personne:
    def __init__(self, id, nom, prenom):
        self.id = id
        self.nom = nom
        self.prenom = prenom

if __name__ == "__main__":
            

    class Client:
        id = 0
        nom = "nom"
        prenom = "John"

        def afficher_personne(self):
            print(f"Personne ID : {self.id}")
            print(f"Titulaire : {self.prenom} {self.nom}")
        
        
        

    class   CompteCourant:
        def __init__(self, numero, titulaire, sold = 0):
            self.numero = numero
            self.titulaire = titulaire
            self.solde = sold
    # Ajoutez, un constructeur prenant en paramètre : 
    # 	- Le numéro, le titulaire ,le solde
        # def __init__(self, numero, titulaire, solde):
        #     self.numero = numero
        #     self.titulaire = titulaire
        #     self.solde = solde
    #Comportement:
        def Retrait(self,somme):
            if somme <0:
                print("Somme doive pas etre negative")
            else:
                self.solde -= somme

        def Depot(self, somme):
            if somme <0:
                print("Somme doive pas etre negative")
            elif self.solde <somme:
                print("Solde insuffisant")
            else:
                self.solde += somme

        def afficher_compte(self):
            print(f"Compte numéro : {self.numero}")
            print(f"Titulaire : {self.titulaire.prenom} {self.titulaire.nom}")
            print(f"Solde : {self.solde}")
        
        
    
    # Contrainte:
    #  - Pas de retrait de somme négative
    #  - Pas de dépot de somme négative
    #  - Retrait ne doit amener à un solde négatif            
    person1 = Personne(1,"Mircea","Bordeianu")
    person2 = Personne(2,"Vlad","Oleatovskii")
    person3 = Personne(3,"Olga","Cojuhari")

    comppte1 = CompteCourant(1000,person1,1000)
    comppte2 = CompteCourant(2000,person2,2000)
    comppte3 = CompteCourant(3000,person3,3000)

    comppte1.afficher_compte()
    comppte1.Depot(500)
    comppte1.afficher_compte()
    comppte1.Retrait(700)
    client1 = Client()

    client2 = Client()
    client2.id, client2.nom, client2.prenom = 1,"Mircea","Bordeianu"
    print('_'*50)
    client2.afficher_personne()

    print(client2.id)