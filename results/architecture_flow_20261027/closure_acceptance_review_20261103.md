# 验收逐项核查（进行中）

验收依据为 `requirements.json`，该文件的约束未因本核查而更改。以下为截至本次核查的证据与未完成事项；“已登记”不等于全部科学或完整性验收通过。

| 项目 | 当前证据与范围 | 状态或限制 |
|---|---|---|
| provenance | `benchmark_protocol.json`、`registered_study_continuation_20261029/registration.json`、二进制构建清单和 `configs/sources.lock.json` | 版本和执行脚本已登记；完整共享输入重哈希尚在执行 |
| physical_audit | `graph_audits_v2/`、各 `benchmark_models/*/manifest.json`、`capacity_selection.json` | 统计属于所声明的共同平面控制模型；并非等面积或等过孔预算 |
| compatibility | `crossflow_validation/summary.json`、`adapter_validation/summary.json`、`evaluation_analysis/input_bindings.json` | 两项试运行汇总通过；正式合法样本还由分析器逐对检查语义、布局、图与审计绑定；完整输入重哈希待结束 |
| dual_baseline | `evaluation_analysis/summary.json` 的 `routing_dual`，及 `closure_common_cohort_maxima_20261103.json` | 均值与修正极值使用共同完整电路集合；2D 仅匹配逻辑容量，资源差异已披露 |
| placement_routing | 协议 `evaluation` 项、评估案例及 `factorial_interactions` | 双布局与 A0/R1/B2 已登记分析；覆盖受失败影响，不能将成功子集外推 |
| hyperparameters | `training_jobs.json`、`selected_configs.json`、`training_analysis/summary.json` | 每种变体八组登记点、训练选参和测试种子分离；多个参数联动，不能识别单参数因果效应 |
| ablations | `evaluation_analysis/summary.json` 的 `ablations` | 固定与每变体等预算调参均有结果，失败留在登记分母；共同完整样本较少 |
| architecture_ranking | 同一汇总的 `architecture_rankings` | 只有 1/14 个测试电路在所有架构、流程、三个种子共同成功，不能支持普遍排序反转 |
| external_baselines | `published_reference_analysis.json`、`evaluation_analysis/summary.json`、`docs/三基线对比_2026-10-27.md` | 文献基线、后续移植版 B2、官方 A0 分列；缺失相同分母时不计算论文直接比率 |
| timing | `serial_protocol.json`、`serial_analysis/summary.json`、`p1_thread_envelope_review_20261031.json` | 三次串行重复及准备成本已记录；共享主机非独占；P1 出现额外线程，与每进程单线程约束矛盾，该约束未通过 |
| validation | 各案例 `route_audit.json`、分析输入绑定及 `closure_terminal_allocation_scan_20261103.json` | 合法样本同时要求 VPR FULL 和限定范围的独立审计；后者不覆盖完整终端映射等检查 |
| closure | `closure_historical_rehash_20261103.json`、`closure_analysis_bindings_rehash_20261103.json`、`closure_shared_graphs_rehash_20261103.json` | 历史清单 1,137 项、分析绑定 8,584 项、共享图与架构 144 项重哈希通过；最终归档待完成 |
| partition_balance_sensitivity | `partition_balance_sensitivity_protocol.json`、`balance_invocations/all.json`、`balance_analysis/summary.json` | 48 个登记组合已处理并保留失败；literal 与 relative3 分列，训练/测试各两个电路，不能外推 |

所有项目仍需在完整输入复核和最终归档后重新判定。`threads_per_process=1` 的矛盾不得标为通过，也不能以说明限制替代实际满足该约束。
