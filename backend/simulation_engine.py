# simulation_engine.py

from stress import update_station_stress
from propagation import propagate_stress

class RailwaySimulation:

    def __init__(self, graph):

        self.graph = graph

        self.trains = []

        self.time = 0

    def add_train(self, train):

        self.trains.append(train)

    def update_station_loads(self):
        for node in self.graph.nodes():
            self.graph.nodes[node]["load"] = self.graph.nodes[node].get(
                "base_load", 0
            )

        for _, _, data in self.graph.edges(data=True):
            data["trains"] = 0

        for train in self.trains:
            station = train.current_station()
            next_station = train.next_station()
            if not station:
                continue

            if train.status == "scheduled":
                self.graph.nodes[station]["load"] += train.load_contribution
                continue

            if next_station:
                current_share = 1 - train.progress
                next_share = train.progress
                self.graph.nodes[station]["load"] += (
                    train.load_contribution * current_share
                )
                self.graph.nodes[next_station]["load"] += (
                    train.load_contribution * next_share
                )
                if self.graph.has_edge(station, next_station):
                    self.graph[station][next_station]["trains"] += 1
            else:
                self.graph.nodes[station]["load"] += train.load_contribution

    def tick(self):

        self.time += 1

        for train in self.trains:
            if train.reached_destination():
                train.dwell_ticks += 1
                if train.dwell_ticks >= 4:
                    train.start_return_service(self.graph, self.time)
            else:
                train.move(self.graph, self.time)

        self.update_station_loads()

        update_station_stress(self.graph)

        propagate_stress(
            self.graph,
            propagation_factor=0.25
        )
