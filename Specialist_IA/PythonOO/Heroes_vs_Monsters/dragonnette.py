# This file defines the Dragonnet class.
# A dragonnet has +1 Endurance, gold, and leather.

from de import De
from monster import Monster


class Dragonnette(Monster):
    def __init__(self):
        # Initialize common monster data.
        super().__init__()

        # Dragonnet gold is calculated with one d6.
        d6 = De(1, 6)
        self.definir_or(d6.lance())

        # Dragonnet leather is calculated with one d4.
        d4 = De(1, 4)
        self.definir_cuir(d4.lance())

    @property
    def endurance(self):
        # Dragonnet bonus: effective endurance = base endurance + 1.
        # The base endurance itself is not modified.
        return super().endurance + 1

    def __str__(self):
        # Display the dragonnet.
        return f"Dragonnet FOR={self.force}, END={self.endurance}, PV={self.pv}/{self.pv_max}, Or={self.or_}, Cuir={self.cuir}"