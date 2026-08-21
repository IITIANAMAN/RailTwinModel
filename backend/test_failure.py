# test_failure.py

from graph import build_network
from train import Train
from failure import (
    fail_track,
    get_operational_graph
)

G = build_network()

print("\nORIGINAL ROUTE")

train = Train(
    "T101",
    "Mumbai",
    "Nagpur"
)

train.compute_route(G)

print(train.route)

# Simulate failure

fail_track(
    G,
    "Pune",
    "Nashik"
)

# Build operational graph

H = get_operational_graph(G)

print("\nAFTER FAILURE")

train.compute_route(H)

print(train.route)