# failure.py

def fail_track(graph, station1, station2):

    if graph.has_edge(station1, station2):

        graph[station1][station2]["status"] = "failed"

        print(
            f"TRACK FAILURE: "
            f"{station1} <-> {station2}"
        )

    else:

        print("Track does not exist.")


def repair_track(graph, station1, station2):

    if graph.has_edge(station1, station2):

        graph[station1][station2]["status"] = "healthy"

        print(
            f"TRACK REPAIRED: "
            f"{station1} <-> {station2}"
        )


def get_operational_graph(graph):

    operational = graph.copy()

    failed_edges = []

    for u, v, data in operational.edges(data=True):

        if data["status"] == "failed":
            failed_edges.append((u, v))

    operational.remove_edges_from(failed_edges)

    return operational


def reroute_all_trains(
    trains,
    operational_graph,
    current_time=0,
    failed_edge=None,
):

    results = {}
    for train in trains:
        if not train.reached_destination():
            results[train.id] = train.reroute(
                operational_graph,
                current_time=current_time,
                failed_edge=failed_edge,
            )
    return results
