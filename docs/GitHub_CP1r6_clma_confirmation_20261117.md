# 显式SDC报告修复与clma独立输入确认

[投稿12](../research/dac_v14_20261112/submission_narrative_12/build/main.pdf)保持六页、42行完整配对，可独立作者审阅。本次没有新增完整收益主张，不改方法、prior-art、四档代价结论或已核验费用。

## CP1r6：仅报告表达式修复

Frisc原两臂核验失败来自契约不允许、报告却读取的`explicit_sdc_spec`字段。新冻结版本直接报告已经SHA256校验的实际SDC文本；仍核对原生命令的SDC路径、实际约束回显、全端点及原有全部门槛。不给没有声明的I/O延迟填默认值，也不虚构外部应用要求。

全部88条原assert的AST逐条相同；唯一运行代码变化是核验报告表达式（及其摘要清单）。算法、native binaries、搜索机会、物理Tdel、预算、接受和终结规则完全不变。两个已有Frisc SDC分支和实际无SDC分支检查通过，6项错误SDC绑定/原生命令缺SDC/约束回显摘要错误均被原门槛拒绝。没有重跑Frisc或LSTM的native/STA，旧CP1r5及原失败回执保留。

[修复差异及验证](../research/dac_v14_20261112/confirmation_release_cp1r6_01/checker_validation.json) · [可重建源包](../research/dac_v14_20261112/confirmation_release_cp1r6_01/current_sta_cp1r6_source.tar.gz)。复用既有固定哈希依赖包，源包独立恢复、guard实际执行、扩展/worker导入及clma迁移入口准入均通过。这些是软件/来源验证，不是新算法收益。

## clma：不同电路，真实新布局

固定VTR提交`0b912334fdd83bb754b302146ac0d1ec9edc9a0e`中的clma含8381个.names、33个pclk锁存器。此前CP1确认未登记该电路；不宣称全研究未见留出集。打包为945CLB/144IO，共1089块。按既定最小器件、各资源不超过80%规则选择现有n40 Hybrid-O，未参考路由质量。

一次实际seed21布局将483块放在层0、606块放在层1；架构族与此前相同，不计新架构。两臂共用实际布局、图字节及预先登记20ns时钟SDC，不指定I/O延迟或外部应用时序需求。打包3.038411秒、布局17.054743秒单独计费，不能拼成完整路由时间。

## 已完成阶段与仍运行的部分

[原生资源阶段回执](../research/dac_v14_20261112/cp1r6_clma_pair_01/native_resource_terminal_01.json)：初始合法CPD15.053021940ns、106027wire/4SB/450CB；3个超出终端跨层参考的网络，但当前STA/共享域规则的可选组为0，阻塞owner组也为0。原owner记录中，三个网均有未被其他owner完全阻塞的局部出口。这与Frisc没有冗余跨层网、elliptic没有跨层占用是不同条件；不据此断言全局不可优化。

native继续原时序阶段，domain按已登记顺序随后运行。原生成功后仍需原有native raw/domain raw/完整配对三项准入；失败保留空质量，不自动重复或改规则。两执行角色为一个输入，种子不算独立样本。

当前没有同输入完整臂耗时，不能从打包/布局或其他电路给出可信完成时刻。资源流程73.35秒、handoff FULL/STA16.31秒是已观察组件，不拼接成完整费用；native终态后以其实际完整费用和工作量更新domain条件性ETA。当前时序候选尚未形成完整收益；投稿12保持。

历史CLSTM恢复仍属补充材料。研究Goal继续active；软件修复、推送和一批结束都不是研究完成条件。
