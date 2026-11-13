#!/usr/bin/env python3
"""Audit a declared A0/R1 population without dropping failed or missing runs.

Python 3.9+, standard library only. Reads observations.csv; never launches VPR.
The defaults describe the registered heldout/W100 population in b132a1d.
Pass explicit selectors if the server's final protocol differs.
"""
import argparse
import csv
import hashlib
import itertools
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_CIRCUITS = (
    "clstm_like.large,clstm_like.medium,clstm_like.small,conv_layer,"
    "conv_layer_hls,dla_like.medium,dla_like.small,lstm,reduction_layer,"
    "robot_rl,tpu_like.large.os,tpu_like.large.ws,tpu_like.small.os,tpu_like.small.ws"
)


def parse_list(value):
    result = [v.strip() for v in value.split(",") if v.strip()]
    if not result or len(result) != len(set(result)):
        raise ValueError("Selectors must be nonempty and contain no duplicates")
    return result


def positive_metric(row, key):
    value = float(row[key])
    if not math.isfinite(value) or value <= 0:
        raise ValueError("Legal run has invalid %s: %s" % (key, row.get("run")))
    return value


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--observations", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--phase", default="heldout")
    p.add_argument("--width", default="100")
    p.add_argument("--circuits", default=DEFAULT_CIRCUITS)
    p.add_argument("--seeds", default="21,23,25")
    p.add_argument("--families", default="sb,cb_o,hybrid_o")
    p.add_argument("--flows", default="p0,p1")
    p.add_argument("--left-role", default="A0")
    p.add_argument("--right-role", default="R1")
    p.add_argument("--source-label", default="user-provided observations; raw routes not re-audited")
    args = p.parse_args()
    if args.left_role == args.right_role:
        p.error("left and right roles must differ")
    selectors = {k: parse_list(getattr(args, k)) for k in ("circuits", "seeds", "families", "flows")}
    wanted = set(itertools.product(selectors["circuits"], selectors["seeds"],
                                   selectors["families"], [args.width], selectors["flows"]))
    key_fields = ("circuit", "seed", "family", "width", "flow")
    roles = (args.left_role, args.right_role)
    grouped = {}
    source_bytes = args.observations.read_bytes()
    with args.observations.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = set(key_fields) | {"phase", "role", "run", "status", "critical_path_ns"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError("Missing CSV fields: %s" % sorted(required - set(reader.fieldnames or [])))
        all_rows = list(reader)
    retained = 0
    for row in all_rows:
        key = tuple(row[k] for k in key_fields)
        if row["phase"] != args.phase or row["role"] not in roles or key not in wanted:
            continue
        slot = grouped.setdefault(key, {})
        if row["role"] in slot:
            raise ValueError("Duplicate condition/role: %s %s" % (key, row["role"]))
        if not row["status"]:
            raise ValueError("Empty status: %s" % row["run"])
        slot[row["role"]] = row
        retained += 1

    pairs = []
    overall = Counter()
    panels = {}
    for key in sorted(wanted):
        pair = grouped.get(key, {})
        left, right = (pair.get(role) for role in roles)
        ls = left["status"] if left else "missing"
        rs = right["status"] if right else "missing"
        panel = panels.setdefault((key[2], key[4]), Counter())
        for stats in (overall, panel):
            stats["declared_pairs"] += 1
            stats["left_legal"] += int(ls == "legal")
            stats["right_legal"] += int(rs == "legal")
            stats["status:%s|%s" % (ls, rs)] += 1
        out = dict(zip(key_fields, key))
        out.update(left_role=roles[0], right_role=roles[1], left_status=ls, right_status=rs,
                   left_run=left["run"] if left else "", right_run=right["run"] if right else "",
                   left_failure_class=left.get("failure_class", "") if left else "",
                   right_failure_class=right.get("failure_class", "") if right else "",
                   left_cpd_ns="", right_cpd_ns="", right_vs_left_improvement_percent="",
                   comparison="not_both_legal")
        if ls == rs == "legal":
            a = positive_metric(left, "critical_path_ns")
            z = positive_metric(right, "critical_path_ns")
            direction = "tie" if math.isclose(a, z, rel_tol=1e-10, abs_tol=1e-12) else ("improved" if z < a else "degraded")
            out.update(left_cpd_ns=a, right_cpd_ns=z,
                       right_vs_left_improvement_percent=100.0 * (a-z)/a,
                       comparison=direction)
            for stats in (overall, panel):
                stats["both_legal"] += 1
                stats[direction] += 1
        pairs.append(out)

    def clean(stats):
        return {
            **{name: stats[name] for name in ("declared_pairs", "left_legal", "right_legal", "both_legal", "improved", "tie", "degraded")},
            "status_pairs_left_then_right": {k[7:]: v for k, v in sorted(stats.items()) if k.startswith("status:")},
        }

    report = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_label": args.source_label,
        "source_path": str(args.observations.resolve()),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "input_rows": len(all_rows), "selected_rows": retained,
        "population": {"phase": args.phase, "width": args.width, **selectors, "roles": roles},
        "expected_rows": 2 * len(wanted),
        "population_complete": retained == 2 * len(wanted),
        "overall": clean(overall),
        "panels": [{"family": family, "flow": flow, **clean(stats)} for (family, flow), stats in sorted(panels.items())],
        "limitations": [
            "Uses recorded status; does not rerun raw route legality or provenance audits.",
            "Win/tie/loss uses reported CPD precision and only pairs in which both runs are legal.",
            "Missing and unsuccessful runs remain in the declared population.",
            "Cases sharing a circuit, seed or architecture are correlated; these counts are not independent trials.",
            "No significance test, global speedup, or causal interpretation is inferred.",
            "Rerun with the server's final observations and verified population before use in a manuscript.",
        ],
    }
    args.out.mkdir(parents=True, exist_ok=False)
    (args.out / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (args.out / "pairs.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(pairs[0]))
        writer.writeheader()
        writer.writerows(pairs)
    lines = ["# 配对结果复算", "", "来源：" + args.source_label, "", "本报告是已有 CSV 的算术复核，未重新审计原始路由。", "",
             "| 架构/布局 | 预定配对 | 左侧合法 | 右侧合法 | 双方合法 | 改善 | 持平 | 退化 |",
             "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for panel in report["panels"]:
        lines.append("| %s/%s | %d | %d | %d | %d | %d | %d | %d |" % tuple(
            panel[k] for k in ("family", "flow", "declared_pairs", "left_legal", "right_legal", "both_legal", "improved", "tie", "degraded")))
    lines.extend(["", "总体：`" + json.dumps(report["overall"], ensure_ascii=False) + "`", "",
                  "总体配对数不能作为独立样本数。任何合法配对收益均应与完整状态表同时报告。", ""])
    (args.out / "summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"output": str(args.out.resolve()), "population_complete": report["population_complete"],
                      "overall": report["overall"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
