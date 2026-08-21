import math
import random

import networkx as nx

from layout import CITY_CATALOG


def haversine_km(first, second):
    lat1 = math.radians(first["y"])
    lon1 = math.radians(first["x"])
    lat2 = math.radians(second["y"])
    lon2 = math.radians(second["x"])
    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1
    value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    )
    return 6371 * 2 * math.asin(math.sqrt(value))


def add_city_node(graph, name, rng=None):
    rng = rng or random
    position = CITY_CATALOG[name]
    capacity = rng.randint(75, 135)
    base_load = rng.randint(18, max(22, int(capacity * 0.68)))
    graph.add_node(
        name,
        x=position["x"],
        y=position["y"],
        load=base_load,
        base_load=base_load,
        capacity=capacity,
        stress=0.0,
    )


def add_track(graph, source, target):
    distance = max(
        80,
        round(haversine_km(graph.nodes[source], graph.nodes[target])),
    )
    graph.add_edge(
        source,
        target,
        distance=distance,
        travel_ticks=max(3, round(distance / 140)),
        capacity=10,
        trains=0,
        status="healthy",
    )


def connect_city(graph, name, connection_count=2):
    candidates = [
        (
            haversine_km(graph.nodes[name], graph.nodes[other]),
            other,
        )
        for other in graph.nodes
        if other != name
    ]
    for _, other in sorted(candidates)[:connection_count]:
        if not graph.has_edge(name, other):
            add_track(graph, name, other)


def build_network(city_count=10, seed=None):
    rng = random.Random(seed)
    city_count = max(5, min(city_count, len(CITY_CATALOG)))
    selected = rng.sample(sorted(CITY_CATALOG), city_count)
    graph = nx.Graph(seed=seed)

    for city in selected:
        add_city_node(graph, city, rng)

    # Nearest-neighbor links guarantee every selected city joins one component.
    unconnected = set(selected)
    connected = {unconnected.pop()}
    while unconnected:
        _, source, target = min(
            (
                haversine_km(graph.nodes[left], graph.nodes[right]),
                left,
                right,
            )
            for left in connected
            for right in unconnected
        )
        add_track(graph, source, target)
        connected.add(target)
        unconnected.remove(target)

    # Add alternate corridors so self-healing has meaningful reroute options.
    for city in selected:
        connect_city(graph, city, connection_count=2)

    return graph


def add_city(graph, name):
    if name not in CITY_CATALOG:
        return False
    if name in graph:
        return False
    add_city_node(graph, name)
    connect_city(graph, name, connection_count=min(3, len(graph) - 1))
    return True
