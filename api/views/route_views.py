from datetime import date
from rest_framework import viewsets
from rest_framework.response import Response
from api.models.direction import Direction
from api.models.edge import Edge
from api.models.location import Location
from api.models.path import Path
from api.models.coordinates import Coordinates
from api.serializers.route_serializer import RouteSerializer
from rest_framework.permissions import IsAuthenticated
from bike_router_ai.agent import Agent
from bike_router_ai.graph_utils import *
import os
import copy

base_agent = Agent()

class RouteViewSet(viewsets.ViewSet):

    permission_classes = ()

    serializer_class = RouteSerializer
    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        
        if serializer.is_valid():
            # since we don't need data persistance,
            # save() will only return the serialized entity
            route = serializer.save()  

            print('\nComputing route...')
            agent = copy.deepcopy(base_agent)

            predicted_path, dijkstra_path = agent.predict_route(
                origin_latlon=(route.origin.coordinates.latitude, route.origin.coordinates.longitude),
                destination_latlon=(route.waypoints[-1].coordinates.latitude, route.waypoints[-1].coordinates.longitude),
            )

            paths = [predicted_path, dijkstra_path]
            graph = agent.env.unwrapped.graph
            
            avg_km_s = 18
            for path in paths:
                path_edges = []
                distance = 0
                # arrival_time = None
                for edge, attr in zip(path_to_edges(path), get_path_edges_attrs(graph, path)):
                    distance+=attr['length']
                    coords_src = get_node_coordinates(graph, edge[0])
                    coords_trg = get_node_coordinates(graph, edge[1])

                    path_edges.append(
                        Edge(
                            source=Coordinates(latitude=coords_src[0], longitude=coords_src[1]),
                            target=Coordinates(latitude=coords_trg[0], longitude=coords_trg[1]),
                            attributes={k:v for k,v in attr.items() if 'geometry' not in attr}
                            # this copies the keys and values of the dict if they meet the criteria
                        )
                    )
                directions = [Direction(**direction) for direction in generate_route_directions(graph, path)]
                print('\nAFTER SERIALIZATION')
                for dire in directions:
                    print(f'covered_edges_indexes {dire.covered_edges_indexes}')
                    print(f'covered_polyline_points_indexes {dire.covered_polyline_points_indexes}')
                route.paths.append(
                    Path(
                        nodes=[
                            Coordinates(
                                latitude=graph.nodes[node]['y'],
                                longitude=graph.nodes[node]['x'],
                            ) for node in path
                        ],
                        edges=path_edges,
                        directions=directions,
                        polyline_points=[
                            Coordinates(
                                latitude=point[0],
                                longitude=point[1],
                            ) for point in get_route_polyline_coordinates(graph, path)
                        ],
                        distance_meters=distance,
                        eta_seconds=distance/(avg_km_s*1000/3600) #converting to m/s,
                    )
                )

            route.paths_geojson = get_routes_as_geojson(graph, paths)
            
            # the serializer variable saves every change done to the route instance
            return Response(serializer.data, status=201) # 201 means CREATED, while 200 only means OK
        return Response(serializer.errors, status=400)