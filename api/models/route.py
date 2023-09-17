from datetime import datetime


class Route:
    def __init__(self, origin, waypoints):
        # Required values
        self.origin = origin
        self.waypoints = waypoints

        # Initial Values
        self.departure_time = datetime.now()

        # This will be computed after the prediction by the model
        self.arrival_time = None
        self.distance_meters = 0
        self.eta_seconds = 0
        self.path_nodes = []
        self.path_edges_attributes = []
        self.path_geojson = {}
        