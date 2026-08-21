from graph import build_network

from train import Train

from failure import (
    fail_track,
    get_operational_graph
)

G = build_network()

train = Train(
    "T101",
    "Mumbai",
    "Nagpur"
)

train.compute_route(G)

print("Original Route")
print(train.route)

train.move()

print("\nCurrent Station")
print(train.current_station())

fail_track(
    G,
    "Pune",
    "Nashik"
)

H = get_operational_graph(G)

train.reroute(H)

print("\nNew Route")
print(train.route)