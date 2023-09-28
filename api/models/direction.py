class Direction:
    def __init__(self, ending_action, street_name, covered_edges_indexes, covered_polyline_points_indexes):
        self.ending_action = ending_action
        self.street_name = street_name
        self.covered_edges_indexes = covered_edges_indexes
        self.covered_polyline_points_indexes = covered_polyline_points_indexes