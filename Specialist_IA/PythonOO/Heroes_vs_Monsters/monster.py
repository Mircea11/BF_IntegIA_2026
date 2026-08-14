# This file defines the parent class for all monsters.
# A monster is a Personnage with possible loot: gold and leather.

from personnage import Personnage

class Monster(Personnage):
    def __init__(self):
          # Reuse the initialization of Personnage: force, endurance, pv.
        super().__init__()
               # By default, a monster has no gold and no leather.
        self.__aur = 0
        self.__cuir = 0
        @property 
        def aur(self):
             # Read-only access to the monster's gold.
        # We use aur because "or" is a Python keyword.
            return self.__aur

        @property 
        def cuir_(self):
                     # Read-only access to the monster's gold.
                # We use aur  because "or" is a Python keyword.
            return self.__cuir
    
