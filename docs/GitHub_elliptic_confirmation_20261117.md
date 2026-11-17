# Elliptic独立电路确认：实际输入准入与固定队列

[登记与范围](../research/dac_v14_20261112/cp1r5_elliptic_pair_01/STATUS.md) · [实际输入核验](../research/dac_v14_20261112/VTR_elliptic_input_01/completion.json) · [冻结完整配对计划](../research/dac_v14_20261112/cp1r5_elliptic_pair_01/plan.json) · [后续只读准入计划](../research/dac_v14_20261112/ELLIPTIC_complete_admission_01/plan.json)

使用固定VTR提交中的elliptic.blif：不同于现有CP1电路的公开映射顺序网表，3602个.names、1122个re pclk锁存器。未根据旧QoR选输入；不称未见测试集、新架构或应用SDC实例。

已完成实际打包/布局与字节核验。395个CLB、245个IO共640块，完整块名和唯一坐标匹配，打包语义保持。按预登记容量规则选择现有n40/W100 Hybrid-O，实际布局seed21固定。成功打包1.568822秒，布局12.939523秒；此前三次准备失败0.038256/0.151780/0.157401秒均保留。没有路由查询；打包/布局内部STA与费用属于上游。

已启动固定CP1r5 native→domain完整队列，来源采用实际回执派生的明确适配记录，不伪造历史manifest。两臂预算、接受规则、查询与终结选点均未改变。终结后已登记并启动等待的native raw、domain raw、pair三个只读阶段，复用原核验器及已验证的时序字段适配，不新增机制或例外。

本次报告是启动时快照：当时native资源流程运行，domain尚未执行，三个只读阶段等待原owner终结。尚无完整合法质量或配对收益。没有同输入整臂观测前不给时间点估计，随后根据实际native完整费用更新domain条件ETA；阶段超时不视为整个流程上界。

需要回答的科学问题是：依赖感知重构能否在不同电路上形成预算内资源—时序取舍，完整费用是否有工程价值。无切口、无收益、退化、失败和超时均保留。只有整臂和配对通过后，才更新相关实验行、适用性、摘要和结论。

[六页投稿09](../research/dac_v14_20261112/submission_narrative_09/build/main.pdf)保持独立作者审阅；已核验LSTM整臂、BNN对称费用及四档代价对照不变。历史CLSTM恢复留补充材料。原公开9734eee/279bdb4与后续提交保留，研究Goal保持active。
