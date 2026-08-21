from graph import build_network
from simulation import Train

G = build_network()

train = Train(
    "T101",
    "Mumbai",
    "Nagpur"
)

train.compute_route(G)

print(train.route)

while train.position < len(train.route)-1:

    print(train.current_station())

    train.move()

    def fail_track(graph, u, v):
        if graph.has_edge(u, v):
            graph[u][v]["status"] = "failed"
        
    def healthy_graph(graph):
        H = graph.copy()

        failed = [
            (u, v)
            for u, v, data in H.edges(data=True)
            if data["status"] == "failed"
        ]

        H.remove_edges_from(failed)

        return H
    
fail_track(G, "Pune", "Nashik")

H = healthy_graph(G)

train.compute_route(H)