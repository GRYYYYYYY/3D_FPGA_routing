# TPU-OS整臂判定与完整配对

**实际配对：通过。**

| 角色 | 质量准入 | CPD(ns) | 线长/SB/CB | 自身根setup改善/退化/hold新增 | 完整命令(s) | PSS(GiB) |
|---|---|---:|---:|---:|---:|---:|
| native | passed | 7.812205993 | 360117/17/1563 | 108/0/0 | 941.321435 | 2.808 |
| domain | passed | 7.812205993 | 360121/17/1563 | 108/0/0 | 944.174382 | 2.831 |

D−N：线长+4、SB+0、CB+0、CPD+0.000000000ns；setup 0改善/0退化，hold新增0。

单次完整N/D实测费用比1.003031（+0.303%），仅描述该次配对，不是N/D/D/N对称计时或统计速度主张。未拼接组件费用。

原独立检查及后续只读费用另列：
- native原检查：11.896343640983105秒。
- domain原检查：11.670919381082058秒。
- native只读阶段：21.580909秒，original_full_and_additional_raw_admission_passed。
- domain只读阶段：22.075162秒，original_full_and_additional_raw_admission_passed。
- pair只读阶段：12.896291秒，matched_full_quality_pair。

TPU-OS是不同于TPU-WS的数据流/网表，仍属同TPU工作负载家族和两层Hybrid-O架构；无新架构、未见留出集或应用SDC主张。原失败、拒绝及费用保留。只有本次实际准入支持的表格和适用性可更新，投稿07在此之前保持。
