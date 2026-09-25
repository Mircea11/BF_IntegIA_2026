from random import randint


class De:
    def __init__ (self, minimum : int, maximum : int):
        if minimum > maximum:
            raise ValueError("Le minimum ne peut pas être supérieur au maximum")

 
        self.__minimum = minimum
        self.__maximum = maximum

    @property
    def minimum(self):
        return self.__minimum

    @property
    def maximum(self):
        return self.__maximum

    def lance(self):
        return randint(self.minimum, self.maximum)
    