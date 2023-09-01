class Trip:
    def __init__(self, origin, waypoints):
        # Initial Values
        self.origin = origin
        self.waypoints = waypoints # The last waypoint is the destination

        # this will be computed after the prediction by the model
        self.routes = []
        self.routes_geojson = {}