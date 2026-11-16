"""Short current research entry; detailed component/history records remain linked."""
from pathlib import Path

def render(status,D):
    rows=[]
    for owner in status['owners']:
        if not owner['verified_live'] and not owner.get('flow_active_stage'):continue
        phase=owner.get('effective_wait') or owner['phase_status']
        if owner.get('flow_active_stage'):phase+=' → '+owner['flow_active_stage']['phase']
        rows.append(f"| {owner['batch']} | {phase} | {owner['pid']} |")
    paper=Path(status['paper_pdf']).relative_to(D)
    return f'''# 当前研究状态（{status['observed_at']}）

Goal active；公开证据基点 `9734eee`，最新增量 `{status['latest_incremental_publication']['commit'][:7]}`。本地实际回执优先；无固定日期、总调用次数或矩阵完成停止条件。[本轮说明](../../docs/GitHub_robot_owner_scope_progress_20261116.md) · [完整机器状态与证据索引](CURRENT_STATUS.json)。

统一方法：当前 STA 重选事务组 → 跨层共享域 → 按网络失败释放 → 容量证书与当前余量驱动的 owner 协调 → 固定根规则下接受完整合法事务 → 重选与独立终结选点 → 完整时序组合。中间构造不要求逐个改善 CPD。[完整独立开发包 dev03](standalone_unified_method_component_03.json)已迁移原串行控制器；实际整流程验证仍排队，确认版尚未冻结。先前组件、真实请求重放和子进程清理验证只证明对应接口，不证明完整算法收益。

最新机制证据：[robot 精确域/容量审计](robot_release_capacity_cut_01/completion.json)表明两个实际释放网络的原域禁止返回源层，而同层出口被事务外 owner 占满。释放域不释放 owner。[18 次残余容量路径检查](robot_owner_local_reachability_01/completion.json)中，两次目标单独剪除均无同层路径；16次释放 owner 分支后均可达，无超时。这些路径不包含 owner 重接，不能算16次成功修复。[已登记 native 范围对照](robot_owner_scope_pair_01/plan.json)固定原通用选组器首选：目标3连接与目标＋owner4连接，两臂均 unrestricted；只改变协调范围，排在 clstm 之后，尚未执行。

跨输入：[结构筛选](structural_input_screen_01/completion.json)保留五个合法历史根和 attention 初始失败。clstm/reduction 有6/268个共享候选切口、均无当前支持的完全阻塞源出口证书；robot 三个实际物理起点有2/0/30个证书，p1同时改变 packing，非纯布局因果对照。新增完整方法结果仍为0。[clstm 固定 dev03 两臂](portable_clstm_pair_01/plan.json)在完整方法检查后从物理输入新路由；实际起点必须匹配，先决检查失败则保持未执行。原 [attention 与 robot s23 SDC 配对](unified_input_integration_01/plan.json)保留先前登记版本；同树不同 seed 不算独立输入。

| 已核验完整 BNN 配置 | CPD/ns | wire / SB / CB | 完整秒 |
|---|---:|---:|---:|
| native |13.228145690|2059631 / 82 / 5062|7933.245509|
| domain-first |13.228145690|2061417 / 43 / 5060|9754.312096|
| 单遍索引 native |13.228145690|2059631 / 82 / 5062|7463.174179|
| 同流程缓存／stream native |13.228145690|2059631 / 82 / 5062|约7247（限定原 GNU-time）|

原匹配两臂：SB −47.56%，SB＋CB 约−0.797%，wire＋1786，完整时间约＋22.95%；setup 534改善/803退化，无新增 hold 违例。占用减少不等于面积或功耗降低。stream 的观察者丢失、全程 PSS 缺口及短暂并发保留，不能称无干扰统计加速；新工程改进须匹配两臂，稳定后交错计时。

完整结果边界：robot native/domain 为251116/9/653与251136/9/652，同13.354624073 ns，377.71/424.45 s；20 wire和46.74 s换1 CB。conv_layer 两臂初始失败，SPMV/CB-only无适用切口，softmax同质量，SB-only严格时序无额外收益。R1五连接 owner 两臂均2070653/32/5071、完整端点向量相同，归因于协调范围扩大。R1/Tf原生菜单已闭合，不能重跑。

| 实际存活 owner 或子阶段 | 阶段 | 登记 PID |
|---|---|---:|
{chr(10).join(rows)}

BNN query-reduction domain 之后按现有顺序执行：未执行的线长组合验证 → robot no-release → 完整 terminal-wire BNN → attention/robot-SDC → 独立 native 观测/事务/完整方法检查 → clstm → robot owner 范围对照。PID 必须与 start ticks、终结回执交叉核对；正常 pool 轮换不触发恢复。各批次原规则及已完成结果保持不变。

[当前六页正文]({paper})沿问题—机制—完整结果—取舍—消融—开销与范围组织，22行统一主表保留失败；robot 条件机制证明已整合，未执行消融未写成结论。[证据绑定](mechanism_inputs_paper_binding_04.json)核验页数、主表与视觉；[档案](multiobjective_closed_stream_quality_01/verification.json)为671条合法观测、34个完整质量配置，其中33个完整观察者测量、1个限定 GNU-time，均不等于独立样本数。详细局部轨迹、组件回放、恢复记录留在证据索引与补充材料。

接续：以真实终结结果决定下一项干预，优先完成确认版本的实际运行、跨输入匹配和三机制归因。普通失败/退化用于调整方向；未执行计划、结构路径和局部时间不替代完整可复现收益。
'''
