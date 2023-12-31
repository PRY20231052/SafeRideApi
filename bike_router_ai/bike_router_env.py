from gymnasium import Env
from gymnasium.spaces import Discrete, Box, Dict, Tuple
import numpy as np
import random
from decouple import config
import pandas as pd

from bike_router_ai.graph_utils import *

# Valores maximos y minimos de latitude y longitude de Lima Metropolitana
MIN_LIM_LAT = -12.25    
MAX_LIM_LAT = -11.56
MIN_LIM_LON = -77.18
MAX_LIM_LON = -76.80

class BikeRouterEnv(Env):

    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 144}

    def __init__(
        self,
        place=None,
        simplify=False,
        graphml_path=None,
        crime_data_excel_path=None,
        requested_district=None,
        randomize_ori_dest_on_reset=True,
        force_arriving=False,
        log=False,
        render_mode='human',
        graph_size=13.3,
        window_resolution=1000,
        window_aspect_ratio=(1,1),
        difficultie=0.5,
    ):
        """
        difficultie: Used on training. Determines how far away does the origin and destination need to be from each other.
                Maxes at level 4, after that, it will set any origin and destination, no matter the distane between them
                eg. difficultie = 0.5 ->  0 km  < distance_ori_dest <= 0.5 km
                    difficultie = 1   ->  0 km  < distance_ori_dest <= 1 km
                    difficultie = 3   ->  1 km  < distance_ori_dest <= 3 km
                    difficultie = 3.5 -> 1.5 km < distance_ori_dest <= 3.5 km
                    difficultie > 4   ->  0 km  < distance_ori_dest <= inf km
                Works with decimal values as well.
        
        If human-rendering is used (which is not), `self.window` will be a reference to the window that we draw to.
        `self.clock` will be a clock that is used to ensure that the environment is rendered at the correct framerate.
        They will remain `None` until human-mode is used for the first time.
        """

        print('Initializing the env...')

        self.force_arriving = force_arriving
        self.randomize_ori_dest_on_reset = randomize_ori_dest_on_reset
        self.log = log
        self.difficultie = difficultie

        # Variables related to render()
        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode
        self.graph_size = graph_size  # The size of the road network graph
        self.window = None
        self.window_resolution = window_resolution  # The size of the PyGame window
        self.window_aspect_ratio = window_aspect_ratio
        self.clock = None

        GOOGLE_MAPS_API_KEY = config('GOOGLE_MAPS_API_KEY')
        configure(google_maps_api_key=GOOGLE_MAPS_API_KEY)

        # Get the city/place Graph and setting origin and destination
        if graphml_path:
            print('Loading map graph from file...')
            self.graph = load_graph_from_file(graphml_path)
        else:
            print('Fetching map data from OSM api...')
            self.graph = get_graph(place, simplify=simplify)
            #save_graph_to_file(self.graph, 'city_graph.graphml')

        self.crime_points = []
        if crime_data_excel_path:
            # Set sheet_name to none to get the full crime points from SB and SI all together
            self.crime_points = self.get_crime_points(crime_data_excel_path, requested_district) 

        ##########################################################################################################################
        
        # DEFINING ACTION SPACE
        self.max_actions = 8 # Amount of actions that we expect the agent to have available at max
        #self.max_actions = get_max_node_neighbors(self.graph) # this loops the whole graph and finds he max amount of neighbors a node can have
        
        self.action_space = Discrete(self.max_actions)

        # DEFINING OBSERVATION SPACE (information relevant to know for the agent's training)
        self.edge_attributes_spaces = {
            'cycleway_level': Box(
                low=-1,
                high=2,
                dtype=np.int8
            ), # 0=none, 1=unsafe, 2=safe
            'maxspeed': Box(
                low=-1,
                high=120,
                dtype=np.int8
            ), # Max car speed
            'relative_bearing': Box(
                low=-1,
                high=360.0,
                dtype=np.float32
            ),
            'end_node_visited_status': Box(
                low=-1,
                high=1,
                dtype=np.int8
            ),
        }

        # The max number of closest points the agent will be able to see,
        self.num_prox_crime_points = 5

        self.observation_space = Dict({
            'current_latlon': Box(
                low=np.array([MIN_LIM_LAT, MIN_LIM_LON]),
                high=np.array([MAX_LIM_LAT, MAX_LIM_LON]),
                dtype=np.float64
            ),
            'destination_latlon': Box(
                low=np.array([MIN_LIM_LAT, MIN_LIM_LON]),
                high=np.array([MAX_LIM_LAT, MAX_LIM_LON]),
                dtype=np.float64
            ),
            'steps_count': Box(
                low=0,
                high=np.inf,
                dtype=np.int16
            ),
            'steps_tolerance': Box(
                low=0,
                high=np.inf,
                dtype=np.int16
            ),
            'distance_to_destination': Box(
                low=0.0,
                high=np.inf,
                dtype=np.float32
            ),
            'traveled_distance': Box(
                low=0.0,
                high=np.inf,
                dtype=np.float32
            ),
            'previous_step': Dict(self.edge_attributes_spaces),
            'num_possible_steps': Box(
                low=0,
                high=self.max_actions,
                dtype=np.int8
            ),
            'possible_steps': Tuple([Dict(self.edge_attributes_spaces)]*self.max_actions),
            'closest_crime_points': Tuple([
                Dict({
                    "latlon": Box(
                        low=np.array([MIN_LIM_LAT, MIN_LIM_LON]),
                        high=np.array([MAX_LIM_LAT, MAX_LIM_LON]),
                        dtype=np.float64
                    ),
                    "distance": Box(
                        low=0.0,
                        high=np.inf,
                        dtype=np.float32
                    ),
                })
            ]*self.num_prox_crime_points), #len(self.crime_points)
        })

        self.reset()
        print('Env succesfully initialized!')


    def reset(self, seed=None, options=None):
        # We need the following line to seed self.np_random
        super().reset(seed=seed)
        
        self.went_too_far = False
        self.revisiting = False
        self.arrived = False
        self.selected_invalid_action = False

        # Assigning random origin and destination
        if self.randomize_ori_dest_on_reset == True:
            random_index = random.randint(0, len(self.graph.nodes)-1)
            self.origin_node = list(self.graph.nodes)[random_index]
            while True:
                random_index = random.randint(0, len(self.graph.nodes)-1)
                self.destination_node = list(self.graph.nodes)[random_index]
                dist = get_distance_between_nodes(self.graph, self.origin_node, self.destination_node)
                # If origin and destination are different and the distance between them is within the range desire by the difficultie level, then we stop searching destination
                if self.destination_node != self.origin_node: 
                    if self.difficultie > 4: break
                    if ((self.difficultie - 2)*1000 if self.difficultie > 1 else 0) < dist <= self.difficultie * 1000: break
        else:
            assert len(self.route_origin_and_waypoints_ids) >= 2, 'Not enough nodes to compute a route. At least 2 node IDs inside self.route_origin_and_waypoints_ids are neeeded. Please call set_origin_and_waypoints() to insert new origin and waypoints'
            # First path to compute will always go from the first ID to the second ID
            self.origin_node = self.route_origin_and_waypoints_ids[0]
            self.destination_node = self.route_origin_and_waypoints_ids[1]
            # We pop out the first ID so when it resets, it computes the path from the second to thrid, and so on...
            # On the last path computation, we expect that this pop will only leave us with a SINGLE ID, the final destination
            self.route_origin_and_waypoints_ids.pop(0)

        # NOTE: AT THIS POINT WE EXPECT THAT ORIGIN AND DESTINATION ARE BOTH SET AS DESIRED

        # Returning to origin node
        self.current_node = self.origin_node
        self.path = [self.current_node]

        # When inserting nodes with ids it returns a list of paths with just one element so we have to add [0] at the end. idk why
        self.shortest_path = get_shortest_path(self.graph, self.origin_node, self.destination_node)

        self.traveled_distance = 0.0
        self.distance_origin_destination = get_distance_between_nodes(self.graph, self.origin_node, self.destination_node)
        self.distance_tolerance_multiplier = self._calculate_distance_tolerance(self.distance_origin_destination)        

        self.current_node_neighbours = get_node_neighbours(self.graph, self.current_node) # Defining initial possible steps
        # 1: possible action, 0: impossible action
        self.action_mask = np.array(
            [1] * len(self.current_node_neighbours) + [0] * (self.max_actions - len(self.current_node_neighbours)),
            dtype=np.int8
        )

        # setting initial last step attributes all to -1 so the agent can learn that it means we haven't done a step yet
        self.previous_step = {key: -1 for key in self.edge_attributes_spaces}
        
        obs = self._get_obs()
        info = self._get_info()

        return obs, info
    
    def set_origin_and_waypoints(self, origin_latlon, waypoints_latlons: list, log=False):
        
        assert len(waypoints_latlons) > 0, 'YOU MUST PROVIDE AT LEAST ONE WAYPOINT!'

        self.randomize_ori_dest_on_reset = False
        waypoints_latlons.insert(0, origin_latlon)


        # THIS IS THE LIST OF POINTS THAT THE RESULTING ROUTE NEEDS TO GOT THROUGH
        self.route_origin_and_waypoints_ids = []
        node_id = 0

        for latlon in waypoints_latlons:
            print(f'Inserting node wiht latlon {latlon} into graph...', end='')
            returned_node_id = insert_node_in_graph_v2(self.graph, node_id, latlon, log=log)
            self.route_origin_and_waypoints_ids.append(returned_node_id)
            node_id += 1
        
        # WE DONT CALL RESET INSIDE, WE EXPECT RESET TO BE CALL
        # RIGHT AFTER SETTING THE ORIGIN AND WAYPOINTS.
        # IF WE DON'T, WEIRD BEHVAIOR IS GONNA HAPPEN
        

    def get_crime_points(self, excel_path, sheet_name=None):
        crime_data = pd.read_excel(excel_path, sheet_name=sheet_name)
        crime_points = []
        if not sheet_name: # if none, retrieve all crime data together
            for key, data_frame in crime_data.items():
                for index, row in data_frame.iterrows():
                    crime_points.append((row['latitude'], row['longitude']))
        elif isinstance(sheet_name, str): # retrieves the data only for the requested sheet
            for index, row in crime_data.iterrows():
                crime_points.append((row['latitude'], row['longitude']))
        return crime_points
    

    def _is_close_to_crime_point(self, current_latlon, tolerance_radius_meters=120):
        for crime_point_latlng in self.crime_points:
            distance = get_distance_between_points(current_latlon, crime_point_latlng)
            if distance <= tolerance_radius_meters:
                return True
        return False
    
    def _get_reward_base_on_proximity_to_crime_points(self, crime_points, tolerance_radius_meters=120):
        reward = 6 # if we are not close to any crime point, then this will be our reward
        for crime_point in crime_points:
            if crime_point['distance'] <= tolerance_radius_meters:
                # for each crime point that's within our tolerance range, we will be decreasing the reward
                reward -= 3
        return reward


    def _get_edge_attributes(self, u, v):

        edge_attributes = self.graph[u][v][0]

        if 'maxspeed' in edge_attributes:
            maxspeed = edge_attributes['maxspeed']
            if type(maxspeed) == type([]): # Sometimes 'maxspeed' returns as a LIST of speedlimits
                maxspeed = int(maxspeed[0])
            maxspeed = int(maxspeed)
        else:
            maxspeed = 30 if edge_attributes['highway'] == 'residential' else 50

        # relative to the destination
        relative_bearing = calculate_edge_relative_bearing(self.graph, u, v, self.destination_node)

        return {
            'cycleway_level': int(edge_attributes['cycleway_level']) if 'cycleway_level' in edge_attributes else 0,
            'maxspeed': maxspeed,
            'relative_bearing': relative_bearing,
            'end_node_visited_status': 1 if v in self.path else 0
        }


    def _get_obs_possible_steps(self):
        possible_steps = []
        for neighbour in self.current_node_neighbours:
            possible_steps.append(self._get_edge_attributes(self.current_node, neighbour))
        possible_steps += [{key: -1 for key in self.edge_attributes_spaces}] * (self.max_actions - len(self.current_node_neighbours))
        return tuple(possible_steps)

    def _get_closest_crime_points(self):
        distances = [] # random number
        crime_points = [] # random number
        for crime_point_latlng in self.crime_points:
            distance = get_distance_between_points(
                [self.graph.nodes[self.current_node]['y'], self.graph.nodes[self.current_node]['x']],
                crime_point_latlng,
            )
            crime_points.append((list(crime_point_latlng)))
            distances.append(distance)
            
        sorted_indexes = np.argsort(distances)

        crime_points_sorted_by_proximity = []
        sorted_distances = []
        for i in sorted_indexes:
            crime_points_sorted_by_proximity.append(crime_points[i])
            sorted_distances.append(distances[i])

        return crime_points_sorted_by_proximity, sorted_distances
    

    def _get_obs(self):
        crime_points_sorted_by_proximity, sorted_distances = self._get_closest_crime_points()
        crime_points_sorted_by_proximity = tuple(
            [{ "latlon": point, "distance": dist } for point, dist, _ in zip(crime_points_sorted_by_proximity, sorted_distances, range(self.num_prox_crime_points))]
        )
        return {
            'current_latlon': [
                self.graph.nodes[self.current_node]['y'],
                self.graph.nodes[self.current_node]['x']
            ],
            'destination_latlon': [
                self.graph.nodes[self.destination_node]['y'],
                self.graph.nodes[self.destination_node]['x']
            ],
            'steps_count': len(self.path) - 1,
            'steps_tolerance': int(len(self.shortest_path) * 1.2),
            'distance_to_destination': get_distance_between_nodes(
                self.graph, self.current_node, self.destination_node
            ),
            'traveled_distance': self.traveled_distance,
            'previous_step': self.previous_step,
            'num_possible_steps': len(self.current_node_neighbours),
            'possible_steps': self._get_obs_possible_steps(),
            'closest_crime_points': crime_points_sorted_by_proximity,
        }


    def _get_info(self):
        # For some reason, in keras-rl2 the info is being check that it is not a list
        # other wise it raises ValueError: The truth value of an array with more than one element is ambiguous. Use a.any() or a.all()
        # so we are not allow to return list or arrays (maybe even tuples) inside the info dict. UNLESS WE CHANGE core.py
        return {
            'went_too_far': self.went_too_far,
            'revisiting': self.revisiting,
            'arrived': self.arrived,
            'selected_invalid_action': self.selected_invalid_action
            # 'path': self.path,
            # 'shortest_path': self.shortest_path
        }

    def _calculate_reward_based_on_orientation(self, relative_bearing):
        max_reward = 15 # min reawrd will alwyas be negative max reward

        min_bearing = 0
        max_bearing = 180
        if 180 < relative_bearing <= 360:
            relative_bearing -= 180 # to set it in the same half
            min_bearing = 180
            max_bearing = 0
        
        normalized_bearing = (relative_bearing - max_bearing)/(min_bearing - max_bearing)
        reward = (normalized_bearing * 2*max_reward) - max_reward
        return reward


    def _calculate_distance_tolerance(self, distance):
        max_distance = 2000 # Para San Borja
        max_multiplier = 1.7
        min_multiplier = 1.3
        if distance >= max_distance: return min_multiplier
        tolerance_multiplier = ((min_multiplier - max_multiplier) / (max_distance)) * distance + max_multiplier
        return tolerance_multiplier


    def _evaluate_observation(self, obs):

        reward = 0

        # if we exceed the amount of steps done in the shortest_path
        # start taking off rewards. Will be a few points at the beggining
        # but it will increase over time.
        if obs['steps_count'] > obs['steps_tolerance']:
            exceeded_steps = obs['steps_count'] - obs['steps_tolerance']
            if exceeded_steps > 0: reward -= exceeded_steps # More steps means even less reward

        # Reward the agent if it travels in a low speed limit highway
        if obs['previous_step']['maxspeed'] < 40: reward += 3

        #0: no cycleway, 1: unsafe cycleway, 2: safe cycle_way
        if obs['previous_step']['cycleway_level'] == 1: reward += 2
        elif obs['previous_step']['cycleway_level'] == 2: reward += 4

        # Reward if distance_to_destination is getting smaller
        if obs['distance_to_destination'] < get_distance_between_nodes(
            self.graph, self.path[-2], self.destination_node
        ): reward += 20
        else: reward -= 10

        # if it's heading in the direction of the destination
        # relative_bearing(to the destination) == orientation
        # max_reward = 15, min_reward = -15
        reward += self._calculate_reward_based_on_orientation(
            obs['previous_step']['relative_bearing']
        )

        reward += self._get_reward_base_on_proximity_to_crime_points(obs['closest_crime_points'])

        # Episode Termination conditions
        if self.current_node == self.destination_node:
            self.arrived = True
            reward += 200
            terminated = True
        # If revisiting node
        elif len(self.path) > 1 and obs['previous_step']['end_node_visited_status'] == 1: 
            self.revisiting = True
            reward -= 100
            terminated = True
        # If it's going too far away
        elif obs['distance_to_destination'] > self.distance_origin_destination * self.distance_tolerance_multiplier:
            self.went_too_far = True
            reward -= 100
            terminated = True
        else:
            terminated = False
        
        # Forcing path to reach the destination
        if terminated and not self.arrived and self.force_arriving:
            if self.revisiting: self.path.pop(-1)
            path_to_dest = get_shortest_path(self.graph, self.path[-1], self.destination_node)
            self.path.pop(-1)
            self.path += path_to_dest
            self.arrived = True

        # Meaning that the episode got stuck (not supported)
        truncated = False

        info = self._get_info()

        return reward, terminated, truncated, info

    def set_randomize_ori_dest_on_reset(self, value):
        self.randomize_ori_dest_on_reset = value

    def get_action_mask(self):
        return self.action_mask

    def step(self, action):

        # EVALUAR CAMBIAR CAMPO DE ACCION PARA QUE SEA MOVIMIENTO FIJO EN BASE A COORDENADAS
        # CASTIGAR POR ESCOGER 

        if self.log: print(f'Selected action {action} from {self.current_node_neighbours}')
        
        # Agent took a non-valid action
        if action >= len(self.current_node_neighbours):
            self.selected_invalid_action = True
            terminated = True
            
            if terminated and not self.arrived and self.force_arriving:
                if self.revisiting: self.path.pop(-1)
                path_to_dest = get_shortest_path(self.graph, self.path[-1], self.destination_node)
                self.path.pop(-1)
                self.path += path_to_dest
                self.arrived = True

            #                obs, reward, terminated, trunc, info
            return self._get_obs(), -100, terminated, False, self._get_info()
        
        # Apply action
        self.current_node = self.current_node_neighbours[action]
        self.previous_step = self._get_edge_attributes(self.path[-1], self.current_node)
        self.path.append(self.current_node)

        # Adding to the traveled distance
        # btw, self.path[-1] == self.current_node
        last_edge_length = self.graph[self.path[-2]][self.path[-1]][0]['length']
        self.traveled_distance+=last_edge_length

        # get the new neighbours from current node
        self.current_node_neighbours = get_node_neighbours(self.graph, self.current_node)

        # update the mask for possible actions
        self.action_mask = np.array(
            [1]*len(self.current_node_neighbours) + [0]*(self.max_actions - len(self.current_node_neighbours)),
            dtype=np.int8
        )

        # Observe the resulting state after applying action
        obs = self._get_obs()
        
        # Calculates reward, verifies episode termination conditions, and more
        reward, terminated, truncated, info = self._evaluate_observation(obs)

        return obs, reward, terminated, truncated, info


    def render(self):
        pass
        # if self.window is None and self.render_mode == "human":
        #     pygame.init()
        #     pygame.display.init()
        #     height = int(self.window_aspect_ratio[0]*(self.window_resolution/self.window_aspect_ratio[1]))
        #     width = self.window_resolution
        #     self.window = pygame.display.set_mode((height, width))
        # if self.clock is None and self.render_mode == "human":
        #     self.clock = pygame.time.Clock()

        # # Getting the figure of the road network [quite slow]
        # fig, axis = plot_graph(
        #     self.graph,
        #     [self.current_node, self.destination_node],
        #     self.path,
        #     show_neighbors=[True, False],
        #     size=self.graph_size,
        #     node_size=5
        # )

        # self.window.blit(fig,(-190, -190))
        # plt.close(fig)
        # del fig

        # pygame.event.pump()
        # pygame.display.update()

        # # We need to ensure that human-rendering occurs at the predefined framerate.
        # # The following line will automatically add a delay to keep the framerate stable.
        # fps = self.metadata["render_fps"]
        # self.clock.tick(fps)

    def close(self):
        pass
        # if self.window is not None:
        #     pygame.display.quit()
        #     pygame.quit()