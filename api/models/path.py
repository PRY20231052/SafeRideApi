from typing import Iterable

from api.models.coordinates import Coordinates
from api.models.direction import Direction
from api.models.edge import Edge
from datetime import datetime

class Path:
    def __init__(
            self,
            nodes: Iterable[Coordinates],
            edges: Iterable[Edge],
            directions: Iterable[Direction],
            polyline_points: Iterable[Coordinates],
            distance_meters: float,
            eta_seconds: float,
        ):
        self.nodes = nodes
        self.edges = edges
        self.directions = directions
        self.polyline_points = polyline_points
        self.distance_meters = distance_meters
        self.eta_seconds = eta_seconds
        self.arrival_time = datetime.now()