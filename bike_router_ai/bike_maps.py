import gmaps
import googlemaps
import osmnx as ox

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

# Calculates the road node closest to the origin coordinates (lat, lon)
def get_nearest_road_coordinates(latlon):
    if not configuration_completed: return print('Please call configure() first!')
    nearest_road = google_maps.snap_to_roads(latlon)
    lat = nearest_road[0]['location']['latitude']
    lon = nearest_road[0]['location']['longitude']
    return (lat, lon)


def find_nodes_by_attributes(graph, attributes, values):
    if not configuration_completed: return print('Please call configure() first!')
    matching_nodes = []
    for node in graph.nodes(data=True):
        match_status = False
        # node MUST match all the give attributes values
        for i, att in enumerate(attributes):
            if node[1][att] == values[i]:
                match_status = True
            else:
                match_status = False
        if match_status: matching_nodes.append(node)
    return matching_nodes


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


def insert_new_node_in_edge(graph, node_id, node_latlon, edge):
    # If node already exists in the network then do nothing
    if find_nodes_by_attributes(graph, ['y', 'x'], [node_latlon[0], node_latlon[1]]):
        print(f"Node {node_id} already in Network")
        return []

    added_edges = []
    edge_attrs = graph[edge[0]][edge[1]][0]  # Copy edge attributes

    # Adding node
    graph.add_node(node_id, y=node_latlon[0], x=node_latlon[1], street_count=2)

    # Adding edges
    # TODO: check BEARINGS!!!
    graph.add_edge(
        edge[0],
        node_id,
        **{**edge_attrs, 'length': get_distance_between_nodes(graph, edge[0], node_id), 'bearing': get_edge_bearing(graph, edge[0], node_id)}
    )
    graph.add_edge(
        node_id,
        edge[1],
        **{**edge_attrs, 'length': get_distance_between_nodes(graph, node_id, edge[1]), 'bearing': get_edge_bearing(graph, node_id, edge[1])}
    )
    added_edges += [(edge[0], node_id), (node_id, edge[1])]

    if edge_attrs['oneway'] == False:  # is the edge bi directional? then add reversed edges
        graph.add_edge(
            edge[1],
            node_id,
            **{**edge_attrs, 'length': get_distance_between_nodes(graph, edge[1], node_id), 'bearing': get_edge_bearing(graph, edge[1], node_id)}
        )
        graph.add_edge(
            node_id,
            edge[0],
            **{**edge_attrs, 'length': get_distance_between_nodes(graph, node_id, edge[0]), 'bearing': get_edge_bearing(graph, node_id, edge[0])}
        )
        added_edges += [(edge[1], node_id), (node_id, edge[0])]
        graph.remove_edge(edge[1], edge[0])  # Remove original edge from graph

    graph.remove_edge(edge[0], edge[1])  # Remove original edge from graph
    return added_edges


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


def plot_graph(graph, highlighted_nodes=[], path=None, show_neighbors=False, size=15, node_size=15):
    # Drawing the graph bla bla this doc
    
    if show_neighbors == True:
        show_neighbors = [True for hn in highlighted_nodes]

    n_groups = [highlighted_nodes]
    n_g_colors = ['red']

    e_groups = []
    e_g_colors = []
    
    if path and len(path) >= 2:
        path_edges = []
        for i, node in enumerate(path):
            if i > 0: path_edges.append((path[i-1], node))

        e_groups.append(path_edges)
        e_g_colors.append('green')

    if not highlighted_nodes:
        ox.plot_graph(graph, figsize=(size, size), node_size=node_size)
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
        figsize=(size, size),
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


def convert_nodes_to_coordinates(graph, nodes, invert=False):

    """
    nodes: takes one or a list of nodes of the graph
    invert: if True, coords will be return as 'lonlat' instead of deafault 'latlon'
    """

    if type(nodes) != type([]): # if nodes isnt a list
        return (graph.nodes[nodes]['x'], graph.nodes[nodes]['y']) if invert else (graph.nodes[nodes]['y'], graph.nodes[nodes]['x'])
    
    coordinates_list = []
    for node in nodes:
        if invert:
            coords = (graph.nodes[node]['x'], graph.nodes[node]['y'])
        else:
            coords = (graph.nodes[node]['y'], graph.nodes[node]['x'])
        coordinates_list.append(coords)
    return coordinates_list

def get_routes_as_geojson(graph, paths:list, invert=False):
    """
    graph: a NetworkX Directed Graph of the city
    paths: list of paths to display in the map, where each path is a list of node_ids from the provided graph
    invert: if True, coords will be return as 'lonlat' instead of deafault 'latlon'

    Returns a GeoJson data for displaying with GoogleMaps API
    """
    routes_features = []
    for i, path in enumerate(paths):
        # For some stupid reason, geojson_layer needs the coordinates in LonLat...
        route_coordinates = convert_nodes_to_coordinates(graph, path, invert=invert)
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
    return {
        "type": "FeatureCollection",
        "features": routes_features
    }

def get_routes_geojson_layer(graph, paths, colors, stroke_weight=5, stroke_opacity=1.0):
    
    routes_features = []
    routes_origins = []

    for i, path in enumerate(paths):
        if len(path) >= 2:
            # For some stupid reason, geojson_layer needs the coordinates in LonLat...
            route_coordinates = convert_nodes_to_coordinates(graph, path, invert=True)
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
        origin_latlon = convert_nodes_to_coordinates(graph, path[0])
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
    pinned_nodes_coordinates = convert_nodes_to_coordinates(graph, pinned_nodes)

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

def insert_node_in_graph(graph, node_id, node_latlon, log=True):
    # Snapping origin and destination coordinates to the closet point of an edge (road)
    road_latlon = get_nearest_road_coordinates(node_latlon)
    if log: print(f'\nClosest road located at coordinates: {road_latlon}')

    # Getting the nearest edge of origin and destination (LatLon) respectively
    added_edges = []
    nearest_edge = ox.distance.nearest_edges(graph, road_latlon[1], road_latlon[0])

    if log: print("\nOld origin edge data:")
    if log: print(graph[nearest_edge[0]][nearest_edge[1]][0])
    
    # Inserting origin and destination nodes into respective edges
    added_edges += insert_new_node_in_edge(
        graph,
        node_id,
        road_latlon,
        nearest_edge
    )

    if log:
        print("\nNew edges data:")
        for edge in added_edges:
            print(f'{edge} {graph[edge[0]][edge[1]][0]}')

    return graph


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