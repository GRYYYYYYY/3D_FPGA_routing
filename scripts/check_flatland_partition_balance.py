#!/usr/bin/env python3
"""Independently audit the scalar weighted hMETIS graphs emitted by P1.

Uses the pinned OpenROAD additive percentage-point balance convention.
Does not mutate a partition or treat process success as balance feasibility.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


def audit(graph, assignment, parts, balance):
    assert parts >= 2 and math.isfinite(balance) and balance >= 0
    lines = [s.strip() for s in Path(graph).read_text().splitlines()
             if s.strip() and not s.lstrip().startswith('%')]
    header = list(map(int, lines[0].split()))
    assert len(header) == 3 and header[2] == 11, 'Expected scalar vertex/edge weighted P1 format 11'
    edges, vertices, _ = header
    assert len(lines) == 1 + edges + vertices
    weights = [float(s) for s in lines[1 + edges:]]
    assert all(math.isfinite(w) and w > 0 for w in weights)
    labels = list(map(int, Path(assignment).read_text().split()))
    assert len(labels) == vertices and all(0 <= v < parts for v in labels)
    totals = [sum(w for w, label in zip(weights, labels) if label == i)
              for i in range(parts)]
    total = sum(weights)
    lower = total * max(0, 1 / parts - balance * .01)
    upper = total * (1 / parts + balance * .01)
    unit = all(w == 1 for w in weights)
    return dict(vertices=vertices, edges=edges, parts=parts,
                balance_argument=balance, partition_weights=totals,
                lower_each=lower, upper_each=upper,
                balanced=all(lower - 1e-6 <= t <= upper + 1e-6 for t in totals),
                unit_weight_integer_feasible=(parts * math.ceil(lower - 1e-6) <= vertices <=
                                              parts * math.floor(upper + 1e-6)) if unit else None,
                graph_sha256=hashlib.sha256(Path(graph).read_bytes()).hexdigest(),
                assignment_sha256=hashlib.sha256(Path(assignment).read_bytes()).hexdigest())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('graph', type=Path)
    parser.add_argument('assignment', type=Path)
    parser.add_argument('--parts', type=int, default=2)
    parser.add_argument('--balance', type=float, required=True)
    args = parser.parse_args()
    print(json.dumps(audit(args.graph, args.assignment, args.parts, args.balance), indent=2))
