from api.models.custom_user import CustomUser
from api.models.location import Location
from django.db import models

class FavoriteLocation(Location):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    alias = models.CharField(max_length=255)

    def __init__(self, coordinates, user, name, address, alias):
        # Llama al constructor de la clase base (Location)
        super().__init__(coordinates=coordinates, name=name, address=address)
        
        # Asigna el usuario, user_id, y alias
        self.user = user
        self.alias = alias

    def __str__(self):
        return self.alias

