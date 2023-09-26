from datetime import datetime
from typing import Iterable
from api.models.location import Location

class Route:
    def __init__(self, origin:Location, waypoints:Iterable[Location]):
        # Required values
        self.origin = origin
        self.waypoints = waypoints

        # Initial Values
        self.departure_time = datetime.now()

        # This will be computed after the prediction by the model
        self.paths = []
        self.paths_geojson = {}
        