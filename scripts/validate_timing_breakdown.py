#!/usr/bin/env python3
"""Check the CHANZ detailed-report repair against the unchanged native STA output."""
import json
from pathlib import Path
import re
from check_route import audit, batch_graph_evidence, read_trace, sha256

ROOT = Path(__file__).resolve().parents[1]


def main():
    native = ROOT / "results/runs/fixture_ex5p_native_csv"
    repaired = ROOT / "results/runs/fixture_ex5p_detailed_fixed"
    graph = ROOT / "results/runs/fixture_ex5p_balanced1/rr_graph.xml"
    route = repaired / "routed.route"
    assert read_trace(native / "routed.route") == read_trace(route)
    assert sha256(native / "report_net_timing.csv") == sha256(repaired / "report_net_timing.csv")
    evidence = batch_graph_evidence(graph, [route])
    checked = audit(graph, route, graph_evidence=evidence)
    assert checked["passed"] and checked["routed_connection_delays"]["available"]
    incoming = {}
    for net in read_trace(route).values():
        for previous, current in zip(net["trace"], net["trace"][1:]):
            if previous.switch != -1 and current.kind != "SINK":
                key = current.inode
                value = previous.switch
                if key in incoming:
                    assert incoming[key] == value
                incoming[key] = value
    count, vertical, max_error = 0, 0, 0.
    for line in (repaired / "report_timing.setup.rpt").read_text().splitlines():
        node = re.match(r"\| \((OPIN|IPIN|CHANX|CHANY|CHANZ):(\d+)", line)
        numbers = re.search(r"\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*$", line)
        if not node or not numbers:
            continue
        switch = incoming[int(node[2])]
        expected = float(evidence["switch_timing"][switch].get("Tdel", 0)) * 1e9
        error = abs(float(numbers[1]) - expected)
        assert error <= .00050001, (line, expected)
        max_error = max(max_error, error)
        count += 1
        vertical += node[1] == "CHANZ"
    assert count > 0 and vertical > 0
    result = {"native_route_unchanged": True, "native_atom_delay_slack_csv_byte_identical": True,
              "checked_detailed_resource_rows": count, "checked_chanz_rows": vertical,
              "maximum_rounding_error_ns": max_error, "report_precision_ns": .001,
              "independent_route_audit_passed": checked["passed"],
              "routed_connection_delays": checked["routed_connection_delays"],
              "scope": "This model has verified zero RC; compare displayed increments to actual switch Tdel. The repair changes reporting, not STA or routing."}
    (ROOT / "results/timing_breakdown_validation.json").write_text(json.dumps(result, indent=2) + "\n")
    (ROOT / "results/fixture_ex5p_detailed_fixed.audit.json").write_text(json.dumps(checked, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
