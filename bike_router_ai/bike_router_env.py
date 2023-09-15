import gymnasium as gym
from gymnasium import Env
from gymnasium.spaces import Discrete, Box, Dict, Tuple
import numpy as np
import random
from bike_router_ai import bike_maps as bm
from decouple import config

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
        graphml_path=None,
        origin_latlon=None,
        destination_latlon=None,
        force_arriving=False,
        randomize_ori_dest_on_reset=True,
        origin_id=0,
        destination_id=1,
        log=False,
        render_mode='human',
        graph_size=13.3,
        window_resolution=1000,
        window_aspect_ratio=(1,1),
    ):
        print('Initializing the env...')

        self.force_arriving = force_arriving
        self.randomize_ori_dest_on_reset = randomize_ori_dest_on_reset
        self.log = log

        # Monitoring flag variables
        self.went_too_far = False
        self.revisiting = False
        self.arrived = False

        """
        If human-rendering is used, `self.window` will be a reference to the window that we draw to.
        `self.clock` will be a clock that is used to ensure that the environment is rendered at the correct framerate.
        They will remain `None` until human-mode is used for the first time.
        """

        # Variables related to render()
        assert render_mode is None or render_mode in self.metadata["render_modes"]
        self.render_mode = render_mode
        self.graph_size = graph_size  # The size of the road network graph
        self.window = None
        self.window_resolution = window_resolution  # The size of the PyGame window
        self.window_aspect_ratio = window_aspect_ratio
        self.clock = None

        GOOGLE_MAPS_API_KEY = config('GOOGLE_MAPS_API_KEY')
        bm.configure(google_maps_api_key='AIzaSyDg0gEkbdTWKu8kRRrc5RdmWnL0LulvaC0')

        # Get the city/place Graph and setting origin and destination
        if graphml_path:
            self.graph = bm.load_graph_from_file(graphml_path)
        else:
            self.graph = bm.get_graph(place, simplify=False)
            #bm.save_graph_to_file(self.graph, 'city_graph.graphml')

        # Assignin Origin and Destination
        if origin_latlon and destination_latlon:
            # Adding given origin and destination to the graph
            self.randomize_ori_dest_on_reset = False
            print(f'Setting origin coordinates {origin_latlon} and destination coordinates {destination_latlon}')
            self.origin_node = origin_id
            self.destination_node = destination_id
            bm.insert_node_in_graph(self.graph, self.origin_node, origin_latlon, log=False)
            bm.insert_node_in_graph(self.graph, self.destination_node, destination_latlon, log=False)
        else:
            print("Assigning random existing graph's nodes as origin and destination")
            random_index = random.randint(0, len(self.graph.nodes)-1)
            self.origin_node = list(self.graph.nodes)[random_index]
            while True:
                random_index = random.randint(0, len(self.graph.nodes)-1)
                self.destination_node = list(self.graph.nodes)[random_index]
                if self.destination_node != self.origin_node: break

        self.current_node = self.origin_node
        self.path = [self.current_node]

        # When inserting nodes with ids it returns a list of paths with just one element so we have to add [0] at the end. idk why
        self.shortest_path = bm.get_shortest_path(self.graph, self.origin_node, self.destination_node)

        self.distance_origin_destination = bm.get_distance_between_nodes(self.graph, self.origin_node, self.destination_node)
        self.traveled_distance = 0.0

        # DEFINING ACTION SPACE
        self.max_actions = bm.get_max_node_neighbors(self.graph) # Amount of actions that we expect the agent to have available at max
        #self.max_actions = 6

        self.current_node_neighbours = bm.get_node_neighbours(self.graph, self.current_node) # Defining initial possible steps
        # 1: possible action, 0: impossible action
        self.action_mask = np.array(
            [1] * len(self.current_node_neighbours) + [0] * (self.max_actions - len(self.current_node_neighbours)),
            dtype=np.int8
        )
        self.action_space = Discrete(self.max_actions)


        # DEFINING OBSERVATION SPACE (information relevant to know for the agent's training)
        self.edge_attributes_spaces = {
            'cycleway_level': Box(
                low=0,
                high=2,
                dtype=np.int8
            ), # 0=none, 1=unsafe, 2=safe
            'maxspeed': Box(
                low=30,
                high=100,
                dtype=np.int8
            ), # Max car speed
            'relative_bearing': Box(
                low=0.0,
                high=360.0,
                dtype=np.float32
            ),
            'end_node_visited_status': Box(
                low=0,
                high=1,
                dtype=np.int8
            ),
        }

        # setting initial last step attributes all to -1 so the agent can learn that it means we haven't done a step yet
        self.previous_step = {key: -1 for key in self.edge_attributes_spaces}

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
        })
        print('Env succesfully initialized!')


    def _get_edge_attributes(self, u, v):

        edge_attributes = self.graph[u][v][0]
        cycleway_level = 1 if edge_attributes['highway'] == 'cycleway' else 0

        if 'maxspeed' in edge_attributes:
            maxspeed = edge_attributes['maxspeed']
            if type(maxspeed) == type([]): # Sometimes 'maxspeed' returns as a LIST of speedlimits
                maxspeed = int(maxspeed[0])
            maxspeed = int(maxspeed)
        else:
            maxspeed = 30 if edge_attributes['highway'] == 'residential' else 50

        # relative to the destination
        relative_bearing = bm.calculate_relative_bearing(self.graph, u, v, self.destination_node)

        return {
            'cycleway_level': cycleway_level,
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


    def _get_obs(self):
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
            'steps_tolerance': len(self.shortest_path) - 1,
            'distance_to_destination': bm.get_distance_between_nodes(
                self.graph, self.current_node, self.destination_node
            ),
            'traveled_distance': self.traveled_distance,
            'previous_step': self.previous_step,
            'num_possible_steps': len(self.current_node_neighbours),
            'possible_steps': self._get_obs_possible_steps()
        }


    def _get_info(self):
        # For some reason, in keras-rl2 the info is being check that it is not a list
        # other wise it raises ValueError: The truth value of an array with more than one element is ambiguous. Use a.any() or a.all()
        # so we are not allow to return list or arrays (maybe even tuples) inside the info dict. UNLESS WE CHANGE core.py
        return {
            'went_too_far': self.went_too_far,
            'revisiting': self.revisiting,
            'arrived': self.arrived,
            # 'path': self.path,
            # 'shortest_path': self.shortest_path
        }

    def _calculate_reward_based_on_orientation(self, relative_bearing, bearing_sweetspot):
        if 0 <= relative_bearing <= bearing_sweetspot or 360-bearing_sweetspot <= relative_bearing <= 360:
            return 10
        elif bearing_sweetspot < relative_bearing <= 90 or 270 <= relative_bearing < 360-bearing_sweetspot:
            return 5
        else:
            return -10


    def _evaluate_observation(self, obs):

        reward = 0

        # if we exceed the amount of steps done in the shortest_path
        # start taking off rewards. Will be a few points at the beggining
        # but it will increase over time.
        if obs['steps_count'] > obs['steps_tolerance']:
            exceeded_steps = obs['steps_count'] - obs['steps_tolerance']
            reward -= exceeded_steps/2 # More steps means even less reward

        if obs['previous_step']['maxspeed'] < 40:
            reward += 2

        #0: no cycleway, 1: unsafe cycleway, 2: safe cycle_way
        if obs['previous_step']['cycleway_level'] == 1:
            reward += 2
        elif obs['previous_step']['cycleway_level'] == 2:
            reward += 4

        # Reward if distance_to_destination is getting smaller
        if obs['distance_to_destination'] < bm.get_distance_between_nodes(
            self.graph, self.path[-2], self.destination_node
        ):
            reward += 6
        else:
            reward -= 2


        # if it's heading in the direction of the destination
        # relative_bearing(to the destination) == orientation
        reward += self._calculate_reward_based_on_orientation(
            obs['previous_step']['relative_bearing'],
            bearing_sweetspot=20
        )


        # Episode Termination conditions
        if self.current_node == self.destination_node:
            self.arrived = True
            reward += 500
            terminated = True
        elif len(self.path) > 1 and obs['previous_step']['end_node_visited_status'] == 1: # If revisiting node
            self.revisiting = True
            reward -= 500
            terminated = True
            if self.force_arriving:
                self.path.pop(-1)
                self.path += bm.get_shortest_path(self.graph, self.path[-1], self.destination_node)
                self.arrived = True
        elif obs['distance_to_destination'] > self.distance_origin_destination*1.20:
            self.went_too_far = True
            reward -= 500
            terminated = True
        else:
            terminated = False


        # Meaning that the episode got stuck (not supported by keras-rl2)
        truncated = False

        info = self._get_info()

        return reward, terminated, truncated, info

    def set_randomize_ori_dest_on_reset(self, value):
        self.randomize_ori_dest_on_reset = value

    def get_action_mask(self):
        return self.action_mask

    def set_origin_and_destination(self, origin_latlon, destination_latlon):
        self.randomize_ori_dest_on_reset = False
        self.origin_node = 0
        self.destination_node = 1
        bm.insert_node_in_graph(self.graph, self.origin_node, origin_latlon, log=False)
        bm.insert_node_in_graph(self.graph, self.destination_node, destination_latlon, log=False)
        self.reset()


    def step(self, action):
        if self.log: print(f'Selected action {action} from {self.current_node_neighbours}')

        # Apply action
        self.current_node = self.current_node_neighbours[action]
        self.previous_step = self._get_edge_attributes(self.path[-1], self.current_node)
        self.path.append(self.current_node)

        # Adding to the traveled distance
        # btw, self.path[-1] == self.current_node
        last_edge_length = int(self.graph[self.path[-2]][self.path[-1]][0]['length'])
        self.traveled_distance+=last_edge_length

        # get the new neighbours from current node
        self.current_node_neighbours = bm.get_node_neighbours(self.graph, self.current_node)

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


    def reset(self, seed=None, options=None):

        # We need the following line to seed self.np_random
        super().reset(seed=seed)

        self.went_too_far = False
        self.revisiting = False
        self.arrived = False

        # Assigning random origin and destination
        if self.randomize_ori_dest_on_reset == True:
            random_index = random.randint(0, len(self.graph.nodes)-1)
            self.origin_node = list(self.graph.nodes)[random_index]
            while True:
                random_index = random.randint(0, len(self.graph.nodes)-1)
                self.destination_node = list(self.graph.nodes)[random_index]
                if self.destination_node != self.origin_node: break

        # Returning to origin node
        self.current_node = self.origin_node

        self.path = [self.current_node]
        self.shortest_path = bm.get_shortest_path(self.graph, self.origin_node, self.destination_node)

        self.traveled_distance = 0.0
        self.current_node_neighbours = bm.get_node_neighbours(self.graph, self.current_node)

        self.action_mask = np.array(
            [1] * len(self.current_node_neighbours) + [0] * (self.max_actions - len(self.current_node_neighbours)),
            dtype=np.int8
        )

        self.previous_step = {key: -1 for key in self.edge_attributes_spaces}

        obs = self._get_obs()
        info = self._get_info()

        return obs, info


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
        # fig, axis = bm.plot_graph(
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