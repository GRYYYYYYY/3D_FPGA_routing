# 当前研究状态

观察时间：2026-11-17T00:50:08.779181+00:00。Goal active；公开证据基点9734eee及279bdb4后续更新保留。

统一方法：当前STA、跨层冗余与容量阻塞用于选择完整连接组；在事务副本中使用跨层共享域、按网失败释放及阻塞owner协调；完整组合经物理/容量/FULL/STA检查，在固定根预算下接受或恢复。终结选点独立于中间提交；native享有相同选组、owner与收敛机会。

| 当前登记批次 | 实际状态 | owner PID |
|---|---|---:|
| cp1r3_distinct_input_cohort_01 | running_confirmation_arm [lstm/domain] → fresh_route_and_complete_resource | 3149073 |
| CP1r3_supplemental_verifier_01 | priority_dependency: cp1r3_distinct_input_cohort_01 | 1993735 |
| CP1r3_raw_admission_01 | priority_dependency: CP1r3_supplemental_verifier_01 | 2488794 |
| interrupted_stage_reconciliation_01 | priority_dependency: CP1r3_raw_admission_01 | 2488847 |
| robot_p1_prefix_recovery_01 | priority_dependency: interrupted_stage_reconciliation_01 | 2488900 |
| interrupted_flow_recovery_01 | priority_dependency: robot_p1_prefix_recovery_01 | 2488979 |
| empty_query_patch_validation_01 | priority_dependency: interrupted_flow_recovery_01 | 2489030 |

[BNN N/D/D/N完整对称计时](BNN_timing03_balanced_receipt_01/completion.json)已终结，原独立完整核验及四臂匹配均通过。完整命令时间按登记顺序为7329.044554 / 9146.351492 / 9112.139276 / 7288.184845s；D0/N0=1.24795960，D1/N1=1.25026182；N均值7308.614699s，D均值9129.245384s，均值之比1.24910749（约+24.91%）。使用原始完整计时区间，未拼接阶段或扣减observer CPU。所有同角色轨迹、请求、原生工作及六个实际图载荷字节一致；配对新鲜初始树、完整CPD/setup/hold/端点ID/约束匹配，终态完整端点比较兼容。共享主机/OS缓存未受控，两次每臂仅支持描述性费用。缺失内存观察依次22/28/27/29，保留采样局限。

同一BNN输入复现资源—时序取舍：两臂CPD同13.228145690ns；N为2059631wire/82SB/5062CB，D为2061417wire/43SB/5060CB。SB减少47.56%，SB+CB从5144到5103减少0.797%，线长+1786。D相对N的setup为534改善/803退化，新增hold违例退化0；不满足端点完全无退化。资源计数减少反映固定架构占用，未测面积/功耗。历史完整时间+22.95%与新交错观察+24.91%分别保留；不能称为普遍收益或统计加速。

独立证据没有增加：四次计时是同一电路、布局与架构的重复测量。CP1r3精度专用封装已实际完成，原三输入/六角色队列已接棒；[实际预检](cp1r3_distinct_input_cohort_01/preflight.json)记录冻结配置、公开源码重建、还原后保护程序/worker导入及迁移后的准入检查通过。大字节与完整输出门槛仍由逐输入准备和测量命令执行，不能将元数据准入当作结果通过。准备/公开重建8.494s、LSTM输入准备17.220s单独计费，不并入算法墙钟。逐臂实际状态以上表为准。LSTM与DLA-like.small为不同已知电路；eltwise SB-only仅为已知电路/架构的不同实际布局。保持冻结协议，不按结果替换输入或重复已完成角色。

当前lstm/domain新鲜初始路由通过原FULL/完整精度STA/物理门槛：14.600438192ns，2388086wire/509SB/8316CB。图构建395.045s、初始原生命令371.262s分别记录，不拼接为完整时间。该状态是初始准入证据，尚非完整方法结果或配对收益。

资源前缀已接受6次，最新核验检查点为14.600438192ns、2389149wire/460SB/8316CB。最近接受的资源窗口事务相对其前态setup 3改善/1退化，新增hold违例退化0；该事务完整耗时518.163s。完整算法时间与配对确认仍不可用，不把资源阶段检查点冒充终态或域收益。

最近完成尝试为round5/candidate0，接受=True，事务处理回执通过=True，完整事务耗时518.163s。原规则原因：reuse_on: Exact fixed-budget conditions satisfied；reuse_off: not_executed_domain_candidate_accepted。拒绝/失败费用同样保留；此处不替代接受检查点或完整流程费用。

[已封存LSTM/native资源子流程](CP1r3_lstm_native_resource_phase_01/completion.json)：驱动6775.915s，接受4次、尝试12个作用域，owner提交0。按原精确变化记录沿接受链还原的初始到资源终态setup为20改善/5退化，新增hold违例退化0；未新增整向量重读。终结endpoint规则在6个同源候选中无合格选点，保留原资源终态；交接FULL/STA通过。该包仅封存资源子流程，完整方法是否准入须另查原独立核验终态；当前活动阶段以上表实际进程为准。

[LSTM/domain第三次接受事务中的失败释放](LSTM_domain_release_scope_01/completion.json)：网2896的pin3在域内九次搜索失败后触发按网释放，释放后第二次搜索成功；整组八请求完成，原候选FULL/STA/物理审计通过。完整事务517.483214s，相对前态+194线长/−7SB/CB不变，CPD同14.600438192ns，setup2改善/2退化、hold违例退化0。七个SB的变化属于整组事务，没有匹配的no-release反事实，不能全部归因于释放；也不是完整配对方法收益。

LSTM/native完整命令已结束（returncode=0），实测7615.074177s；原冻结完整核验在74.441375s后失败，原角色状态仍为`execution_or_verification_failed`、quality=null。PSS峰值11816576KiB，缺失内存观察33次，observer CPU 901.393597s不扣减。

[独立只读元数据诊断](CP1r3_lstm_native_binding_failure_audit_01/completion.json)确认：准备登记封存后，原控制器在执行前追加runtime路径/hash；仅撤销这两处追加即可精确还原三个owner的准备hash，实际执行登记则与追加后的字节匹配。原失败、原文件及冻结版本均保留。这不代替尚未完成的来源/字节/完整请求/FULL/STA/整向量/物理复核；该角色不进入论文收益或正式配对比值，不重跑原生查询。

机制归因仍受原证据限制：BNN九个guided资源角色无失败释放；既有R1 owner联合修复N/D相同结果归于协调范围扩大。robot三臂只证明该事务中域/释放改变可行取舍，尚非完整确认。conv_hls确认无收益、TPU初始超时、SPMV/CB-only无切口、Robot SDC无接受收益、attention/conv-layer初始失败继续保留。

当前CP1r3确认终结后，Priority04保持已登记补充验证器在先，随后执行CP1r3完整请求/原始STA/实际字节/物理证明/配对准入，再执行四臂只读来源/字节/完整请求/FULL/STA/端点/物理审计、robot-p1及四臂阶段接续，最后开发空查询回放。独立投稿候选稿与逐项实验影响、条件性ETA见submission_candidate_01；历史恢复不是稿件统一前置条件。reduction/native原成功日志与running manifest必须独立审计；不改写历史completion、不重复已完成原生查询。新执行阶段单独登记计费，接续费用不冒充冷启动完整费用。

论文：[当前六页正文](paper_snapshots/current_balanced_cost_20261116/build/current_repair_main.pdf)。paper19将四次匹配完整计时用两行汇总；主表42行，三行早期BNN工程明细完整移入补充材料。原paper18及prior-art、贡献边界、9篇引用保持；没有新增独立输入或CP1r3结果。[新增费用主张绑定](BNN_timing03_balanced_claim_binding_01.json)仅补充同一输入完整费用和复现性证据，不新增独立输入或跨输入收益。完整轨迹与审计留补充材料。最新已核验公开提交见CURRENT_STATUS.json的latest_incremental_publication。Goal不因计时完成、推送、普通负结果或日期终止。
