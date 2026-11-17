# LSTM整臂判定与完整配对表

**整臂准入：通过；实际配对：通过。**

| 角色 | 准入 | CPD(ns) | Wire / SB / CB | 自身根setup改善/退化/hold新增 | 完整原命令(s) |
|---|---|---:|---:|---:|---:|
| native | passed | 14.600438192 | 2388083/492/8316 | 20/5/0 | 7615.074177 |
| domain | passed | 14.600438192 | 2390270/422/8316 | 71/27/0 | 26657.726866 |

原执行结束与原验证失败均保持。上述通过指本次补充整臂准入；没有把失败候选改写为成功。

domain完整命令受外部归档ctime干扰。只报告实测26657.726866秒，不推算无干扰时间、不计算正式完整时间比。BNN匹配N/D/D/N的+24.91%完整开销结论保持独立。

实际配对D−N：wire +2187，SB −70，CB 0，CPD 0；setup 51改善/23退化，hold新增0。起点树、约束、端点向量及六项图载荷实际匹配，两臂配置仅domain模式/反馈不同。

本次只读核验实测（与完整算法命令分列）：
- domain_supplement: readonly_gate_passed；333.35752256959677秒。
- domain_raw: readonly_gate_passed；709.5322254709899秒。
- pair_matching: readonly_gate_passed；13.744580622762442秒。

原419SB、2390877wire候选超cap402，原策略拒绝保持。ctime失败的另一个419SB、2390832wire候选超357，原FULL_STA_failed保持，自己的CPD/端点已单独核验。后者没有历史成功回执，也未被控制器接受。

四档代价对照已完成：0/0.5为251140/9/654，1/2为251125/9/654；全部合法但违反CB≤653。共享域加失败释放给251160/9/653；机制增量仅限该同源固定组，不外推所有权重或输入。CLSTM历史恢复只留补充材料。


六页[投稿06派生修订版07](../research/dac_v14_20261112/submission_narrative_07/build/main.pdf)已完成源码/PDF核对与版面审阅，原06保持。更新表I的LSTM两臂、摘要、适用性、结论，以及表II的已完成四档代价增量；问题、引言/prior-art、方法、BNN完整取舍及表III数值保持。

[完整配对表](../research/dac_v14_20261112/submission_narrative_07/LSTM_PAIR_TABLE.md) · [证据影响与作者审阅](../research/dac_v14_20261112/submission_narrative_07/EXPERIMENT_IMPACT.md) · [完整准入判定](../research/dac_v14_20261112/LSTM_domain_whole_admission_03/admission_decision.json)。

本轮新执行native/STA为0。原失败、被拒候选、后续接受与费用均保留，两个419SB候选不混用。独立LSTM整臂核验已经终结，不再列作待办；CLSTM历史恢复只留补充。原CP1r3冻结核验失败并未改写，新增结论属于实际补充整臂准入。

公开证据基点9734eee及279bdb4保留；本次快照接续c304f2bb79a6636c1abeef7c758856791b8a15e5。Git成功和本轮队列终结不构成研究Goal完成条件。
