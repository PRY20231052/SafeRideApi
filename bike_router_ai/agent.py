import torch as th
from stable_baselines3 import PPO
from sb3_contrib import RecurrentPPO
from stable_baselines3.common.vec_env import DummyVecEnv 
from bike_router_ai.bike_router_env import BikeRouterEnv
from gymnasium.wrappers import FlattenObservation

from bike_router_ai.graph_utils import *

import os
import copy

# Initializing the Env
flatten_base_env = FlattenObservation(
    BikeRouterEnv(
        graphml_path=f'{os.getcwd()}/bike_router_ai/graph_SB_SI_w_cycleways_simplified.graphml',
        crime_data_excel_path=f'{os.getcwd()}/bike_router_ai/criminal_data.xlsx',
        force_arriving=True,
    )
)

class Agent:
    def __init__(self):
        self.env = copy.deepcopy(flatten_base_env)
        self.ppo = PPO.load(
            path=f'{os.getcwd()}/bike_router_ai/trained_agents/ppo.zip',
            env=DummyVecEnv([lambda: self.env])
        )

    def predict_route(self, origin_latlon, destination_latlon):
        """
        Predicts the route for an origin point `origin_latlon`
        to a destination point `destination_latlon`.
        Returns both the path predicted by the agent as a list of nodes from the graph
        and the Dijkstra path in the env, also as a list of nodes from the graph
        """

        self.env.unwrapped.set_origin_and_destination(
            origin_latlon,
            destination_latlon
        )

        obs, info = self.env.reset()
        terminated = False
        episode_reward = 0

        while not terminated:
            action = self.ppo.predict(obs)
            action = action[0]
            obs, reward, terminated, truncated, info = self.env.step(action)
            episode_reward += reward

        print(f'Finished with reward {episode_reward}')
        print(f'Status: arrived:{self.env.unwrapped.arrived}  invalid_action:{self.env.unwrapped.selected_invalid_action} revisiting:{self.env.unwrapped.revisiting} went_too_far:{self.env.unwrapped.went_too_far} ')
            
        return self.env.unwrapped.path, self.env.unwrapped.shortest_path