from src.gtfs_loader import GTFSLoader
from collections import defaultdict

class Edge:
    def __init__(self, to_stop, departure, arrival, trip_id, route_name):
        self.to_stop = to_stop
        self.departure = departure
        self.arrival = arrival
        self.trip_id = trip_id
        self.route_name = route_name

    @property
    def travel_time(self):
        return self.arrival - self.departure
    
class GraphBuilder:
    def __init__(self, loader):
        self.stop_times = loader.stop_times
        self.stops = loader.stops
        self.trips = loader.trips
        self.routes = loader.routes

        self.graph = defaultdict(list)

    def build_graph(self):
        """Builds adjacency list graph from GTFS data."""

        trip_to_route = self.trips.set_index('trip_id')['route_id'].to_dict()

        route_names = self.routes.set_index('route_id')['route_short_name'].to_dict()

        for trip_id, group in self.stop_times.groupby('trip_id'):

            group = group.sort_values('stop_sequence')

            route_id = trip_to_route.get(trip_id)
            route_name = route_names.get(route_id, '')

            stops_list = group.to_dict('records')

            for i in range(len(stops_list) - 1):

                curr = stops_list[i]
                nxt = stops_list[i + 1]

                from_stop = curr["stop_id"]
                to_stop = nxt["stop_id"]

                departure = curr["dep_sec"]
                arrival = nxt["arr_sec"]

                edge = Edge(
                    to_stop=to_stop,
                    departure=departure,
                    arrival=arrival,
                    trip_id=trip_id,
                    route_name=route_name
                )

                self.graph[from_stop].append(edge)

        for stop_id in self.graph:
            self.graph[stop_id].sort(key=lambda e: e.departure)

        return self.graph
    
    def add_transfer_edges(self, transfer_time=300):
        """
        Adds transfer edges between stops belonging to the same station
        transfer_time default: 5 minutes
        """

        if "parent_station" not in self.stops.columns:
            return

        station_groups = self.stops.groupby("parent_station")

        for station_id, group in station_groups:

            stop_ids = group["stop_id"].tolist()

            for a in stop_ids:
                for b in stop_ids:
                    if a == b:
                        continue

                    edge = Edge(
                        to_stop=b,
                        departure=0,
                        arrival=transfer_time,
                        trip_id=None,
                        route_name="TRANSFER"
                    )

                    self.graph[a].append(edge)
