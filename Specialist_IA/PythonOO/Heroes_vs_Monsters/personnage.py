from de import De
from outils import generer_caracteristique, modificateur

class Personnage:
    def __init__(self):
        self.__force_base = generer_caracteristique()
        self.__endurance_base = generer_caracteristique()

        self.__pv_max = self.endurance + modificateur(self.endurance)
        self.__pv = self.__pv_max
    @property
    def force(self): 
        return self.__force_base

    @property
    def endurance(self):
        return self.__endurance_base

    @property 
    def pv(self):
        return self.__pv

    @property
    def pv_max(self):
        return self.__pv_max



    def frapper (self, cible):
        d4 = De(1,4)
        degats = d4.lance() + modificateur(self.force)

        print(f"{self} frappe {cible}")
        print(f"Dégats : {degats}")

        cible.subir_degats(degats)

    def subir_degats(self, degats):
        self.__pv -= degats

    def est_mort(self):
        return self.pv <=0

    def se_reposer(self):
        self.__pv = self.__pv_max

    def __str__(self):
        return f"Personnage FOR={self.force}, END={self.endurance}, PV={self.pv}/{self.pv_max}"
        
