import sys
import time
from src.algorithms.astar import AStar
from src.algorithms.tabu import TabuSearchSolver
from src.utils.output_formatter import OutputFormatter
from src.utils.time import time_to_seconds
from src.utils.cli import parse_args, find_parent_station_id, get_data

USAGE = (
    "Usage: python task_tabu.py <A> <L> <t|p> [YYYYMMDD] [HH:MM]\n"
    "  A        – start station (np. 'Wrocław Główny')\n"
    "  L        – list of station names to visit, separated by semicolons (e.g., 'Legnica;Lubin')\n"
    "  t|p      – criterion: t = time, p = number of transfers\n"
    "  YYYYMMDD – travel date (default: today)\n"
    "  HH:MM    – departure time (default: now)\n"
)


def find_stop_id(name, metadata):
    name_lower = name.strip().lower()
    for stop in metadata.values():
        if stop.stop_name.strip().lower() == name_lower:
            return stop.stop_id
    return None

def main():
    # Parse cli arguments
    start_name, locations_names, mode, target_date, start_time_str = parse_args(sys.argv[1:], USAGE, list_mode=True)

    graph, metadata = get_data(target_date=target_date)

    start_id = find_parent_station_id(start_name, metadata)
    if start_id is None:
        print(f"Station not found: '{start_name}'")
        sys.exit(1)

    locations_ids = []
    for loc_name in locations_names:
        loc_id = find_parent_station_id(loc_name, metadata)
        if loc_id:
            locations_ids.append(loc_id)
        else:
            print(f"Station not found: '{loc_name}'")
            sys.exit(1)

    if not locations_ids:
        print("Error: List of stations to visit is empty or invalid.")
        sys.exit(1)

    start_time_sec = time_to_seconds(start_time_str)

    # Finding the path
    astar = AStar(graph, metadata)
    tabu = TabuSearchSolver(astar, start_id, locations_ids, mode, start_time_sec)
    start_perf = time.perf_counter()
    final_path, total_cost = tabu.solve(iterations=50, sample_size=15)
    execution_time = time.perf_counter() - start_perf

    if final_path is None:
        print("Error: No valid route found connecting all points.")
        sys.exit(1)

    # Formatting and printing
    segments = OutputFormatter.format_path(final_path)
    OutputFormatter.print_stdout(segments, metadata)
    OutputFormatter.print_stderr(total_cost, execution_time, mode)

if __name__ == "__main__":
    main()