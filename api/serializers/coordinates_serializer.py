from rest_framework import serializers
from api.models.coordinates import Coordinates

class CoordinatesSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()

    def create(self, data):
        return Coordinates(**data)