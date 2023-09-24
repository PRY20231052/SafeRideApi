from datetime import date
from rest_framework import viewsets
from rest_framework.response import Response
from api.models.edge import Edge
from api.models.location import Location
from api.serializers.location_serializer import LocationSerializer
from api.serializers.route_serializer import RouteSerializer
from rest_framework.permissions import IsAuthenticated
from bike_router_ai.bike_router_env import BikeRouterEnv
from bike_router_ai.graph_utils import *
import os
import copy

# Initializing the Env
base_env = BikeRouterEnv(
    graphml_path=f'{os.getcwd()}/bike_router_ai/graph_SB_SI_w_cycleways_simplified.graphml',
    crime_data_excel_path=f'{os.getcwd()}/bike_router_ai/criminal_data.xlsx',
)

class RouteViewSet(viewsets.ViewSet):

    serializer_class = RouteSerializer
    permission_classes = ()

    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            # since we don't need data persistance,
            # save() will only return the serialized entity
            route = serializer.save()  

            print('\nComputing route...')
            env = copy.deepcopy(base_env)
            env.set_origin_and_destination(
                origin_latlon=(route.origin.latitude, route.origin.longitude),
                destination_latlon=(route.waypoints[-1].latitude, route.waypoints[-1].longitude),
            )

            # TODO: implement model computation of the route
            generated_path = env.shortest_path
            route.path_geojson = get_routes_as_geojson(env.graph, [generated_path])
            
            route.path_edges = []
            edges = path_to_edges(generated_path)
            attrs = get_path_edges_attrs(env.graph, generated_path)
            for edge, attr in zip(edges, attrs):
                # print(attr['length'])
                # print(type(attr['length']))
                route.distance_meters+=attr['length']
                coords_0 = get_node_coordinates(env.graph, edge[0])
                coords_1 = get_node_coordinates(env.graph, edge[1])
                source = Location(latitude=coords_0[0], longitude=coords_0[1])
                target = Location(latitude=coords_1[0], longitude=coords_1[1])
                if 'geometry' in attr: attr.pop('geometry') #######
                route.path_edges.append(Edge(source=source, target=target, attributes=attr))

            route.path_nodes = [
                Location(
                    latitude=env.graph.nodes[node]['y'],
                    longitude=env.graph.nodes[node]['x'],
                ) for node in generated_path
            ]
            
            avg_km_s = 18
            route.eta_seconds = route.distance_meters/(avg_km_s*1000/3600) #converting to m/s
            # route.arrival_time = None
            
            # the serializer variable saves every change done to the route instance
            return Response(serializer.data, status=201) # 201 means CREATED, while 200 only means OK
        return Response(serializer.errors, status=400)