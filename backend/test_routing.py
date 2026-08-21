# test_routing.py

from graph import build_network

from stress import (
    update_station_stress
)

from routing import (
    healthiest_route
)

G = build_network()

update_station_stress(G)

route = healthiest_route(
    G,
    "Mumbai",
    "Nagpur"
)

print("\nHEALTHIEST ROUTE\n")

print(route)