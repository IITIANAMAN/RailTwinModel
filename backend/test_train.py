# test_train.py

from graph import build_network
from train import Train

G = build_network()

train = Train(
    "T101",
    "Mumbai",
    "Nagpur"
)

train.compute_route(G)

print("Route:")
print(train.route)

print("\nMovement Simulation:\n")

while True:

    print(train)

    if train.reached_destination():
        break

    train.move()