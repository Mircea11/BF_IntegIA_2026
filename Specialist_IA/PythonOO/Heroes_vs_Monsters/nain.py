# This file defines the Nain class.
# A dwarf is a hero with +2 Endurance.
# The base endurance is not modified; only the public property adds the bonus.

from hero import Hero


class Nain(Hero):
    @property
    def endurance(self):
        return super().endurance + 2

    def __str__(self):
        return f"Nain FOR={self.force}, END={self.endurance}, PV={self.pv}/{self.pv_max}"