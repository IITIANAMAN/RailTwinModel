from graph import build_network

from stress import (
    update_station_stress
)

from propagation import (
    propagate_stress
)

G = build_network()

for node in G.nodes():

    G.nodes[node]["load"] = 0

G.nodes["Mumbai"]["load"] = 100

update_station_stress(G)

print("\nBEFORE\n")

for node in G.nodes():

    print(
        node,
        round(
            G.nodes[node]["stress"],
            2
        )
    )

propagate_stress(G)

print("\nAFTER\n")

for node in G.nodes():

    print(
        node,
        round(
            G.nodes[node]["stress"],
            2
        )
    )