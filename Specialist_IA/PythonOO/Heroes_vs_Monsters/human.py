# This file defines the Humain class.
# A human is a hero with +1 Force and +1 Endurance.
# The base values are not modified; only the public properties add the bonus.
from hero import Hero

class Humain(Hero):
    @property
    def force(self):
        return super().force + 1

    @property
    def endurance(self):
        return super().endurance + 1

    def __str__(self):
        return f"Humain FOR={self.force}, END= {self.endurance}, PV={self.pv}/{self.pv_max}"
    
    