from rest_framework import serializers
from api.models.coordinates import Coordinates
from api.models.location import Location
from api.serializers.coordinates_serializer import CoordinatesSerializer

class LocationSerializer(serializers.Serializer):
    coordinates = CoordinatesSerializer()
    name = serializers.CharField(max_length=100, required=False)
    address = serializers.CharField(max_length=100, required=False)

    def create(self, data):
        return Location(
            coordinates=CoordinatesSerializer().create(data.pop('coordinates'))
        )