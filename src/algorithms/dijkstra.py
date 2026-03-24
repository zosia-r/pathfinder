import heapq

class Dijkstra:

    def __init__(self, builder):
        # graph is a dictionary: { station_id: [Edge, Edge, ...] }
        self.graph = builder.build_graph()

    def shortest_path(self, start_station, goal_station, start_time, mode="t", transfer_buffer=5):
        if start_station not in self.graph or goal_station not in self.graph:
            return None, float("inf")

        priority_queue = []

        best_costs = {}
        parent = {}
        parent_edge = {}
        entry_count = 0  # tie-breaker for the priority queue
        
        
        if mode == "t":
            initial_cost = start_time
        else:
            initial_cost = 0
        
        # elements in queue: (cost, tie_breaker, current_time, station_id, trip_id)
        heapq.heappush(priority_queue, (initial_cost, entry_count, start_time, start_station, None))
        best_costs[start_station] = initial_cost

        while priority_queue:
            cost, _, current_time, u, current_trip = heapq.heappop(priority_queue)

            if u == goal_station:
                return self._reconstruct_path(parent, parent_edge, start_station, u), cost

            for edge in self.graph.get(u, []):
                is_transfer = 1 if current_trip is not None and current_trip != edge.trip_id else 0
                
                required_departure = current_time
                if is_transfer:
                    required_departure += transfer_buffer

                if edge.departure < required_departure:
                    continue

                if mode == "t":
                    new_cost = edge.arrival
                else:
                    new_cost = cost + is_transfer

                v = edge.to_stop
                if v not in best_costs or new_cost < best_costs[v]:
                    best_costs[v] = new_cost
                    parent[v] = u
                    parent_edge[v] = edge
                    entry_count += 1
                    heapq.heappush(priority_queue, (new_cost, entry_count, edge.arrival, v, edge.trip_id))

        return None, (float("inf"), float("inf"))

    def _reconstruct_path(self, parent, parent_edge, start_station, goal_station):
        path = []
        current = goal_station
        while current in parent_edge:
            path.append((current, parent_edge[current]))
            current = parent[current]
        
        path.append((start_station, None))
        path.reverse()
        return path