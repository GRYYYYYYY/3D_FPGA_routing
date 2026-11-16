# 六页正文：路由相关工作与贡献边界

本次继承 `42ae2e4`，公开证据基点保持 `9734eee`。原实验、输入、队列版本和本地 HEAD／索引保持不变；研究 Goal active，不设固定日期、总调用次数或矩阵完成停止条件。

[正文](../research/dac_v14_20261112/paper_snapshots/current_routing_position_20261116/build/current_repair_main.pdf)仍为六页、22行统一主表，参考文献由4项增至9项。新增五项直接相关原始工作，并按首次引用顺序排列：

- [Liu 等，2014，期刊原始摘要](https://www.jcad.cn/en/article/id/55a65d33-15d9-4ecf-99e5-27e8d9edf3a9)：已有 PathFinder 后的关键连接时序修复。
- [AIR，ASP-DAC 2020 原论文](https://csuncle.com/uploads/aspdac2020/pdf/p338_5C-2.pdf)：增量保留合法子树及多次收敛；作者站点访问失败后核对了原论文镜像。
- [CRoute，FCCM 2019 作者机构稿](https://biblio.ugent.be/publication/8640095)：时序驱动的连接级路由。
- [LaZagna，ICCAD 2025 作者版本](https://arxiv.org/abs/2505.05579v4)：可配置三维架构与垂直互连基础设施；明确区分出版年份和2026年作者修订。
- [Poolad 等，2026，v3](https://arxiv.org/html/2606.06421v3)：CHANZ 与多芯粒 lookahead；当前结果尚未覆盖这些架构和启发式。

正文因此明确：当前 STA、保留子树、增量重路由及多次收敛都是既有技术。研究贡献落在条件跨层共享域、按网络失败释放、容量证书驱动的 owner 范围和固定约束下的完整候选接受，以及对应局部归因和完整费用证据；没有声称重新发明原生路由器，或实测优于上述外部实现。AIR 跨收敛保留历史拥塞成本，与当前导入上下文重置价格的模式不同，这项边界已写入方法部分。

[补充比较表与来源定位](../research/dac_v14_20261112/routing_related_work_01/comparison.md)区分已有机制、当前证据及尚未验证范围，没有把不同论文的数值比率混入本地主表。两段局部路径／核心时间及 budget64 轨迹细节从正文移入补充材料，主文保留机制含义。两幅图、22行数据、671条观测及34个完整质量配置的口径均未改变。全部六页完成视觉检查，无溢出或截断；[源码／PDF／证据绑定](../research/dac_v14_20261112/routing_position_paper_binding_05.json)已封存。

另修正一处状态矛盾：旧 implementation_status_09 继承的“完整时序组合尚未迁移”布尔值，与已通过的 dev03 代码迁移证据冲突。[status_10](../research/dac_v14_20261112/unified_confirmation_candidate_01/implementation_status_10.json)将该字段改为已迁移，保留旧记录；实际完整 native 执行和确认冻结仍为未完成。

本轮没有新增 native 调用、独立输入结果或完整费用结论。BNN domain 仍在运行；线长组合、robot no-release、完整 terminal-wire BNN、跨输入配对、独立运行检查及 robot owner 范围对照按原顺序接续。当前完整 BNN 的 SB减少47.56%、SB＋CB约减少0.797%、完整时间约增加22.95%仍是对应原匹配两臂的结论。最新进程状态见[当前入口](../research/dac_v14_20261112/CURRENT_STATUS.md)，不将排队或结构模型写成已完成实验。
