# routing.py

import networkx as nx


def edge_cost(graph, u, v):
    edge = graph[u][v]
    if edge.get("status") == "failed":
        return float("inf")

    distance = edge["distance"] / 100

    stress_u = graph.nodes[u]["stress"]
    stress_v = graph.nodes[v]["stress"]
    stress_penalty = ((stress_u + stress_v) / 2) * 4
    utilization = edge.get("trains", 0) / max(edge.get("capacity", 1), 1)
    congestion_penalty = utilization * 6

    return distance + stress_penalty + congestion_penalty


def build_weighted_graph(graph):

    H = graph.copy()

    for u, v in H.edges():

        H[u][v]["cost"] = edge_cost(
            H,
            u,
            v
        )

    return H


def healthiest_route(
    graph,
    source,
    destination
):

    H = build_weighted_graph(graph)

    try:
        return nx.shortest_path(
            H,
            source,
            destination,
            weight="cost"
        )
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return []
