#!/usr/bin/env python3
"""Render checked research results as Markdown tables and standalone figures."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
import statistics

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
ORDER = ["a0", "a1_w2", "a2", "a3", "a4_whole", "a4_subtree", "flute_soft", "steiner_field",
         "a0_prune", "a1_w2_prune", "a3_prune", "a0_instrumented", "a1_tuned", "a3_tuned", "a4_tuned"]
LABELS = {"a0": "A0", "a1_w2": "A1 (w=2)", "a2": "A2", "a3": "A3",
          "a4_whole": "A4 whole", "a4_subtree": "A4 subtree", "flute_soft": "FLUTE soft",
          "steiner_field": "Field control", "a0_prune": "A0 prune", "a1_w2_prune": "A1 prune",
          "a3_prune": "A3 prune", "a0_instrumented": "A0 instrumented", "a1_tuned": "A1 tuned",
          "a3_tuned": "A3 tuned", "a4_tuned": "A4 tuned"}
GROUPS = {"native20_w100": "20 个公开电路，原生三维混合架构，W=100",
          "architecture_sweep": "2 个固定布局 × 8 种垂直架构设置",
          "paired_seeds_w100": "5 个电路 × 3 个配对布局种子，W=100",
          "elliptic_w160": "elliptic 相同布局的独立 W=160 容量实验",
          "sequential_timing": "2 个代表用例 × 15 个设置 × 3 次串行计时"}


def label(name):
    return LABELS.get(name, name)


def percent(metric, expected=None):
    if not metric:
        return "—"
    value = f"{100 * (metric['geomean'] - 1):+.2f}%"
    if expected is not None and metric["cases"] != expected:
        value += f" (n={metric['cases']})"
    return value


def save_figure(figure, destination):
    for suffix in ["png", "svg"]:
        figure.savefig(destination.with_suffix("." + suffix), dpi=180, bbox_inches="tight")
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()
    data = json.loads((ROOT / "results/analysis.json").read_text())
    if data["provisional"] and not args.allow_incomplete:
        raise RuntimeError("Final figures require the strict, complete evidence collection")
    figures = ROOT / "docs/figures"
    figures.mkdir(exist_ok=True)
    rows = data["rows"]
    summaries = {(r["dataset"], r["variant"]): r for r in data["summaries"]}
    text = ["# 实验结果（由已归档证据自动生成）", "",
            f"生成于 {data['utc']}。状态：{'**临时结果，实验或审计尚未完成**' if data['provisional'] else '**实验与规定审计已完成**'}。", "",
            f"纳入 {len(rows)} 次路由运行；其中 {sum(r['native_success'] for r in rows)} 次通过原生成功判定，"
            f"{sum(r['valid_solution'] for r in rows)} 次同时通过独立有向图/容量审计。"
            f"状态计数：`{dict(Counter(r['status'] for r in rows))}`。", "",
            "所有主比较都已核对 architecture、packed netlist、placement、RRG 的 SHA256 一致。"
            "成功率按全部运行计算；QoR 比率只纳入双方均成功且通过审计的相同用例。"
            "表中百分比为 treatment / A0 的几何均值减 1；负值表示该指标减少。"
            "缺少跨层连接或分母为零时，该项比率不定义；指标样本数与配对用例数不同时单独标注 n。"
            "多个种子和架构设置不是独立电路样本，不据此声称统计显著性。", "",
            "串行计时先对每个用例/变体的 3 次运行取中位数，再作配对比率。其他矩阵的并行运行时间仅保留在 CSV 中作筛查。"
            "计时在共享主机进行，未独占处理器或固定 CPU 频率。", ""]
    for group, title in GROUPS.items():
        text.extend([f"## {title}", "", "| 方法 | 合法结果/运行 | 配对用例 | CPD | 线长 | 垂直资源 | 跨层连接均值延迟 |", "|---|---:|---:|---:|---:|---:|---:|"])
        for variant in ORDER:
            summary = summaries.get((group, variant))
            if not summary:
                continue
            ratios = summary["ratios_to_a0"]
            text.append(f"| {label(variant)} | {summary['valid_solutions']}/{summary['runs']} | {summary['paired_cases']} | " +
                        " | ".join(percent(ratios.get(metric), summary["paired_cases"]) for metric in ["critical_path_ns", "wirelength", "vertical_channels", "routed_delay_remote_mean_ns"]) + " |")
        text.append("")
    text.extend(["## 直接归因比较", "", "下表使用各比较双方共同成功的相同用例，避免用不同分母的总体均值相减。", "",
                 "| 数据集 | 分子 / 分母 | 配对用例 | CPD | 线长 | 垂直资源 |", "|---|---|---:|---:|---:|---:|"])
    for comparison in data["comparisons"]:
        if comparison["dataset"] not in GROUPS or comparison["dataset"] == "sequential_timing":
            continue
        ratios = comparison["ratios"]
        text.append(f"| {comparison['dataset']} | {label(comparison['treatment'])} / {label(comparison['baseline'])} | {comparison['paired_cases']} | " +
                    " | ".join(percent(ratios.get(metric), comparison["paired_cases"]) for metric in ["critical_path_ns", "wirelength", "vertical_channels"]) + " |")
    text.extend(["", "## 串行计时原始汇总", "", "范围为 3 次测量的最小值—最大值，**不是置信区间**。"
                 "VPR Routing took 包括路由阶段内的规划；进程 wall time 还包括启动、图读取和报告等。所有计时运行均开启相同逐网络时序 CSV。", "",
                 "| 用例 | 方法 | 路由秒中位数 [范围] | wall 秒中位数 | 峰值 RSS MiB 中位数 | heap pushes 中位数 |", "|---|---|---:|---:|---:|---:|"])
    timing = defaultdict(list)
    for row in rows:
        if row["dataset"] == "sequential_timing" and row["valid_solution"]:
            timing[row["circuit"], row["variant"]].append(row["metrics"])
    for (case, variant), metrics in sorted(timing.items(), key=lambda item: (item[0][0], ORDER.index(item[0][1]))):
        seconds = [r["router_seconds"] for r in metrics]
        text.append(f"| {case} | {label(variant)} | {statistics.median(seconds):.3f} [{min(seconds):.3f}—{max(seconds):.3f}] | "
                    f"{statistics.median(r['process_wall_seconds'] for r in metrics):.3f} | "
                    f"{statistics.median(r['peak_rss_kib'] for r in metrics)/1024:.1f} | "
                    f"{statistics.median(r['heap_pushes'] for r in metrics):.0f} |")
    text.extend(["", "## 失败记录", "", "失败和超时不作为合法 QoR；VPR 提前收敛预测失败不构成不可布线证明。", "",
                 "| 数据集 | 用例 | 变体 | 状态 | 原生终止信息 |", "|---|---|---|---|---|"])
    for row in rows:
        if row["native_success"]:
            continue
        reason = row["metrics"].get("native_abort_reason", row["metrics"].get("native_failure_reason", "详见该运行 vpr.log"))
        text.append(f"| {row['dataset']} | {row['circuit']} | {label(row['variant'])} | {row['status']} | {reason} |")
    text.extend(["", "## 图与底层数据", "", "- [全部运行 CSV](../results/analysis.csv)；[带哈希、审计和配对比较的 JSON](../results/analysis.json)。",
                 "- [逐迭代拥塞/CPD/线长](../results/convergence.json)，迭代 heap 数受原生日志显示舍入影响，总 heap 计数使用原生整数统计。",
                 "- [QoR](figures/qor.png)；[相同剪枝下逐用例比较](figures/attribution.png)；[成功/失败矩阵](figures/native20_status.png)；[串行运行时间](figures/timing.png)。",
                 "- 详细有向路径审计在 `results/audits/`；原始命令、日志、route、资源使用和输入哈希在 `results/runs/<run>/`。", ""])
    (ROOT / "docs/实验结果.md").write_text("\n".join(text))

    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
    variant_order = ORDER[1:11]
    panels = [("native20_w100", "20-circuit fixed-input study"), ("architecture_sweep", "Architecture sensitivity"),
              ("paired_seeds_w100", "Paired placement seeds")]
    figure, axes = plt.subplots(1, 3, figsize=(15, 5.2), sharey=True)
    for ax, (group, title) in zip(axes, panels):
        for offset, metric, color, caption in [(-.16, "critical_path_ns", "#206a9a", "CPD"), (.16, "wirelength", "#d57928", "Wirelength")]:
            xs, ys = [], []
            for index, variant in enumerate(variant_order):
                ratio = summaries.get((group, variant), {}).get("ratios_to_a0", {}).get(metric)
                if ratio:
                    xs.append(100 * (ratio["geomean"] - 1)); ys.append(index + offset)
            ax.scatter(xs, ys, color=color, label=caption, s=35)
        ax.axvline(0, color="0.5", linewidth=.8)
        ax.set_title(title); ax.set_xlabel("Geometric mean change vs A0 (%)")
        ax.grid(axis="x", alpha=.2)
    axes[0].set_yticks(range(len(variant_order)), [label(v) for v in variant_order]); axes[0].invert_yaxis()
    axes[0].legend(loc="best")
    figure.suptitle("Jointly legal paired cases only; failures remain in the separate status table" + (" [PROVISIONAL]" if data["provisional"] else ""))
    figure.tight_layout(); save_figure(figure, figures / "qor")

    figure, axes = plt.subplots(1, 3, figsize=(15, 4.6))
    for ax, (group, title) in zip(axes, panels):
        comparison = next((r for r in data["comparisons"] if r["dataset"] == group and
                           r["baseline"] == "a0_prune" and r["treatment"] == "a4_subtree"), None)
        if comparison:
            ratios = list(comparison["case_ratios"].values())
            ax.scatter([100*(r["critical_path_ns"]-1) for r in ratios],
                       [100*(r["wirelength"]-1) for r in ratios], color="#206a9a", alpha=.65, label="Paired case")
            means = comparison["ratios"]
            ax.scatter(100*(means["critical_path_ns"]["geomean"]-1), 100*(means["wirelength"]["geomean"]-1),
                       marker="D", color="#d57928", s=65, label="Geometric mean")
            title += f" (n={comparison['paired_cases']})"
        ax.axhline(0, color="0.5", linewidth=.8); ax.axvline(0, color="0.5", linewidth=.8)
        ax.set_title(title); ax.set_xlabel("CPD change (%)"); ax.set_ylabel("Wirelength change (%)")
        ax.grid(alpha=.15)
    if axes[-1].get_legend_handles_labels()[0]:
        axes[-1].legend()
    figure.suptitle("A4 subtree / A0 with identical pruning threshold; lower-left improves both metrics")
    figure.tight_layout(); save_figure(figure, figures / "attribution")

    native = [r for r in rows if r["dataset"] == "native20_w100"]
    circuits = sorted({r["circuit"] for r in native})
    variants = ORDER[:11]
    values = np.full((len(circuits), len(variants)), np.nan)
    for row in native:
        values[circuits.index(row["circuit"]), variants.index(row["variant"])] = 1 if row["valid_solution"] else 0 if not row["native_success"] else .5
    figure, ax = plt.subplots(figsize=(11, 8))
    ax.imshow(values, cmap=matplotlib.colors.ListedColormap(["#d7a4a4", "#e6d79b", "#71aaa0"]), vmin=0, vmax=1, aspect="auto")
    for row_index in range(len(circuits)):
        for column_index in range(len(variants)):
            value = values[row_index, column_index]
            symbol = "?" if np.isnan(value) else "S" if value == 1 else "F" if value == 0 else "P"
            ax.text(column_index, row_index, symbol, ha="center", va="center", fontsize=7)
    ax.set_yticks(range(len(circuits)), circuits); ax.set_xticks(range(len(variants)), [label(v) for v in variants], rotation=45, ha="right")
    ax.set_title("20-circuit study: S=legal+audited; F=failed/timeout; P=audit pending; ?=pending")
    figure.tight_layout(); save_figure(figure, figures / "native20_status")

    if timing:
        cases = sorted({case for case, _ in timing})
        figure, axes = plt.subplots(1, len(cases), figsize=(14, 5), squeeze=False)
        for ax, case in zip(axes[0], cases):
            variants = [v for v in ORDER if (case, v) in timing]
            for index, variant in enumerate(variants):
                measurements = [r["router_seconds"] for r in timing[case, variant]]
                median = statistics.median(measurements)
                ax.errorbar(median, index, xerr=[[median-min(measurements)], [max(measurements)-median]], fmt="o", color="#206a9a", capsize=3)
            ax.set_yticks(range(len(variants)), [label(v) for v in variants]); ax.invert_yaxis()
            ax.set_xlabel("Native routing seconds (median; min-max)"); ax.set_title(case); ax.grid(axis="x", alpha=.2)
        figure.suptitle("Three sequential repetitions; shared host; all planning included")
        figure.tight_layout(); save_figure(figure, figures / "timing")
    print(json.dumps({"provisional": data["provisional"], "rows": len(rows), "report": "docs/实验结果.md"}))


if __name__ == "__main__":
    main()
