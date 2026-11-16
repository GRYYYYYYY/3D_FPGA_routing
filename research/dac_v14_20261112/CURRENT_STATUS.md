# 当前研究状态

观察时间：2026-11-16T13:30:59.279150+00:00。Goal active；公开证据基点9734eee，原开发状态、冻结版本与失败回执保留。

统一方法：按当前STA、跨层冗余与容量阻塞选完整连接组；在私有树上执行共享域、按网失败释放及owner协调；经物理/容量/FULL/STA完整检查，在固定根预算下接受或恢复，终结选点独立于中间提交。native享有同等选组、owner和收敛机会。CP1r2独立冻结，不追认旧开发结果为确认。

| 当前登记批次 | 实际状态 | owner PID |
|---|---|---:|
| BNN_interleaved_timing_03 | running → complete_current_STA_timing | 1695383 |
| empty_query_patch_validation_01 | waiting_for_registered_BNN_interleaved_timing03 | 3003214 |
| confirmation_release_cp1r3_01 | waiting_for_registered_empty_query_fixture_validation | 3596581 |
| robot_p1_prefix_recovery_01 | waiting_for_registered_CP1r3_preparation | 3960008 |
| cp1r3_distinct_input_cohort_01 | waiting_for_registered_robot_prefix_recovery | 603102 |

新增确认：[CP1r2四臂终结证据](cp1r2_cross_circuit_cohort_01/terminal_evidence_01/completion.json)。两个预先固定的已知独立电路/实际物理输入中，conv_hls两臂合法，初始树/完整向量匹配，终态同14.351002164ns、84291wire/0SB/37CB、4491setup/hold分量；零提交/提案，505.17/500.90s。18个当前关键连接固定/放宽容量均无物理时序增益。确认一个固定菜单无收益输入，不是普遍收益或全局最优。

TPU_ws两臂均触发原1800s初始执行保护，完整尝试1904.67/1906.23s，PSS2.434/2.433GiB，缺失观察0/0。无合法根/质量/端点比较；不是200迭代拥塞失败或不可路由证明。四角色原回执、实际费用与PID身份均保留，无残留后代，不重跑。

机制：[robot固定25连接/5网三臂消融](robot_union_mechanism_02/verification_v2.json)已只读核验。源251161/10/653；native合法251140/9/654，setup240改善/0退化，却超原CB653上限；domain/no-release精确回滚；domain/release合法251160/9/653，CPD同13.354624073ns，setup240改善/32退化、hold增加0，满足资源预算但不满足端点无退化。共享导入命令194.52s，非各臂独立整流程费用；三个候选未提交原actor。域改变本例取舍，释放使该受限事务可行，owner范围扩大另行归因。

[robot-p1 owner接续审计](robot_owner_reentry_audit_02/completion.json)确认4次自动native owner提交及当前状态重入：231045/47/6677→231113/47/6673，CPD同11.633691344ns，即+68wire/−4CB；一阶段setup退化1。既有reload完整精度CPD/setup/hold/约束/端点ID精确相同，确认旧检查仅误比显示精度。仍是中断开发轨迹，不是完整确认或域收益。precision patch02已暂存，未写入CP1r2。

新增归因核对：[10配置/9个声明物理输入矩阵](mechanism_selection_evidence_01/completion.json)是既有数据分析，不是新增独立确认。4配置初始无共享切口；6配置有切口但其中softmax、严格SB-only无额外垂直节省。SB-only两时序设置同初始树/48条候选/资源上限，CPD cap1.00/1.02下domain相对native多省SB为0/4，通用规则必须包含时序预算。所有实际guided资源角色均已覆盖审计：BNN9角色/0释放、robot3角色/5释放。资源owner依赖可避免跨层冗余与目标/owner余量；时序owner需要同一正延迟见证的容量冲突，不能混用两者。[开发分流原型](mechanism_triage_validation_02/completion.json)未装入冻结版本、无实测节省。

完整费用：历史BNN同13.228145690ns，domain+1786wire换39SB/2CB；SB−47.56%，SB+CB−0.797%，完整时间+22.95%。对称工程改动的domain单次9116.40s，相对9754.31s少6.54%；优化后N/D比值仍待当前N/D/D/N完整交错计时。空查询补丁验证在其后排队，无已测节省。

无效、失败与边界：SPMV/CB-only无切口，Robot SDC无接受收益，conv-layer/attention初始路由失败；TPU为初始执行超时。旧加载错误、5次监督中断及4次保护程序打包失败单列基础设施费用。现有owner联合修复N/D同结果归于协调扩大，不能归于域。

论文：[当前六页PDF](paper_snapshots/current_mechanism_triggers_20261116/build/current_repair_main.pdf)，主表43行：36终结尝试、2组基础设施失败、5个局部组件。保留六节主线、机制伪代码与路由相关工作；新增完整确认无收益、TPU超时、robot三臂、owner局部接续及主张边界。历史轨迹/恢复与完整审计留补充材料。已公开版本以CURRENT_STATUS.json的latest_incremental_publication回执为准。

新确认协议：[CP1r3三输入/六角色](cp1r3_distinct_input_cohort_01/protocol.json)已登记在robot接续之后，包括LSTM、DLA-like.small和SB-only布局对照。尚未激活实际配置、重建或准入，不能声称确认通过。SB对照与旧主表同声明电路/图/打包，但1883块中1882块实际坐标不同，是新布局而非新电路；其余原始字节/新鲜根仍待核验。协议先绑定来源/规则，实际CP1r3冻结、公开源码重建及检查通过后，先封存配置再运行；现有版本和队列不变。

后续：保持当前计时规则，完成已登记只读空查询验证；[精度专用CP1r3准备](confirmation_release_cp1r3_01/plan.json)已登记在其后、获取串行锁才打包，不含空查询补丁/新路由，尚未形成新版本执行证据。[robot-p1完整接续](robot_p1_prefix_recovery_01/plan.json)已实现并登记在CP1r3之后，24项元数据负向检查通过，原7步/合法拒绝档案/根预算保留；原生请求与STA复用仍须串行重图/完整轨迹核验，尚无新实验结果或冷启动费用。其余中断输入另行接续，继续真正不同输入/架构及通用机制规则研究。Goal不因批次、推送或普通负结果终止。
