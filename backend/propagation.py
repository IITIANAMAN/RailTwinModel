# propagation.py

def propagate_stress(graph, propagation_factor=0.25):

    current_stress = {}

    for node in graph.nodes():
        current_stress[node] = (
            graph.nodes[node]["stress"]
        )

    new_stress = {}

    for node in graph.nodes():

        neighbors = [
            neighbor
            for neighbor in graph.neighbors(node)
            if graph[node][neighbor].get("status") != "failed"
        ]

        if len(neighbors) == 0:

            new_stress[node] = current_stress[node]
            continue

        avg_neighbor_stress = (
            sum(
                current_stress[n]
                for n in neighbors
            )
            /
            len(neighbors)
        )

        propagated = (
            (1 - propagation_factor) * current_stress[node]
            + propagation_factor * avg_neighbor_stress
        )

        new_stress[node] = min(
            propagated,
            1.0
        )

    for node in graph.nodes():

        graph.nodes[node]["stress"] = (
            new_stress[node]
        )
