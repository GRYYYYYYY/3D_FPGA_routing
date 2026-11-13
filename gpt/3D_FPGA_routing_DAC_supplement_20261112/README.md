# 3D_FPGA_routing：DAC 2027 补充实验执行包

日期：2026-11-12，北京时间。用户已确认摘要注册完成。

本包仅针对 `GRYYYYYYY/3D_FPGA_routing`。公开仓库截至本次核对仍为 `b132a1d13eec8351cfcdc371bfc03611f678291b`（2026-11-09）。服务器端 v13 稿件和最终实验结果尚未在本次分析中读取。本包中的新实验均为待执行设计，没有在用户服务器上启动。

## 使用方法

1. 将整个目录放到服务器项目目录下的独立位置；保留现有冻结结果。
2. 将 `CODEX_TASK.txt` 内容发给该项目现有 Codex 会话。它应先读取服务器最新 v13、最终结果和已存在的补充实验，复用已完成的等价工作，再执行仍有缺口的部分。
3. `EXPERIMENT_PROTOCOL.md` 是详细设计；`experiment_matrix.json` 是 102 个预定运行角色的明确列表。该 JSON 不是现有项目 runner 的直接输入，需由 Codex 适配并绑定实际输入、二进制及配置后注册。
4. `summarize_pairs.py` 是可立即运行的只读复算工具。它不调用 VPR，不改变已有实验。示例：

```bash
python3 /path/to/this-package/summarize_pairs.py \
  --observations results/architecture_flow_20261027/serial_strict_reexecution_20261103/evaluation_analysis/observations.csv \
  --out results/dac_supplement_20261112/pair_summary_current \
  --source-label 'Server final frozen study; specify commit and audit record here'
```

输出目录必须尚不存在，以免覆盖旧报告。脚本默认的总体是原协议 14 个 heldout 电路、seed 21/23/25、SB/CB-O/Hybrid-O、P0/P1、W100、A0/R1。若服务器最终协议不同，先核对再显式传入选择参数，不能为了得到更好结果而删样本。

## 已实际完成的工作

- 核对公开仓库版本和相关源码补丁。
- 独立复算公开快照的 252 个 A0/R1 配对；`baseline_snapshot_20261109/` 包含输出。117 个双方合法配对中，CPD 为 34 改善、51 持平、32 退化；A0 合法 118 个，R1 合法 117 个。
- 对新复算脚本的结果进行独立计数和输入 SHA-256 核对。
- 明确两个最小代码改动：共享 DP 的干净对照，以及具备局部等价依据的反向查询省略。

这些计数是 11 月 9 日快照的算术复核，不是服务器 v13 最终状态；脚本使用已记录的 legal 状态，没有重新审计原始 route。

## 预期交付

一份可复现的机制消融表、一份运行代价表、一份固定布局宽度诊断表，以及能够逐项对应这些证据的论文修订。性能没有改善时，同样交付完整结果并收窄相应主张。补充实验在 11 月 15 日 20:00 北京时间停止新增运行，11 月 16 日完成分析，17–18 日修改和审阅论文。

全文官方截止为 2026-11-18 17:00 US Pacific，即北京时间 11-19 09:00。内部以 11 月 18 日完成提交准备。

## 来源

- [公开快照](https://github.com/GRYYYYYYY/3D_FPGA_routing/commit/b132a1d13eec8351cfcdc371bfc03611f678291b)
- [机制归因核查](https://github.com/GRYYYYYYY/3D_FPGA_routing/blob/b132a1d13eec8351cfcdc371bfc03611f678291b/results/architecture_flow_20261027/serial_strict_reexecution_20261103/mechanism_attribution_review_20261106.json)
- [预最终结果核查](https://github.com/GRYYYYYYY/3D_FPGA_routing/blob/b132a1d13eec8351cfcdc371bfc03611f678291b/results/architecture_flow_20261027/serial_strict_reexecution_20261103/prefinal_summary_review_20261109.json)
- [R1 源码补丁](https://github.com/GRYYYYYYY/3D_FPGA_routing/blob/b132a1d13eec8351cfcdc371bfc03611f678291b/patches/snapshot_20261109/architecture_r1.patch)
- [DAC 官方投稿说明](https://dac.com/2027/program/research-manuscript-submissions)

