from rest_framework import viewsets
from rest_framework.response import Response
from api.serializers.route_serializer import RouteSerializer
from bike_router_ai.bike_router_env import BikeRouterEnv
from bike_router_ai import bike_maps as bm
import os

class RouteViewSet(viewsets.ViewSet):

    serializer_class = RouteSerializer

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            route = serializer.save()  # since we don't need data persistance, save() will only return the serialized entity
            print('\nComputing route...')
            # ori_latlon = (-12.10161732961656, -77.00394302315615)
            # dest_latlon = (-12.106505040854119, -76.99688661904237)

            env = BikeRouterEnv(
                graphml_path=f'{os.getcwd()}/bike_router_ai/city_graph.graphml',
                origin_latlon=(route.origin.latitude, route.origin.longitude),
                destination_latlon=(route.waypoints[-1].latitude, route.waypoints[-1].longitude)
            )
            # TODO: implement model computation of the route
            route.path_geojson = bm.get_routes_as_geojson(env.graph, [env.shortest_path])

            # the serializer variable saves every change done to the route instance
            return Response(serializer.data, status=201) # 201 means CREATED, while 200 only means OK
        return Response(serializer.errors, status=400)