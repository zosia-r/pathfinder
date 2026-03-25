import sys
from src.utils.time import sec_to_time

class OutputFormatter:

    @staticmethod
    def format_path(path):
        """
        Groups the path into segments of continuous train rides.

        path[0] = (start_id, None)
        path[1:] = (stop_id, edge)
        Returns a list of segments:
          { 'from': stop_id, 'to': stop_id, 'line': str,
            'dep': int (seconds), 'arr': int (seconds), 'trip_id': str }
        """
        if not path:
            return []

        segments = []
        current_segment = None

        for i in range(1, len(path)):
            stop_id, edge = path[i]
            prev_stop_id = path[i - 1][0]

            if edge is None:
                continue

            # New segment if:
            #   1. First segment overall
            #   2. trip_id changed (transfer to a different train)
            if current_segment is None or edge.trip_id != current_segment["trip_id"]:
                if current_segment is not None:
                    segments.append(current_segment)
                current_segment = {
                    "from": prev_stop_id,
                    "to": stop_id,
                    "line": edge.route_name,
                    "dep": edge.departure,
                    "arr": edge.arrival,
                    "trip_id": edge.trip_id,
                }
            else:
                # Continuation of the same train ride
                current_segment["to"] = stop_id
                current_segment["arr"] = edge.arrival

        if current_segment is not None:
            segments.append(current_segment)

        return segments

    @staticmethod
    def print_stdout(segments, metadata):
        if not segments:
            print("Connection not found.")
            return

        header = (
            f"{'From Station':<30} | {'To Station':<30} | "
            f"{'Line':<10} | {'Departure':<10} | {'Arrival':<10}"
        )
        print(header)
        print("-" * len(header))

        for seg in segments:
            from_name = metadata[seg["from"]].stop_name
            to_name   = metadata[seg["to"]].stop_name
            dep_time  = sec_to_time(seg["dep"])
            arr_time  = sec_to_time(seg["arr"])

            print(
                f"{from_name:<30} | {to_name:<30} | "
                f"{seg['line']:<10} | {dep_time:<10} | {arr_time:<10}"
            )

    @staticmethod
    def print_stderr(cost, execution_time, mode):
        """Prints metrics to standard error."""
        if mode == "t":
            label = "Travel Time (s)"
        else:
            label = "Number of Transfers"

        sys.stderr.write("\n[METRICS]\n")
        sys.stderr.write(f"{label}: {cost}\n")
        sys.stderr.write(f"Calculation Time: {execution_time:.6f} s\n")