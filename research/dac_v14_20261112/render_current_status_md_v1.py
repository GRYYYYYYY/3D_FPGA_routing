"""Current facts and research direction; detailed history stays in the evidence index."""
from pathlib import Path

def render(status,D):
    rows=[]
    for owner in status['owners']:
        if not owner['verified_live'] and not owner.get('flow_active_stage'):continue
        phase=owner.get('effective_wait') or owner['phase_status']
        if owner.get('flow_active_stage'):phase+=' → '+owner['flow_active_stage']['phase']
        rows.append(f"| {owner['batch']} | {phase} | {owner['pid']} |")
    recovery=status['original_flow_recovery'];paper=Path(status['paper_pdf']).relative_to(D)
    return f'''# 当前研究状态（{status['observed_at']}）

Goal active；公开证据基点为 `9734eee`，后续增量的已发布范围以独立发布回执为准。无固定日期、总调用或矩阵完成停止条件。[公开进度基点](../../docs/GitHub_progress_20261115.md) · [机器状态](CURRENT_STATUS.json)。

统一方法以当前 STA 重选事务组，按跨层冗余构造共享域；网络搜索失败时释放其域，容量阻塞时另行协调 owner。完整合法候选按固定时序/资源规则接受，终结选点与中间接受分离。[开发入口](run_complete_unified_method_v1.py)已接通资源、owner 协调、重选组、终结选点和时序阶段；[通用 owner 接口](current_owner_transaction_validation_01/completion.json)重建原两臂 native 参数，无切口 SPMV 实际执行不启动求解。完整分支仍待实际集成结果与独立打包冻结，不能称为已完成跨输入确认。

[最新校正档案](multiobjective_engineering_inventory_01/verification.json)：**658 条合法观测、33 个成功完整配置、5 个成功电路身份、3 个垂直家族**。33 是配置数量，不是独立样本数。继承计数漏掉四个早期完整配置；旧 640 条档案实际有 30 个，历史回执未覆盖。[当前六页稿]({paper}) 已按六段主线重构，21 行统一主表含 2 个初始失败角色及各自端点变化；旧档案计数已校正，历史轨迹和恢复审计保存在补充材料。

| 已验证完整 BNN 配置 | CPD/ns | wire / SB / CB | 完整秒 |
|---|---:|---:|---:|
| native |13.228145690|2059631 / 82 / 5062|7933.245509|
| domain-first |13.228145690|2061417 / 43 / 5060|9754.312096|
| 单遍索引 native |13.228145690|2059631 / 82 / 5062|7463.174179|

原匹配两臂：SB 减少 47.56%，SB+CB 总计数减少约 0.797%，wire 增加 1786，完整时间增加约 22.95%；setup 534 改善/803 退化，无新增 hold 违例。占用节省不等于器件面积或功耗下降。单遍索引是同质量的单次工程观察；尚未取得优化后两臂的交错计时结论。

输入证据及无效输入：robot 两臂为 251116/9/653 与 251136/9/652，同 13.354624073 ns，377.71/424.45 s；domain 用 20 wire 与 46.74 s 换 1 CB。conv_layer 两臂初始路由失败（260.10/254.57 s）；SPMV/CB-only 无适用切口；softmax 两臂同质量；SB-only 严格时序下无额外资源收益。seed11/19 相同初始树不算新起点。

归因：五连接 owner 协调的 native/domain 均为 2070653/32/5071，同完整端点向量，收益归于扩大协调范围。两连接结果多 4 wire，保留支配点。budget64 实际查询多重集合不变而事务 18→32，BNN 导入工作流多 46 wire；新分组阈值只是开发假设。robot release 单标志消融仍待执行。

进程恢复：原完整 BNN 测量进程存活核验 **{recovery['verified_live']}**，外层观察者已丢失；[独立恢复监控](supervision_recovery_20261115_01/status.json)保留子流程并控制后续调度。观察缺口和短暂重叠不补写成完整无干扰计时。原失败回执均保留。[新恢复队列](unexecuted_recovery_20261115_01/plan.json)只接续此前未执行的组合 LOAD、robot 消融和 terminal-wire 完整流程；先等待原流程及现有 query-reduction 批次，原规则不改。

| 实际存活 owner 或子阶段 | 阶段 | 原登记 owner PID |
|---|---|---:|
{chr(10).join(rows)}

[新登记集成配对](unified_input_integration_01/plan.json)：attention native/domain，以及 robot s23/p0 native/domain（同 packing、真实不同布局，明确 clk 20 ns、I/O max1 ns/min0 ns SDC）。两臂只改 domain_mode/domain_feedback，owner 均 unrestricted，所有工程改进一致；这是开发验证，尚无结果，SDC 是声明的基准目标而非外部应用要求。排在现有恢复链之后，独立只读比较 owner 已登记。

[独立运行组件](standalone_native_runtime_dev_01/README.md)已封装为[24 KB 源码与 guard 包](standalone_native_runtime_artifact_01/standalone_native_runtime_component_01.tar.gz)，解包自检通过；迁出工程后，正常/超时/线程拒绝/输入篡改/错误二进制检查通过，实际 tiny 物理审计与原回执相同，错误 switch 被拒绝、失败角色计数保留。新 VPR 调用为 0，不增加独立电路或完整配置计数。完整方法的选组、事务、STA 依赖仍待封装；不能把组件封存当作完整确认版冻结。

接续重点：独立可执行确认版本、真实不同布局/路由起点、具有明确 SDC 的新实例，以及正文“问题—机制—完整结果—取舍—消融—开销与范围”。历史局部轨迹、恢复时间和审计移到补充材料；负结果用于调整方法。
'''
