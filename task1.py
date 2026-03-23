import sys
import time
from datetime import datetime
from src.gtfs_loader import GTFSLoader
from src.graph_builder import GraphBuilder
from src.algorithms.dijkstra import Dijkstra
from src.output_formatter import OutputFormatter


USAGE = (
    "Użycie: python task1.py <A> <B> <t|p> [YYYYMMDD] [HH:MM]\n"
    "  A, B      – nazwy stacji (np. 'Wrocław Główny')\n"
    "  t|p       – kryterium: t = czas, p = liczba przesiadek\n"
    "  YYYYMMDD  – data podróży (domyślnie: dzisiaj)\n"
    "  HH:MM     – godzina odjazdu (domyślnie: teraz)\n"
)


def parse_args():
    args = sys.argv[1:]

    if len(args) < 3:
        print(USAGE)
        sys.exit(1)

    start_name = args[0]
    end_name   = args[1]
    mode_raw   = args[2].strip().lower()

    if mode_raw not in ("t", "p", "time", "transfers"):
        print(f"Nieprawidłowe kryterium: '{mode_raw}'. Użyj 't' lub 'p'.")
        sys.exit(1)
    mode = "t" if mode_raw in ("t", "time") else "p"

    now = datetime.now()

    # Data – opcjonalna
    if len(args) >= 4:
        target_date = args[3].strip()
        try:
            datetime.strptime(target_date, "%Y%m%d")
        except ValueError:
            print(f"Nieprawidłowy format daty: '{target_date}'. Oczekiwano YYYYMMDD.")
            sys.exit(1)
    else:
        target_date = now.strftime("%Y%m%d")

    # Godzina – opcjonalna
    if len(args) >= 5:
        time_str = args[4].strip()
        parts = time_str.split(":")
        if len(parts) == 2:
            time_str += ":00"
        elif len(parts) != 3:
            print(f"Nieprawidłowy format godziny: '{args[4]}'. Oczekiwano HH:MM lub HH:MM:SS.")
            sys.exit(1)
    else:
        time_str = now.strftime("%H:%M:%S")

    return start_name, end_name, mode, target_date, time_str


def find_parent_station_id(name, metadata):
    """Szuka stacji po nazwie w słowniku metadata (tylko stacje nadrzędne)."""
    name_lower = name.strip().lower()
    for stop in metadata.values():
        if stop.stop_name.strip().lower() == name_lower:
            return stop.stop_id
    return None


def main():
    start_name, end_name, mode, target_date, start_time_str = parse_args()

    # Ładowanie danych GTFS
    loader = GTFSLoader()
    loader.load_all(target_date=target_date)

    # Budowa grafu
    builder = GraphBuilder(loader)
    builder.build_graph()
    metadata = builder.get_metadata()

    # Mapowanie nazw na ID stacji nadrzędnych
    start_id = find_parent_station_id(start_name, metadata)
    end_id   = find_parent_station_id(end_name, metadata)

    if start_id is None:
        print(f"Nie znaleziono stacji: '{start_name}'")
        sys.exit(1)
    if end_id is None:
        print(f"Nie znaleziono stacji: '{end_name}'")
        sys.exit(1)
    if start_id == end_id:
        print("Stacja startowa i docelowa są takie same.")
        sys.exit(1)

    start_time_sec = loader._time_to_seconds(start_time_str)

    # Szukanie trasy
    dijkstra = Dijkstra(builder)
    start_perf = time.perf_counter()
    path, cost = dijkstra.shortest_path(start_id, end_id, start_time_sec, mode=mode)
    execution_time = time.perf_counter() - start_perf

    if path is None:
        print(f"Brak połączenia między '{start_name}' a '{end_name}' w dniu {target_date} od {start_time_str}.")
        sys.exit(1)

    # Formatowanie i wypisywanie
    segments = OutputFormatter.format_path(path)
    OutputFormatter.print_stdout(segments, metadata)
    OutputFormatter.print_stderr(cost, execution_time, mode)


if __name__ == "__main__":
    main()