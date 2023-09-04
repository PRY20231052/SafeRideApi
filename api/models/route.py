class Route:
    def __init__(self, origin, waypoints):
        # Initial values
        self.origin = origin
        self.waypoints = waypoints

        # This will be computed after the prediction by the model
        self.distance_meters = 0
        self.eat_seconds = 0
        self.path_geojson = {}
        