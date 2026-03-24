import heapq
import math

class AStar:
    def __init__(self, builder, metadata):
        # Initialize graph and station data
        self.graph = builder.build_graph()
        self.metadata = metadata

    def haversine(self, stop1, stop2):
        # Calculate distance in km between two sets of coordinates
        s1 = self.metadata[stop1]
        s2 = self.metadata[stop2]
        
        R = 6371
        d_lat = math.radians(s2.lat - s1.lat)
        d_lon = math.radians(s2.lon - s1.lon)
        a = (math.sin(d_lat / 2)**2 + 
             math.cos(math.radians(s1.lat)) * math.cos(math.radians(s2.lat)) * math.sin(d_lon / 2)**2)
        return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

    def get_heuristic(self, current_stop, goal_stop, mode):
        # Estimated cost to reach the destination
        if mode == 'p':
            # For transfers: check if stations share at least one line
            current_lines = self.metadata[current_stop].lines
            goal_lines = self.metadata[goal_stop].lines
            if not (current_lines & goal_lines):
                return 1 # At least one transfer needed
            return 0
        
        # For time: straight line distance / max train speed
        dist = self.haversine(current_stop, goal_stop)
        v_max_km_s = 200 / 3600 # 200 km/h
        return dist / v_max_km_s

    def shortest_path(self, start_station, goal_station, start_time, mode="t", transfer_buffer=5):
        open_list = [] # Nodes to check
        closed_list = set() # Already checked nodes
        
        g_costs = {} # Best known cost to reach a state
        parent = {} # Track the path
        parent_edge = {} 
        entry_count = 0 # Tie-breaker for the priority queue

        # State is (station_id, trip_id) to handle transfers correctly
        start_state = (start_station, None)
        start_g = (start_time, 0) if mode == "t" else (0, start_time)
        h_val = self.get_heuristic(start_station, goal_station, mode)
        
        # f = actual cost (g) + estimated cost to goal (h)
        start_f = (start_g[0] + h_val, start_g[1])
        
        heapq.heappush(open_list, (start_f, entry_count, start_g, start_time, start_station, None))
        g_costs[start_state] = start_g

        while open_list:
            # Pick the most promising node
            f, _, g, current_time, u, current_trip = heapq.heappop(open_list)
            current_state = (u, current_trip)

            if u == goal_station:
                return self._reconstruct_path(parent, parent_edge, start_station, u), g[0]

            if current_state in closed_list:
                continue
            
            closed_list.add(current_state)

            # Check all outgoing connections
            for edge in self.graph.get(u, []):
                is_transfer = 1 if current_trip is not None and current_trip != edge.trip_id else 0
                required_dep = current_time + (transfer_buffer if is_transfer else 0)

                # Skip if train departs too early
                if edge.departure < required_dep:
                    continue

                if mode == "t":
                    new_g = (edge.arrival, g[1] + is_transfer)
                else:
                    new_g = (g[0] + is_transfer, edge.arrival)

                v = edge.to_stop
                neighbor_state = (v, edge.trip_id)
                
                # Update if we found a better way to this state
                if neighbor_state not in g_costs or new_g < g_costs[neighbor_state]:
                    g_costs[neighbor_state] = new_g
                    h = self.get_heuristic(v, goal_station, mode)
                    
                    new_f = (new_g[0] + h, new_g[1])
                    
                    parent[neighbor_state] = current_state
                    parent_edge[neighbor_state] = edge
                    
                    # Re-check if it was already "finished" but now has a better cost
                    if neighbor_state in closed_list:
                        closed_list.remove(neighbor_state)
                        
                    entry_count += 1
                    heapq.heappush(open_list, (new_f, entry_count, new_g, edge.arrival, v, edge.trip_id))

        return None, float("inf")

    def _reconstruct_path(self, parent, parent_edge, start_station, goal_station):
        # Backtrack from goal to start using the parent dictionary
        path = []
        
        # Find which specific trip reached the goal
        current_state = None
        for state in parent_edge:
            if state[0] == goal_station:
                current_state = state
                break
        
        if not current_state:
            return None

        while current_state in parent_edge:
            edge = parent_edge[current_state]
            path.append((current_state[0], edge))
            current_state = parent[current_state]
        
        path.append((start_station, None))
        path.reverse()
        return path