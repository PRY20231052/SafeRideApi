from datetime import date
from rest_framework import viewsets
from rest_framework.response import Response
from api.models.edge import Edge
from api.models.location import Location
from api.models.path import Path
from api.models.coordinates import Coordinates
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
                origin_latlon=(route.origin.coordinates.latitude, route.origin.coordinates.longitude),
                destination_latlon=(route.waypoints[-1].coordinates.latitude, route.waypoints[-1].coordinates.longitude),
            )

            # TODO: implement model computation of the route
            generated_path = env.shortest_path
            paths = [generated_path]
            
            avg_km_s = 18
            for path in paths:
                path_edges = []
                distance = 0
                # arrival_time = None
                for edge, attr in zip(path_to_edges(generated_path), get_path_edges_attrs(env.graph, generated_path)):
                    distance+=attr['length']
                    coords_src = get_node_coordinates(env.graph, edge[0])
                    coords_trg = get_node_coordinates(env.graph, edge[1])

                    if 'geometry' in attr: attr.pop('geometry') #######

                    path_edges.append(
                        Edge(
                            source=Coordinates(latitude=coords_src[0], longitude=coords_src[1]),
                            target=Coordinates(latitude=coords_trg[0], longitude=coords_trg[1]),
                            attributes=attr
                        )
                    )
                route.paths.append(
                    Path(
                        nodes=[
                            Coordinates(
                                latitude=env.graph.nodes[node]['y'],
                                longitude=env.graph.nodes[node]['x'],
                            ) for node in path
                        ],
                        edges=path_edges,
                        polyline_points=[
                            Coordinates(
                                latitude=point[0],
                                longitude=point[1],
                            ) for point in get_route_polyline_coordinates(env.graph, path)
                        ],
                        distance_meters=distance,
                        eta_seconds=distance/(avg_km_s*1000/3600) #converting to m/s,
                    )
                )

            route.paths_geojson = get_routes_as_geojson(env.graph, paths)
            
            # the serializer variable saves every change done to the route instance
            return Response(serializer.data, status=201) # 201 means CREATED, while 200 only means OK
        return Response(serializer.errors, status=400)