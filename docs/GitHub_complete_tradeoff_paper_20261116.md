# 完整配对取舍进入六页正文

[正文10 PDF](../research/dac_v14_20261112/paper_snapshots/current_complete_tradeoffs_20261116/build/current_repair_main.pdf)及[源码／证据绑定](../research/dac_v14_20261112/complete_tradeoff_paper_binding_10.json)已封存。六页、六节、九条参考文献；33行主表逐字保持，包括31个完整尝试和2个局部条目。没有新增独立实验结果，也没有改动CP1或已登记实验。

主结果图由单个BNN输入的历史局部散点，改为9个合法完整配置配对：分别显示SB＋CB总计数、线长、CPD和完整时间相对native的变化，另列SB／CB绝对变化。数据直接来自正文09绑定的完整结果，未拼接局部费用或当前运行中的质量。各面板独立刻度；每个配对各自使用native分母。配置行不等于独立电路／布局数，无汇总胜率或统计加速主张。

无收益的Softmax、SPMV、Robot-SDC及架构限定案例仍在图中。Conv-layer／Attention的4个初始路由失败和CLSTM／Robot-p1的4个输入加载失败保留在表及图注中，不给失败尝试构造质量差值。原BNN投影、原说明及其历史计数保存在[补充材料](../research/dac_v14_20261112/paper_snapshots/current_complete_tradeoffs_20261116/supplement/historical_BNN_projection/provenance.json)。

开销节新增已核验分解：原1821.07秒完整额外时间中1692.84秒处于资源事务（92.96%）；native/domain分别执行70/1361次连接查询，重复查询分别计数。38.23/1207.26秒核心时间嵌套在上述完整费用内，不能相加。原SB减少47.56%、SB＋CB减少约0.797%、完整时间增加22.95%的结论保持。

实际编译为六页；主表、机制图及参考文献与前版一致；新图数据复算、成本数字绑定和实际渲染检查通过。摘要将“独立feedback”明确为同输入的单独反馈实验，避免混淆独立输入证据。

发布准备时，BNN domain工程臂已接受8个资源步骤，第九轮仍由原控制器执行；完整质量／成本尚未闭合。reduction、修正CLSTM、修正Robot-p1、固定CP1两电路四臂确认、robot三臂联合机制对照按原队列等待。以后续本地终结回执为准，不重复完成批次；本次论文整理不是确认批次完成或研究Goal完成。
