from rest_framework import serializers
from api.models.coordinates import Coordinates
from api.models.edge import Edge
from api.serializers.coordinates_serializer import CoordinatesSerializer

class EdgeSerializer(serializers.Serializer):
    source = CoordinatesSerializer()
    target = CoordinatesSerializer()
    attributes = serializers.DictField()

    def create(self, data):
        return Edge(
            source=CoordinatesSerializer().create(data.pop('source')),
            target=CoordinatesSerializer().create(data.pop('target')),
            attributes=data.pop('attributes')
        )