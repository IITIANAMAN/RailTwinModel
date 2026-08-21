# analytics.py

import networkx as nx


def critical_stations(graph):
    operational = graph.copy()
    operational.remove_edges_from([
        (u, v)
        for u, v, data in operational.edges(data=True)
        if data.get("status") == "failed"
    ])

    centrality = nx.betweenness_centrality(
        operational,
        weight="distance"
    )

    ranked = sorted(
        centrality.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return ranked
