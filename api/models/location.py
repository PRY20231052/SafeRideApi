from api.models.coordinates import Coordinates

class Location:
    def _init_(self, coordinates, name="", address=""):
        self.coordinates = coordinates
        self.name = name
        self.address = address