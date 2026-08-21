import random

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from failure import (
    fail_track,
    get_operational_graph,
    repair_track,
    reroute_all_trains,
)
from graph import add_city, build_network
from layout import CITY_CATALOG
from propagation import propagate_stress
from simulation_engine import RailwaySimulation
from state_exporter import export_state
from stress import update_station_stress
from train import Train


app = FastAPI(title="RailTwin API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TrackRequest(BaseModel):
    source: str
    target: str


class CityRequest(BaseModel):
    name: str | None = None


class TrainRequest(BaseModel):
    train_id: str = Field(min_length=2, max_length=20)
    source: str
    destination: str
    departure_in: int = Field(default=0, ge=0, le=288)
    passengers: int = Field(default=100, ge=10, le=2000)


def initialize_graph(graph):
    simulation = RailwaySimulation(graph)
    simulation.update_station_loads()
    update_station_stress(graph)
    propagate_stress(graph)
    return simulation


def create_simulation(city_count=10, train_count=7, seed=None):
    seed = seed if seed is not None else random.SystemRandom().randint(1, 10_000_000)
    graph = build_network(city_count=city_count, seed=seed)
    graph.graph["seed"] = seed
    simulation = initialize_graph(graph)
    rng = random.Random(seed + 1)
    cities = list(graph.nodes)

    for index in range(train_count):
        source, destination = rng.sample(cities, 2)
        departure = rng.choice([0, 0, 1, 2, 3, 5, 8, 12])
        train = Train(
            f"RT{index + 1:03d}",
            source,
            destination,
            departure_time=departure,
            passengers=rng.randrange(80, 520, 20),
        )
        train.compute_route(
            graph,
            current_time=0,
            preserve_schedule=True,
        )
        simulation.add_train(train)

    simulation.update_station_loads()
    update_station_stress(graph)
    propagate_stress(graph)
    return graph, simulation


G, sim = create_simulation()


@app.get("/state")
def state():
    return export_state(G, sim.trains, sim.time)


@app.post("/tick")
def tick():
    sim.tick()
    return {
        "message": "simulation advanced",
        "time": sim.time,
        "state": export_state(G, sim.trains, sim.time),
    }


@app.post("/fail-track")
def fail(req: TrackRequest):
    if not G.has_edge(req.source, req.target):
        raise HTTPException(status_code=404, detail="Track does not exist")
    fail_track(G, req.source, req.target)
    reroutes = reroute_all_trains(
        sim.trains,
        get_operational_graph(G),
        current_time=sim.time,
        failed_edge=(req.source, req.target),
    )
    sim.update_station_loads()
    return {
        "status": "failed",
        "message": "affected trains safely rerouted",
        "reroutes": reroutes,
    }


@app.post("/repair-track")
def repair(req: TrackRequest):
    if not G.has_edge(req.source, req.target):
        raise HTTPException(status_code=404, detail="Track does not exist")
    repair_track(G, req.source, req.target)
    reroutes = reroute_all_trains(
        sim.trains,
        get_operational_graph(G),
        current_time=sim.time,
    )
    sim.update_station_loads()
    return {"status": "healthy", "reroutes": reroutes}


@app.post("/cities")
def create_city(req: CityRequest):
    available = sorted(set(CITY_CATALOG) - set(G.nodes))
    if not available:
        raise HTTPException(status_code=409, detail="All catalog cities are in use")
    city = req.name or random.choice(available)
    if city not in CITY_CATALOG:
        raise HTTPException(status_code=404, detail="Unknown city")
    if city in G:
        raise HTTPException(status_code=409, detail="City already exists")
    add_city(G, city)
    sim.update_station_loads()
    update_station_stress(G)
    return export_state(G, sim.trains, sim.time)


@app.post("/trains")
def create_train(req: TrainRequest):
    train_id = req.train_id.strip().upper()
    if any(train.id == train_id for train in sim.trains):
        raise HTTPException(status_code=409, detail="Train ID already exists")
    if req.source not in G or req.destination not in G:
        raise HTTPException(status_code=404, detail="Source or destination is not in network")
    if req.source == req.destination:
        raise HTTPException(status_code=400, detail="Source and destination must differ")

    train = Train(
        train_id,
        req.source,
        req.destination,
        departure_time=sim.time + req.departure_in,
        passengers=req.passengers,
    )
    if not train.compute_route(
        get_operational_graph(G),
        current_time=sim.time,
        preserve_schedule=True,
    ):
        raise HTTPException(status_code=409, detail="No operational route is available")
    sim.add_train(train)
    sim.update_station_loads()
    return export_state(G, sim.trains, sim.time)


@app.post("/reset")
def reset():
    global G, sim
    G, sim = create_simulation()
    return export_state(G, sim.trains, sim.time)
