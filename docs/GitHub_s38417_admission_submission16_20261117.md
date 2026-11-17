# s38417 完整配对与投稿16

**实际匹配及整臂准入通过；domain 无额外增量。** 源、完整请求、图字节、原始完整验证、FULL、STA、端点向量、物理、状态连续性及配对检查均通过。两臂是同一公开电路、同一真实布局、同一 Hybrid-O 架构族和明确基准 SDC；不是两个独立电路或新架构。

| 角色 | CPD ns | 线长 / SB / CB | 自身根 setup 改善 / 退化 / 新增 hold | 完整命令 s | 峰值采样 PSS GiB |
|---|---:|---|---|---:|---:|
| native | 11.057135652 | 47973 / 0 / 191 | 137 / 7 / 0 | 535.287 | 1.270 |
| domain | 11.057135652 | 47973 / 0 / 191 | 137 / 7 / 0 | 535.068 | 1.263 |

最终端点全向量相同。初始 native 选择器有2个多次跨层网及2个可选组；两臂各自的首个资源事务都达到线长−24、SB−2、CB不变、CPD不变。原生臂已经实现该局部释放，不能归给domain；完整流程没有domain增量。两臂仅单次顺序计时，不作交错开销或统计加速主张。每臂原完整验证分别2.657/2.525秒，后续native/domain/pair只读检查分别4.057/3.966/2.285秒；上游pack/place分别2.416/14.767秒，均与完整命令分列。

[投稿16 PDF](../research/dac_v14_20261112/submission_narrative_16/build/main.pdf) · [50行完整主表](../research/dac_v14_20261112/submission_narrative_16/COMPLETE_PAIR_TABLE.md) · [配对表](../research/dac_v14_20261112/S38417_complete_admission_01/PAIR_TABLE.md) · [准入判定](../research/dac_v14_20261112/S38417_complete_admission_01/admission_decision.json) · [适用性](../research/dac_v14_20261112/mechanism_applicability_current_06/APPLICABILITY.md) · [未来实验影响](../research/dac_v14_20261112/submission_narrative_16/EXPERIMENT_IMPACT.md)。

投稿15保留。投稿16在摘要、主表、适用范围和结论纳入新结果，前48行及方法、相关工作、机制对照保持；六页、10条参考文献、无排版溢出并完成目视检查。七页初稿保留。BNN对称完整开销24.91%、LSTM归档干扰及四档代价对照的限定结论保持；失败和历史恢复不删除。

该确认及全部既有后续检查终结，当前无已登记运行角色。普通无增量结果用于调整适用性判断，不构成研究Goal结束；下一项应针对有共享机会但原生路径受到可验证容量阻塞的真正不同输入，避免重复已释放的单一状态。
