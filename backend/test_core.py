import unittest

from failure import fail_track, get_operational_graph, reroute_all_trains
from graph import add_city, build_network
from layout import CITY_CATALOG
from propagation import propagate_stress
from simulation_engine import RailwaySimulation
from state_exporter import export_state
from stress import update_station_stress
from train import Train


class RailwayTwinTests(unittest.TestCase):
    def build_simulation(self):
        graph = build_network(city_count=len(CITY_CATALOG), seed=17)
        simulation = RailwaySimulation(graph)
        train = Train("TEST-1", "Mumbai", "Nagpur")
        train.compute_route(graph)
        simulation.add_train(train)
        simulation.update_station_loads()
        update_station_stress(graph)
        return graph, simulation, train

    def test_random_network_is_connected_and_uses_real_cities(self):
        graph = build_network(city_count=12, seed=42)
        self.assertEqual(len(graph), 12)
        self.assertTrue(set(graph.nodes).issubset(CITY_CATALOG))
        self.assertGreaterEqual(len(graph.edges), 11)

    def test_export_is_observation_only_and_contains_schedule(self):
        graph, simulation, train = self.build_simulation()
        first = export_state(graph, simulation.trains, simulation.time)
        second = export_state(graph, simulation.trains, simulation.time)

        self.assertEqual(first["time"], second["time"])
        self.assertIn("departure_time", first["trains"][0])
        self.assertIn("arrival_time", first["trains"][0])
        self.assertTrue(all(0 <= station["risk"] <= 1 for station in first["stations"]))
        self.assertIsNotNone(train.estimated_arrival)

    def test_failure_on_occupied_segment_does_not_crash_next_tick(self):
        graph, simulation, train = self.build_simulation()
        source = train.current_station()
        target = train.next_station()
        train.progress = 0.62
        fail_track(graph, source, target)

        results = reroute_all_trains(
            simulation.trains,
            get_operational_graph(graph),
            current_time=simulation.time,
            failed_edge=(source, target),
        )
        simulation.tick()

        self.assertIn(train.status, {"en_route", "stranded", "arrived"})
        self.assertIn(train.id, results)
        if train.route:
            route_edges = {
                frozenset((train.route[index], train.route[index + 1]))
                for index in range(len(train.route) - 1)
            }
            self.assertNotIn(frozenset((source, target)), route_edges)

    def test_unrelated_failure_preserves_in_flight_progress(self):
        graph, simulation, train = self.build_simulation()
        train.progress = 0.4
        occupied = frozenset((train.current_station(), train.next_station()))
        unrelated = next(
            edge for edge in graph.edges
            if frozenset(edge) != occupied
            and frozenset(edge) not in {
                frozenset((train.route[index], train.route[index + 1]))
                for index in range(len(train.route) - 1)
            }
        )
        fail_track(graph, *unrelated)
        reroute_all_trains(
            simulation.trains,
            get_operational_graph(graph),
            failed_edge=unrelated,
        )
        self.assertEqual(train.progress, 0.4)

    def test_failure_snap_to_destination_marks_train_arrived(self):
        graph, _, train = self.build_simulation()
        source, destination = next(iter(graph.edges))
        train.source = source
        train.destination = destination
        train.route = [source, destination]
        train.position = 0
        train.progress = 0.8
        fail_track(graph, source, destination)
        train.reroute(
            get_operational_graph(graph),
            failed_edge=(source, destination),
        )
        self.assertEqual(train.status, "arrived")

    def test_add_city_connects_it_to_network(self):
        graph = build_network(city_count=5, seed=2)
        city = next(name for name in CITY_CATALOG if name not in graph)
        self.assertTrue(add_city(graph, city))
        self.assertGreaterEqual(graph.degree(city), 1)

    def test_stress_propagation_is_bounded(self):
        graph = build_network(city_count=8, seed=4)
        for node in graph.nodes:
            graph.nodes[node]["load"] = 0
        first = next(iter(graph.nodes))
        graph.nodes[first]["load"] = graph.nodes[first]["capacity"]
        update_station_stress(graph)
        propagate_stress(graph, propagation_factor=0.25)
        self.assertLess(graph.nodes[first]["stress"], 1)
        self.assertTrue(all(0 <= graph.nodes[node]["stress"] <= 1 for node in graph.nodes))

    def test_arrived_train_starts_return_service(self):
        graph, simulation, train = self.build_simulation()
        original_source = train.source
        original_destination = train.destination
        train.position = len(train.route) - 1
        train.status = "arrived"
        for _ in range(4):
            simulation.tick()
        self.assertEqual(train.source, original_destination)
        self.assertEqual(train.destination, original_source)
        self.assertEqual(train.status, "en_route")


if __name__ == "__main__":
    unittest.main()
