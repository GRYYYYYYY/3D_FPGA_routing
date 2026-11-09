#!/usr/bin/env python3
"""Exhaustive directed-resource examples with planted routable congestion.

These are small abstract RRGs, not claims of optimality on a real VPR device.
Enumerate every simple source/sink path, connected acyclic net tree and global
capacity-feasible combination, then independently audit the emitted witness.
"""
import itertools
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from check_route import audit

ROOT = Path(__file__).resolve().parents[1]


def paths(edges, source, sink, prefix=()):
    prefix = (*prefix, source)
    if source == sink:
        yield prefix
    else:
        for following in edges.get(source, []):
            if following not in prefix:
                yield from paths(edges, following, sink, prefix)


def trees(edges, source, sinks):
    result = []
    for branches in itertools.product(*(list(paths(edges, source, sink)) for sink in sinks)):
        parents = {}
        valid = True
        for branch in branches:
            for a, b in zip(branch, branch[1:]):
                if b in parents and parents[b] != a:
                    valid = False
                parents[b] = a
        if valid:
            result.append({"branches": branches, "nodes": set().union(*map(set, branches))})
    return result


def solve(nodes, edges, nets):
    choices = [trees(edges, source, sinks) for source, sinks in nets]
    best, count = None, 0
    for routing in itertools.product(*choices):
        used = {}
        for tree in routing:
            for node in tree["nodes"]:
                used[node] = used.get(node, 0) + 1
        if any(demand > nodes[node][4] for node, demand in used.items()):
            continue
        count += 1
        cost = sum(sum(5 if nodes[n][0] == "CHANZ" else 1 if nodes[n][0] in ("CHANX", "CHANY") else 0 for n in tree["nodes"]) for tree in routing)
        if best is None or cost < best[0]:
            best = cost, routing
    return best, count, [len(c) for c in choices]


def write_witness(directory, nodes, edges, routing):
    root = ET.Element("rr_graph")
    rr_nodes = ET.SubElement(root, "rr_nodes")
    for identity, (kind, x, low, high, capacity) in nodes.items():
        node = ET.SubElement(rr_nodes, "node", id=str(identity), type=kind, capacity=str(capacity), direction="BI_DIR")
        ET.SubElement(node, "loc", xlow=str(x), xhigh=str(x), ylow="0", yhigh="0", layer_low=str(low), layer_high=str(high))
    rr_edges = ET.SubElement(root, "rr_edges")
    for source, sinks in edges.items():
        for sink in sinks:
            ET.SubElement(rr_edges, "edge", src_node=str(source), sink_node=str(sink), switch_id="0")
    graph = directory / "rr_graph.xml"
    ET.ElementTree(root).write(graph)
    lines = []
    for net, tree in enumerate(routing):
        lines.append(f"Net {net} (oracle_{net})")
        seen = set()
        for pin, branch in enumerate(tree["branches"], 1):
            start = 0
            while start + 1 < len(branch) and branch[start + 1] in seen:
                start += 1
            for i, node in enumerate(branch[start:], start):
                kind, x, low, high, _ = nodes[node]
                location = f"({x}, 0, {low})"
                if low != high:
                    location += f" to ({x}, 0, {high})"
                last = i == len(branch) - 1
                lines.append(f"Node: {node} {kind} {location} Switch: {-1 if last else 0}" + (f" Net_pin_index: {pin}" if last else ""))
                seen.add(node)
    route = directory / "routed.route"
    route.write_text("\n".join(lines) + "\n")
    return audit(graph, route)


def main():
    # Net B has only channel 2. Net A can use 2 or 3, with two remote sinks.
    # A locally cheapest assignment can conflict even though a legal route is
    # planted; the shared crossing consumes one channel for the two A sinks.
    nodes = {0: ("SOURCE", 0, 0, 0, 1), 1: ("SOURCE", 1, 0, 0, 1),
             2: ("CHANZ", 0, 0, 1, 1), 3: ("CHANZ", 2, 0, 1, 1),
             4: ("CHANY", 0, 1, 1, 1), 5: ("CHANY", 2, 1, 1, 1),
             6: ("SINK", 0, 1, 1, 1), 7: ("SINK", 2, 1, 1, 1), 8: ("SINK", 1, 1, 1, 1)}
    edges = {0: [2, 3], 1: [2], 2: [4, 8], 3: [5], 4: [6, 7], 5: [6, 7]}
    nets = [(0, [6, 7]), (1, [8])]
    best, feasible, choices = solve(nodes, edges, nets)
    assert best is not None and best[0] == 11
    assert 3 in best[1][0]["nodes"] and 2 not in best[1][0]["nodes"]
    assert 2 in best[1][1]["nodes"]
    destination = ROOT / "results/tiny_exact_congestion"
    destination.mkdir(exist_ok=True)
    checked = write_witness(destination, nodes, edges, best[1])
    assert checked["passed"], checked["errors"]
    assert checked["route"]["vertical_channel_net_occupancy"] == 2
    assert checked["route"]["cross_layer_sink_connections"] == 3

    # Remove the alternative. Exhaustive failure here is a proof only for this
    # finite tiny graph, unlike a timed-out heuristic route on a real device.
    restricted = dict(edges)
    restricted[0] = [2]
    impossible, no_routes, _ = solve(nodes, restricted, nets)
    assert impossible is None and no_routes == 0
    # Reverse a required transition: geometry stays identical, reachability changes.
    reversed_edges = dict(edges)
    reversed_edges[3] = []
    reversed_edges[5] = [3, 6, 7]
    reversed_result, _, _ = solve(nodes, reversed_edges, nets)
    assert reversed_result is None
    report = {"scope": __doc__, "objective": "5 per distinct CHANZ per net + 1 per distinct planar wire per net",
              "optimum": best[0], "feasible_global_routings": feasible, "per_net_tree_counts": choices,
              "planted_shared_crossing_witness_passed": checked["passed"],
              "witness_route": checked["route"], "restricted_capacity_proven_infeasible": True,
              "reversed_transition_proven_infeasible": True,
              "not_proven": ["global optimality or convergence of H3D/VPR on real devices", "physical timing optimality"]}
    (destination / "audit.json").write_text(json.dumps(checked, indent=2) + "\n")
    (ROOT / "results/tiny_exact_summary.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
