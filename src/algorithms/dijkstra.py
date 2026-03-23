import heapq

class Dijkstra:
    """
    A class to find the shortest train path using Dijkstra's algorithm 
    optimized for time-dependent graphs (schedules).
    """

    def __init__(self, builder):
        # The graph is a dictionary: { station_id: [Edge, Edge, ...] }
        self.graph = builder.build_graph()

    def shortest_path(self, start_station, goal_station, start_time, mode="t", transfer_buffer=5):
        """
        Calculates the optimal path from start_station to goal_station.
        
        Args:
            start_station (str): ID of the departure station.
            goal_station (str): ID of the destination station.
            start_time (int): The time user is ready to depart (in seconds/minutes).
            mode (str): 't' to minimize arrival time, 'p' to minimize transfers.
            transfer_buffer (int): Minimum minutes required to change trains.
            
        Returns:
            tuple: (path, final_cost) or (None, infinity) if no path exists.
        """
        if start_station not in self.graph or goal_station not in self.graph:
            return None, float("inf")

        # best_costs stores the lowest cost found so far for each station.
        # Format: { station_id: (primary_cost, secondary_cost) }
        # Mode 't': (arrival_time, transfer_count)
        # Mode 'p': (transfer_count, arrival_time)
        best_costs = {}
        parent = {}
        parent_edge = {}
        entry_count = 0  # Tie-breaker for the priority queue
        
        priority_queue = []
        
        # Initial cost setup based on optimization mode
        if mode == "t":
            initial_cost = (start_time, 0)
        else:
            initial_cost = (0, start_time)
        
        # Elements in queue: (cost_tuple, tie_breaker, current_time, station_id, trip_id)
        heapq.heappush(priority_queue, (initial_cost, entry_count, start_time, start_station, None))
        best_costs[start_station] = initial_cost

        while priority_queue:
            cost, _, current_time, u, current_trip = heapq.heappop(priority_queue)

            # Optimization: if we already found a better way to reach station 'u', skip this one
            if cost > best_costs.get(u, (float("inf"), float("inf"))):
                continue

            # Target reached: Since it's Dijkstra, the first time we pop the goal, it's optimal
            if u == goal_station:
                return self._reconstruct_path(parent, parent_edge, start_station, u), cost[0]

            for edge in self.graph.get(u, []):
                # 1. Determine if a transfer is occurring
                # A transfer happens if we were on a train (current_trip is not None)
                # and the next edge belongs to a different trip.
                is_transfer = 1 if current_trip is not None and current_trip != edge.trip_id else 0
                
                # 2. Check transfer feasibility
                # If transferring, we must add the transfer_buffer to the arrival time
                required_departure = current_time
                if is_transfer:
                    required_departure += transfer_buffer

                # Skip this edge if the train departs before we can board it
                if edge.departure < required_departure:
                    continue

                # 3. Calculate the new cost for the neighbor station 'v'
                if mode == "t":
                    # Primary: Earliest Arrival, Secondary: Minimum Transfers
                    new_cost = (edge.arrival, cost[1] + is_transfer)
                else:
                    # Primary: Minimum Transfers, Secondary: Earliest Arrival
                    new_cost = (cost[0] + is_transfer, edge.arrival)

                v = edge.to_stop
                # 4. Relaxation step: Update if this new path is better (lexicographically)
                if v not in best_costs or new_cost < best_costs[v]:
                    best_costs[v] = new_cost
                    parent[v] = u
                    parent_edge[v] = edge
                    entry_count += 1
                    heapq.heappush(priority_queue, (new_cost, entry_count, edge.arrival, v, edge.trip_id))

        return None, (float("inf"), float("inf"))

    def _reconstruct_path(self, parent, parent_edge, start_station, goal_station):
        """
        Backtracks from goal to start using the parent pointers to build the path list.
        """
        path = []
        current = goal_station
        while current in parent_edge:
            path.append((current, parent_edge[current]))
            current = parent[current]
        
        path.append((start_station, None))
        path.reverse()
        return path