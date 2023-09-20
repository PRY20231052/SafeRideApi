import os
from rest_framework import viewsets
from rest_framework.response import Response
from api.serializers.trip_serializer import TripSerializer
from rest_framework.permissions import IsAuthenticated
from bike_router_ai.bike_router_env import BikeRouterEnv
from bike_router_ai.graph_utils import *

class TripViewSet(viewsets.ViewSet):

    serializer_class = TripSerializer
    permission_classes = ()

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            trip = serializer.save()  # since we don't need data persistance, save() will only return the serialized entity
            print('\nComputing routes for trip...')
            # ori_latlon = (-12.10161732961656, -77.00394302315615)
            # dest_latlon = (-12.106505040854119, -76.99688661904237)

            env = BikeRouterEnv(
                graphml_path=f'{os.getcwd()}/bike_router_ai/city_graph.graphml',
                origin_latlon=(trip.origin.latitude, trip.origin.longitude),
                destination_latlon=(trip.waypoints[-1].latitude, trip.waypoints[-1].longitude)
            )
            # TODO: implement model computation of the route
            trip.routes_geojson = get_routes_as_geojson(env.graph, [env.shortest_path])


            # the serializer variable saves every change done to the route instance
            return Response(serializer.data, status=201) # 201 means CREATED, while 200 only means OK
        return Response(serializer.errors, status=400)