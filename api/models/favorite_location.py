from api.models.custom_user import CustomUser
from api.models.location import Location
from django.db import models

class FavoriteLocation(Location):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    alias = models.CharField(max_length=255)

    def __str__(self):
        return self.alias