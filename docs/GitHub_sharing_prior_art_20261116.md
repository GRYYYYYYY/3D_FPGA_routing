# DAC 2027：已有机制、增量对照与论文贡献边界

研究 Goal 保持 active。本轮继承 `4d85fd6`，保留 `9734eee`、`279bdb4` 及后续更新；不覆盖冻结确认规则、本地开发或原始实验回执。

等待已登记实验时，补充核对了已有引用的[作者机构存档原文](https://backoffice.biblio.ugent.be/download/8640095/8640096)。六页正文进一步明确既有路由基础机制，补充材料新增贡献与归因对照。正文仍围绕当前 STA 选组、跨层共享域、失败释放、阻塞 owner 协调、完整接受规则与终结选点的关系展开。

新增对照区分两类证据：文献提供已发表机制的来源；本地匹配实验提供本研究的可检验增量及归因范围。前者不能替代复现实验，后者不能证明对外部路由器的性能领先。没有搬用跨论文性能数字，也没有声称未逐项研究的 prior art 缺少某个模块。

本地归因保持已有回执边界：R1 owner 的 native/domain 相同结果归于协调范围扩大；BNN 九个域引导资源角色没有实际失败释放事件；robot 的固定范围释放消融只支持对应局部可实现性／取舍。部分 owner 接续和局部消融不升级为完整控制器的普遍收益。补充对照绑定对应既有验证回执，没有重新执行图、原生查询或 STA。

新正文 paper18 已编译为六页并检查六页渲染及修改页整页。43条量化表格记录、九篇参考文献、机制图、结果图、字体和页边距保持不变。此前的种子来源修正继续保留。历史 paper17 与更早版本不改写；本轮没有增加完整实验结果、独立输入、配对时间比例或收益主张。

当前实验仍由原 owner 执行第二轮 domain。第一轮 native/domain 的完整费用为7329.044554/9146.351492秒，已有原队列独立验证；四臂尚未完成，完整轨迹／请求／原生工作量／图字节／起点与端点匹配仍待原批次封存。旧完整配对约22.95%的开销保持其独立证据边界，不能用组件拼接替换。

CP1r3 已登记三输入六角色仍优先于开发接续；同一已知电路的新布局不计新电路或新架构。四臂完整准入审计仍待执行，reduction/native 原始 running manifest 与缺失的历史 completion 保持不变。所有负结果、失败、超时和观测缺失继续保留。

证据入口：

- [六页正文](../research/dac_v14_20261112/paper_snapshots/current_sharing_prior_art_20261116/build/current_repair_main.pdf) 与 [paper18 绑定](../research/dac_v14_20261112/sharing_prior_art_paper_binding_18.json)
- [贡献与归因对照](../research/dac_v14_20261112/sharing_prior_art_paper_evidence_18/contribution_comparison.md)
- [来源定位](../research/dac_v14_20261112/sharing_prior_art_paper_evidence_18/sources.json) 与 [既有实验归因绑定](../research/dac_v14_20261112/sharing_prior_art_paper_evidence_18/evidence_scope_bindings.json)
- [当前状态](../research/dac_v14_20261112/CURRENT_STATUS.md) 与 [第一轮 domain 完整费用](GitHub_BNN_timing03_domain0_20261116.md)

Git 推送、队列结束或普通负结果均不构成研究完成条件。
