# LSTM两臂完整执行结束、原独立验证失败；CP1r3接续DLA-small

公开证据基点9734eee及279bdb4后续更新保留。本次记录真实完整命令、原验证失败及队列交接，不新增论文收益主张。冻结CP1r3和后继队列的预算、接受规则、版本、输入顺序均未改变。

| LSTM角色 | 完整命令 | 实测完整墙钟/s | 原独立研究验证/s | 原验证结果 | 质量准入 |
|---|---|---:|---:|---|---|
| native | 返回0，执行结束 | 7615.074177 | 74.441375 | 失败：owner准备期登记迁移断言 | 未通过，quality=null |
| domain | 返回0，执行结束 | 26657.726866 | 142.926628 | 失败：round013/candidate00原passed=false | 未通过，quality=null |

完整命令时间来自各自原测量回执，原独立研究验证另记，不通过组件相加拼接完整时间。两臂均不是超时；执行结束、路由候选合法、策略可接受和全角色验证通过分别记录。正式配对比例仍为null，不用未准入结果宣称算法收益或开销优势。

## 资源阶段与终结规则

Domain原资源修复在30个登记scope后结束，接受16次（11guided/5native回退）、owner接受0次；资源流程驱动25789.721014秒，内部修复24902.712355秒，不能相加。接受前缀为2390282 wire /422 SB /8316 CB、CPD14.600438191791909ns。

固定终结规则复用已执行同源native候选，在相同SB/CB下选中2390270 wire /422 SB /8316 CB；自身CPD不变、相对接受前缀setup1改善/0退化、hold违例退化0。选择耗时21.665485秒，未新增native查询，也不改原资源策略拒绝。随后实际交接FULL/STA和完整时序阶段结束，时序接受0次，最终回执保持该输出。

三个owner候选均合法而未接受：首个CB超限1；第二个仅−36wire、SB/CB不变且setup退化1；第三个+12wire且无垂直收益、setup退化1。不能把owner未改善称为路由失败，也不将当前LSTM轨迹当作域机制或统一算法的已确认增量。原419SB候选超线长上限402的判定、自身时序和全部原始记录保持。

## 原失败的具体定位

Domain原验证器在line64失败。独立顺序小型元数据诊断确认：此前155个登记来源哈希全部匹配，首个失败为attempt_index15的原completion.passed=false，对应round013/candidate00的guided FULL_STA_failed及[已公开ctime归档干扰事件](GitHub_LSTM_retention_incident_20261117.md)。该155项诊断仅定位断言，不替代完整图/请求/原始STA/全端点/物理审计。原生臂的owner登记迁移断言失败也原样保留。

助手归档硬链接造成的原ctime事件及全部实际费用继续保留，因此该domain完整时间不能称为干净算法开销。没有将原失败改成成功、补造历史completion或重跑昂贵native/STA。后续使用既有实际结果的独立审计解决具体门槛；当前冻结补充/raw的全事务passed要求不会自动消除这一历史失败。

## 当前队列与论文边界

原cohort已自动启动DLA-small/native；DLA-small/domain、eltwise-SB native/domain随后执行。DLA-like.small与LSTM是不同已知电路；eltwise-SB是已知电路/架构的不同实际布局，不计作新电路或新架构。当前DLA状态必须依据[实际进程总表](../research/dac_v14_20261112/CURRENT_STATUS.md)核对，不能从旧running字段推断。

当前确认后顺序仍是：原补充验证器、raw准入、已登记0/0.5/1/2跨层搜索代价基线、四臂只读审计、robot-p1接续、四臂恢复、空查询验证。基线等待raw队列终结，不要求所有角色通过。当前四个剩余角色及原补充沿用条件性规划约2.17–8.67小时；raw、实际基线构建/核验和事件独立审计额外且未校准，普通拒绝不引入Goal停止条件。

[独立六页投稿候选叙事03](../research/dac_v14_20261112/submission_narrative_03/build/main.pdf)保持原问题、机制与贡献边界。TableI的LSTM完整收益和正式费用比例缺来源/字节/请求/FULL/STA/全端点/物理准入；TableII的简单代价基线缺实际执行和零强度等价。摘要、结论不新增跨输入收益。BNN已核验N/D/D/N完整时间+24.91%、SB减少47.56%与SB+CB减少0.797%仍分别按原证据报告；历史完整时间+22.95%不与新观察混合。历史恢复与robot-p1仍不是主稿统一前置条件。

## 原始绑定

- [完整命令与原验证失败分类](../research/dac_v14_20261112/LSTM_complete_execution_01/verification_result.json)
- [完整执行费用与源回执](../research/dac_v14_20261112/LSTM_complete_execution_01/execution_checkpoint.json)
- [domain原验证日志](../research/dac_v14_20261112/LSTM_complete_execution_01/original_domain_verification.log)
- [155项有序小型元数据诊断](../research/dac_v14_20261112/LSTM_complete_execution_01/bounded_line64_diagnosis.json)
- [资源阶段和终结选点完整记录](../research/dac_v14_20261112/LSTM_resource_phase_terminal_01/checkpoint.json)
- [第16步两角色自己的时序、端点、预算判定](../research/dac_v14_20261112/LSTM_native_fallback_progress_05/progress_and_eta.json)
- [owner阶段的原拒绝与费用](../research/dac_v14_20261112/LSTM_owner_phase_progress_01/checkpoint.json)

上述本地归档均为独立文件的有界元数据副本；不创建或删除源硬链接、不改变活动输入元数据，不以归档副本替代尚未执行的独立准入。Goal保持active，推送或队列终结不构成研究完成。
