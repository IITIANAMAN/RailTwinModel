import networkx as nx

class Train:

    def __init__(self, train_id, source, destination):
        self.id = train_id
        self.source = source
        self.destination = destination

        self.route = []
        self.position = 0

    def compute_route(self, graph):
        self.route = nx.shortest_path(
            graph,
            self.source,
            self.destination,
            weight="distance"
        )

    def current_station(self):
        return self.route[self.position]
    
    def move(self):
        if self.position < len(self.route) - 1:
            self.position += 1

