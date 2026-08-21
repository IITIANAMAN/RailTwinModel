from analytics import critical_stations
from layout import CITY_CATALOG
from risk import compute_risk_scores


MINUTES_PER_TICK = 5


def clock_label(tick):
    total_minutes = (6 * 60 + tick * MINUTES_PER_TICK) % (24 * 60)
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


def export_state(graph, trains, current_time):
    critical = critical_stations(graph)
    critical_dict = dict(critical)
    risks = compute_risk_scores(graph, critical_dict)

    stations = [
        {
            "id": node,
            "x": graph.nodes[node]["x"],
            "y": graph.nodes[node]["y"],
            "load": graph.nodes[node]["load"],
            "stress": graph.nodes[node]["stress"],
            "capacity": graph.nodes[node]["capacity"],
            "risk": risks[node],
            "criticality": critical_dict.get(node, 0),
        }
        for node in graph.nodes
    ]

    tracks = [
        {
            "source": source,
            "target": target,
            "status": data["status"],
            "distance": data["distance"],
            "travel_ticks": data.get("travel_ticks", 3),
            "trains": data.get("trains", 0),
            "capacity": data.get("capacity", 1),
            "utilization": (
                data.get("trains", 0) / max(data.get("capacity", 1), 1)
            ),
        }
        for source, target, data in graph.edges(data=True)
    ]

    train_data = []
    for train in trains:
        current = train.current_station() or train.source
        next_station = train.next_station()
        current_position = graph.nodes.get(current, CITY_CATALOG.get(current, {}))

        if next_station and current in graph and next_station in graph:
            next_position = graph.nodes[next_station]
            x = current_position["x"] + (
                next_position["x"] - current_position["x"]
            ) * train.progress
            y = current_position["y"] + (
                next_position["y"] - current_position["y"]
            ) * train.progress
        else:
            x = current_position.get("x", 78)
            y = current_position.get("y", 22)

        train_data.append(
            {
                "id": train.id,
                "source": train.source,
                "current_station": current,
                "next_station": next_station,
                "progress": train.progress,
                "destination": train.destination,
                "route": train.route,
                "status": train.status,
                "passengers": train.passengers,
                "departure_tick": train.departure_time,
                "arrival_tick": train.estimated_arrival,
                "departure_time": clock_label(train.departure_time),
                "arrival_time": (
                    clock_label(train.estimated_arrival)
                    if train.estimated_arrival is not None else "--:--"
                ),
                "x": x,
                "y": y,
            }
        )

    failed_tracks = sum(track["status"] == "failed" for track in tracks)
    average_stress = (
        sum(station["stress"] for station in stations) / len(stations)
        if stations else 0
    )
    health_score = max(
        0,
        100 - average_stress * 65 - failed_tracks * 12,
    )

    return {
        "time": current_time,
        "clock": clock_label(current_time),
        "minutes_per_tick": MINUTES_PER_TICK,
        "stations": stations,
        "tracks": tracks,
        "trains": train_data,
        "available_cities": sorted(set(CITY_CATALOG) - set(graph.nodes)),
        "metrics": {
            "average_stress": average_stress,
            "failed_tracks": failed_tracks,
            "health_score": round(health_score, 1),
            "active_trains": sum(
                train["status"] in {"en_route", "holding"} for train in train_data
            ),
            "scheduled_trains": sum(
                train["status"] == "scheduled" for train in train_data
            ),
            "stranded_trains": sum(
                train["status"] == "stranded" for train in train_data
            ),
        },
        "critical_stations": [
            {"station": name, "score": score}
            for name, score in critical
        ],
    }
