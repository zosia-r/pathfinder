from collections import defaultdict
import pandas as pd
from src.utils.time import sec_to_time

class Stop:
    def __init__(self, stop_id, stop_name, lat=None, lon=None, lines=None):
        self.stop_id = stop_id
        self.stop_name = stop_name
        self.lat = lat
        self.lon = lon
        self.lines = lines if lines is not None else set()

    def __repr__(self):
        return f"{self.stop_name } ({self.stop_id}) - Lines: {self.lines}"


class Edge:
    def __init__(self, to_stop, departure, arrival, trip_id, route_name):
        self.to_stop = to_stop
        self.departure = departure  # seconds from midnight
        self.arrival = arrival      # seconds from midnight
        self.trip_id = trip_id
        self.route_name = route_name

    @property
    def duration(self):
        return self.arrival - self.departure

    def __repr__(self):
        return f"({self.departure}) --> {self.to_stop} ({self.arrival}) via line {self.route_name}"


class GraphBuilder:

    def __init__(self, loader):
        self.stop_times = loader.stop_times
        self.stops = loader.stops
        self.trips = loader.trips
        self.routes = loader.routes

        # graph: parent_station_id -> list of Edges
        self.graph = defaultdict(list)
        self.station_to_lines = defaultdict(set)

    def build_graph(self):

        # dict: trip_id -> route_id
        trip_to_route = self.trips.set_index("trip_id")["route_id"].to_dict()

        # dict: route_id -> route_name
        route_names = (
            self.routes
            .set_index("route_id")
            .apply(
                lambda r: r["route_short_name"]
                if pd.notna(r["route_short_name"]) and str(r["route_short_name"]).strip() != ""
                else r["route_long_name"],
                axis=1,
            )
            .to_dict()
        )

        # dict: stop_id -> parent_station
        platform_to_station = {
            row["stop_id"]: row["parent_station"]
            for _, row in self.stops.iterrows()
        }

        # main loop: for every trip, create edges between consecutive stops
        for trip_id, group in self.stop_times.groupby("trip_id"):
            group = group.sort_values("stop_sequence")
            route_id = trip_to_route.get(trip_id)
            route_name = route_names.get(route_id, "")

            # convert group to list of dicts (one row - one dict from stop_times)
            records = group.to_dict("records")

            for i in range(len(records)):
                curr_rec = records[i]
                curr_station = platform_to_station.get(curr_rec["stop_id"], curr_rec["stop_id"])
                
                if curr_station:
                    self.station_to_lines[curr_station].add(route_name)

                if i < len(records) - 1:
                    next_rec = records[i + 1]
                    from_station = curr_station
                    to_station = platform_to_station.get(next_rec["stop_id"], next_rec["stop_id"])

                    if from_station is None or to_station is None:
                        continue
                    if from_station == to_station:
                        continue

                    edge = Edge(
                        to_stop=to_station,
                        departure=curr_rec["dep_sec"],
                        arrival=next_rec["arr_sec"],
                        trip_id=str(trip_id),
                        route_name=route_name,
                    )
                    self.graph[from_station].append(edge)

        # sort edges by departure time for each station
        for station_id in self.graph:
            self.graph[station_id].sort(key=lambda e: e.departure)

        return self.graph
    
    def get_metadata(self):
        
        metadata = {}
        for _, row in self.stops.iterrows():
            id = row["stop_id"]
            parent = row["parent_station"]
            if id == parent:
                metadata[id] = Stop(
                    stop_id=id,
                    stop_name=row["stop_name"],
                    lat=row.get("stop_lat"),
                    lon=row.get("stop_lon"),
                    lines=self.station_to_lines.get(id, set())
                )
        return metadata

    def print_departures(self, station_id, limit=10):
        if station_id not in self.graph:
            print(f"No departures from station {station_id}")
            return
        
        print(f"Departures from station {station_id}:")
        for edge in self.graph[station_id][:limit]:
            dep_time = sec_to_time(edge.departure)
            arr_time = sec_to_time(edge.arrival)
            print(f"  To {edge.to_stop} at {dep_time} (arrives at {arr_time}) via route {edge.route_name} (trip {edge.trip_id})")