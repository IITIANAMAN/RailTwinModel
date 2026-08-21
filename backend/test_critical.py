from graph import build_network

from analytics import (
    critical_stations
)

G = build_network()

ranking = critical_stations(G)

print("\nCRITICAL STATIONS\n")

for station, score in ranking:

    print(
        f"{station:<12}"
        f"{score:.4f}"
    )