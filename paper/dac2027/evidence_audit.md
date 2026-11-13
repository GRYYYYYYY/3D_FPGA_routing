# 初稿证据核验范围

更新时间：2026-11-10，北京时间。本记录中的最初小文件核验针对训练、主测试、串行计时和平衡敏感性；宽度队列现已终态，其输入封存与[144角色配对凭据复核](data/width_pair_audit.json)单独报告。

## 已完成的核验

读取七份现有绑定清单：evaluation、serial、balance分析，execution contract、runtime dependency、training analysis和selected configurations。它们包含15,541个路径、14,244个独立inode，总计330.82 GiB。不重复读取指向相同inode的别名。

- 对不超过2 MiB的文件以及VPR/线程约束执行文件，重新计算SHA-256，并检查读取前后的文件身份及所有别名。11,061份文件、1.21 GiB均匹配；清单没有缺失路径或预期摘要冲突。
- 对1,136个独立evaluation运行，重新读取manifest、stdout及线程日志，核对分类、指标和已记录的单线程观察。全部一致：552合法、385路由失败、38内存分配失败、161超时。这里的计数去除了多个角色复用同一执行的重复项。
- 385个非合法运行仍有正的日志CPD。正数不是合法完成的证据；论文继续仅对合法、配对成功的结果计算性能比值。
- 训练分母为594：414合法、99路由失败、32内存分配失败、49超时。选参冻结时间为2026-11-04 10:52:44北京时间，早于首次heldout路由的11:09:03。该顺序不等于电路在历史上从未见过。

主测试的角色分母与上述独立执行分母不同：3D主测试756个角色有354合法、280路由失败、121超时及1内存分配失败；另有42个matched-2D角色，其中17合法。不能混合这些分母。

原始核验回执见[data/closed_metadata_audit.json](data/closed_metadata_audit.json)，逐文件记录见[data/closed_metadata_records.jsonl](data/closed_metadata_records.jsonl)。脚本[audit_closed_metadata.py](audit_closed_metadata.py)只写本论文目录，不启动VPR。

## 明确保留的缺口

3,183份大文件、约329.61 GiB在最初核验中只检查清单和存在性。原协调器退出后，独立、可续接的低优先级内容摘要复核已完成：3,183份均通过，0份失败，见[实际回执](build/deferred_file_integrity/summary.json)。该清单不含paired_width。已有独立route审计回执并不等于本轮重新运行了完整checker；线程记录检查也不提供比原观察/trace更强的证明。

## 新增机制证据

[analyze_connection_changes.py](analyze_connection_changes.py)读取两案例、四个已封存route及其独立审计：逐连接核对net ID、名称、Net_pin_index、SOURCE/SINK资源ID及坐标，再比较审计中的switch-delay和。四个route的摘要与原审计一致。

| 案例 | 跨层连接数 | 改善/相同/退化 | 平均switch延迟 A0→R1 (ns) | 平均改善 | 原生CPD改善 |
| --- | ---: | --- | --- | ---: | ---: |
| clstm_like.small | 3,902 | 626 / 2,735 / 541 | 1.55878→1.53305 | 1.65% | 12.96% |
| clstm_like.large | 10,863 | 3,485 / 4,617 / 2,761 | 1.92973→1.87781 | 2.69% | −11.45% |

两案例均为Hybrid-O/P0、W100、seed23。结果来自[data/connection_changes.json](data/connection_changes.json)。它们说明平均连接延迟改善可以伴随关键路径退化。这是zero-RC图上的实际互连switch延迟，排除局部逻辑/cluster内部延迟，不是原生STA路径分解、最终guide采用率或DP的独立因果效应。

文稿验证器还重新计算主均值与串行中位数比，核对补充证据来源摘要、计数一致性、七页结构和字体嵌入。检查数量和结果以[build/verification.json](build/verification.json)为准；这些检查不能替代原件核验或语义审计。

随后完成的[比较口径补充核验](comparison_contracts.md)另核对40图既有清单、552个合法运行的布局与输入凭据、180个串行进程的guard记录和时间区间，共987项检查。文稿验证器同时覆盖R1/A0、R1/B2、R1/R1-off三种串行对照。此步骤重新读取了布局坐标，但仍未读取全部大图或packed原件；原部分核验的3,183份延期清单保持历史原样。
