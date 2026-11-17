# reduction/native开发恢复完整终结；原domain接续

本快照保留9734eee公开证据基点、279bdb4及后续更新。研究Goal保持active；本次终结或Git推送均不是整个研究完成条件。

实际恢复回执passed=true：CPD **12.606378163582121ns**，**1241199 wire/72 SB/3058 CB**；相对自己的初始根，setup **1746改善/286退化**，hold违例退化0，setup/hold各69904个对齐分量。原根1240433 wire/184 SB/3058 CB，终态+766 wire/−112 SB/CB不变；固定线长上限1241674保持，余量475。相同CPD不代表端点不退化。

资源累计接受14步，包含10步原前缀与4步新增；17个作用域包含原前缀，owner提交0。终结选点原3个同源候选均不合格，保留资源终态。原时序阶段正常以no_admissible_candidate_in_current_portfolio结束；规划器为no_positive_current_path_cover，0提案/0接受，不是类型错误、路由失败或缺失执行。资源与时序当前结果均保留全部原规则。

|费用范围|实际秒|解释|
|---|---:|---|
|本次完整恢复后缀|5161.457547|同一次实际恢复输出、测量和全部后继阶段；不是新鲜从头方法|
|原失败尝试|6147.846396|历史回执保持，单列，不与后缀拼成完整时间|
|内部资源恢复|4394.812923|嵌套阶段，含原生复用后的新候选处理、4次接受及拒绝|
|资源驱动|4395.361329|包含内部资源阶段，不与之相加|
|资源到时序交接FULL/STA|198.672361|原登记新阶段，已计入后缀|
|时序内部流程|528.768794|正常闭菜单，已计入后缀|

采样树PSS11167475KiB，内存观察缺失11次；观察器CPU634.701764秒单列，退出后没有存活后代。OS缓存及共享主机条件不受控，不声称冷缓存或统计加速。

reduction/native原成功日志与running manifest的不一致，先由独立阶段审计记录，再由实际恢复封存严格复用：round010/candidate00的269连接原生阶段对应stage_reuse记录passed=true、new_native_calls=0、original_manifest_rewritten=false，stage_reuse_seal也保留原回执不变。旧manifest仍为running，没有补造旧worker completion；后续候选物理审计、FULL/STA及接受步骤按实际新执行分别计费。没有重跑旧昂贵查询或借用旧创建费用。

[完整恢复终态绑定](../research/dac_v14_20261112/reduction_native_complete_recovery_01/checkpoint.json) · [资源阶段与复用来源](../research/dac_v14_20261112/reduction_native_resource_phase_terminal_01/STATUS.md)。这是已知reduction输入的native开发轨迹，公共选择和修复机会中的收益不能归因于domain；不是新独立电路、架构或CP1r3冻结确认。原domain后缀已由同一登记owner自动启动，自己的完整候选、来源与端点核验仍在执行。因此目前没有完整N/D质量结论或正式费用比例；即使两臂恢复完成，两条后缀时间也不会成为完整从头时间。

当前原恢复只剩reduction/domain一个角色。它从自己的4步前缀继续，native本次5161秒和domain历史失败3212秒都不能校准它的剩余长度；当前domain后缀尚无可靠ETA。三档正强度基线只读准入等待同一串行槽，槽可用后约2–5分钟只是以原0档33.07秒审计为参照的条件规划；CLSTM空回执核验随后。所有任务保留单任务保护，未恢复固定Goal日期、调用上限或矩阵终结条件。

当前[六页投稿04稿](../research/dac_v14_20261112/submission_narrative_04/build/main.pdf)、BNN完整取舍及prior-art边界保持。新记录只补充历史恢复结果、工程费用和适用性，不把该未配对开发轨迹加入主稿收益；CP1r3仍为0/3完整配对准入，简单代价三个正强度仍待独立核验。主稿可依靠现有完整证据独立成立，不以历史队列或整个Goal结束为前置条件。
