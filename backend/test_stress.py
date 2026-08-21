# test_stress.py

from graph import build_network
from stress import (
    update_station_stress,
    print_stress
)

G = build_network()

update_station_stress(G)

print_stress(G)