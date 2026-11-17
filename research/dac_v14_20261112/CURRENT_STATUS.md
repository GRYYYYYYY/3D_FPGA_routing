# 当前研究状态

[已登记四档代价基线执行终结](vertical_cost_baseline_terminal_01/STATUS.md)：完整实际尝试353.244486秒，0档等价通过；正强度0.5/1/2的独立准入均因可变progress摘要失败，仍不进入收益。精确旧进度重建与19项小型检查通过；新只读owner等待原串行槽，仅复用已有候选，不重跑native/STA。实际执行剩余0，独立正强度准入剩余3；槽位可用后按原0档33.07秒参照规划2–5分钟，等待槽位未校准。不是完整方法时间或新独立输入。

[CP1r3六角色与已登记准入终结](CP1r3_complete_execution_01/STATUS.md)：完整质量0/6、配对0/3。LSTM执行结束但原/补充验证失败；DLA两臂初始路由失败；SB-layout两臂时序planner执行错误，均保留实际费用，不计算正式比值。native补充主体payload写出后因输出目录缺失报错，raw在前置门槛拒绝、未执行昂贵字节/向量审计。确认/原补充剩余角色均为0；旧确认ETA作废，实际基线构建/四档执行费用另计。[六页投稿04稿](submission_narrative_04/build/main.pdf)只增加失败覆盖与费用，原方法、BNN数值和prior-art不变；[剩余证据影响](submission_narrative_04/EXPERIMENT_IMPACT.md)。

[LSTM归档干扰更正](../../docs/GitHub_LSTM_retention_incident_20261117.md)：助手硬链接归档改变活动源ctime，触发round013/candidate00一次封存失败；135项登记摘要与原最终重哈希一致，失败5项仅ctime变化。保留原失败及费用，不补造成功、不重跑查询、不改预算；当前运行期禁止对上游输入创建/删除硬链接或改元数据。完整LSTM配对及干净计时尚未准入。

[LSTM完整执行与原验证失败](LSTM_complete_execution_01/STATUS.md)：N/D完整命令均返回0，分别实测7615.074177/26657.726866秒；原独立验证分别74.441375/142.926628秒后失败，quality均为null，正式配对比例仍不可用。domain原line64首次失败定位到attempt_index15、round013/candidate00原passed=false；此前155个小型来源哈希均匹配，未重跑native/STA或改历史完成记录。后续以本页实际进程表为准。完整费用保留ctime事件，不称干净算法开销；正文收益主张不变。旧四角色和菜单ETA只作历史情景，当前条件ETA见最新阶段记录。

[DLA-small原N/D初始路由失败](DLA_small_initial_failure_01/STATUS.md)：完整命令分别709.742677/702.413717秒，原日志在W100/200次迭代后均仍有525个过用节点；没有合法起点，未进入修复，不是超时或合法无收益。初始命令仅替换arm输出路径后逐项相同，共同binary/arch/BLIF/RRG登记摘要匹配；未新增大字节独立准入。失败路由打印的CPD不进入质量结果，也不计算算法收益或费用比例。后续实际角色以上表进程身份为准；eltwise-SB是已知电路/架构的新布局，不计新电路/新架构。当前条件ETA见最新阶段记录，旧两臂规划仅作历史记录。

观察时间：2026-11-17T08:18:03.362464+00:00。Goal active；公开证据基点9734eee及279bdb4后续更新保留。

统一方法：当前STA、跨层冗余与容量阻塞用于选择完整连接组；在事务副本中使用跨层共享域、按网失败释放及阻塞owner协调；完整组合经物理/容量/FULL/STA检查，在固定根预算下接受或恢复。终结选点独立于中间提交；native享有相同选组、owner与收敛机会。

| 当前登记批次 | 实际状态 | owner PID |
|---|---|---:|
| robot_p1_prefix_recovery_01 | running_recovery_suffix → continue_resource_from_original_checkpoint | 306104 |
| interrupted_flow_recovery_01 | priority_dependency: robot_p1_prefix_recovery_01 | 306105 |
| empty_query_patch_validation_01 | priority_dependency: interrupted_flow_recovery_01 | 306106 |

[BNN N/D/D/N完整对称计时](BNN_timing03_balanced_receipt_01/completion.json)已终结，原独立完整核验及四臂匹配均通过。完整命令时间按登记顺序为7329.044554 / 9146.351492 / 9112.139276 / 7288.184845s；D0/N0=1.24795960，D1/N1=1.25026182；N均值7308.614699s，D均值9129.245384s，均值之比1.24910749（约+24.91%）。使用原始完整计时区间，未拼接阶段或扣减observer CPU。所有同角色轨迹、请求、原生工作及六个实际图载荷字节一致；配对新鲜初始树、完整CPD/setup/hold/端点ID/约束匹配，终态完整端点比较兼容。共享主机/OS缓存未受控，两次每臂仅支持描述性费用。缺失内存观察依次22/28/27/29，保留采样局限。

同一BNN输入复现资源—时序取舍：两臂CPD同13.228145690ns；N为2059631wire/82SB/5062CB，D为2061417wire/43SB/5060CB。SB减少47.56%，SB+CB从5144到5103减少0.797%，线长+1786。D相对N的setup为534改善/803退化，新增hold违例退化0；不满足端点完全无退化。资源计数减少反映固定架构占用，未测面积/功耗。历史完整时间+22.95%与新交错观察+24.91%分别保留；不能称为普遍收益或统计加速。

独立证据没有增加：四次计时是同一电路、布局与架构的重复测量。CP1r3精度专用封装已实际完成，原三输入/六角色队列已接棒；[实际预检](cp1r3_distinct_input_cohort_01/preflight.json)记录冻结配置、公开源码重建、还原后保护程序/worker导入及迁移后的准入检查通过。大字节与完整输出门槛仍由逐输入准备和测量命令执行，不能将元数据准入当作结果通过。准备/公开重建8.494s、LSTM输入准备17.220s单独计费，不并入算法墙钟。逐臂实际状态以上表为准。LSTM与DLA-like.small为不同已知电路；eltwise SB-only仅为已知电路/架构的不同实际布局。保持冻结协议，不按结果替换输入或重复已完成角色。

[已封存LSTM/native资源子流程](CP1r3_lstm_native_resource_phase_01/completion.json)：驱动6775.915s，接受4次、尝试12个作用域，owner提交0。按原精确变化记录沿接受链还原的初始到资源终态setup为20改善/5退化，新增hold违例退化0；未新增整向量重读。终结endpoint规则在6个同源候选中无合格选点，保留原资源终态；交接FULL/STA通过。该包仅封存资源子流程，完整方法是否准入须另查原独立核验终态；当前活动阶段以上表实际进程为准。

[LSTM/domain第三次接受事务中的失败释放](LSTM_domain_release_scope_01/completion.json)：网2896的pin3在域内九次搜索失败后触发按网释放，释放后第二次搜索成功；整组八请求完成，原候选FULL/STA/物理审计通过。完整事务517.483214s，相对前态+194线长/−7SB/CB不变，CPD同14.600438192ns，setup2改善/2退化、hold违例退化0。七个SB的变化属于整组事务，没有匹配的no-release反事实，不能全部归因于释放；也不是完整配对方法收益。

[已结束观测费用分层](LSTM_observation_cost_layers_01/ENGINEERING_SCOPE.md)覆盖19个普通事务、35次观测，排除不同回调范围的owner事务。新候选评估的原生进程封装均值约107–109秒、物理审计约70秒、准备约39–40秒；剩余时间仍需细分。原生进程封装不是纯搜索或纯STA，内部timer不重复相加；复用候选不重复计费。这是工程定位证据，不是完整配对速度或收益，未改冻结代码。

LSTM/native完整命令已结束（returncode=0），实测7615.074177s；原冻结完整核验在74.441375s后失败，原角色状态仍为`execution_or_verification_failed`、quality=null。PSS峰值11816576KiB，缺失内存观察33次，observer CPU 901.393597s不扣减。

[独立只读元数据诊断](CP1r3_lstm_native_binding_failure_audit_01/completion.json)确认：准备登记封存后，原控制器在执行前追加runtime路径/hash；仅撤销这两处追加即可精确还原三个owner的准备hash，实际执行登记则与追加后的字节匹配。原失败、原文件及冻结版本均保留。这不代替尚未完成的来源/字节/完整请求/FULL/STA/整向量/物理复核；该角色不进入论文收益或正式配对比值，不重跑原生查询。

机制归因仍受原证据限制：BNN九个guided资源角色无失败释放；既有R1 owner联合修复N/D相同结果归于协调范围扩大。robot三臂只证明该事务中域/释放改变可行取舍，尚非完整确认。conv_hls确认无收益、TPU初始超时、SPMV/CB-only无切口、Robot SDC无接受收益、attention/conv-layer初始失败继续保留。

当前CP1r3确认终结后，Priority05保持已登记补充验证器在先，随后执行CP1r3完整请求/原始STA/实际字节/物理证明/配对准入，再执行已登记0/0.5/1/2跨层代价基线，随后执行四臂只读来源/字节/完整请求/FULL/STA/端点/物理审计、robot-p1及四臂阶段接续，最后开发空查询回放。独立投稿候选稿与逐项实验影响、条件性ETA见submission_candidate_01；历史恢复不是稿件统一前置条件。reduction/native原成功日志与running manifest必须独立审计；不改写历史completion、不重复已完成原生查询。新执行阶段单独登记计费，接续费用不冒充冷启动完整费用。

论文：[当前六页正文](paper_snapshots/current_balanced_cost_20261116/build/current_repair_main.pdf)。paper19将四次匹配完整计时用两行汇总；主表42行，三行早期BNN工程明细完整移入补充材料。原paper18及prior-art、贡献边界、9篇引用保持；没有新增独立输入或CP1r3结果。[新增费用主张绑定](BNN_timing03_balanced_claim_binding_01.json)仅补充同一输入完整费用和复现性证据，不新增独立输入或跨输入收益。完整轨迹与审计留补充材料。最新已核验公开提交见CURRENT_STATUS.json的latest_incremental_publication。Goal不因计时完成、推送、普通负结果或日期终止。
