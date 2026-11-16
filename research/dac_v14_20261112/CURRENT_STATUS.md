# 当前研究状态

观察时间：2026-11-16T10:53:13.031645+00:00。Goal active；公开证据基点9734eee；历史结果与冻结包保留。

统一方法：当前STA/跨层冗余选完整连接组，在私有路由上执行共享域、按网失败释放与容量阻塞owner协调，检查完整组合，按固定根预算接受；终结选点独立于中间提交。native享有同等选组、owner与收敛机会。CP1r2修复Linux进程消失时的监督异常并校验保护程序执行权限，算法/规则不变；[新冻结版本](confirmation_release_cp1r2_01/completion.json)不把既有开发结果追认为确认。

| 当前登记批次 | 实际状态 | owner PID |
|---|---|---:|
| cp1r2_cross_circuit_cohort_01 | running_confirmation_arm → private_subreaper | 1586337 |
| robot_union_verification_recovery_01 | shared_serial_slot | 1685640 |
| BNN_interleaved_timing_03 | waiting_for_registered_robot_union | 1695383 |

[已核对的五次中断](execution_reconciliation_20261116_01/completion.json)均有合法初始路由，但因监督器读取消失的/proc进程触发ProcessLookupError而失去完整流程结果。已按PID+start_ticks核对582个测量身份，无存活身份；原回执不改写。修正版通过注入异常及五类真实进程测试。以下仅为失败尝试费用，无完整质量指标：

| 输入/臂 | 实际时间(s) | 采样PSS(GiB) |
|---|---:|---:|
| reduction_pair_01/native | 6147.85 | 10.927 |
| reduction_pair_01/domain | 3211.96 | 10.886 |
| clstm_input_contract_pair_02/native | 641.58 | 2.856 |
| clstm_input_contract_pair_02/domain | 346.66 | 2.822 |
| robot_p1_input_contract_pair_02/native | 1857.32 | 2.639 |

独立证据：CLSTM两臂、robot-p1/native的修正输入已实际加载并完成合法初始路由；完整方法确认仍缺失。reduction保留native10步/domain4步轨迹，不把不同中断点作N/D因果比较。robot-p1/domain从未执行，原计划与缺口保留，后续单独登记接续。

机制与取舍：BNN完整历史配对同13.228145690ns；domain花1786wire换39SB/2CB。SB减少47.56%，SB+CB减少约0.797%；历史完整时间增加22.95%。新domain工程版9116.40s相对历史9754.31s少6.54%，行为核验精确，但尚无稳定优化后N/D时间比。robot失败释放是原作用域的运行使能；owner范围扩大另有端点/资源交换，不能归因于域。

无效或失败输入继续保留：SPMV/CB-only无切口、Robot SDC无接受收益、conv-layer/attention初始路由失败、历史CLSTM/robot-p1打包解释错误。新五次为基础设施中断，不能混入算法负结果。

论文：[当前六页PDF](paper_snapshots/current_runtime_recovery_20261116/build/current_repair_main.pdf)。正文按问题—机制—完整结果—多目标取舍—消融—开销与范围组织；局部轨迹和恢复费用在补充材料。完整CP1r2确认、联合机制效果与对称交错费用仍待实际回执。最新已核验公开提交与回读见CURRENT_STATUS.json的latest_incremental_publication；本轮未发布内容不得视为已公开。

CP1r1四臂因冻结打包误去掉保护程序执行权限而以126终结，均未启动VPR，不算路由失败。原尝试保留在[打包失败回执](CP1r1_packaging_failure_01/completion.json)。CP1r2已通过原生保护测试、固定规则准入及公开源码重建后的同一保护测试。

robot联合机制三臂原生工作已结束，原只读校验器错误要求紧凑回执具有额外字段；[独立校验接续](robot_union_verification_recovery_01/plan.json)等待串行锁，只复核原产物，零新原生工作。CP1r2正在执行，BNN03在该复核后等待，旧BNN01/02均未执行。

下一步按实际CP1r2进程、robot只读复核和BNN03队列继续；接续失败开发轨迹时保留原失败和费用口径。不以矩阵、推送、普通负结果或固定调用数终止Goal。
