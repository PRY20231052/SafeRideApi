from rest_framework import serializers
from api.models.edge import Edge
from api.models.location import Location
from api.serializers.location_serializer import LocationSerializer

class EdgeSerializer(serializers.Serializer):
    source = LocationSerializer()
    target = LocationSerializer()
    attributes = serializers.DictField()

    def create(self, data):
        source = Location(**data.pop('source'))
        target = Location(**data.pop('target'))
        attributes = data.pop('attributes')
        return Edge(source, target, attributes)