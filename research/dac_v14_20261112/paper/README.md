# DAC 2027 当前正式稿与复现入口

当前为 **C221 六页正文**，研究active，本地新增未推送。冻结基准与历史快照保留。最新实验状态见[CURRENT_STATUS](../CURRENT_STATUS.md)，R1/Tf八个原定对照菜单均已闭合；迁移批次仍按冻结规则运行。

[当前6页PDF](../paper_snapshots/current_R1_native_closure_20261115/build/current_repair_main.pdf) · [源码](current_repair_main.tex) · [578条合法观测独立核验](../multiobjective_closed_R1_native_01/verification.json) · [源码/图/PDF绑定01](../R1_native_closure_paper_binding_01.json) · [版面检查](current_visual_review_C221.json)。BNN348观测/208质量坐标；24完整配置、4已知电路/3垂直家族，各共享主机单观察，观测数不是独立样本。

```sh
.venv-lazagna/bin/python research/dac_v14_20261112/verify_R1_native_closure_paper_artifacts_v1.py
```

| BNN实际冷完整配置 | CPD(ns) | wire/SB/CB | 完整秒 | 采样PSS(GiB) |
|---|---:|---:|---:|---:|
| native |13.228145690|2059631/82/5062|7933.245509|11.055|
| guided |13.228145690|2061417/43/5060|9754.312096|11.063|

[配对回执](../complete_resource_timing_full_flow_01/comparison.json)核对fresh有序初始route/完整向量精确相同：native5资源接受/8scope，guided9接受/9scope且省9个OFF；各3次当前STA时序接受。guided以1786wire和1821.066588s换39SB/2CB，setup534改善/803退化、无新增hold违例。组合策略工作量不同，不作单因素或统计速度结论。GNU高水位均约10.235GiB，PSS缺失30/26次。明确输入之后的索引、路由、实际搜索/候选/失败/拒绝、STA/物理检查、恢复和封存计时内；上游RRG/pack/place生成、一次性研究复核另列，OS缓存与共享主机不受控。

旧导入native/guided为2059627/2061389wire，各自同CPD/SB/CB下少4/28wire，质量支配本次对应冷最终态；旧完整成本未知，不能套本次费用。新两实际点在质量—费用联合前沿保留。新domain14个实际初态/候选/交接状态加入档案，**仅实际最终态携带9754.312096s完整费用**。

[native费用分解](../complete_BNN_native_cost_analysis_01/summary.json)与[guided费用分解](../complete_BNN_domain_cost_analysis_01/summary.json)互斥项总和精确等于完整时间。worker包装1644.44/2976.18s、候选LOAD/FULLSTA2349.50/2580.96s、选择/查询/计划1800.02/1908.54s、索引941.91/941.32s，审计/交接等另列。嵌套native core39.98/1209.00s与observer CPU934.74/1268.81s不重复计入/扣除。[交易排行](../BNN_complete_transaction_cost_rank_01/completion.json)定位guided大组搜索，462/294连接两组分别467.41/393.31s；不能由关联推算预算分组加速。

[guided物理差异分解](../cold_domain_wire_delta_analysis_01/completion.json)：新旧时序输入已17网物理不同、+24wire，三交易后19网不同、+28wire；新增4wire来自net37013，另net26319改变物理路径但wire不变。相同请求/查询/二进制不保证相同路径与工作；不能仅归因序列化。[native协议差异](../native_timing_protocol_identity_analysis_01/completion.json)单独保留。

[C216缓存边界](../BNN_complete_cache_boundary_01/completion.json)限定旧全局元数据别名：实际消费者载荷与计时内新建索引字节精确，两配置自身质量/费用不调整；额外目录是静态依赖，不是导入route/candidate/query历史。[单遍索引405.86s](../joint_graph_indexes_BNN_payload_validation_01/completion.json)仅组件结果，6载荷精确，不推算全流程速度；[实际完整工程对照](../complete_BNN_joint_index_flow_01/README.md)与后续[显式缓存路径＋现有流式v2对照](../complete_BNN_closed_stream_flow_01/README.md)已冻结排队。重复parser原型缺少既有guards而未采用；VPR冻结二进制无Cap’n Proto，仍读原XML。

[既有末态wire替代](../BNN_terminal_wire_alternative_01/completion.json)2059567wire/82SB/5062CB在13.607436067ns下setup两改善/零退化，原垂直接受规则拒绝；通用选择在另外4菜单无合格替代。与时序分支的[结构组合2059607wire](../BNN_wire_timing_composition_01/completion.json)通过全容量但尚待native FULL/STA，[一候选LOAD](../BNN_wire_timing_native_validation_01/README.md)实际排队；不进本版合法结果或完整成本。

[BNN垂直下界](../BNN_vertical_cut_bound_01/completion.json)5103由43SB/5060CB达到，不证明wire/CPD最优。[R1单网局部最小值](../R1_single_net_vertical_local_minimum_01/completion.json)当前5104，8个同层出口被其他owner占满。新[五连接联合修复](../R1_owner_release_joint_probe_01/verification.json)自由native与目标CB域两个对照均到**2070653wire/32SB/5071CB、13.421610490ns、完整端点向量不变**，以24wire换1SB；实际route相同，故本scope无额外域收益。[独立档案核验](../multiobjective_R1_joint_owner_escape_01/verification.json)确认RR3507189实际从owner62707转给目标31767，跨过单网局部最小值、总5103达到终端下界，新点非支配。913.074112s是共享导入双臂scope时间，不是每臂或完整算法成本，原actor不提交。

不同的[BFS结构候选](../R1_escape_owner_BFS_candidate_01/completion.json)2070657wire/32SB/5071CB仍需自身native LOAD；[两连接三角色](../partial_escape_owner_intervention_01/README.md)继续冻结执行。实际五连接2070653结果不验证另一BFS路径或其预测。

[Tf native恢复02](../native_checkpoint_recovery_02/bnn_Tf_native/completion.json)已整合本版：11接受/14scope，13.421610490ns、2074388wire/74SB/5062CB，恢复段1707.765911s/6新worker，历史整条时间未知。六个新增合法候选含3拒绝已独立归档。2074308wire候选有19setup改善/4退化，在相同CPD/SB/CB下省80wire；原垂直与完整端点非退化规则均拒绝。同Tf根guided2076038/43/5060以1650wire换31SB/2CB，各自当前选择，成本范围不同不比整条速度。

[R1 native恢复03](../native_checkpoint_recovery_03/bnn_R1_native/completion.json)已整合C221并正常终结：保留4接受/7scope，13.421610490ns、2068956wire/71SB/5072CB，恢复段548.222112s/1新worker。原8root/control菜单现均闭合。历史整条费用未知；新两候选已独立归档，最终checkpoint沿用既有记录引用、不增加重复观察。TableI/图33/正文已列R1/Tf own-current native与guided控制；R1paired以1673wire换38SB/1CB，同CPD，548.22s恢复段不可套历史整条费用。新适配器不重复原rank0/1搜索/LOAD，不制造旧pool终封；已完成Tf直接复用。原冻结队列不改，新费用03→strict04恢复原配置；budget64四角色02仅需前置终结仍可执行，不重复提交。

既有47SB局部链、独立45SB反馈、固定根SB102%取舍、lazy正结果/fused负结果和零修复边界均保留。seed19四次配置精确重现seed11根/轨迹，不增加独立样本。源快照四调用280.37s与lazy两调用203.48s工作量不同；组合费用须实测。当前无面积/功率或统计速度结论。

完整复现使用各批次冻结config和全新输出目录：

| 配置 | driver |
|---|---|
| 原seed完整配置 | `run_complete_serial_seed_flow_v1.py` |
| fused候选导出 | `run_complete_serial_fused_flow_v2.py` |
| ON优先实际接受后停止；新增conv_layer/robot_rl | `run_complete_serial_lazy_flow_v1.py` |
| 同调用源快照 | `run_complete_serial_source_snapshot_flow_v1.py` |
| SB-only固定102%根CPD | `run_complete_serial_timing_budget_flow_v1.py` |
| BNN新路由→完整资源→完整时序 | `run_complete_resource_timing_flow_v1.py` |
| 源快照与ON优先组合 | `run_complete_serial_lazy_source_snapshot_flow_v1.py` |
| 单次扫描索引完整工程对照 | `run_complete_resource_timing_joint_indexes_v1.py` |
| 显式本次缓存路径＋现有流式v2 | `run_complete_resource_timing_joint_stream_v1.py` |

各批次`plan.json`、`configs/*.json`及`queue/registration.json`绑定输入/实现。外层`measure_process_tree_v1.py --output <new-measurement> -- <python> <driver> --config <frozen-config> --output <new-flow>`测完整时间/树内存；重现实验仍需取得`critical_scope_runner.lock`、使用新目录，不启动第二个原队列owner。所有当前native实验与后继保持原登记版本/规则，新策略用独立版本。

新增conv_layer/robot_rl四配置与源快照/lazy组合两配置已注册但无结果；前者是已知历史电路、只导入明确物理输入后新路由，不称unseen/held-out。正文重建用`tools/tectonic --keep-logs --outdir <new-build-directory> current_repair_main.tex`，当前投影v29、源码与六页PDF绑定。公开追溯参考`7b2834743007b36ce5890320e15a0ffa7dea1eb3`，新增未推送；研究无总体日期、调用数或矩阵停止条件。C214入口备份在`../continuation_history/C215_paper_entry_backup/`。

## 历史详细文稿与实验入口

以下记录保留各自历史范围；旧pending、页数和作者信息不约束当前研究。

- [论文源码](main.tex)：同步方法、消融、失败机制、转移验证和正式计时口径；这是持续更新的开发稿，不是最终页数合规的投稿版本。
- [已有PDF](build/main.pdf)：最新54页开发证据稿已含C136：强A0严格三步达到13.228145690ns，保留低wire候选与六个联合前沿组，并同步资源诊断/跨层共享消融及完整开销。共享六臂实际排队，收益未知；构建与数值文本核对不代表最终页数或投稿就绪。
- [当前开发状态](DEVELOPMENT_STATUS.md)与[研究日志](../RESEARCH_LOG.md)：已验证结果、分支选择及后续工作。
- [主张与证据](claims_evidence.md)：C01–C17为历史总体，C18–C34为新增开发证据；[摘要绑定清单](data/evidence_v14_ledger.json)记录已绑定的小文件来源，不代表全仓库内容重审。
- [机制与消融](mechanisms_and_ablation.md)：保留旧机制案例，加入实际执行的同参数分配、delay、guide和更新结果；旧16次/12小时提案仅作历史记录。
- [六电路Tf汇总](../target_feedback_six_circuit_summary.json)和[四电路转移汇总](../target_feedback_transfer_circuit_summary.json)：失败保留，条件CPD均值与成功率分开。
- [正式计时登记](../formal_timing_01/registration.json)：5电路、3轮旋转A0/R1/U，共45角色。U是冻结的全网络反馈加闭包缓存版本；45角色已全部合法完成并封存；[完整报告](../formal_timing_01/final_report.md)显示U相对旧R1进程时间降低21.010567%，相对A0仍有6.245726%开销。该结论不外推后续版本或成功率。
- [保留前缀诊断队列](../retained_prefix_pipeline_01/identity.json)：构建完成；eltwise默认关闭/trace开启等价门及独立审计已通过，TPU配对诊断已通过；开启项抵扣与保留树源端评分也已分别验证，均未推广。首次审计目录错误已记录，恢复复用了2次原生结果，新增route为0。
- [原13项历史核查](acceptance_13.md)、[历史证据审计](evidence_audit.md)和[历史交付说明](README_v13_history.md)：只描述各自旧阶段，日期、次数和收尾条件不约束当前研究。旧作者清单缺口不阻塞算法与实验。

首次合法化设置下的新增质量收益局限于eltwise；新增count2强原生对照在该例已反超Tf，不能把首次合法结果外推为充分收敛后的优势。Tf对V在六已见电路中1改善、4持平、1共同失败；四转移电路中3持平、1共同失败，没有新增成功案例。共享DP在两组同参数消融中保住该局部收益，不能据此宣称普遍有效。conv另有经独立复核的固定SOURCE首出口容量障碍，结论只适用于该记录映射；该失败继续保留在实验分母。

在此开发目录运行 `bash build.sh` 可构建PDF；正式计时已结束，可构建最新开发稿。历史提取、核验、归档脚本的作用范围是v13数据，不能用它们覆盖当前新增证据或把旧七页校验当作开发稿验收。重建后须重新核对实际页数、引用、版面和新增数值；历史成功回执不证明最新源码已经构建。正式成本表已从封存结果导出；诊断通过后再决定下一项算法改动。


当前新增current-STA证据：[失败状态与调度](../joint_native_cut_feedback_summary_01.json)、[近关键双策略与原生对照](../current_sta_near_selector_summary_01.json)、[完整执行核算](../current_sta_cut_near_execution_accounting_01.json)。这些本地结果晚于公开f7167bd；不等于已推送。CPD持平台阶已有endpoint改善实例，但额外资源/运行代价和后续CPD收益仍需验证；持续科研目标active，旧日期/次数/矩阵条件不恢复。

C93–C96新增自动原生修复、目标范围对照及近关键受影响前缀容量证据。严格分支从封存强R1自主到5.832274663ns；代码、论文和证据均为f7167bd之后本地新增，未推送。Tf自动原生批次另行登记运行，不把本轮局部operator终态当科研终止。

C97–C100加入完成的Tf自动修复和局部时序预算容量证据；SPMV独立批次不纳入尚未完成的质量结论。全部为f7167bd之后本地新增，尚未推送；研究目标保持active。

C101–C102加入完成的SPMV自动修复、A0对照、精确Tf复用和候选审查缓存验证。当前0.2ns近端点实验独立运行，未纳入完成结论。新结果仍未推送。

C103–C105新增SPMV合法端点台阶、同态2x2采用机制及完整路由物理证据缓存验证。未宣称超过A0 CPD或整体路由加速；下一步时序锥诊断尚未实现。所有新工作仍为本地结果。

C106–C107更新：实际时序锥已定位严格占优输入遮蔽，当前最差路径六连接均达固定端点物理最短距离。自动回溯选择器已实跑但尚未集成控制器；BNN原始Tf/A0/R1观察登记继续。SPMV CPD不变；新增结果仍仅本地，旧快照f7167bd未包含。

C108–C109按问题/机制、整体状态、Pareto、对照消融、完整代价新增多目标章节。档案包含强基线，历史拒绝不被改写；正式确认仍待统一冻结选点及等机会实验。新BNN释放/联合修复登记独立于已完成旧观察。

C110–C111追加BNN实际资源接受、强基线直接筛查、容量/余量组合依据及完整成本。档案90记录并保留精度未决和支配关系；新增联合实验仍独立进行。本地更新未推送。

C112–C113归并已完成BNN四臂组件、真实LUT并列瓶颈、零资源余量回放、接受态10目标诊断及关键串联依赖；仅持有者及强基线仍在实际队列中。

C114–C115：当前正文六臂表及仅持有者结论已更新，新增紧凑选择器实现/差分/组件开销章节。旧快照不变，强基线对照仍在运行，完整算法时间未知。

C116–C117新增强A0首次合法配对及端点退化尾部、三起点同CPD资源取舍；当前路径模式DP和自动请求构造替代手工历史目标列表，代理/实际原生结果分开，未来多轮预算锚点与当前进步比较已分离验证。

C118–C120更新强A0/R1十二臂、完整共享流程/核心不同口径、已实现自动流程与R1只读回放、临时容量顺序竞争及保留资源独立候选。后续批次仍按原版本运行；已构建/微型回归不代替BNN质量结果。新成果均在f7167bd之后，仅本地、未推送。

C121–C122加入统一组选的Tf资源收益与A0时序/线长取舍，保留端点向量退化；新增静态原生事务批量复用分支及小图真实失败恢复验证。大图等价与完整性能未知，既有当前STA/保留实验不改。本地新增未推送。

C123–C125更新四自动轨迹完整结果、A0调度未推进前沿及端点提案类反例；新增关键持有者/非关键释放范围扩展与条件距离复用。原生五臂仍待验证，无全局CPD或完整算法加速主张。本地更新未推送。

C126区分资源保留ON的实现断言和最终质量失败，补充多sink回归、隔离stage04 reached位图修复及代表性大图恢复配对。原stage03批次仍按原规则继续，新大图收益未知。

C127–C130新增可验证正结果及限制：扩展自由原生与preset候选相同，原生kernel不变；两顺序形成CPD/线长取舍，根零余量自动流程成立。更新开发摘要和方法贡献，保留初始guide历史负结果；跨方法共同绝对预算、跨电路和冷完整成本继续验证。本地新增未推送。


按连接数分组的新干预已实现于 `run_connection_budget_resource_repair_v1.py`，四角色[队列](../connection_budget_resource_dev_01/queue/registration.json)等待两阶段对照后执行。固定64连接预算保留完整切口；无切口可容纳时单独取第一完整切口。已通过[66个实际选择窗口回放](../connection_budget_grouping_validation_01/completion.json)，其中19个改变分组；BNN实际462连接的旧窗口新选54连接。历史查询耗时与回放连接数不能作为新完整轨迹加速或质量收益；需等待实际native/FULLSTA与终封。新旧actor均已实际登记，请从CURRENT_STATUS核对，避免重复提交。

只读后处理准备：`../BNN_domain_archive_postprocessing_preflight_01.json`登记独立owner，等待原cold pair queue终结，随后提取实际domain互斥费用、追加全部实际FULL/STA/独立审计状态并独立重建事件集合验证。`analyze_complete_BNN_case_cost_v2.py`已在完成的native配置精确回放旧全部费用与嵌套诊断，实际失败协议耗时也核对；metadata引用9条/独立consumer回执6份区分统计。domain归档实际状态数、最终质量、总时间、内存及24配置是否成立须以实际验证回执为准，不从计划推定。新图v30源码要求已验证新档案才执行，目前C217/图v29/554条/23配置不变。任何只读解析错误保留日志并修复解析，不重跑native。
