# Frisc固定确认：明确SDC与有跨层占用、无当前冗余组的初始观察

[登记与范围](../research/dac_v14_20261112/cp1r5_frisc_pair_01/STATUS.md) · [实际输入](../research/dac_v14_20261112/VTR_frisc_input_01/completion.json) · [完整确认计划](../research/dac_v14_20261112/cp1r5_frisc_pair_01/plan.json) · [后续三项准入](../research/dac_v14_20261112/FRISC_complete_admission_01/plan.json)

Frisc为固定VTR提交中的另一公开映射顺序电路：3539个.names、886个锁存器。它是不同电路，不是Elliptic换seed。实际打包393CLB、136IO，共529块；预先固定最小已核验设备、各资源占用≤80%规则，选择已有n25/W100 Hybrid-O，未用路由质量选择尺寸。n25已有独立物理/同平面/导入字节及原生完整检查；本次将这个benchmark_models目录之外的现成设备纳入可用清单，没有生成新图。不同尺寸不称新架构族，也不能隔离归因电路或架构变化。

真实seed21布局在层0有82块、层1有447块。打包1.564739秒、布局6.496700秒；费用属于上游。两臂共享明确20ns pclk SDC；未额外指定I/O延迟，实际原生时序解释须在后续完整证据中匹配。这是基准约束，不是外部应用要求。

固定CP1r5 N→D完整队列及终结后三项raw/pair准入已启动，算法、预算、接受和终结规则不变。启动快照后的native资源阶段正常终结：初始16.383991053ns、41568wire/0SB/256CB，multi-crossing nets=0，正冗余同层owner目标/可用联合组均0，资源尝试/接受均0。与Elliptic零跨层占用不同，Frisc有跨层占用，但当前结构没有登记选择器可用的冗余组。不能由占用数推断可释放性；该阶段记录不证明全局最优、完整无收益或配对结果。

时序阶段及domain后续按原规则继续，全部失败、退化和拒绝保留，不根据QoR重选布局或尺寸。尚无同输入完整费用时，不用Elliptic或准备费用估算完成点；native完整结束后更新条件ETA。

[六页投稿10](../research/dac_v14_20261112/submission_narrative_10/build/main.pdf)保持独立作者审阅。没有把未完成Frisc结果写为收益。通过完整准入后只更新对应实验行和范围；原公开基点、投稿稿与本地更新保留，研究Goal继续active。
