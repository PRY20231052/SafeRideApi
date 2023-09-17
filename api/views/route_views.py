from datetime import date
from rest_framework import viewsets
from rest_framework.response import Response
from api.models.location import Location
from api.serializers.location_serializer import LocationSerializer
from api.serializers.route_serializer import RouteSerializer
from bike_router_ai.bike_router_env import BikeRouterEnv
from bike_router_ai import bike_maps as bm
import os
import copy

# Initializing the Env
base_env = BikeRouterEnv(
    graphml_path=f'{os.getcwd()}/bike_router_ai/graph_SB_SI_w_cycleways.graphml',
    crime_data_excel_path=f'{os.getcwd()}/bike_router_ai/criminal_data.xlsx',
)

class RouteViewSet(viewsets.ViewSet):

    serializer_class = RouteSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            route = serializer.save()  # since we don't need data persistance, save() will only return the serialized entity

            print('\nComputing route...')

            env = copy.deepcopy(base_env)
            env.set_origin_and_destination(
                origin_latlon=(route.origin.latitude, route.origin.longitude),
                destination_latlon=(route.waypoints[-1].latitude, route.waypoints[-1].longitude),
            )

            # TODO: implement model computation of the route
            # route.arrival_time = None
            # route.distance_meters = 0
            # route.eta_seconds = 0
            
            route.path = [Location(
                latitude=env.graph.nodes[node]['y'],
                longitude=env.graph.nodes[node]['x'],
            ) for node in env.shortest_path]
            route.path_geojson = bm.get_routes_as_geojson(env.graph, [env.shortest_path])

            # the serializer variable saves every change done to the route instance
            return Response(serializer.data, status=201) # 201 means CREATED, while 200 only means OK
        return Response(serializer.errors, status=400)