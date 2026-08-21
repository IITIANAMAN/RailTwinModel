# stress.py


def calculate_station_stress(load, capacity):

    if capacity == 0:
        return 1.0

    stress = load / capacity

    return min(stress, 1.0)


def update_station_stress(graph):

    for node in graph.nodes():

        load = graph.nodes[node]["load"]
        capacity = graph.nodes[node]["capacity"]

        graph.nodes[node]["stress"] = (
            calculate_station_stress(
                load,
                capacity
            )
        )


def print_stress(graph):

    print("\nSTATION STRESS\n")

    for node in graph.nodes():

        stress = graph.nodes[node]["stress"]

        print(
            f"{node:<12}"
            f"Stress = {stress:.2f}"
        )