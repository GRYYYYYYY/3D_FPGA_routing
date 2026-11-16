# 当前研究状态

观察时间：2026-11-16T21:31:56.507406+00:00。Goal active；公开证据基点9734eee及279bdb4后续更新保留。

统一方法：当前STA、跨层冗余与容量阻塞用于选择完整连接组；在事务副本中使用跨层共享域、按网失败释放及阻塞owner协调；完整组合经物理/容量/FULL/STA检查，在固定根预算下接受或恢复。终结选点独立于中间提交；native享有相同选组、owner与收敛机会。

| 当前登记批次 | 实际状态 | owner PID |
|---|---|---:|
| cp1r3_distinct_input_cohort_01 | running_confirmation_arm [lstm/native] → private_subreaper | 3149073 |
| interrupted_stage_reconciliation_01 | priority_dependency: cp1r3_distinct_input_cohort_01 | 3149126 |
| robot_p1_prefix_recovery_01 | priority_dependency: interrupted_stage_reconciliation_01 | 3149178 |
| interrupted_flow_recovery_01 | priority_dependency: robot_p1_prefix_recovery_01 | 3149228 |
| empty_query_patch_validation_01 | priority_dependency: interrupted_flow_recovery_01 | 3149280 |

[BNN N/D/D/N完整对称计时](BNN_timing03_balanced_receipt_01/completion.json)已终结，原独立完整核验及四臂匹配均通过。完整命令时间按登记顺序为7329.044554 / 9146.351492 / 9112.139276 / 7288.184845s；D0/N0=1.24795960，D1/N1=1.25026182；N均值7308.614699s，D均值9129.245384s，均值之比1.24910749（约+24.91%）。使用原始完整计时区间，未拼接阶段或扣减observer CPU。所有同角色轨迹、请求、原生工作及六个实际图载荷字节一致；配对新鲜初始树、完整CPD/setup/hold/端点ID/约束匹配，终态完整端点比较兼容。共享主机/OS缓存未受控，两次每臂仅支持描述性费用。缺失内存观察依次22/28/27/29，保留采样局限。

同一BNN输入复现资源—时序取舍：两臂CPD同13.228145690ns；N为2059631wire/82SB/5062CB，D为2061417wire/43SB/5060CB。SB减少47.56%，SB+CB从5144到5103减少0.797%，线长+1786。D相对N的setup为534改善/803退化，新增hold违例退化0；不满足端点完全无退化。资源计数减少反映固定架构占用，未测面积/功耗。历史完整时间+22.95%与新交错观察+24.91%分别保留；不能称为普遍收益或统计加速。

独立证据没有增加：四次计时是同一电路、布局与架构的重复测量。CP1r3精度专用封装已实际完成，原三输入/六角色队列已接棒；[实际预检](cp1r3_distinct_input_cohort_01/preflight.json)记录冻结配置、公开源码重建、还原后保护程序/worker导入及迁移后的准入检查通过。大字节与完整输出门槛仍由逐输入准备和测量命令执行，不能将元数据准入当作结果通过。准备/公开重建8.494s、LSTM输入准备17.220s单独计费，不并入算法墙钟。逐臂实际状态以上表为准。LSTM与DLA-like.small为不同已知电路；eltwise SB-only仅为已知电路/架构的不同实际布局。保持冻结协议，不按结果替换输入或重复已完成角色。

机制归因仍受原证据限制：BNN九个guided资源角色无失败释放；既有R1 owner联合修复N/D相同结果归于协调范围扩大。robot三臂只证明该事务中域/释放改变可行取舍，尚非完整确认。conv_hls确认无收益、TPU初始超时、SPMV/CB-only无切口、Robot SDC无接受收益、attention/conv-layer初始失败继续保留。

之后按登记顺序执行四臂只读来源/字节/完整请求/FULL/STA/端点/物理审计，再做robot-p1及四臂阶段接续，最后开发空查询回放。reduction/native原成功日志与running manifest必须独立审计；不改写历史completion、不重复已完成原生查询。新执行阶段单独登记计费，接续费用不冒充冷启动完整费用。

论文：[paper18六页正文](paper_snapshots/current_sharing_prior_art_20261116/build/current_repair_main.pdf)的prior-art、贡献边界、43行主表与9篇引用保持不变。[新增费用主张绑定](BNN_timing03_balanced_claim_binding_01.json)仅补充同一输入完整费用和复现性证据，不新增独立输入或跨输入收益。完整轨迹与审计留补充材料。最新已核验公开提交见CURRENT_STATUS.json的latest_incremental_publication。Goal不因计时完成、推送、普通负结果或日期终止。
