#!/usr/bin/env python3
"""Independently audit VPR text routes against the exact exported XML RRG.

This checks directed transitions, tree structure, RR capacities and explicit
physical-channel groups. VPR's FULL route checker remains required for endpoint
mapping, reserved local OPINs, non-configurable closure and bus-mux selection.
Only routed nodes and CHANZ metadata are retained; edges are streamed.
"""

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sys
import time
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class TraceNode:
    inode: int
    kind: str
    low: tuple
    high: tuple
    switch: int
    pin: int | None


NET_RE = re.compile(r"^Net\s+(\d+)\s+\((.*)\)(.*)$")
NODE_RE = re.compile(
    r"^Node:\s*(\d+)\s+(\w+)\s+\(([^)]+)\)"
    r"(?:\s+to\s+\(([^)]+)\))?.*?Switch:\s*(-?\d+)"
    r"(?:\s+Net_pin_index:\s*(-?\d+))?"
)


def sha256(path):
    """Hash a file in bounded memory for provenance."""
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def coordinates(text):
    """Return (x, y, layer), accepting old planar VPR traces."""
    result = tuple(int(item.strip()) for item in text.split(","))
    if len(result) == 2:
        result += (0,)
    if len(result) != 3:
        raise ValueError(f"Invalid route coordinates: {text}")
    return result


def read_trace(path):
    """Parse non-global nets, retaining repeated branch-point records."""
    nets = {}
    current = None
    with open(path, encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            header = NET_RE.match(line)
            if header:
                current = None
                if "global net" not in header[3]:
                    current = int(header[1])
                    if current in nets:
                        raise ValueError(f"Duplicate net {current}")
                    nets[current] = {"name": header[2], "trace": []}
            elif line.startswith("Node:"):
                match = NODE_RE.match(line)
                if match is None or current is None:
                    raise ValueError(f"Malformed/unassociated route node at line {number}")
                low = coordinates(match[3])
                nets[current]["trace"].append(TraceNode(
                    int(match[1]), match[2], low,
                    coordinates(match[4]) if match[4] else low,
                    int(match[5]), int(match[6]) if match[6] else None,
                ))
    if not any(net["trace"] for net in nets.values()):
        raise ValueError("Route has no non-global routed nets")
    return nets


def graph_records(path):
    """Yield complete nodes, edges and switches with bounded XML overhead."""
    stack = []
    for event, element in ET.iterparse(path, events=("start", "end")):
        if event == "start":
            stack.append(element)
            continue
        if len(stack) == 3 and stack[1].tag in ("rr_nodes", "rr_edges", "switches"):
            yield stack[1].tag, element
            stack[1].remove(element)
        elif len(stack) == 2:
            stack[0].remove(element)
        stack.pop()


def read_graph_evidence(rr_graph, wanted_nodes, wanted_edges):
    """Stream one exact graph for a bounded union of independently parsed routes."""
    nodes = {}
    available_edges = set()
    node_types = Counter()
    switch_types = Counter()
    switch_timing = {}
    z_fanin = Counter()
    z_fanout = Counter()
    total_edges = 0
    for section, element in graph_records(rr_graph):
        attrs = element.attrib
        if section == "rr_nodes":
            inode = int(attrs["id"])
            kind = attrs["type"]
            node_types[kind] += 1
            if inode not in wanted_nodes and kind != "CHANZ":
                continue
            loc = element.find("loc").attrib
            zlow = int(loc.get("layer_low", loc.get("layer", "0")))
            zhigh = int(loc.get("layer_high", loc.get("layer", "0")))
            low = (int(loc["xlow"]), int(loc["ylow"]), zlow)
            high = (int(loc["xhigh"]), int(loc["yhigh"]), zhigh)
            nodes[inode] = {"kind": kind, "low": low, "high": high,
                            "capacity": int(attrs["capacity"]),
                            "direction": attrs.get("direction", "NONE"),
                            "timing": dict(element.find("timing").attrib) if element.find("timing") is not None else {}}
        elif section == "rr_edges":
            total_edges += 1
            edge = (int(attrs["src_node"]), int(attrs["sink_node"]), int(attrs["switch_id"]))
            if edge[0] in nodes and nodes[edge[0]]["kind"] == "CHANZ":
                z_fanout[edge[0]] += 1
            if edge[1] in nodes and nodes[edge[1]]["kind"] == "CHANZ":
                z_fanin[edge[1]] += 1
            if edge in wanted_edges:
                available_edges.add(edge)
        elif section == "switches":
            switch_types[attrs.get("type", "unknown")] += 1
            switch_timing[int(attrs["id"])] = dict(element.find("timing").attrib) if element.find("timing") is not None else {}
    return {"path": str(Path(rr_graph).resolve()), "sha256": sha256(rr_graph), "nodes": nodes,
            "available_edges": available_edges, "node_types": node_types, "switch_types": switch_types,
            "z_fanin": z_fanin, "z_fanout": z_fanout, "total_edges": total_edges,
            "switch_timing": switch_timing,
            "wanted_nodes": set(wanted_nodes), "wanted_edges": set(wanted_edges)}


def batch_graph_evidence(rr_graph, routes):
    """Collect a graph evidence cache once for several fixed-input routes."""
    wanted_nodes, wanted_edges = set(), set()
    for path in routes:
        for net in read_trace(path).values():
            trace = net["trace"]
            wanted_nodes.update(n.inode for n in trace)
            wanted_edges.update((a.inode, b.inode, a.switch) for a, b in zip(trace, trace[1:]) if a.switch != -1)
    return read_graph_evidence(rr_graph, wanted_nodes, wanted_edges)


def audit(rr_graph, route, resource_map=None, graph_evidence=None):
    """Audit a saved route; return scoped evidence, not a full legality claim."""
    started = time.monotonic()
    nets = read_trace(route)
    errors = []
    occupancy = Counter()
    required_edges = set()
    route_metadata = {}
    per_net_nodes = {}
    sink_count = 0
    remote_sink_count = 0
    for net_id, net in nets.items():
        trace = net["trace"]
        if not trace:
            continue
        if trace[0].kind != "SOURCE":
            errors.append(f"net {net_id}: root is not SOURCE")
        seen = set()
        pins = set()
        previous = None
        for node in trace:
            metadata = (node.kind, node.low, node.high)
            if node.inode in route_metadata and route_metadata[node.inode] != metadata:
                errors.append(f"node {node.inode}: inconsistent trace metadata")
            route_metadata[node.inode] = metadata
            branch_restart = previous is not None and previous.switch == -1
            if branch_restart:
                if node.inode not in seen or node.kind == "SINK":
                    errors.append(f"net {net_id}: detached/invalid branch restart at {node.inode}")
                if node.switch == -1:
                    errors.append(f"net {net_id}: empty branch at {node.inode}")
            else:
                if previous is not None:
                    required_edges.add((previous.inode, node.inode, previous.switch))
                    if node.kind == "SOURCE":
                        errors.append(f"net {net_id}: non-root SOURCE")
                if node.inode in seen and node.kind != "SINK":
                    errors.append(f"net {net_id}: cycle/reconvergence at {node.inode}")
                occupancy[node.inode] += 1
            if node.kind == "SINK":
                sink_count += 1
                remote_sink_count += node.low[2] != trace[0].low[2]
                if node.switch != -1:
                    errors.append(f"net {net_id}: SINK {node.inode} has outgoing switch")
                if node.pin is None or node.pin < 1 or node.pin in pins:
                    errors.append(f"net {net_id}: missing/duplicate SINK pin index {node.pin}")
                else:
                    pins.add(node.pin)
            seen.add(node.inode)
            previous = node
        if trace[-1].switch != -1:
            errors.append(f"net {net_id}: unfinished branch")
        if not pins or pins != set(range(1, len(pins) + 1)):
            errors.append(f"net {net_id}: absent/noncontiguous terminal pin indices")
        per_net_nodes[net_id] = seen

    imported = json.loads(Path(resource_map).read_text()) if resource_map else None
    mapped_nodes = {n for group in imported["channels"].values() for n in group["nodes"]} if imported else set()
    wanted_nodes = set(route_metadata) | mapped_nodes
    evidence = graph_evidence or read_graph_evidence(rr_graph, wanted_nodes, required_edges)
    if evidence["path"] != str(Path(rr_graph).resolve()):
        raise ValueError("Graph evidence path mismatch")
    if not wanted_nodes.issubset(evidence["wanted_nodes"]) or not required_edges.issubset(evidence["wanted_edges"]):
        raise ValueError("Graph evidence does not cover this route")
    nodes = evidence["nodes"]
    available_edges = evidence["available_edges"]
    node_types = evidence["node_types"]
    switch_types = evidence["switch_types"]
    z_fanin, z_fanout = evidence["z_fanin"], evidence["z_fanout"]
    total_edges = evidence["total_edges"]
    for inode, metadata in route_metadata.items():
        if inode in nodes and metadata != (nodes[inode]["kind"], nodes[inode]["low"], nodes[inode]["high"]):
            errors.append(f"node {inode}: trace differs from exact RRG type/location")
    for inode in sorted(set(route_metadata) - nodes.keys()):
        errors.append(f"route node {inode} absent from RRG")
    for edge in sorted(required_edges - available_edges):
        errors.append(f"missing directed edge/switch: {edge}")
    overuse = []
    for inode, used in occupancy.items():
        if inode in nodes and used > nodes[inode]["capacity"]:
            overuse.append({"node": inode, "occupancy": used, "capacity": nodes[inode]["capacity"]})
    errors.extend(f"capacity exceeded: {item}" for item in overuse)

    # CHANZ is already the physical channel in this pinned native model. Legacy
    # paired CHANX encodings require a separately verified, explicit mapping.
    physical_groups = {f"chanz:{inode}": {"nodes": [inode], "capacity": node["capacity"]}
                       for inode, node in nodes.items() if node["kind"] == "CHANZ"}
    if resource_map:
        assigned = {inode for group in physical_groups.values() for inode in group["nodes"]}
        for identity, group in imported["channels"].items():
            members = set(group["nodes"])
            if identity in physical_groups or not members or assigned & members:
                raise ValueError(f"Overlapping/empty physical channel group: {identity}")
            if group["capacity"] < 1:
                raise ValueError(f"Invalid physical capacity for {identity}")
            # Each legacy physical group has only two nodes; scanning the
            # million-node dict_keys view for every group is quadratic.
            if any(inode not in nodes for inode in members):
                raise ValueError(f"Physical channel {identity} refers to absent RRG nodes")
            assigned.update(members)
            physical_groups[identity] = group
    group_by_node = {inode: identity for identity, group in physical_groups.items() for inode in group["nodes"]}
    physical_use = Counter()
    net_metrics = {}
    for net_id, used in per_net_nodes.items():
        channels = {group_by_node[inode] for inode in used if inode in group_by_node}
        physical_use.update(channels)
        horizontal_length = sum(
            1 + abs(nodes[inode]["high"][0] - nodes[inode]["low"][0])
            + abs(nodes[inode]["high"][1] - nodes[inode]["low"][1])
            for inode in used if inode in nodes and nodes[inode]["kind"] in ("CHANX", "CHANY")
        )
        z_hops = sum(abs(nodes[inode]["high"][2] - nodes[inode]["low"][2])
                     for inode in used if inode in nodes and nodes[inode]["kind"] == "CHANZ")
        net_metrics[str(net_id)] = {"name": nets[net_id]["name"], "vertical_channels": len(channels),
                                   "native_layer_hops": z_hops, "horizontal_track_length": horizontal_length,
                                   "cross_layer_sink_connections": sum(node.kind == "SINK" and node.low[2] != nets[net_id]["trace"][0].low[2]
                                                                       for node in nets[net_id]["trace"])}
    for identity, used in physical_use.items():
        if used > physical_groups[identity]["capacity"]:
            errors.append(f"physical channel {identity}: {used} nets exceed capacity {physical_groups[identity]['capacity']}")

    # This pinned study uses zero wire/switch R/C and fixed switch delays.
    # Sum actual RRG switch Tdel along each directed tree path only when that
    # model is verified. General RC trees require VPR's full Elmore calculation.
    switches = evidence["switch_timing"]
    used_switches = {edge[2] for edge in required_edges}
    timing_supported = all(n in nodes and all(float(nodes[n]["timing"].get(k, 0)) == 0 for k in ("R", "C")) for n in route_metadata)
    timing_supported &= all(s in switches and all(float(switches[s].get(k, 0)) == 0 for k in ("R", "Cin", "Cout", "Cinternal")) for s in used_switches)
    delays, remote_delays = [], []
    if timing_supported and not errors:
        for net_id, net in nets.items():
            if not net["trace"]:
                continue
            arrival = {}
            per_pin = {}
            previous = None
            for node in net["trace"]:
                if previous is None:
                    arrival[node.inode] = 0.
                elif previous.switch != -1:
                    arrival[node.inode] = arrival[previous.inode] + float(switches[previous.switch].get("Tdel", 0.)) * 1e9
                if node.kind == "SINK":
                    per_pin[str(node.pin)] = arrival[node.inode]
                    delays.append(arrival[node.inode])
                    if node.low[2] != net["trace"][0].low[2]:
                        remote_delays.append(arrival[node.inode])
                previous = node
            net_metrics[str(net_id)]["routed_sink_delay_ns"] = per_pin

    def delay_summary(values):
        ordered = sorted(values)
        return {"connections": len(ordered), "mean_ns": sum(ordered) / len(ordered),
                "p95_ns": ordered[min(len(ordered) - 1, int(.95 * len(ordered)))], "max_ns": ordered[-1]} if ordered else None

    return {
        "schema": 1,
        "scope": "directed_edges_tree_routed_resource_capacity",
        "passed": not errors,
        "full_legality_requires": ["VPR --check_route full", "independent endpoint mapping for standalone certification"],
        "not_checked": ["netlist/placement endpoint identity", "local OPIN reservations",
                        "nonconfigurable edge closure", "bus-mux shared selection"],
        "errors": errors,
        "inputs": {"rr_graph": str(rr_graph), "rr_graph_sha256": evidence["sha256"],
                   "route": str(route), "route_sha256": sha256(route),
                   "resource_map_sha256": sha256(resource_map) if resource_map else None},
        "graph": {"nodes_by_type": dict(node_types), "edges": total_edges,
                  "switches_by_type": dict(switch_types), "physical_vertical_channels": len(physical_groups),
                  "native_chanz_with_fanin_and_fanout": sum(z_fanin[n] > 0 and z_fanout[n] > 0 for n, a in nodes.items() if a["kind"] == "CHANZ"),
                  "native_chanz_without_fanin": sum(z_fanin[n] == 0 for n, a in nodes.items() if a["kind"] == "CHANZ"),
                  "native_chanz_without_fanout": sum(z_fanout[n] == 0 for n, a in nodes.items() if a["kind"] == "CHANZ")},
        "route": {"routed_nets": len(per_net_nodes), "sink_terminals": sink_count,
                  "cross_layer_sink_connections": remote_sink_count,
                  "directed_edges": len(required_edges), "overused_rr_nodes": len(overuse),
                  "vertical_channel_net_occupancy": sum(physical_use.values()),
                  "unique_used_vertical_channels": len(physical_use),
                  "horizontal_track_length": sum(item["horizontal_track_length"] for item in net_metrics.values())},
        "nets": net_metrics,
        "routed_connection_delays": {"available": timing_supported and not errors,
                                      "model": "Sum of actual switch Tdel on zero-RC directed route trees; excludes intra-cluster logic/local delay; CPD remains native VPR STA",
                                      "all": delay_summary(delays), "remote": delay_summary(remote_delays)},
        "audit_wall_seconds": time.monotonic() - started,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rr-graph", required=True, type=Path)
    parser.add_argument("--route", required=True, type=Path)
    parser.add_argument("--resource-map", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = audit(args.rr_graph, args.route, args.resource_map)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({key: result[key] for key in ("passed", "scope", "route", "errors")}, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
