import sys
from datetime import datetime
from src.utils.gtfs_loader import GTFSLoader
from src.utils.graph_builder import GraphBuilder

def parse_args(args, USAGE, list_mode=False):

    if len(args) < 3:
        print(USAGE)
        sys.exit(1)

    start_name = args[0]

    if list_mode:
        end_name = args[1].split(';')
    else:
        end_name = args[1]
        
    mode       = args[2]

    if mode not in ('t', 'p'):
        print(f"Invalid mode: '{mode}'. Expected 't' for time or 'p' for transfers.")
        sys.exit(1)

    # Date – optional
    if len(args) >= 4:
        target_date = args[3].strip()
        try:
            datetime.strptime(target_date, "%Y%m%d")
        except ValueError:
            print(f"Invalid date format: '{target_date}'. Expected YYYYMMDD.")
            sys.exit(1)
    else:
        target_date = datetime.now().strftime("%Y%m%d")

    # Time – optional
    if len(args) >= 5:
        time_str = args[4].strip()
        parts = time_str.split(":")
        if len(parts) == 2:
            time_str += ":00"
        elif len(parts) != 3:
            print(f"Invalid time format: '{args[4]}'. Expected HH:MM or HH:MM:SS.")
            sys.exit(1)
    else:
        time_str = datetime.now().strftime("%H:%M:%S")

    return start_name, end_name, mode, target_date, time_str


def find_parent_station_id(name, metadata):
    name_lower = name.strip().lower()
    for stop in metadata.values():
        if stop.stop_name.strip().lower() == name_lower:
            return stop.stop_id
    return None

def get_data(target_date=None):
    loader = GTFSLoader()
    loader.load_all(target_date=target_date)

    builder = GraphBuilder(loader)
    graph = builder.build_graph()
    metadata = builder.get_metadata()

    return graph, metadata