from graph import build_network
from train import Train

from simulation_engine import RailwaySimulation


G = build_network()

train1 = Train(
    "T101",
    "Mumbai",
    "Nagpur"
)

train2 = Train(
    "T102",
    "Mumbai",
    "Kolhapur"
)

train1.compute_route(G)
train2.compute_route(G)

sim = RailwaySimulation(G)

sim.add_train(train1)
sim.add_train(train2)

for step in range(5):

    print(
        f"\n===== TIME {sim.time} ====="
    )

    for train in sim.trains:

        print(
            train.id,
            train.current_station()
        )

    sim.tick()

    for node in G.nodes():

        print(
            node,
            "Load:",
            G.nodes[node]["load"],
            "Stress:",
            round(
                G.nodes[node]["stress"],
                2
            )
        )