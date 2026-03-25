import random
from collections import deque

class TabuSearch:
    def __init__(self, astar_solver, start_node, locations, mode="t", start_time=0, fixed_tabu_size=False):
        self.astar = astar_solver
        self.start_node = start_node
        self.locations = locations  # list L of stop_ids
        self.mode = mode
        self.start_time = start_time
        self.fixed_tabu_size = fixed_tabu_size
        
        self.tabu_list = deque() #double-ended queue -> FIFO
        self.max_tabu_size = len(locations) * 2  if self.fixed_tabu_size else None
        self.best_solution = None
        self.best_cost = float('inf')
        
        self.cost_cache = {}

    def get_path_cost(self, u, v, current_time):
        state_key = (u, v, current_time)
        if state_key in self.cost_cache:
            return self.cost_cache[state_key]
        
        path, cost = self.astar.shortest_path(u, v, current_time, mode=self.mode)
        self.cost_cache[state_key] = (path, cost)
        return path, cost

    def calculate_total_tour_cost(self, tour):
        """Calculates the total cost of the tour A -> L1 -> L2 -> ... -> Ln -> A."""
        current_time = self.start_time
        current_node = self.start_node
        total_cost = 0
        full_detailed_path = []
        current_trip = None

        for next_node in tour:
            path, cost = self.get_path_cost(current_node, next_node, current_time)
            if path is None: return float('inf'), []

            if self.mode == 't':
                duration = cost - current_time
                total_cost += duration
                current_time = cost
            else:
                segment_transfers = 0
                for _, edge in path:
                    if edge is None:
                        continue
                    if current_trip is not None and edge.trip_id != current_trip:
                        segment_transfers += 1
                    current_trip = edge.trip_id
                total_cost += segment_transfers
                current_time = path[-1][1].arrival if path[-1][1] else current_time
            
            if full_detailed_path:
                full_detailed_path.extend(path[1:])
            else:
                full_detailed_path.extend(path)
            current_node = next_node

        # back to A
        path, cost = self.get_path_cost(current_node, self.start_node, current_time)
        if path is None: return float('inf'), []
        
        if self.mode == 't':
            total_cost += (cost - current_time)
        else:
            segment_transfers = 0
            for _, edge in path:
                if edge is None:
                    continue
                if current_trip is not None and edge.trip_id != current_trip:
                    segment_transfers += 1
                current_trip = edge.trip_id
            total_cost += segment_transfers
            
        full_detailed_path.extend(path)
        return total_cost, full_detailed_path

    def solve(self, iterations=100, sample_size=10):
        # random initial solution
        current_tour = list(self.locations)
        random.shuffle(current_tour)
        
        self.best_solution = list(current_tour)
        self.best_cost, _ = self.calculate_total_tour_cost(self.best_solution)

        for k in range(iterations):
            neighbors = self.get_sampled_neighbors(current_tour, sample_size) # sampling
            best_neighbor = None
            best_neighbor_cost = float('inf')
            best_move = None

            for neighbor, move in neighbors:
                cost, _ = self.calculate_total_tour_cost(neighbor)
                
                # aspiration 
                is_tabu = move in self.tabu_list
                if not is_tabu or cost < self.best_cost:
                    if cost < best_neighbor_cost:
                        best_neighbor_cost = cost
                        best_neighbor = neighbor
                        best_move = move

            if best_neighbor:
                current_tour = best_neighbor
                # update tabu list
                self.tabu_list.append(best_move)
                if self.fixed_tabu_size:
                    if len(self.tabu_list) > self.max_tabu_size:
                        self.tabu_list.popleft()

                if best_neighbor_cost < self.best_cost:
                    self.best_cost = best_neighbor_cost
                    self.best_solution = list(best_neighbor)

        _, final_path = self.calculate_total_tour_cost(self.best_solution)
        return final_path, self.best_cost

    def get_sampled_neighbors(self, tour, sample_size):
        neighbors = []
        n = len(tour)
        all_possible_moves = [(i, j) for i in range(n) for j in range(i + 1, n)]
        
        # sampling 
        sampled_moves = random.sample(all_possible_moves, min(sample_size, len(all_possible_moves)))
        
        for i, j in sampled_moves:
            new_tour = list(tour)
            new_tour[i], new_tour[j] = new_tour[j], new_tour[i]
            neighbors.append((new_tour, (i, j)))
        return neighbors