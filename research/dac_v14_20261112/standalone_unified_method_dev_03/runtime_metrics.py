"""Unchanged native metric parser, extracted without unrelated CLI defaults."""
import re
def parse_metrics(log):
    """Extract native reported values without treating failure as a solution."""
    result = {}
    patterns = {
        "critical_path_ns": r"Final critical path delay \(least slack\):\s+([\d.eE+-]+)\s+ns",
        "wirelength": r"Total wirelength:\s+(\d+)",
        "router_seconds": r"Routing took\s+([\d.eE+-]+)\s+seconds",
        "iterations": r"Successfully routed after\s+(\d+)\s+routing iterations",
    }
    for key, pattern in patterns.items():
        matches = re.findall(pattern, log)
        if matches:
            result[key] = float(matches[-1]) if key not in ("wirelength", "iterations") else int(matches[-1])
    result["native_full_check_passed"] = "Completed routing consistency check successfully." in log
    result["routing_success_reported"] = "Circuit successfully routed" in log
    return result
