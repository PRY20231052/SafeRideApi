from api.models.coordinates import Coordinates

class Location:
    def __init__(self, coordinates):
        self.coordinates = coordinates

        self.name = ""
        self.address = ""