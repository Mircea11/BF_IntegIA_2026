# This file defines the Loup class.
# A wolf is a monster that gives leather but no gold.

from de import De
from monster import Monster

class Loup(Monster):
    def __init__(self):
        # Initialize common monster data.
        super().__init__()

        # Wolf leather is calculated with one d4.
        d4 = De(1, 4)
        self.definir_cuir(d4.lance())

    def __str__(self):
        # Display the wolf.
        return f"Loup FOR={self.force}, END={self.endurance}, PV={self.pv}/{self.pv_max}, Cuir={self.cuir}"