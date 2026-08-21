from pprint import pprint

from graph import build_network
from train import Train

from simulation_engine import RailwaySimulation

from state_exporter import export_state


G = build_network()

train = Train(
    "T101",
    "Mumbai",
    "Nagpur"
)

train.compute_route(G)

sim = RailwaySimulation(G)

sim.add_train(train)

sim.tick()

state = export_state(
    G,
    sim.trains,
    sim.time
)

pprint(state)