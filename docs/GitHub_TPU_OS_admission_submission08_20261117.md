# TPU-OS完整配对通过与投稿08

TPU-OS两臂原始完整检查、来源/请求/实际状态连续性/FULL/原始STA/端点/物理及实际配对均通过。原raw准入01失败保留，02只识别实际timing-repair worker格式：冻结旧二进制并未实现资源阶段seed-order/failure-release开关，不能猜填字段。源码、执行二进制、worker命令及请求均绑定；资源事务检查未改，其余科学门槛继续执行。没有native或STA重跑。

| 角色 | CPD(ns) | 线长 | SB | CB | 自身根setup改善/退化/hold新增 | 完整命令(s) | PSS(GiB) |
|---|---:|---:|---:|---:|---:|---:|---:|
| native | 7.812205993 | 360117 | 17 | 1563 | 108/0/0 | 941.321435 | 2.808 |
| domain | 7.812205993 | 360121 | 17 | 1563 | 108/0/0 | 944.174382 | 2.831 |

实际起点360013wire/35SB/1563CB相同；两臂最终完整端点向量相同，domain多4wire。两臂均4次资源接受、无失败释放、无owner事务。因此两臂共有的18SB节省不能归给域限制、失败释放或owner协调；这个输入未观察到domain增量。完整命令单次D/N=1.00303079（+0.303%），仅描述本次共同环境中的一次配对，不是对称交错或统计费用主张。

TPU-OS与TPU-WS是不同数据流/网表，属于同TPU家族和两层Hybrid-O架构；不是新架构或未见留出集，不引出应用SDC主张。资源菜单正常闭合并不证明全局最优，不为4wire追加局部调优。

费用分列：原独立checker11.896344/11.670919秒；原raw01三阶段22.034798/21.227776/0.155744秒并保留失败，等待原队列1231.207077秒。只读02三阶段21.580909/22.075162/12.896291秒，完整队列56.586478秒。核验费用未拼入算法完整时间，也未从完整命令中扣除组件时间。

[完整配对与判定](../research/dac_v14_20261112/TPU_OS_complete_admission_02/PAIR_TABLE.md) · [准入记录](../research/dac_v14_20261112/TPU_OS_complete_admission_02/admission_decision.json) · [机制事实与边界](../research/dac_v14_20261112/TPU_OS_complete_admission_02/mechanism_summary.json)

## 投稿交付

[六页投稿08 PDF](../research/dac_v14_20261112/submission_narrative_08/build/main.pdf) · [源码](../research/dac_v14_20261112/submission_narrative_08/main.tex) · [影响清单](../research/dac_v14_20261112/submission_narrative_08/EXPERIMENT_IMPACT.md)

投稿07完整保护，08仅更新相关摘要、表I、迁移覆盖、适用性和结论。正文表I仍36行：两行重复BNN冷启动数值移入补充表，但正文保留22.95%历史冷启动费用和24.91%匹配交错费用。LSTM已准入质量与归档干扰限制、四档代价对照、prior-art和方法均保持。TPU-WS原超时仍列出，与TPU-OS严格区分。六页构建、文本/数据一致性、整稿及表I视觉检查通过。

当前登记的原始执行和必要只读均终结，剩余角色0、核验阶段0；不再沿用旧ETA。后续重点是依据共享冗余、阻塞及预算区分机制适用条件，并核对不同输入/物理起点后另行登记匹配确认；不是重跑BNN或TPU局部点。当前稿无需等待新实验。Goal保持active，队列终结或负结果不构成研究完成。
