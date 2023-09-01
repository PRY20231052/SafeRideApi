from rest_framework import serializers
from api.models.location import Location

class LocationSerializer(serializers.Serializer):
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    address = serializers.CharField(max_length=100, required=False)

    def create(self, validated_data):
        return Location(**validated_data)
