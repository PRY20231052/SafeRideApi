from rest_framework import serializers
from api.models.edge import Edge
from api.models.path import Path
from api.models.coordinates import Coordinates
from api.serializers.coordinates_serializer import CoordinatesSerializer
from api.serializers.edge_serializer import EdgeSerializer

class PathSerializer(serializers.Serializer):
    nodes = CoordinatesSerializer(many=True)
    edges = EdgeSerializer(many=True)
    polyline_points = CoordinatesSerializer(many=True)
    
    distance_meters = serializers.FloatField()
    eta_seconds = serializers.FloatField()
    arrival_time = serializers.DateTimeField(required=False)

    def create(self, data):
        return Path(
            nodes=[
                CoordinatesSerializer().create(node_data) for node_data in data.pop('nodes')
            ],
            edges=[
                EdgeSerializer().create(edge_data) for edge_data in data.pop('edges')
            ],
            polyline_points=[
                CoordinatesSerializer().create(point_data) for point_data in data.pop('polyline_points')
            ],
            **data
        )