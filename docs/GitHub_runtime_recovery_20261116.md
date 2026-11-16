# 统一方法运行纠错、失败费用与接续

以9734eee为公开证据基点，保留本地开发、原冻结包和全部失败回执。此次没有新增独立输入上的完整算法收益。Goal继续，不以批次、推送或普通负结果作为停止条件。

统一方法保持当前STA选组→跨层共享域→按网失败释放→容量阻塞owner协调→完整事务检查与固定根预算接受→终结选点→当前STA时序修复。native有匹配的选组、owner及收敛机会；不要求每个中间模块单独改善CPD。

## 新核实的证据与失败分类

[五次开发中断](../research/dac_v14_20261112/execution_reconciliation_20261116_01/completion.json)都已有合法初始路由，但监督器读取消失进程时未处理ProcessLookupError，导致完整流程中断。按582个测量PID及start_ticks核验，没有存活身份；原回执未改写，缺失的监督回执也未补造。

| 输入/臂 | 失败尝试时间(s) | 结果边界 |
|---|---:|---|
| reduction/native | 6147.85 | 10次已验证资源提交，不是完整方法终态 |
| reduction/domain | 3211.96 | 4次已验证资源提交，不能与native中断点作配对收益比较 |
| CLSTM corrected/native | 641.58 | 修正输入已实际加载并完成合法初始路由 |
| CLSTM corrected/domain | 346.66 | 同上，完整方法未通过 |
| robot-p1 corrected/native | 1857.32 | 修正输入及不同布局起点实际进入合法路由；完整结果缺失 |

robot-p1/domain仍未执行。旧输入加载失败仍保留，不能把修正后的初始成功回写到旧批次。

[CP1r1四次打包失败](../research/dac_v14_20261112/CP1r1_packaging_failure_01/completion.json)来自此次冻结操作误去掉保护程序的执行权限：conv_hls N/D花181.96/185.03s，tpu_ws N/D花103.04/103.59s，均以126结束，VPR调用数为零。它们不是拥塞、无收益或电路不适用证据。

## 固定版本与可执行验证

[CP1r2](../research/dac_v14_20261112/confirmation_release_cp1r2_01/completion.json)从原CP1复制，运行时代码只修复两处消失进程读取；算法、选择顺序、根预算、接受和终结规则保持原样。准入增加执行权限检查。原CP1、CP1r1与dev03未修改。

[进程测试](../research/dac_v14_20261112/method_phase_proc_race_validation_02/completion.json)覆盖两类消失异常、权限错误不被吞掉，以及真实正常退出、短命进程、超时、孤儿和外部中断。[保护程序实跑](../research/dac_v14_20261112/confirmation_release_cp1r2_01/guard_execution.json)验证普通子进程、线程/clone阻断及继承行为。

[公开源码重建](../research/dac_v14_20261112/confirmation_release_cp1r2_01/public_source_reconstruction.json)从源码包和固定NumPy/lxml wheels重建1292个绑定文件；实际扩展导入、重定位准入及重建后的保护程序测试通过。源码包不含完整依赖、外部VPR二进制或大物理输入。重建入口：

```bash
python3 research/dac_v14_20261112/restore_confirmation_cp1r2_dependencies.py \
  --source-archive research/dac_v14_20261112/confirmation_release_cp1r2_01/current_sta_cp1r2_source.tar.gz \
  --wheel-dir /path/to/hash-pinned-wheels --output /fresh/outside-project/CP1r2
```

依赖锁见[requirements](../research/dac_v14_20261112/confirmation_cp1_wheels_requirements.txt)。包中继承的freeze_receipt.json明确标识旧CP1，只作历史来源；当前身份由CP1r2的release_manifest.json和实际confirmation_input.json确定。重建与准入成功不等于完整算法确认。

## 当前执行与机制归因

[CP1r2队列](../research/dac_v14_20261112/cp1r2_cross_circuit_cohort_01/plan.json)沿用原先选择的conv_hls、tpu_ws实际输入，已经开始执行。新版本、配置在新结果前固定；已失败的启动尝试及其费用独立保留。

[robot三臂原生执行](../research/dac_v14_20261112/robot_union_mechanism_02/transaction/completion.json)已结束，native和domain+release生成候选，domain-no-release失败回滚。共享导入实验实测194.52s；它不是冷启动整算法成本。旧只读校验器错误地要求禁用域/回滚的紧凑回执含有额外字段，故完整发布校验尚未通过。[独立只读接续](../research/dac_v14_20261112/robot_union_verification_recovery_01/plan.json)按原轨迹重建缺失的校验关联，等待串行锁，零新增原生修复。不得提前宣布完整机制验证成功。

[BNN交错计时03](../research/dac_v14_20261112/BNN_interleaved_timing_03/plan.json)在上述复核后执行，N/D/D/N配置逐字等同原登记。01/02角色都未执行；无重复测量或有利结果替换。

既有owner native/domain相同结果仍归于协调范围扩大。失败释放在固定scope中是运行使能；局部机制不得泛化为完整算法普遍收益。

## 完整费用与六页正文

历史完整BNN配对同13.228145690ns，domain增加1786wire，减少39SB/2CB，完整时间增加22.95%。82→43是SB减少47.56%；5144→5103是SB+CB减少0.797%。完整domain工程版9116.40s相对9754.31s少6.54%，行为逐项核验一致；新优化后N/D费用比仍待稳定交错计时。

[正文13](../research/dac_v14_20261112/paper_snapshots/current_runtime_recovery_20261116/build/current_repair_main.pdf)仍为六页、六段主线，字体和页边距不变。主表36行：32条完整尝试、2条基础设施失败分组（涵盖9次尝试）、2条局部消融；分组仅给费用范围，逐臂原始回执在补充材料。初始失败、无切口、无收益和退化结论继续保留。正文支持具体完整权衡与局部机制，不支持尚未完成的CP1r2跨输入优势、应用时序保证或统计加速。

实时接续以[当前状态及PID核验](../research/dac_v14_20261112/CURRENT_STATUS.md)为准。后续独立结果和只读机制复核需按真实回执继续整合。
