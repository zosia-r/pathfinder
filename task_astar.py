import sys
import time
from datetime import datetime
from src.gtfs_loader import GTFSLoader
from src.graph_builder import GraphBuilder
# Importujemy nową klasę AStar
from src.algorithms.astar import AStar 
from src.output_formatter import OutputFormatter

USAGE = (
    "Użycie: python task_astar.py <A> <B> <t|p> [YYYYMMDD] [HH:MM]\n"
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

    # Data
    if len(args) >= 4:
        target_date = args[3].strip()
        try:
            datetime.strptime(target_date, "%Y%m%d")
        except ValueError:
            print(f"Nieprawidłowy format daty: '{target_date}'. Oczekiwano YYYYMMDD.")
            sys.exit(1)
    else:
        target_date = now.strftime("%Y%m%d")

    # Godzina
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
    name_lower = name.strip().lower()
    for stop in metadata.values():
        if stop.stop_name.strip().lower() == name_lower:
            return stop.stop_id
    return None

def main():
    start_name, end_name, mode, target_date, start_time_str = parse_args()

    # 1. Ładowanie danych GTFS [cite: 116, 163]
    loader = GTFSLoader()
    loader.load_all(target_date=target_date)

    # 2. Budowa grafu i pobranie metadanych (współrzędnych) [cite: 191, 194]
    builder = GraphBuilder(loader)
    builder.build_graph()
    metadata = builder.get_metadata()

    # 3. Mapowanie nazw na ID
    start_id = find_parent_station_id(start_name, metadata)
    end_id   = find_parent_station_id(end_name, metadata)

    if not start_id or not end_id:
        print(f"Błąd: Nie znaleziono stacji {start_name} lub {end_name}.")
        sys.exit(1)

    start_time_sec = loader._time_to_seconds(start_time_str)

    # 4. Inicjalizacja AStar z metadanymi dla heurystyki [cite: 41, 44]
    # Przekazujemy metadata, aby algorytm miał dostęp do stop_lat i stop_lon
    astar = AStar(builder, metadata)
    
    start_perf = time.perf_counter()
    
    # 5. Wywołanie wyszukiwania ścieżki A* [cite: 219, 220]
    path, cost = astar.shortest_path(start_id, end_id, start_time_sec, mode=mode)
    
    execution_time = time.perf_counter() - start_perf

    if path is None:
        print(f"Brak połączenia między '{start_name}' a '{end_name}'.")
        sys.exit(1)

    # 6. Formatowanie i wypisywanie wyników [cite: 216]
    segments = OutputFormatter.format_path(path)
    OutputFormatter.print_stdout(segments, metadata)
    
    # Wartość kryterium i czas obliczeń na stderr zgodnie z instrukcją
    OutputFormatter.print_stderr(cost, execution_time, mode)

if __name__ == "__main__":
    main()