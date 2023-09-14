from rest_framework import serializers
from api.models.location import Location
from api.models.route import Route
from api.serializers.location_serializer import LocationSerializer

class RouteSerializer(serializers.Serializer):
    # Required data
    origin = LocationSerializer()
    waypoints = LocationSerializer(many=True)

    # Not required data (will be generated by the model)
    departure_time = serializers.DateTimeField(required=False)
    arrival_time = serializers.DateTimeField(required=False)
    distance_meters = serializers.IntegerField(required=False)
    eta_seconds = serializers.IntegerField(required=False)
    path = LocationSerializer(many=True, required=False)
    path_geojson = serializers.DictField(required=False)

    def create(self, data):
        origin_data = data.pop('origin')
        waypoints_data = data.pop('waypoints')

        origin = Location(**origin_data) # unpacks a dictionary and assigns its values to the corresponding parameters
        waypoints = [Location(**waypoint_data) for waypoint_data in waypoints_data]

        return Route(origin=origin, waypoints=waypoints)