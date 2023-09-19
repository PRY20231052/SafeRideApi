import gmaps
import googlemaps
import osmnx as ox
import numpy as np
import math
from shapely.geometry import Point
from shapely.geometry import LineString
from copy import deepcopy

configuration_completed = False
google_maps = None

def configure(google_maps_api_key):
    # Setting API KEY
    gmaps.configure(api_key=google_maps_api_key)
    global google_maps
    google_maps = googlemaps.Client(key=google_maps_api_key)

    global configuration_completed
    configuration_completed = True


def save_graph_to_file(graph, path):
    ox.save_graphml(graph, path)


def load_graph_from_file(path):
    return ox.load_graphml(path)


def get_max_node_neighbors(graph):
    if not configuration_completed: return print('Please call configure() first!')
    max_n = 0
    for node in graph.nodes():
        num_neighbours = len(list(graph.neighbors(node)))
        if num_neighbours > max_n:
            max_n = num_neighbours

    return max_n


def get_distance_between_nodes(graph, node1, node2):
    if not configuration_completed: return print('Please call configure() first!')
    return ox.distance.great_circle_vec(
        graph.nodes[node1]['y'],
        graph.nodes[node1]['x'],
        graph.nodes[node2]['y'],
        graph.nodes[node2]['x']
    )


def calculate_relative_bearing(graph, u, v, ref):
    """
    Calcualtes the relative bearing of edge u,v,
    in reference to the node 'ref'
    Returns and angle in degrees
    """
    if not configuration_completed: return print('Please call configure() first!')
    bearing_u_v = ox.bearing.calculate_bearing(
        graph.nodes[u]['y'],
        graph.nodes[u]['x'],
        graph.nodes[v]['y'],
        graph.nodes[v]['x']
    )
    bearing_u_ref = ox.bearing.calculate_bearing(
        graph.nodes[u]['y'],
        graph.nodes[u]['x'],
        graph.nodes[ref]['y'],
        graph.nodes[ref]['x']
    )
    relative_bearing = bearing_u_v - bearing_u_ref
    relative_bearing = (relative_bearing + 360) % 360
    return relative_bearing


def get_edge_bearing(graph, node1, node2):
    return ox.bearing.calculate_bearing(
        graph.nodes[node1]['y'],
        graph.nodes[node1]['x'],
        graph.nodes[node2]['y'],
        graph.nodes[node2]['x']
    )


def change_nodes_colors_by_groups(graph, nodes_groups, colors_groups, default_color='w'):
    # nodes_groups: contains lists of nodes in groups, each group is meant to be set to a single color
    # colors_groups: contains a list of colors for respective nodes group
    nc = [default_color for n in graph.nodes.items()]
    for i, node in enumerate(graph.nodes):
        for j, group in enumerate(nodes_groups):
            if node in group:
                nc[i] = colors_groups[j]
                break
    return nc


def change_edges_colors_by_groups(graph, edges_groups, colors_groups, default_color='w'):
    assert len(edges_groups) == len(colors_groups), 'Legnth of edge_groups and colors_groups must be the same'
    ec = [default_color for e in graph.edges()]

    i = 0
    for u, v, k in graph.edges(keys=True):
        for j, group in enumerate(edges_groups):
            if (u, v) in group:
                ec[i] = colors_groups[j]
                break
        i += 1
    return ec


def change_edges_colors(graph, edges, color, default_color='w'):
    ec = []
    for u, v, k in graph.edges(keys=True):
        if (u, v) in edges:
            ec.append(color)
        else:
            ec.append(default_color)
    return ec

def path_to_edges(path):
    path_edges = []
    for i, node in enumerate(path):
        if i > 0: path_edges.append((path[i-1], node))
    return path_edges


def plot_graph(graph, highlighted_nodes=[], highlighted_edges=[], path=None, show_neighbors=False, figsize=(15, 15), node_size=15):
    # Drawing the graph bla bla this doc
    
    if show_neighbors == True:
        show_neighbors = [True for hn in highlighted_nodes]
    
    n_groups = []
    n_g_colors = []
    if highlighted_nodes:
        n_groups.append(highlighted_nodes)
        n_g_colors.append('red')

    e_groups = []
    e_g_colors = []
    if highlighted_edges:
        e_groups.append(highlighted_edges)
        e_g_colors.append('red')
    
    if path and len(path) >= 2:
        path_edges = path_to_edges(path)
        e_groups.append(path_edges)
        e_g_colors.append('green')

    if not highlighted_nodes and not highlighted_edges:
        ox.plot_graph(graph, figsize=figsize, node_size=node_size)
        return

    if show_neighbors:
        edges = []
        neighbors = []
        for i, node in enumerate(highlighted_nodes):
            if show_neighbors[i]:
                for neighbor in graph.neighbors(node):
                    neighbors.append(neighbor)
                    edges.append((node, neighbor))
        n_groups.append(neighbors)
        n_g_colors.append('blue')
        e_groups.append(edges)
        e_g_colors.append('yellow')

    # Setting colors, if groups are empty it will return a list with
    # the colors as the default value 'white'
    n_colors = change_nodes_colors_by_groups(graph, n_groups, n_g_colors)
    e_colors = change_edges_colors_by_groups(graph, e_groups, e_g_colors)

    # Plot the graph
    return ox.plot_graph(
        graph,
        figsize=figsize,
        node_size=node_size,
        node_color=n_colors,
        edge_color=e_colors,
        show=False # This won't display the graph through matplotlib.show
    )

def get_node_neighbours(graph, node):
    steps = []
    for neighbor in graph.neighbors(node):
        steps.append(neighbor)
    return steps


def get_node_coordinates(graph, nodes, invert=False):
    """
    node: node or a list of nodes from the graph
    invert: if True, coords will be return as 'lonlat' instead of deafault 'latlon'
    """

    if type(nodes) != type([]): # if nodes isnt a list, so its a single node
        return [graph.nodes[nodes]['x'], graph.nodes[nodes]['y']] if invert else [graph.nodes[nodes]['y'], graph.nodes[nodes]['x']]
    
    coordinates_list = []
    for node in nodes:
        if invert: coords = [graph.nodes[node]['x'], graph.nodes[node]['y']]
        else: coords = [graph.nodes[node]['y'], graph.nodes[node]['x']]
        coordinates_list.append(coords)

    return coordinates_list


def get_distance_between_points(point1, point2, coordinates_format='latlon'):
    if not configuration_completed: return print('Please call configure() first!')
    if coordinates_format == 'latlon':
        return ox.distance.great_circle_vec(
            point1[0],
            point1[1],
            point2[0],
            point2[1]
        )
    elif coordinates_format == 'lonlat':
        return ox.distance.great_circle_vec(
            point1[1],
            point1[0],
            point2[1],
            point2[0]
        )
    else: Exception('Invalid value for parameter `coordinates_format`. Valid formats: "latlon", "lonlat"')

# DEPRECATED
def arrange_points(points, starting_point, coordinates_format='lonlat'):

    """
    DEPRECATED AND INCOMPLETE
    points: list of coordinate points to be arrange in position order
    starting_point: a point inside the points list that's suppoused to be the start of the line, from where the rest of the points follow the line
    coordinates_format: the format of the coordinates of the given points. Can be 'latlon' or 'lonlat'.
    """

    print(f'Points to arrange: {points}')
    distances_matrix = np.zeros((len(points), len(points)))
    
    for i, point1 in enumerate(points):
        for j, point2 in enumerate(points):
            if i != j:
                distance = get_distance_between_points(point1, point2, coordinates_format=coordinates_format)
                distances_matrix[i][j] = distance

    # index = points.index(starting_point)
    # arranged_points = [points[index]]

    # sorted_array = np.sort(distances_matrix[index])
    # print(sorted_array)

    # for i, point1 in enumerate(points):
    #     for j, point2 in enumerate(points):
    #         if i != j:
    #             shortest_distance = distances_matrix[i][j]

    # print(distances_matrix)
    # print('=========================================')

    return points


def get_path_edges_attrs(graph, path):
    edges_attrs = []
    for i in range(len(path)-1):
        attrs = graph[path[i]][path[i+1]][0]
        edges_attrs.append(attrs)
    return edges_attrs


def get_routes_as_geojson(graph, paths:list, invert=False, allow_curves=True):
    """
    graph: a NetworkX Directed Graph of the city
    paths: path or list of paths to display in the map, where each path is a list of node_ids from the provided graph
    invert: if True, coords will be return as 'lonlat' instead of deafault 'latlon'

    Returns a GeoJson data for displaying with GoogleMaps API
    """
    routes_features = []
    for path_index, path in enumerate(paths):
        route_coordinates = []
        for i, node in enumerate(path):
            # if it's not the last node and its edge doesn't has a geometry attr (meaning it's a curved line)
            # The 'geometry' edge attribute refers to the the points (IN LONLAT FORMAT) needed to recreate the curved line,
            # for the lines inside a simplify map
            if allow_curves and i < len(path)-1 and 'geometry' in graph[node][path[i+1]][0]:
                geometry_coords = list(graph[node][path[i+1]][0]['geometry'].coords)

                # SOME TIMES curves are showing in different order
                # Assuming that is not that fucked up and that only thing happening is that
                # they are just in reverse, and not in weird order, this should do the trick

                # if the geometry coords are backwards
                if get_node_coordinates(graph, node, invert=True) == list(geometry_coords[-1]):
                    geometry_coords.reverse()

                # we don't add the last point of the curved since it's the same as the end node of the whole edge
                # Same point that's gonna be added in the next iteration for the next edge
                for j in range(len(geometry_coords)-1):
                    if invert: route_coordinates.append(list(geometry_coords[j]))
                    else: route_coordinates.append([geometry_coords[j][1], geometry_coords[j][0]])

            else:
                route_coordinates.append(get_node_coordinates(graph, node, invert=invert))

        routes_features.append(
            {
                "type": "Feature",
                "id": f"Route_{path_index}",
                "properties": {},
                "geometry": {
                    "type": "LineString",
                    "coordinates": route_coordinates
                }
            }
        )
    return {
        "type": "FeatureCollection",
        "features": routes_features
    }

#Deprecated
def get_routes_geojson_layer(graph, paths, colors, stroke_weight=5, stroke_opacity=1.0):
    
    routes_features = []
    routes_origins = []

    for i, path in enumerate(paths):
        if len(path) >= 2:
            # For some stupid reason, geojson_layer needs the coordinates in LonLat...
            route_coordinates = get_node_coordinates(graph, path, invert=True)
            routes_features.append(
                {
                    "type": "Feature",
                    "id": f"Route_{i}",
                    "properties": {},
                    "geometry": {
                        "type": "LineString",
                        "coordinates": route_coordinates
                    }
                }
            )
        origin_latlon = get_node_coordinates(graph, path[0])
        routes_origins.append(origin_latlon)

    if len(routes_features) > 0:
        # Create a GeoJSON layer from the route collection
        geojson_layer = gmaps.geojson_layer(
            {
                "type": "FeatureCollection",
                "features": routes_features
            },
            stroke_color=colors,
            stroke_weight=stroke_weight,
            stroke_opacity=stroke_opacity
        )
    else:
        geojson_layer = None

    origins_layer = gmaps.symbol_layer(
        routes_origins,
        stroke_color=colors,
        scale=5
    )

    return geojson_layer, origins_layer

def show_routes_in_google_maps_widget(graph, center, paths:list, colors:list=['red'], pinned_nodes:list=[], width=1300, height=800, zoom=15):
    
    # Creating Gmaps Figure
    fig = gmaps.figure(
        center=center,
        zoom_level=zoom,
        layout={'width': f'{width}px', 'height': f'{height}px'}
    )

    geojson_layer, origins_layer = get_routes_geojson_layer(graph, paths, colors)
    pinned_nodes_coordinates = get_node_coordinates(graph, pinned_nodes)

    if geojson_layer: fig.add_layer(geojson_layer)
    if origins_layer: fig.add_layer(origins_layer)

    if pinned_nodes:
        pins_layer = gmaps.marker_layer(pinned_nodes_coordinates)
        fig.add_layer(pins_layer)

    return fig


def plan_path(graph, ori):
    current_node = ori
    path = []
    while current_node != "f":
        path.append(current_node)
        print(f'POSSIBLE STEPS FROM NODE: {current_node}')
        possible_steps = get_node_neighbours(graph, current_node)
        for i, step in enumerate(possible_steps):
            print(f'  [{i}] -> {step}')
        opt = input("Select step: ")
        if opt == 'e': break
        current_node = possible_steps[int(opt)]
    return path

def get_shortest_path(graph, origin, dest):
    return ox.distance.shortest_path(graph, origin, dest)



def get_graph(place=None, center_latlon=None, dist=1000, network_type="walk", simplify=True):
    if not configuration_completed: return print('Please call configure() first!')
    if place:
        graph = ox.graph_from_place(
            place,
            network_type=network_type,
            simplify=simplify
        )
    elif center_latlon:
        graph = ox.graph.graph_from_point(
            center_latlon,
            dist=dist,
            network_type=network_type,
            simplify=simplify
        )

    # Add angle compass information to graph
    graph = ox.bearing.add_edge_bearings(graph)
    return graph


# Calculates the road node closest to the origin coordinates (lat, lon)
def get_nearest_road_coordinates(latlon):
    if not configuration_completed: return print('Please call configure() first!')
    nearest_road = google_maps.snap_to_roads(latlon)
    lat = nearest_road[0]['location']['latitude']
    lon = nearest_road[0]['location']['longitude']
    return (lat, lon)


# Calculates the road node closest to the origin coordinates (lat, lon)
def get_projection_point(target:list, a:list, b:list, coordinates_format='latlon'):
    """
    Given 2 coordinate points (`a` and `b`),
    returns the coordinates of the projection of the 
    point `target` in the vector `a`--->`b`
    """

    if coordinates_format=='lonlat':
        # converting to latlon
        target.reverse()
        a.reverse()
        b.reverse()
    
    point = Point(target) 
    line = LineString((a,b))
    dist = line.project(point) #numpy float
    projected_point = list(line.interpolate(dist).coords)
    projected_point = list(projected_point[0])
    
    return projected_point


def get_point_to_edge_distance(point, edge):
    x, y = point
    edge_start, edge_end = edge
    x1, y1 = edge_start
    x2, y2 = edge_end
    
    # Calculate the coefficients of the line equation ax + by + c = 0
    a = y1 - y2
    b = x2 - x1
    c = (x1 * y2) - (x2 * y1)
    
    # Calculate the perpendicular distance from the point to the line
    return abs((a*x + b*y + c)) / math.sqrt(a**2 + b**2)


def find_nodes_by_attributes(graph, attributes):
    if not configuration_completed: return print('Please call configure() first!')
    matching_nodes = []
    for node in graph.nodes(data=True):
        match_status = False
        # node MUST match all the give attributes values
        for key, value in attributes.items():
            # node[0] corresponds to the ndoe id, node[1] correspondes to the data of the node
            if node[1][key] == value:
                match_status = True
            else:
                match_status = False
        if match_status: matching_nodes.append(node)
    return matching_nodes


def insert_new_node_in_edge(graph, node_id, node_latlon, edge):
    """
    Returns the id of the inserted node and a list of added edges. If a node that matches the coordinates of the node to insert
    then it returns the id of that matching node and and empty list since there was no edges added
    """
    added_edges = []

    # If node already exists in the network then do nothing
    matching_nodes = find_nodes_by_attributes(graph, {'y': node_latlon[0], 'x': node_latlon[1]})
    if matching_nodes:
        print(f"Node already in Network")
        return matching_nodes[0][0], added_edges # Returning the id of the found node

    
    edge_attrs = graph[edge[0]][edge[1]][0]  # Copy edge attributes
    with_geometry = False

    if 'geometry' in edge_attrs:
        with_geometry = True
        # Inside the Geometry we are using LONLAT format for coordinates
        node_lonlat = list(node_latlon)
        node_lonlat.reverse() #to LON LAT

        point = Point(node_lonlat) 

        geometry_coords = list(edge_attrs['geometry'].coords)

        sub_edges = []
        distances = []
        projected_points = []

        for i in range(len(geometry_coords)-1):
            sub_edge = [list(geometry_coords[i]), list(geometry_coords[i+1])]

            # THIS IS HOW YOU PROJECT A POING TO A LINE
            sub_line_string = LineString(sub_edge)
            dist = sub_line_string.project(point) #numpy float
            projected_point = list(sub_line_string.interpolate(dist).coords)
            projected_point = list(projected_point[0])
            
            sub_edges.append(sub_edge)
            distances.append(get_distance_between_points(node_lonlat, projected_point, coordinates_format='lonlat'))
            projected_points.append(projected_point)

            # print(sub_edges[-1], distances[-1], projected_points[-1])

        distances = np.array(distances)
        min_dist_index = np.argmin(distances)
        new_node_lonlat = projected_points[min_dist_index]
        new_node_index = min_dist_index + 1 # we add one becase we are gonna insert this point after the start point of the closest sub edge
        geometry_coords.insert(new_node_index, tuple(new_node_lonlat))
        
        linestring_0_n = LineString(geometry_coords[:new_node_index+1])
        linestring_n_1 = LineString(geometry_coords[new_node_index:])
        linestring_1_n = linestring_n_1.reverse()
        linestring_n_0 = linestring_0_n.reverse()

        node_latlon = new_node_lonlat
        node_latlon.reverse()
        node_latlon = tuple(node_latlon)


    # Adding node
    graph.add_node(node_id, y=node_latlon[0], x=node_latlon[1], street_count=2)

    # Adding new edges
    attributes = {**edge_attrs,
        'length': get_distance_between_nodes(graph, edge[0], node_id),
        'bearing': get_edge_bearing(graph, edge[0], node_id),
    }
    if with_geometry: attributes['geometry'] = linestring_0_n
    graph.add_edge(edge[0], node_id, **attributes)


    attributes = {**edge_attrs,
        'length': get_distance_between_nodes(graph, node_id, edge[1]),
        'bearing': get_edge_bearing(graph, node_id, edge[1]),
    }
    if with_geometry: attributes['geometry'] = linestring_n_1
    graph.add_edge(node_id, edge[1], **attributes)


    added_edges += [(edge[0], node_id), (node_id, edge[1])]

    if edge_attrs['oneway'] == False:  # is the edge bi directional? then add reversed edges
        attributes = {**edge_attrs,
            'length': get_distance_between_nodes(graph, edge[1], node_id),
            'bearing': get_edge_bearing(graph, edge[1], node_id)
        }
        if with_geometry: attributes['geometry'] = linestring_1_n
        graph.add_edge(edge[1], node_id, **attributes)

        attributes = {**
            edge_attrs,
            'length': get_distance_between_nodes(graph, node_id, edge[0]),
            'bearing': get_edge_bearing(graph, node_id, edge[0])
        }
        if with_geometry: attributes['geometry'] = linestring_n_0
        graph.add_edge(node_id, edge[0], **attributes)

        added_edges += [(edge[1], node_id), (node_id, edge[0])]

        graph.remove_edge(edge[1], edge[0])  # Remove original edge from graph

    graph.remove_edge(edge[0], edge[1])  # Remove original edge from graph

    print('INSERTED!')
    return node_id, added_edges


def insert_node_in_graph_v2(graph, node_id, latlon, log=False): 
    # This implementation removes the need of requesting to the Google API
    # for the latitude and longitude of the nearest edge poing (that will be the coordinates of the new nodes)
    # It's 1 second faster
    
    # Getting the nearest edge
    added_edges = []
    nearest_edge = ox.distance.nearest_edges(graph, latlon[1], latlon[0])
    node_latlon = get_projection_point(
        latlon,
        get_node_coordinates(graph, nearest_edge[0]),
        get_node_coordinates(graph, nearest_edge[1])
    )
 
    if log:
        print("\nOld origin edge data:")
        if 'geometry' in graph[nearest_edge[0]][nearest_edge[1]][0]:
            print(graph[nearest_edge[0]][nearest_edge[1]][0])
        else: print('No geometry found')
    
    # Inserting origin and destination nodes into respective edges
    node_id, edges = insert_new_node_in_edge(
        graph,
        node_id,
        node_latlon,
        nearest_edge
    )
    added_edges += edges

    if log:
        print("\nNew edges data:")
        for edge in added_edges:
            if 'geometry' in graph[edge[0]][edge[1]][0]:
                print(f'{edge} {graph[edge[0]][edge[1]][0]}')
            else: print('No geometry found')

    return node_id


def insert_node_in_graph(graph, node_id, node_latlon, log=False):
    # Snapping origin and destination coordinates to the closet point of an edge (road)
    road_latlon = get_nearest_road_coordinates(node_latlon)
    if log: print(f'\nClosest road located at coordinates: {road_latlon}')

    # Getting the nearest edge of origin and destination (LatLon) respectively
    added_edges = []
    nearest_edge = ox.distance.nearest_edges(graph, road_latlon[1], road_latlon[0]) # TAKES THE MOST TIME

    if log: print("\nOld origin edge data:")
    if log: print(graph[nearest_edge[0]][nearest_edge[1]][0])
    
    # Inserting origin and destination nodes into respective edges
    node_id, edges = insert_new_node_in_edge(
        graph,
        node_id,
        node_latlon,
        nearest_edge
    )
    added_edges += edges

    if log:
        print("\nNew edges data:")
        for edge in added_edges:
            print(f'{edge} {graph[edge[0]][edge[1]][0]}')

    return node_id


# Deprecated
def get_place_graph_with_origin_and_destination(place, origin_id, origin_latlon, destination_id, destination_latlon, network_type="walk", simplify=True):
    
    # Creating Graph of District's road Network
    graph = ox.graph_from_place(place, network_type=network_type, simplify=simplify)
    # Add angle compass information to graph
    graph = ox.bearing.add_edge_bearings(graph)

    # Snapping origin and destination coordinates to the closet point of an edge (road)
    origin_road_latlon = get_nearest_road_coordinates(origin_latlon)
    destination_road_latlon = get_nearest_road_coordinates(destination_latlon)
    print(f'Closest road to origin (LatLon): {origin_road_latlon}')
    print(f'Closest road to destination (LatLon): {destination_road_latlon}')
    print("")

    # Getting the nearest edge of origin and destination (LatLon) respectively
    added_edges = []
    origin_nearest_edge = ox.distance.nearest_edges(graph, origin_road_latlon[1], origin_road_latlon[0])
    print("Old origin edge data:")
    print(graph[origin_nearest_edge[0]][origin_nearest_edge[1]][0])

    destination_nearest_edge = ox.distance.nearest_edges(graph, destination_road_latlon[1], destination_road_latlon[0])
    print("Old destination edge data:")
    print(graph[destination_nearest_edge[0]][destination_nearest_edge[1]][0])

    # Inserting origin and destination nodes into respective edges
    added_edges += insert_new_node_in_edge(
        graph,
        origin_id,
        origin_road_latlon,
        origin_nearest_edge
    )
    added_edges += insert_new_node_in_edge(
        graph,
        destination_id,
        destination_road_latlon,
        destination_nearest_edge
    )

    print("\nNew edges data:")
    for edge in added_edges:
        print(f'{edge} {graph[edge[0]][edge[1]][0]}')

    # Check neighbors
    target_nodes = [origin_id, destination_id]
    for node in target_nodes:
        print('')
        print(f'Node: ({node}) {graph.nodes[node]}')
        print("Neighbors:")
        for neighbor in graph.neighbors(node):
            print(f'    {neighbor}: ', end="")
            print(graph.nodes[neighbor])

    # Drawing the resulting graph
    #graph_fig, axis = draw_graph(graph, target_nodes)

    return graph


def add_cycleway_levels(graph, avenues_keywords, exclude=[], log=False):
    """
    Returns a <networkx.MultiDiGraph> with cycleway_level attribute added to its edges attributes
    
    graph <networkx.MultiDiGraph>: the city graph
    avenues_keywords <List>: keywords of the names of the avenues with cycleways
    exclude <List>: avenue names to exclude, use in case of duplicate names
    """
    cycleway_edges = []
    cycleway_nodes = []

    for u, v, data in graph.edges(data=True):
        for keyword in avenues_keywords:
            if 'name' in data and data['name'] not in exclude and keyword in data['name']:
                if u not in cycleway_nodes: cycleway_nodes.append(u)
                if v not in cycleway_nodes: cycleway_nodes.append(v)
                if log: print(data['name'])
                cycleway_edges.append((u, v))
                data['cycleway_level'] = 2
                break # found so no need for continue checking
            else:
                data['cycleway_level'] = 0

    return graph, cycleway_edges, cycleway_nodes