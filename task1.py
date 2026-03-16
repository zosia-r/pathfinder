from src.gtfs_loader import GTFSLoader
from src.graph_builder import GraphBuilder

loader = GTFSLoader("./data/")
loader.load_all("20260317")

builder = GraphBuilder(loader)
graph = builder.build_graph()

builder.add_transfer_edges()

#print first 3 stops and their edges (formatted for readability)
for stop_id, edges in list(graph.items())[:3]:
    stop_name = loader.stops[loader.stops['stop_id'] == stop_id]['stop_name'].values[0]
    print("\nSTOP:", stop_id, "-", stop_name)

    for edge in edges[:10]:  # first 10 edges for this stop
        to_stop_name = loader.stops[loader.stops['stop_id'] == edge.to_stop]['stop_name'].values[0]
        dep_time = f"{edge.departure // 3600:02d}:{(edge.departure % 3600) // 60:02d}:{edge.departure % 60:02d}"
        arr_time = f"{edge.arrival // 3600:02d}:{(edge.arrival % 3600) // 60:02d}:{edge.arrival % 60:02d}"
        print(
            "  ->",
            edge.to_stop, "-", to_stop_name,
            "dep:", dep_time,
            "arr:", arr_time,
            "line:", edge.route_name
        )
        print("----" * 10)