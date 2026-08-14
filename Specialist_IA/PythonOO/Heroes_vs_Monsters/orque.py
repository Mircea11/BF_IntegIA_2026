# This file defines the Orque class.
# An orc is a monster with +1 Force and gold.

from de import De
from monster import Monster


class Orque(Monster):
    def __init__(self):
        # Initialize common monster data.
        super().__init__()

        # Orc gold is calculated with one d6.
        d6 = De(1, 6)
        self.definir_or(d6.lance())

    @property
    def force(self):
        # Orc bonus: effective force = base force + 1.
        # The base force itself is not modified.
        return super().force + 1

    def __str__(self):
        # Display the orc.
        return f"Orque FOR={self.force}, END={self.endurance}, PV={self.pv}/{self.pv_max}, Or={self.or_}"