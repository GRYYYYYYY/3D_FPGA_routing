# 历史恢复终态与必要只读核验接续

本快照保留9734eee公开证据基点、279bdb4及后续更新，研究Goal保持active。正在运行的reduction/native及已登记队列规则不变；本次汇总不增加查询或论文收益主张。

|历史轨迹|恢复回执报告的终态|新后缀秒|原失败秒（单列）|资格|
|---|---|---:|---:|---|
|CLSTM/native|6.849416589461ns；226922 wire/3 SB/915 CB；setup153改善/10退化、hold退化0|206.331049|641.584947|开发恢复终态，非冻结确认配对|
|CLSTM/domain|未执行恢复，quality=null|准入0.005978|原记录保留|原阶段审计失败，恢复被准入门槛挡住|
|robot-p1|11.633691343604ns；231101 wire/47 SB/6673 CB；setup34改善/1退化、hold退化0|705.290739|1857.322629|开发恢复终态，非新独立输入|

这些后缀时间分别属于自己的实际恢复命令，不与原失败时间拼成新鲜完整方法费用，不计算完整N/D比例。没有将CLSTM与CP1r3的LSTM混为同一结果。CLSTM/native时序阶段线长226894→226922（+28），自己的CPD改善0.007638778499ns；原时序阶段与恢复登记的绝对上限均为227133 wire/3 SB/915 CB，policy均为timing_under_resources。226894是锚点，不是线长上限；10个setup退化明确保留，不误称端点不退化模式通过。

[具体证据及预算绑定](../research/dac_v14_20261112/legacy_recovery_progress_02/STATUS.md)保留原资源/时序登记、实际恢复结果、阶段失败及旧进程身份。它们只影响补充材料的恢复与适用性说明，不扩大六页投稿主稿TableI、摘要或结论。

CLSTM/domain原审计的JSONDecodeError已定位到reuse_on_native_supervision.json零字节文件。原审计实际source_sha256绑定空字节摘要，随后才进入reduction输入；原代码在绑定后立即读取JSON。配套active记录中旧supervisor/child身份均已终止，worker存在成功封存记录。原空文件、失败审计和未执行恢复判定全部不改，不能仅凭这些元数据推定整个候选或恢复已通过。

[受限独立只读核验](../research/dac_v14_20261112/CLSTM_domain_empty_supervision_audit_02/STATUS.md)已登记：复用原audit_one门槛，仅对这一个精确空文件交叉核对原摘要、已死身份和成功封存worker；再由已有解析器核验完整23请求顺序，并保留全部来源/字节/FULL/STA/端点检查。实际身份及20项拒绝检查通过，共21项小型检查；完整原始字节核验尚未执行，缺失的候选物理/STA和恢复仍须另行登记验证。新核验不补造历史监督退出状态，不重跑已完成原生查询，不自动进入恢复适配器。

该唯一新owner已排在原[三档代价基线只读协调](GitHub_vertical_cost_terminal_20261117.md)终结之后，再等待同一串行槽。当前reduction/native仍在原恢复命令中，之后是reduction/domain；代价基线实际执行已完成353.244486秒、0档等价已通过，三个正强度仍未独立准入。已有19项进度原像检查、此次21项身份检查分别用于具体基础设施问题，不当成算法实验或独立电路证据。

条件ETA保持：基线实际执行剩余0角色，必要正强度准入剩余3；原0档完整审计33.07秒仅支持槽位可用后约2–5分钟的规划，等待当前恢复释放槽位时间未校准。CLSTM独立阶段核验随后单独计费，尚无实际完整审计耗时。没有恢复固定研究日期、总调用上限或矩阵终结条件。

[当前六页投稿04稿](../research/dac_v14_20261112/submission_narrative_04/build/main.pdf)与BNN数值、统一方法和prior-art边界保持。CP1r3仍为0/3完整匹配准入，正强度基线尚不进入表II收益；已有419 SB候选的原预算拒绝也保持。当前稿不等待历史恢复或整个Goal结束，[剩余实验的局部影响](../research/dac_v14_20261112/submission_narrative_04/EXPERIMENT_IMPACT.md)继续适用。实际队列与证据见[当前状态](../research/dac_v14_20261112/CURRENT_STATUS.md)。
