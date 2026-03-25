import sys
import time
from datetime import datetime
from src.utils.gtfs_loader import GTFSLoader
from src.utils.graph_builder import GraphBuilder
from src.algorithms.astar import AStar 
from src.utils.output_formatter import OutputFormatter
from src.utils.cli import get_data, parse_args, find_parent_station_id
from src.utils.time import time_to_seconds

USAGE = (
    "Usage: python main_astar.py <A> <B> <t|p> [YYYYMMDD] [HH:MM]\n"
    "  A, B      – stations (np. 'Wrocław Główny')\n"
    "  t|p       – criterion: t = time, p = number of transfers\n"
    "  YYYYMMDD  – travel date (default: today)\n"
    "  HH:MM     – departure time (default: now)\n"
)



def main():
    # Parse cli arguments
    start_name, end_name, mode, target_date, start_time_str = parse_args(sys.argv[1:], USAGE)

    graph, metadata = get_data(target_date=target_date)

    start_id = find_parent_station_id(start_name, metadata)
    end_id   = find_parent_station_id(end_name, metadata)

    if start_id is None:
        print(f"Station not found: '{start_name}'")
        sys.exit(1)
    if end_id is None:
        print(f"Station not found: '{end_name}'")
        sys.exit(1)
    if start_id == end_id:
        print("Start and end stations are the same.")
        sys.exit(1)

    start_time_sec = time_to_seconds(start_time_str)

    # Finding the path
    astar = AStar(graph, metadata)
    start_perf = time.perf_counter()
    path, cost = astar.shortest_path(start_id, end_id, start_time_sec, mode=mode)
    
    execution_time = time.perf_counter() - start_perf

    if path is None:
        print(f"No connection found between '{start_name}' and '{end_name}'.")
        sys.exit(1)

    # Formatting and printing
    segments = OutputFormatter.format_path(path)
    OutputFormatter.print_stdout(segments, metadata)
    OutputFormatter.print_stderr(cost, execution_time, mode)

if __name__ == "__main__":
    main()