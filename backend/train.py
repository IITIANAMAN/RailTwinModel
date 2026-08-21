from routing import healthiest_route


class Train:
    def __init__(
        self,
        train_id,
        source,
        destination,
        departure_time=0,
        passengers=100,
    ):
        self.id = train_id
        self.source = source
        self.destination = destination
        self.departure_time = max(0, departure_time)
        self.passengers = passengers
        self.route = []
        self.position = 0
        self.progress = 0.0
        self.status = "scheduled" if self.departure_time > 0 else "en_route"
        self.dwell_ticks = 0
        self.load_contribution = max(1, self.passengers // 10)
        self.estimated_arrival = None

    def compute_route(self, graph, current_time=0, preserve_schedule=False):
        route = healthiest_route(graph, self.source, self.destination)
        return self._apply_route(
            graph,
            route,
            current_time=current_time,
            preserve_schedule=preserve_schedule,
        )

    def _apply_route(self, graph, route, current_time=0, preserve_schedule=False):
        self.route = route
        self.position = 0
        self.progress = 0.0
        if not self.route:
            self.status = "stranded"
            self.estimated_arrival = None
            return False
        travel_ticks = sum(
            graph[self.route[index]][self.route[index + 1]].get("travel_ticks", 3)
            for index in range(len(self.route) - 1)
        )
        start_time = max(current_time, self.departure_time)
        self.estimated_arrival = start_time + travel_ticks
        if len(self.route) == 1:
            self.status = "arrived"
            self.dwell_ticks = 0
            return True
        if not preserve_schedule or current_time >= self.departure_time:
            self.status = "en_route"
        return True

    def current_station(self):
        if not self.route:
            return None
        return self.route[self.position]

    def next_station(self):
        if not self.route or self.position >= len(self.route) - 1:
            return None
        return self.route[self.position + 1]

    def occupied_segment(self):
        next_station = self.next_station()
        if next_station and self.progress > 0:
            return self.current_station(), next_station
        return None

    def move(self, graph, current_time):
        if self.status == "scheduled":
            if current_time < self.departure_time:
                return
            self.status = "en_route"
        if self.status != "en_route" or not self.route or self.reached_destination():
            return

        current = self.current_station()
        next_station = self.next_station()
        if not next_station or not graph.has_edge(current, next_station):
            self.status = "stranded"
            return
        edge = graph[current][next_station]
        if edge.get("status") == "failed":
            self.status = "holding"
            return

        self.progress += 1 / max(edge.get("travel_ticks", 3), 1)
        if self.progress >= 1.0:
            self.progress -= 1.0
            self.position += 1
            if self.reached_destination():
                self.progress = 0.0
                self.status = "arrived"
                self.dwell_ticks = 0

    def reached_destination(self):
        return bool(self.route) and self.position == len(self.route) - 1

    def reroute(self, graph, current_time=0, failed_edge=None):
        current = self.current_station()
        next_station = self.next_station()
        occupied = self.occupied_segment()

        if failed_edge:
            failed_key = frozenset(failed_edge)
            remaining_edges = {
                frozenset((self.route[index], self.route[index + 1]))
                for index in range(self.position, len(self.route) - 1)
            }
            if failed_key not in remaining_edges:
                return True
            if occupied:
                # Resolve an affected in-flight train to its nearest endpoint.
                current = next_station if self.progress >= 0.5 else current
        elif occupied:
            return True

        if current is None:
            self.status = "stranded"
            return False
        route = healthiest_route(graph, current, self.destination)
        return self._apply_route(
            graph,
            route,
            current_time=current_time,
            preserve_schedule=self.status == "scheduled",
        )

    def start_return_service(self, graph, current_time):
        previous_source = self.source
        self.source = self.destination
        self.destination = previous_source
        self.departure_time = current_time
        self.compute_route(graph, current_time=current_time)

    def schedule_label(self):
        return {
            "departure": self.departure_time,
            "arrival": self.estimated_arrival,
        }
