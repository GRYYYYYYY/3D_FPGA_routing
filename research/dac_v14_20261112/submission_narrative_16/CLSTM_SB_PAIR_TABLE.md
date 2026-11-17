# CLSTM-small SB-only整臂判定与完整配对

**实际配对：通过。**

| 角色 | 质量准入 | CPD(ns) | 线长/SB/CB | 自身根setup改善/退化/hold新增 | 完整命令(s) | PSS(GiB) |
|---|---|---:|---:|---:|---:|---:|
| native | passed | 6.590324286 | 234918/941/0 | 176/652/0 | 1430.079576 | 2.778 |
| domain | passed | 6.590324286 | 234970/940/0 | 193/644/0 | 918.129700 | 2.770 |

D−N：线长+52、SB-1、CB+0、CPD+0.000000000ns；setup 85改善/22退化，hold新增0。

单次完整N/D实测费用比0.642013（-35.799%），仅描述该次配对，不是N/D/D/N对称计时或统计速度主张。未拼接组件费用。

原独立检查及后续只读费用另列：
- native原检查：16.86671055853367秒。
- domain原检查：10.188255809247494秒。
- native只读阶段：38.647765秒，original_full_and_additional_raw_admission_passed。
- domain只读阶段：18.725139秒，original_full_and_additional_raw_admission_passed。
- pair只读阶段：17.756773秒，matched_full_quality_pair。

CLSTM-small是历史Hybrid-O恢复中同一个已知电路；此处SB-only图及实际布局不同，不计新电路、新架构家族、未见留出集或应用SDC。架构和布局同时不同，不单独归因架构。原失败、拒绝及费用保留。只有本次实际准入支持的表格和适用性可更新，投稿08在此之前保持。
