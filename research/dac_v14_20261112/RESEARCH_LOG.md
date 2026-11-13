# 研究日志

## 2026-11-12：基线核查与H1

服务器v13身份为20261110-v13。最终CSV只读复算得到252个A0/R1主配对，双方合法117，34改善/51持平/32退化；完整分母及分架构布局表见final_pairs。原冻结主实验、源码、二进制均保持原位。

H1基于最新本地R1独立源码实现候选级部分delay评分：确定距离保留原值，缺测距离乘以端点/方向独立的median(delay/unit/proxy)标度，用8个unit先验样本作收缩。几何代理先验保留，未测不等于不可达，不省略reverse查询，不扩大预算。初始范围为spmv和softmax / Hybrid-O / P0 / W100 / seed11。候选表可行性仍由SCC保证。

校准单元检查通过：空数据、unit、合法零距离、离群点、非法样本和偶数中位数。独立top-1控制在staging中，250组独立枚举检查通过；尚未接入实际路由，不能宣称DP消融完成。

第一批h1_dev_01四条新route均触发seccomp SIGSYS，登记为thread_constraint_violated，CPD不可用。路由本身完成后在analysis阶段触发，构建cache核查定位唯一相关差异VPR_EXECUTION_ENGINE=auto，Tatum本身已serial。修复为与旧R1相同的VPR_EXECUTION_ENGINE=serial。保留失败日志、第一次二进制及摘要、恢复原因；h1_dev_02为新attempt，不覆盖h1_dev_01。

第一批的路由阶段诊断（仅机制线索，不是合法最终QoR）：spmv原全双侧评分0/107，新方案107/107连接至少一个候选使用测距；softmax从0/108到108/108。两个电路查询数仍分别148、69，settled数606208、282624均未增加。这里“至少一个候选有测距”不等于全部候选双侧精确，也不等于最终关键路径改善。修复构建后须再次核实。

下一步：完成serial修复并运行F复现门；M完成FULL及独立审计后比较质量与代价。若退化，保留结果并分析校准/最终选择覆盖与关键路径；继续可靠性加权时间单位guide及独立DP对照，不能据单轮负结果终止。

## H1有效配对完成

h1_dev_02四条新route全部FULL与独立审计通过，两个F均复现旧R1正文和指标。M相对R1：spmv CPD退化3.1632%，softmax持平，两电路几何均值退化1.5693%。查询数仍148/69；spmv SB占用从1降0而CPD恶化，CB均967。单纯校准部分延迟不予推广，继续查排序可靠性和引导机制，未冻结确认。

下一独立实验：保持旧评分，H仅添加criticality * (0.25 * 所选候选测距侧覆盖率 * graph delay unit)的非偏好跨层搜索惩罚，不写入Tdel或STA；RCV路径不启用此项。N为同候选表独立top-1，G仅切geometry，其他参数一致。先spmv/softmax各F/H/N/G，包含新构建F复现门。该8角色是当前问题的开发实验，不是总研究上限。

## 独立H2/DP/geometry开发批完成

h2_dp_dev_01八条新route全部合法并完成输入封存。F/H和F/N的全序列有限表fingerprint相同（spmv88次、softmax43次），F复现旧R1正文和指标。H的spmv CPD改善0.0518%，迭代19→15；softmax持平；两电路几何均值改善0.0259%，但对A0仍退化0.0543%。N/G的CPD与R1持平；spmv迭代分别15/17。这是初步机制证据，不足以冻结。

统一记录见observations_all.csv/json，含失败状态、CPD、实际跨层资源、迭代、规划及全进程秒数；历史ptrace与新seccomp开发时间明确分开，不作正式加速比。新查询预算未放大。H1未组合进H2。下一步应扩大原开发集（保持失败分母）、补最终guide采用率与关键路径trace、研究针对候选查询和按反馈更新。当前没有研究阻碍，没有冻结候选或宣称目标完成。

## 恢复持续目标：扩展与选择性反馈实现

上一目标轮分类为实质进展（产生代码、12条新合法路由及审计，保留4条线程保护失败），本轮目标已在界面恢复active。启动h2_expansion_01四个原开发电路×F/H/N/G，三并发、每进程1800s/64GiB、不改总研究范围。原attention_layer两基线失败，仍执行新臂以检验成功恢复。

eltwise_layer四臂全部通过独立审计，F复现旧R1 CPD6.96208ns；H=8.07101ns（退化15.9281%）、N=7.26027ns（退化4.2831%）、G=7.69053ns（退化10.4631%）。旧A0=9.93208ns。新H不能凭spmv微小改善推广。全扩展尚未结束，中间分母固定为4电路，未完成/失败/待审计如实保留。

新增feedback_candidate_02：静态SCC和距离缓存复用；仅VPR已选择reroute的net检查反馈（推荐入口或实际推荐跨层边端点过用、remote criticality漂移>=0.15、实际crossing集合Jaccard变化>=0.25）；尝试间隔>=3轮。重新定价使用原opening的当前拥塞成本，新旧赋值在同表/同层次上比较，要求代理成本改善>5%；当没有任何符合criticality的远端pin时明确清空旧guide，这属于失效guide停用而不是代理成本改进。保留旧候选并经SCC再次验证，保留高扇出回退。动态反馈不主动要求VPR重布线、不改变原生prune策略。

完整旧树事务沿用既有恢复机制，并扩展为恢复guide及反馈状态。新H3D_FINAL与CSV绑定VPR最后恢复的best-route版本，而不是最后一轮guide；独立审计按最终route重建每个pin的source/sink和跨层资源。planned_criticality明确不是最终STA关键度。

编译通过。500组最优赋值成本一致性、4,280项独立枚举固定赋值成本、冷却/触发/滞回边界、分支轨迹及错误终端拒绝测试通过。真实U和强制rollback X尚待运行，不能视为已验证。feedback_queue等待扩展4个电路至少2个终态且已无未启动电路，届时仅启动一个串行pilot，以维持总VPR并发<=3。候选01在执行前因全不合格pin清空逻辑修正而被02取代，旧候选文件保留。

已知范围：当前动态价格仍以crossing入口为主，未独立建模所有CB出口拥塞；此为后续依据实际反馈数据改进的方向。候选定向查询/排名不确定性分配尚未实现。正式计时仍未开始，开发开销不作正式加速比。

## 候选查询复用原型（未接入VPR）

本轮前一目标轮判为实质进展；首先核验旧扩展协调器、三个VPR与反馈等待队列存活，没有重复提交。attention_layer_F如旧基线一样失败，H已经接续；bnn_F完成，H接续，gemm_F仍在运行。

query_prototype实现单端点稀疏可恢复Dijkstra：新目标请求复用settled终端及frontier，所有请求共用固定累计settlement上限；目标全确定即停，未settled的tentative标签不暴露为真实距离。单状态node/heap条目保护命中后不恢复部分展开，已确定距离仍可读取。pending目标集合避免每次展开扫描全部目标。

500个随机有向图、2,000项终端距离与原有无界参考Dijkstra一致，覆盖零权、环、不可达、分批配额和目标切换；单独核对累计预算、重复目标零额外工作、tentative标签不暴露、内存停止。小图示例7次settlement替代重复搜索10次，只证明复用机制，不是实际RRG收益。

尚未接入VPR，也未修改运行中或排队候选。下一步必须实现整个端点frontier缓存的总内存上限与淘汰计费；仅单端点上限不足以控制大量端点的总内存。候选定向目标和关键度/排序不确定性调度须在相同总预算下验证，再进入真实RRG和配对路由。

## 真实RRG查询与缓存淘汰验证

从冻结spmv R1输入与最终route按net升序固定选择8条跨层连接，导出完整Hybrid-O W100图（1,028,568节点、4,994,132边）；SHA绑定见query_prototype/rrg_spmv/binding.json。独立参考在物理边上运行完整同层Dijkstra，不依赖原型的虚拟终端。16次定向请求、11个端点方向中，10次测得距离全部与参考一致，6次4096预算耗尽仍为未知而非不可达。复用累计11,510次settlement，相比每请求重建31,187次；旧R1本身已有端点结果缓存，因此这些数值不能解释成相对R1的加速。目标来自已完成最终route，属于正确性诊断，不能作为部署时的候选选择策略。

新增独立frontier缓存：LRU状态槽、有限且不淘汰的端点方向预算账本、跨端点累计work cap；重建被逐出状态只得到原端点剩余预算，账本满时拒绝新端点。达到全局work cap仍能读取驻留的已知精确距离。10,000次交替请求、key错误、异常重试、预算耗尽及逐出回访测试通过。限制为容器条目数量而非精确字节，实际进程内存保护仍必需。异常时保守扣除尚可分配预算，这种记账不能算实际settlement。

真实图缓存槽位对照：{"11": {"requests": 16, "measured_exact": 10, "newly_settled": 11510, "log": "nodes=1028568 edges=4994132 queries=16 total_work=11510 evictions=0 restarts=0"}, "2": {"requests": 16, "measured_exact": 10, "newly_settled": 11510, "log": "nodes=1028568 edges=4994132 queries=16 total_work=11510 evictions=9 restarts=0"}, "1": {"requests": 16, "measured_exact": 9, "newly_settled": 12312, "log": "nodes=1028568 edges=4994132 queries=16 total_work=12312 evictions=11 restarts=1"}}

原型尚未接入生产VPR；当前运行与排队的不可变二进制未修改。下一步用规划前可知的候选而非最终route目标注册比较，检验关键度/排名不确定性调度与覆盖率，再开展配对路由。

机制结论：2槽保持10次有效测距/11,510次展开；1槽只剩9次/12,312次，逐出重建消耗剩余预算。此结果不是通用缓存最小规模建议。目标提前停止不改变Dijkstra展开序列，相同端点预算下不能单独增加精确测距覆盖。下一查询假设应分别考察候选定向双向搜索（合法停止条件、同计费展开总量）或按关键度和排序不确定性重分配节省的工作，而不是仅把定向终止作为覆盖改善。

## 候选定向双向查询：独立验证与VPR接入

上一轮为实质进展，本轮先核验原扩展协调器、反馈队列及VPR实际进程，没有重提旧任务。双向查询维护两个有向frontier，只有最小键和不低于已找到路径上界时才暴露精确测距。两侧settlement合并计费；截断的路径上界不作为精确延迟。200个随机有向图、20,000完整Floyd-Warshall对照和20,000受限预算检查通过。

在已绑定真实RRG的16个诊断目标上，原H3dDelaySearch端点缓存得到10/16精确值、45,056次settlement；双向候选查询得到16/16精确值、2,352次settlement。双方使用同一4096端点方向累计上限，多个候选共享账本，不给重复端点新预算。所有已测值匹配独立物理图参考。该小组目标来自已完成route，不能推断prospective质量或进程加速。

独立src加入默认关闭VPR_H3D_TARGET_DELAY，限制为edge encoding+mixed delay。初始查询目标来自当前几何/拥塞/已有测距排序后的K个多样化SCC可行候选；不读取最终route。精确值按候选缓存，端点预算跨候选及后续请求保留。只保存精确结果，双向frontier每请求释放，最多200,000标签和500,000堆项；进程64GiB保护保留。与已测/校准估计混合评分配套，不启用H或反馈。当前是固定几何/多样性目标顺序，尚无关键度/排名不确定性自适应调度。

构建通过，冻结到target_query_candidate_01。已登记串行spmv/softmax F/M/T，F先复现旧R1、M再复现h1_dev_02 M，T才比较查询机制；FULL、独立图审计、最终guide审计和完整输入封存要求保持。队列等待反馈pilot终态及总并发空位，上限仍为3个VPR。新增M→T配对分析及查询计数统一导出字段。真实路由结果尚未产生，不宣称候选有效。

复查排队脚本时发现run_feedback.py曾从D/src计算相对冻结stage/src路径，会在登记前ValueError。本轮在pilot尚未启动时修正为全程读取candidate02冻结源码；保留旧脚本及SHA变更凭证feedback_runner_source_binding_fix.json，未修改冻结候选。此为启动脚本错误的主动修复，不是算法结果。

接入复审发现同一sink端点可能被后续pin查询扩充测距缓存，最终DP中的缺测估计应使用同一最终缓存重新标定。已在实际执行前补充统一sink尺度刷新，重编译并冻结target_query_candidate_02，保留未执行candidate01和原队列身份。新队列仍依赖反馈pilot终态，没有取消或重启任何VPR实验。

## 关键路径迁移与无guide同层网络诊断

本轮首先核验原进程存活；上一轮为实质进展。复用已经保存的最差setup路径报告（--timing_report_npaths 0仍输出worst 1），未新增route或analysis进程。按packed atom输出netname、固定placement的sink cluster位置匹配最终RR树。所有45个配对连接记录都只有一个匹配的RR SINK位置。此匹配不是完整atom-pin到cluster-pin证书；图合法性沿用已通过的FULL和独立审计。对所用RR节点核验R/C为零，物理switch Tdel按float32解码求和，不把它替代最终STA。

spmv M相对F：原最差路径跨层连接new_n11504物理延迟1.17249→0.99430ns；但新最差路径RAM输出net Big_Channel_.CH_22.CH0.mat_val[5]的同层连接0.84934→2.70760ns。该net只有1个sink且0个远端sink，不会获得直接跨层guide。H版本同一RAM连接仍0.84934ns。

eltwise F/H的最差路径全部同层。net new_n16746有132个sink但0个远端sink；旧最差sink连接4.00838→0.84934ns，新最差sink连接1.03517→4.20948ns。bram_select[5]有4个sink且0远端，其相同关键连接1.41446→1.60028ns。最差终点改变且逻辑深度不同，不能将两个不同路径的CPD差全部归为某一条边的恶化，更不能说路由改变了逻辑。证据证明未引导网络发生间接路由变化，尚未定位具体拥塞事件。后续评价增加全同层网络物理连接退化尾部，优先继续T与U独立验证，不直接推广H或仅放大预算。

bnn四臂现已完成FULL和独立审计：F/H/N/G=13.4216/13.5998/13.4216/13.4292ns；H迭代35→20但CPD退化1.3277%，N同CPD且21轮。F/H全部836张有限表fingerprint相同。四电路扩展当前2/4完成，分母不缩小。反馈pilot已经在真实进程PID3604464启动；源码绑定修复生效，F/U路由已完成但全批审计尚待结束，暂不据此宣称合法QoR。

## 反馈与候选查询完整小开发批、下一公平配额对照

feedback_dev_01六条新route全部合法，FULL/独立图审计/最终guide审计与input seal均通过。两次X各实际触发一次guide rollback；X只作为事务恢复诊断，统一结果中明确标注，不计作算法收益。U两电路CPD及迭代与F相同：spmv7.04599ns/19轮、softmax8.97575ns/13轮。spmv规划3.280→5.562s，完整进程21.505→22.809s；softmax规划4.177→4.155s，进程42.751→40.394s；这些为单次开发计时，不作正式加速比。

细查不能把所有accepted都当代价改善：spmv37次尝试=9次清空失效guide+4次旧代价inf的替换+24次有限代价相等拒绝；softmax10次=6次清空+2次inf替换+2次有限代价相等拒绝。两个U都没有有限到有限的代价改善接受。inf替换来自旧赋值不能覆盖新的eligible连接。共同guided pins采用数完全相同：spmv78/104、softmax94/108；spmv新增101个guide中94个集中于net5144，新集合只有25个实际采用。不可用总体103/205与81/107直接声称采用率改善。触发资源与入口计价资源可能不一致，尤其实际过用发生在CB后继通道；此为待验证假设，不是已证明原因。

保持candidate02和原参数，feedback_expansion_01已启动eltwise/attention F/U；前者有明显间接平面退化，后者原A0/R1失败，检验更拥塞或失败恢复场景。attention的F/H/N/G扩展已全部失败，保留完整分母，不使用非法路由的CPD参与排名。gemm扩展仍在运行。

target_query_dev_01六条F/M/T新route全部合法、默认F和M复现、最终guide审计及input seal通过。T的spmv=7.04599ns/21轮，恢复M的退化但未超过R1（19轮）；softmax8.97575ns/13轮持平。spmv T工作584851对M606208，softmax同为282624；规划分别M3.169→T3.591s、M4.186→T4.412s。候选池双侧测距spmv235→221、softmax228→39，知情连接107→106、108→105。由最终route目标诊断得到的16/16优势不能外推至真实规划。可能存在首个困难目标占满端点预算、丢弃重复搜索frontier、忽略非目标但已经可测的候选等问题。

新增已编译target_query_quota_candidate_01与正在运行的target_query_quota_dev_01：F/M/T/Q，Q每目标最大256=4096/16次settlement，所有目标共用同一端点4096账本；未知仍未知，双向工作与丢弃工作全部计费。不组合H或U。F/M/T需复现已有路由；新增H3D_SELECTED_DELAY单列最终planner选择候选的测距可用性（仅mixed scorer；不等于最终STA或采用率）。当前Q为固定公平配额，不是关键度/不确定性自适应，也没有保留未完成的双向frontier。结果尚待验证，不冻结推广。

配套诊断：匹配net/pin及相同SOURCE/SINK RR身份，四组连接尾部比较均无未配对连接；eltwise H全同层网络18275条连接中1460条恶化>0.1ns，p99增量1.301ns，均值却略有改善。bnn H跨层连接均值改善0.074ns，但混合网络的同层连接均值恶化0.149ns。此为探索性物理延迟分布，不替代电路平衡CPD或最终关键度。45条最差路径相关物理连接与已有独立审计延迟在1e-6ns内一致，脚本/输入/结果哈希绑定。

统一导出补充失败迭代：原parser只从成功报告提取iterations，失败attention实际完成200轮。现在保留native成功值，否则读取最后完整iteration表行并标明证据来源，同时输出最后过用RR节点数；非法CPD仍不进入质量比较。计数解析与无关数值行拒绝测试通过。

## 更难案例的正结果与后续确认

feedback_expansion_01的eltwise F/U已完成全部审计：U CPD6.37264ns对F6.96208ns，改善8.4664%；迭代46→34。150次更新尝试中4次有限代价改善、40次旧赋值不完整替换、43次失效guide清空；这次出现了小pilot没有的有限代价优化。共同140个guided pins采用100→102，7个失去采用、9个新增采用。SB占用134→84，CB占用958→972，不能把SB减少直接等同CPD因果。规划4.905537→8.698463s，全进程32.429240→34.981679s，额外开销尚未优化；没有正式加速结论。保持candidate02不变排队bnn F/U（feedback_bnn_dev_01），等待Q批封存和空位；attention F/U继续失败恢复验证。单电路正结果不冻结，也不与尚未独立证明有益的H/T组合。

Q批spmv四臂已全部审计：Q CPD7.04599ns与R1持平，17轮（F19/T21）；506369次settlement、1816次局部quota停止。最终planner选中候选双侧实测M/T/Q为33/59/32（共107pin）。因此上一段候选池覆盖下降不代表最终选择覆盖下降：T选中双侧覆盖更高，Q固定公平配额反而未改善选中覆盖。softmax尚待整批结束；下一步应根据目标难度、测距确定性与重复frontier工作调整，而非认定固定256最优。

Q批已完整结束：8条全部合法并通过最终guide审计及input seal，F/M/T复现门通过。softmax各臂8.97575ns/13轮；M/T/Q选中双侧覆盖43/19/16（108pin），Q261155次settlement，规划4.410s对F4.195s。固定256不提升CPD或选中双侧覆盖；spmv的迭代收益可保留为待正式确认线索，不宣称加速。下轮优先延续U的bnn/attention验证，并分解动态重规划开销，候选查询可继续研究frontier/已确定距离复用与关键度/不确定性分配。

## 规划开销剖析与精确 SCC 闭包优化

profile_generation_dev_01三臂F/U/O已完成FULL、独立图/最终guide审计和input seal。F/U分别复现既有F/U；O与U的完整route body、CPD/迭代/线长、所有H3D_TABLE和刷新决策及最终guide CSV完全一致。代际标记仅替换闭包visited哈希，未改变候选评分或搜索预算。独立原图BFS对照20,000次及uint8代际回绕检查通过。该临时小图第四槽实验已经结束，恢复正常总并发最多3个VPR。

eltwise U的fast planner总耗时8.4468s中，闭包cache miss占7.5362s（89.22%）；DP solve合计仅约2.21ms。O将372次闭包miss耗时降至4.0812s，完整规划9.094675→5.566296s，全进程35.542212→32.777878s，仍保留U的CPD6.37264ns/34轮；F为6.96208ns/46轮、规划5.095821s、全进程31.982617s。此为并发环境单次instrumented开发观测，不作正式加速比，且O全进程仍略慢于F。profile分阶段互斥，reach统计包含在candidates等阶段内，不重复相加。bnn O已排队复用严格匹配、封存且审计通过的U作为质量参考，关闭profile，检查跨电路等价性；正式计时仍需重新配对轮换。

真实RRG探针使用既有spmv诊断端点：883930个SCC中有两个72320节点的大SCC；不同同层同方向端点闭包共享139245个SCC，单闭包约139247或139286。原始hash与generation闭包完全相同。由此提出进一步缓存大SCC公共闭包。实现独立opt-in VPR_H3D_SHARED_CLOSURE，按SCC成员数选最多8个hub（至少64成员），两方向总共最多4194304个int条目；固定allowed masks归属缓存实例。每次精确遍历遇到hub后合并其完整已排序闭包，去重保持全部端点，容量不足仍精确遍历。此条目上限不替代整个进程内存保护，构建与union瞬时空间另计。20,000次随机原图BFS检查包括方向、容量0/7/10000、mask重配/调用者修改和重叠hub。真实11端点诊断也逐项相同，缓存556980条目，构建约0.016s。该样本来自旧最终路由，只证实实现和重复结构，不充当候选选择或QoR证据；实际VPR验证待完成。

feedback_expansion_01现已封存：attention F/U均失败且200轮，U未恢复成功，非法路由CPD不进入比较。bnn F/U两个路由进程已结束（都13.4216ns），独立审计/封存尚未完成，不提前宣称已验证。gemm G仍运行，F/H/N不能因已结束就缩小整批分母。

eltwise U物理连接尾部补充：按同net/pin及SOURCE/SINK RR完全配对，无未匹配连接。全同层网络18275连接中2837条恶化>0.1ns，p99增量1.30842ns，均值增量-0.01620ns；混合网络同层pin均值改善0.09105ns，而跨层pin均值恶化0.02214ns。CPD改善不等于所有连接改善，也不能仅用跨层平均延迟解释。结果见critical_path_diagnostics/eltwise_U_delay_tails.json，输入哈希绑定；不替代STA关键度分析。

bnn F/U现已通过FULL、独立图/最终guide审计及input seal。CPD同为13.4216ns；U迭代35→19，但规划261.885414→336.824487s、全进程532.741297→598.971438s。497次尝试中303清空、27旧赋值不完整替换、5有限成本改善；153次有限相等拒绝。共同1013 guided pins采用778→777（10失/9得），并未普遍提高采用。O关闭profile的bnn确认已自动启动。大图有8855806 SCC，当前S缓存16MiB条目限制可能只容纳部分方向，需根据实际cache entries/命中证据决定调整，不预先放大。

跨五个已登记U开发电路（spmv、softmax、eltwise、attention、bnn）聚合见feedback_circuit_summary.json：相对R1双方合法4/5，1改善3持平0退化，按电路CPD几何均值改善2.1873%；attention保留失败分母。相对A0同为4/5双方合法，2改善1持平1退化，几何均值改善10.7720%，最差spmv退化0.16049%。此为已见开发集单seed结果，不称独立泛化或成功率提升；gemm U尚未登记。运行时间未与历史混比。

## 公共闭包真实路由通过，向大图确认

shared_closure_dev_01四条F/U/O/S全部FULL、独立图和最终guide审计通过，input seal通过。F复现R1，U复现feedback02，O/S的完整route body、CPD/迭代/线长、候选表和全部refresh/clear序列及最终guide CSV与U一致。S缓存556980条目，372次闭包miss共0.085935s（O4.044475s、U7.442062s）。同批规划F/U/O/S=4.936455/8.870211/5.446462/1.536816s；全进程32.374854/35.184781/32.128296/28.320744s；F CPD6.96208/46轮，其他三臂6.37264/34轮。总规划包含共享缓存构建，不只计算闭包命中时间。并发、instrumented单次开发结果，不替代正式轮换计时；当前质量证据与U相同。

shared_confirmation_dev_01 bnn S已启动，原64GiB/1800s/disk80GiB，正常总VPR<=3，profile开启用于大图开销归因。质量参考复用严格匹配并封存的bnn U，要求完整决策/route/guide相同。并行另有bnn O确认（profile关闭）及gemm G末臂。S队列identity中policy说明沿用旧模板文字，实际依赖、命令、候选SHA及registration均正确，另存shared_confirmation_queue_annotation.json明确更正，未改动已执行runner或封存证据。

下一步优先等大图O/S完整审计，核验S缓存容量/退化情况，再补齐gemm动态更新及其他开发输入；稳定后正式配对轮换计时。候选评分/自适应查询与引导改进仍独立保留，尚不与U组合。当前无阻碍、无最终方法冻结；本轮为实质进展。

## 同存储上限的无损闭包压缩与失败残余定位

本轮先核验上一轮三个真实VPR进程及PID start ticks，没有重启任务。上一轮属于实质进展。bnn O/S进程完成，完整route/table/refresh/guide与U相同，CPD13.4216ns/19轮；O规划185.687987s、进程442.105350s，S规划106.123473s、进程371.745103s。S缓存4160331条目，接近4194304上限，残余闭包开销仍占主导；独立审计/封存尚待完成，不提前计作审计后性能证据。

闭包结构探针显示同13.9万元素反向闭包仅31～33段，正向约1.2万段。新增VPR_H3D_COMPACT_CLOSURE，在普通sorted vector与inclusive run端点对之间择小，保持4194304个stored int word上限。查询直接将区间与局部闭包归并，不保留第二份解压缓存，原sorted结果和SCC语义完全不变；临时输出/allowed masks/allocator开销仍由进程保护约束。5万随机集合对分别验证plain/compact（10万检查），含空集、整型极值、稠密/稀疏；2万原图BFS检查含双方向、容量0/7/10000和mask重配；11真实探针全部相同，556980逻辑条目用48206 words。源码/二进制/测试receipt绑定compact_closure_candidate_01。

compact_closure_dev_01 eltwise S/C完成FULL、独立图/guide审计和input seal，两者与旧U完整route/决策/guide相同，CPD6.37264ns/34轮。实际VPR compact缓存556980逻辑条目仅9626words（实际连续段数不同于原XML探针，具体编号/构图顺序来源尚未定位，不混用存储数）；S556980words，两者均收纳4个hub/direction，无拒绝。S/C规划1.648866/1.796742s、进程28.172265/28.921376s，压缩这次没有小图速度收益，不能只报存储收益而忽略时间。相同候选已启动bnn C确认，原64GiB/1800s；另启动gemm F/C（同压缩优化，F静态必须复现R1后才运行动态C）以补齐第六个开发电路及同参数动态消融。正常最多3个VPR。

attention失败trace诊断没有新增route：每net对RR去重计占用，使用RRG真实capacity，重建过用数F231/U232与native最后iteration完全吻合。F为230 CHANY+1 CHANX，U为231 CHANY+1 IPIN；过用节点均不在实际或推荐跨层边两端，且没有任何当前guided net占用。全端点同层网络独占的过用节点F228/U224。两臂只共享73个过用RR，说明残余冲突位置可变化，不能归因于同一个固定资源；也不能从最终残余反推全过程无间接影响。该证据表明仅更新跨层guide无法直接消除这些最终平面冲突，后续成功率研究需要检查合法宽度边界、原生搜索约束或平面拥塞反馈。此分析不将失败路由认定合法，也不使用其CPD作质量比较。见failure_diagnostics/attention_overuse.json。

bnn O/S随后已完成全部FULL、独立图/最终guide审计和input seal，可作为合法的等价优化开发观测。bnn C路由进程也结束：FULL通过、完整route/table/refresh/guide与旧U相同，CPD13.4216ns/19轮；规划21.553123s、进程293.384776s，1790次闭包miss合计10.317962s。相同4194304-word上限下缓存4个hub/direction、无拒绝，5547108逻辑条目仅90926words。独立审计/封存尚待完成，暂不宣称该批已全审计；此为并发开发计时，正式计时待稳定候选。下一优化假设是避免为每个端点复制整个共享闭包：当前输出仍物化完整sorted vector并被endpoint cache保存，需用峰值RSS与安全共享视图/精确intersection实验验证，不能只据时间猜测。

## 精确共享视图与更新动作消融

本轮先核验真实gemm F进程，bnn C已完成全部FULL、独立图/最终guide审计和input seal。h2扩展全部route终态，剩余gemm图审计线程仍处于R状态并消耗CPU，主线程等待并非证明停滞，未重启任何任务。

新增VPR_H3D_CLOSURE_VIEW：端点缓存只保存局部遍历集合和不可变公共闭包的共享所有权，直接精确判断与entry/exit组件集合相交，不再为每个端点复制整个union。shared_ptr<const ...>快照在索引重配或销毁后仍有效；生产配置每graph仅建立一次，端点缓存随planner释放，配置跨代内存不作单cap内保证。hub stored-word上限仍4194304，物理Tdel/候选排序/关键度/更新触发和事务恢复不变。20,000次原图BFS、378,200次view交集、50,000随机集合对（100,000plain/compact比较、32,400,000 membership检查）通过，含整型极值和空集；生命周期测试覆盖重配置/owner销毁。真实RRG11端点全部union等价、11,000次交集对照通过，只保存150局部SCC和11共享引用。相关源码/测试/原型证据绑定profile_reach/view_validation.json。

closure_view_dev_01 eltwise C/V已全部审计和封存，两者完整route/table/refresh/guide与旧U相同，CPD6.37264ns/34轮。规划C1.670268→V1.319775s，全进程28.808518→27.324314s；峰值RSS1067948→1067760KiB，几乎不变，不能声称该小图峰值内存改善。V缓存372端点，仅9891局部SCC+372共享引用。bnn V同64GiB/1800s确认已启动，以检验大图额外内存与规划收益；以上均为开发计时，正式轮换仍待稳定候选。

同时为质量机制而非单纯性能准备feedback_action_candidate_01与F/V/D/R独立消融：F静态，V完整动态更新，D只接受no-eligible-pin清空提案，R只接受非清空重新赋值。保留相同触发、cooldown、margin、候选计算/DP/当前价格；计算后才过滤接受动作，不把少算工作混入此机制比较。F必须复现R1，V必须复现旧U；D/R逐个action事件检查过滤逻辑与最终accept日志一致，再做完整路由/guide审计。拒绝动作保留旧guide和原生reroute，事务恢复代码不改。接受的清空提案可能原本没有非空guide，现有计数不等于实际撤销的guide数；机制判断以配对QoR/路由为准。实验正在执行，尚不解释未审计的单臂结果。

feedback_action_dev_01四臂现已全部FULL/独立图/最终guide审计及input seal通过，动作过滤逐条验证通过。F/D完整route body相同：6.96208ns/46轮；V/R完整route body相同：6.37264ns/34轮。D接受52个清空提案、拒绝57个原本被接受的非清空提案；最终guide比F少14pin但完整路由不变。R接受43个非清空提案（4有限改善、39旧赋值不完整），拒绝59个清空提案；完整路由与V一致，但最终guide集合293pin对V245pin不同。故仅凭整体采用率或清空计数无法解释QoR，本案例收益依赖重新赋值；不能外推所有电路的清空都无效。所有变化保持真实Tdel/STA与原生拥塞机制。

据此新增feedback_prior_candidate_01和R/P/I后续消融：R复现上一R；P只接受finite旧代价的非清空改善，I只接受nonfinite旧代价的非清空替换。仍计算相同候选/代价/DP、保留触发与margin，不把跳过计算当作本轮开销收益。旧代价nonfinite表示当前有限候选表不能完整表达旧赋值，不自动等同所有相关pin都新进入关键集合。三臂原8GiB/1800s/disk80GiB，已启动。

bnn V路由进程完成：FULL和完整route/table/refresh/guide等价门通过，CPD13.4216ns/19轮。规划10.650433s、全进程271.769604s、峰值RSS10731220KiB；对先前C开发观测21.553123s/293.384776s/14957296KiB。V缓存1790端点，42069局部SCC+1790共享引用。C和V不是正式轮换计时，不能将跨开发批时间比作为正式加速；V独立审计及input seal待完成。该大图峰值内存下降支持避免端点物化的假设，仍需gemm等更大图验证。

R/P/I后续消融现已全部FULL、独立图/guide审计和input seal通过。R控制完整路由/决策/guide复现前一R；P完整route body=静态F，CPD6.96208ns/46轮；I完整route body=R=完整动态V，CPD6.37264ns/34轮。P只接受1次有限旧代价改善，I只接受38次旧代价nonfinite替换。I最终330个guided pins与R293/V245不同，但路由相同，再次说明整体guide计数不能解释质量。实验表明本case的收益集中在当前表无法完整表示旧赋值时的替换；不将它过度解释为已证明所有触发都是新增critical pin，也不推断有限成本更新在其他电路无用。I三臂仍计算完整提案，并未实现跳过冗余planning的优化。bnn I迁移实验已在完整封存后启动，参数/输入对齐旧U/A0/R1，允许真实退化且不要求route相等。必须先看迁移再考虑简化默认动态策略。

本轮收尾新增终态：h2_expansion_01四电路全批审计/封存完成且errors=[]。合并早期spmv/softmax，F/H/N/G六电路均保留，5/6双方合法；H为1改善1持平3退化，按电路CPD几何均值退化3.3913%，最差15.9281%；N为4持平1退化，几何均值退化0.8423%；G为3持平2退化，几何均值退化2.0217%。attention全臂失败不缩小分母。结果见static_ablation_circuit_summary.json；没有因H负结果停止其他方向。

bnn V已通过独立图/最终guide审计和input seal，之前进程结果升级为全审计开发结果。gemm优化静态F也完成native FULL且完整route/CPD/迭代复现冻结R1（13.1564ns/19轮），全进程1287.219185s；动态C已启动，整批独立审计尚待C结束，未提前标为全审计。统一导出加入峰值RSS和view计数时捕获并修复一个键名替换错误，原始实验/封存不受影响；重导出并逐项对照bnn V原日志1790端点/42069局部项/1790共享引用/10731220KiB。

bnn I迁移的native进程现已完成：FULL通过、CPD13.4216ns持平，但28轮对完整U/V的19轮，全进程286.927785s。24个incomplete替换被接受，过滤395个原本会接受的动作；独立图/guide审计尚在进行。这个初步结果不支持把eltwise的I-only规则直接推广，默认完整策略保持不变。新增bnn R后续验证并排队在I封存后执行：只恢复finite-prior重赋值、继续拒绝clear，区分迭代回退来自哪类被抑制的动作。复用feedback_prior_candidate_01，输入/保护/参数均同I和已封存U，最多3个VPR，不因这一退化结束研究。

## 动态组件消融、旧赋值缺失归因与新门槛触发

dynamic_components_dev_01已全部FULL、独立图/最终guide审计和input seal通过。同K16/query4096/mincriticality0.7/opening16/miss2（Z仅miss=0），F/V/N/G/Z CPD=6.96208/6.37264/7.88356/7.67462/9.93208ns，迭代46/34/35/37/43。N关闭共享DP，G几何评分，Z规划仍启用但搜索偏好为零。F复现旧R1、V复现U，Z完整route body/线长/CPD/迭代与A0完全一致（zero_bias_a0_check.json）。动态收益在此例依赖保留的DP、delay与实际偏好，不仅是重规划本身；不推广为所有电路结论。

prior_trace_candidate_01新增只读旧赋值诊断，prior_trace_dev_01 V/T两臂全部审计/封存，与U route/table/refresh/guide完全相同。analyze_prior_reasons.py核验150尝试、107有表尝试；40次接受旧代价inf全部只由新越过0.7门槛的空guide造成，215 pin事件、210不同net/pin。旧criticality是上次接受状态、不是每轮前值；九位有效数字按float32往返检查阈值。43清空中6次原有guide非空、37次原本为空。不把accepted计数或所有210pin当成CPD因果。

bnn I/R两批已全部审计封存，均CPD13.4216ns；I28轮、R23轮、fullU/V19轮，route各不相同。恢复有限成本更新只恢复部分迭代收益，保留完整清空策略另有收益，不能从eltwise单例取消任一分支。I/R全进程286.927785/280.988819s，V271.769604s，仍仅开发观测。

据新归因实现eligibility_trigger_candidate_01：只在VPR已选中重布线网络中，对remote pin从上次接受criticality<0.7变为>=0.7且guide空时增加触发。沿用cooldown3、原评分/4096预算/完整接受规则；不做I-only，不改物理Tdel/STA/拥塞。新增H3D_REFRESH_TRIGGER和H3D_ELIGIBILITY_TRIGGER核验额外尝试与冷却，不把重复checks当unique pin。默认off需完整复现U，on可能退化。eltwise V/B注册eligibility_trigger_dev_01，8GiB/1800s/disk80GiB，同view/profile/trace，正常最多3VPR。首次系统python缺lxml在注册/route前退出，日志eligibility_trigger_runner.log保留；改用既有.venv-lazagna解释器，无route重试。

gemm F/C两个路由进程完成：CPD同13.1564，19→20轮，全进程1287.219185→1345.377661s；独立审计仍进行，不提前算入合法聚合。完整科研目标保持active，未冻结最终方案，正式计时待稳定后执行。

门槛触发小pilot已全部审计/封存：V/B完整route相同，CPD6.37264/34轮；V复现U的完整决策/guide。B额外16次触发，167尝试对V150，接受inf51对40，全部仅新eligible空guide（242事件236不同pin）。最终guide245→265，common235采用154→143（18失7得），新增30pin采用12，10pin退出。规划1.323252→1.395937s、全进程26.717611→26.767856s，未见QoR收益。verify_eligibility_trigger核验真实触发、cooldown及累计计数；初版checker误把每轮累计summary假设成单行，修正为末行并检查单调性，无route重跑。registration_annotation更正沿用模板note中的trace说明，原注册与runner不修改。

eligibility_expansion_dev_01已启动，串行bnn/spmv/softmax B-only：严格匹配并复用sealed U/A0/R1质量参考，不将旧时间当正式基线；64GiB/1800s/disk80GiB，总VPR<=3。继续完整更新策略，只增加门槛触发并保留同quality参数；不因小pilot无收益中止科研，不默认启用该触发。

## 六电路完整反馈结果与已确定距离复用

上一轮为progress：新门槛触发实现/验证、动态组件与旧赋值归因更新了权威代码和证据。本轮先核实/proc runner和真实VPR，没有因旧state或观察缺失重启。gemm F/C现在完成FULL、独立图/最终guide审计和input seal：CPD同13.1564ns、19→20轮，规划30.877287→76.907281s，完整路由进程1287.219185→1345.377661s。1059更新尝试中402旧代价不完整替换、576清空、0有限成本改善；保持退化。aggregate_feedback.py新增可重复六电路选择与全分母汇总，5/6双方合法，相对R1一改善四持平，CPD几何均值改善1.753729%；相对A0三改善一平一退，改善8.852956%，最差spmv退化0.160490%。attention仍失败，无成功率提升。

eligibility_expansion_dev_01三电路全部审计封存：bnn/spmv/softmax CPD均同fullU；迭代19/17/13，只有spmv从19降17。额外trigger90/28/13，全部接受；三例接受inf108/31/15全部仅新eligible空guide。仍保留opt-in，不能把新增guide等同收益。generic analyzer逐事件核验cooldown、触发、prior账本和float32门槛。

新target_reuse_candidate_01独立于feedback/timing-guide：沿用Q的K16/query4096/targetquota256/calibrated scorer，缓存双向查询已经settle的端点侧精确距离。forward直接缓存crossing entry距离；reverse须对crossing source所有子边的min进行证据约束，只有已settled child距离+非负switchdelay <= 端点frontier lower bound才认证，未知上界不当实测。memory stop不导出。使用原端点累计工作账本、不增加settlements；前驱检查/缓存开销仍计入规划，不称零成本。incidental缓存只在values.size<200000时接收；日志endpoint_entry_cap表示该接收阈值，不是直接target精确答案的总条目上限，后者仍可按原预算新增，实验需保留capacity_stops。当前未实现frontier恢复或不确定性调度。

query_reuse随机独立Floyd：20000完整+20000有界查询，45498导出label、36379多出口证书，全通过。原16真实RRG请求导出2336label但0 crossing证书，不能据此声称真实证书已验证。额外oracle选择远目标的stress确认7294 crossing证书（43762labels、45056两侧settlements），实际1028568nodes/4994132edges；该目标仅验证，不作为prospective策略或QoR证据。所有validation/source/binary绑定，4GiB/300s诊断保护。

target_reuse_dev_01登记F/Q/E spmv/softmax，64GiB/1800s/disk80GiB，全部无feedback/timingguide/view，Q必须复现旧Q的完整route/table/guide再做E，F复现R1。spmv E暂见7.04234对Q7.04599ns、17轮同；覆盖和工作在整批封存后分析，不直接等同更多信息带来普遍收益。eltwise/bnn Q/E扩大验证准备完成并排队，依赖small pilot inputseal且<=2 liveVPR；复用严格配对A0/R1，原Q首次出现在新电路，不伪称历史Q对照。一次提前启动被seal断言挡在outdir/route创建之前，日志target_reuse_expansion_dev_01.log保留；随后使用显式队列，无route重复。

view_gemm_dev_01已登记并启动：复用完整封存的gemm C（引用角色U明确标注实际C），只开启精确view，要求route/table/refresh/guide全部相同，验证大图规划和内存。C峰值50186916KiB，V保留64GiB/1800s/disk80GiB；正常总VPR<=3。不把此前bnn收益直接外推gemm，不作正式计时结论。科研目标继续active，无阻碍。

target_reuse_dev_01六条现已全部审计和input seal。F复现R1，Q完整route/table/guide复现旧Q。spmvQ/E CPD7.04599/7.04234ns，同17轮，改善0.05180%但仍不及A0的7.03470。E新增3552条incidental测距，settlements506369→498261（-1.60%），选中候选有任侧测距96→86/107，双侧32→33；规划3.578908→3.629493s，进程20.805112→20.906739s。softmax均8.97575/13轮；E新增2748，settlements261155→254896（-2.40%），有任侧108→98/108，双侧16→25，规划4.405993→4.415331s、进程41.345306→41.800057s。所有capacity/memory stops为0，额外测量改变校准/排名但不普遍提升有效覆盖或速度；不作正式加速结论。target_reuse_expansion_dev_01现已通过前置seal并开始eltwise/bnn Q/E，正常64GiB/1800s，旧A0/R1严格匹配复用。距离前沿复用、关键度和排名不确定性调度仍待研究，不能把本次settled结果复用称为完整自适应查询。

扩大验证首个eltwise Q/E已完成native FULL及独立图/guide审计，但整批input seal待bnn结束：CPD6.78852→6.56420ns，59→58轮；进程34.127749→33.780485s。相对静态R1的6.96208有改善，但仍不及既有完整动态U的6.37264。E任侧测距113→116/149、双侧18→19，新增4998缓存条目；此例与小spmv/softmax的覆盖下降不同，继续等待bnn再决定是否组合有效方向。当前实际运行gemmV和bnnQ，勿重启已审计eltwise。

## 端点侧持久双向前沿：独立实现、完整小批与精确view确认

上一轮为progress：E实现、独立证书核验、六电路U聚合与新对照改变了代码/权威证据。本轮重新检查真实/proc和manifest，gemmV、bnnQ存活时未重启。bnnQ随后native FULL完成CPD13.5998/19轮，差于R1的13.4216；E仍运行，整批未封存，退化保留。P查询是下一独立方向，不因局部收益就组合feedback/H。

persistent_query_candidate_01新增H3dPersistentBidirectional：端点侧Dijkstra前沿跨目标保留，每目标另一侧重建。所有虚拟crossing terminals从首次查询起存在且不扩展，避免复用目标变化时实际已变图的旧one-shot前沿。每次两侧新增settlement及terminal结算计入4096同一端点/方向总账本，quota256；LRU8状态，持久精确cache和work ledger不随淘汰删除。每次活跃query两侧合计200000labels/500000heap limits，瞬时容器/原图等额外空间保留进程保护。端点relaxation内存截断会poison前沿、不能不安全恢复；另一侧截断不破坏已保存端点状态。不是纯决策等价优化，不声称已按criticality/排名不确定性调度。

随机Floyd独立oracle验证480000连续查询、13264terminal证书事件，包含129786内存stop、目标改变、零预算和非负零权。真实RRG原目标重复3轮48请求验证目标值/同4096预算，LRU1/8分别47/23淘汰，原目标均无incidental证书，不能当非空验证。远目标oracle stress16轮256请求，LRU1/8分别2176/3004证书事件，均逐项对照独立unbounded endpoint oracle；两侧实际计费均45056且每key<=4096。真实目标仅作验证，不当prospective方法。记录persistent_query/validation.json、stress_validation.json，源码/输入哈希绑定，4GiB/300s保护。

persistent_query_dev_01 E/P四条全部FULL、独立图/最终guide审计与input seal。E复现旧E route/table/guide。P的spmvCPD7.04234/17轮、softmax8.97575/13轮均同E，但route不同。spmvE/P settled498261→371525（约-25.44%），选中pin任侧测距86→96/107、双侧33→42，planning3.645280→3.509506s，process20.957247→20.904906s；softmax254896→217940（约-14.50%），任侧98→102/108、双侧25→40，plan4.609708→4.397987，process41.455447→40.643484。峰值RSS分别E/P1040656/1040680和2349248/2349160KiB，基本相同。P的terminal events23001/8944包含淘汰后重复结算，非unique cache entries；实际budget sum与日志对账通过，无memory stops。只是开发观测，不作正式加速结论。

persistent_view_dev_01 O两条已完整审计/封存，开启精确generation/shared/compact/view和profile，query仍为P、无feedback/H。完整route/table/refresh/guide全同sealed P。spmv/softmax规划1.124117/1.928740s，进程18.850990/37.793233s。避免把P降低的查询工作误当全部规划开销：剩余精确闭包表示优化仍有明显开发收益。将该精确优化用于后续P较大图迁移；正式同环境轮换计时仍待稳定方案。

persistent_expansion_dev_01已准备并由queue_persistent_expansion.py唯一owner等待两个seal：target_reuse_expansion_dev_01和persistent_view_dev_01，随后<=2已有VPR才启动。新运行P-only eltwise/bnn，复用严格匹配已封存E/A0/R1质量结果，P启用已确认精确view，同K16/4096/256/criticality.7/opening16/miss2/slots8；64GiB/1800s/disk80GiB，总VPR<=3，不把历史E时间当正式对照。大图失败/退化不改变整个科研goal。

下一可检验假设记录persistent_query/NEXT_EXPERIMENT.md：先做决策不变诊断，检查选中缺测候选的校准估计是否低于端点前沿已证明的有限下界，再决定是否以max(原估计,下界)抑制乐观排名。该设计尚未实现，不能算当前结果或自适应调度；需要独立oracle覆盖LRU、内存stop和反向多出口。既有合法图、物理Tdel、STA与原生拥塞均保留。

bnnQ/E路由进程现均结束且native FULL：CPD13.5998均劣于R1的13.4216，E迭代19→33，规划265.757342→266.076356s，进程524.402583→544.328117s。E任侧测距1212→1065/1317、双侧223→247，新增46612距离，未知选择增加，不能作为统一默认；独立审计/整批seal仍进行。gemmV native FULL及完整route/table/refresh/guide等价门通过，13.1564ns/20轮；规划27.389007s（C76.907281）、进程1257.053452（C1345.377661）、峰值27530788KiB（C50186916），独立审计/封存尚待完成，不写成正式加速。

机制边界补充：E/P同时改变terminal图和frontier保留，已实现的P确实不重复settle保留状态中的节点，但总工作差异还受候选/校准轨迹影响。NEXT_EXPERIMENT前置universal-terminal、每目标销毁frontier的Z严格消融；保留精确cache和总work ledger。slots=1不能替代该消融。此项尚未实现，不将未跑实验写成贡献证据。

## 严格前沿消融、可证明下界与扩大迁移的封存结果

本轮读取/proc与原队列receipt后确认target_reuse_expansion、persistent_expansion、view_gemm、retention_ablation、delay_bound、bound_clamp及bound_clamp_expansion全部完成独立审计和input seal，没有重启任何已结束任务。gemmV完整route/table/refresh/guide=C，13.1564ns/20轮，规划27.389007s、进程1257.053452s、峰值27530788KiB；升级为全审计开发证据，仍不是正式加速比。

Q/E eltwise6.78852→6.56420ns、59→58轮；bnn均13.5998ns差于R1，19→33轮。优化P的eltwise6.64602ns/39轮、bnn13.6074ns/19轮，均差于E。四电路统一Q/E/P聚合保留这些退化，禁止按电路选最好臂。

严格retention-off Z保持universal-terminal图、exact cache与4096 lifetime ledger，只在每次query后清前沿。spmv/softmax P/Z均CPD相同，Z完整route=旧E；P工作371525/217940，Z499109/255074。虽然端点工作降低，反侧工作增加，P规划1.237169/2.003338s对Z1.199400/1.982747s，进程19.603662/41.747490对18.820835/39.594006。不能将减少settlement直接写成加速。analyze_retention_ablation.py记录丢弃、重启与预算审计。

下界诊断D不改决策，traceoff/on完整route/table/guide相同。640000随机连续query、2483794约束及真实RRG下界检查通过，包含LRU和memory stop。spmv/softmax选中missing-side 76/74事件中22/9低于已证明有限bound。空/poisoned前沿不宣称新下界或不可达。下界只针对规划proxy，非物理STA。

L对missing侧使用max(calibrated estimate,bound)，exact不变，同4096/256与view。小P/L全部审计封存，P复现旧D；spmv7.04234ns持平但17→18轮，softmax8.97575ns/13轮不变。扩展L：eltwise6.70280ns/35轮差于P6.64602但优于R16.96208；bnn13.4216ns/19轮恢复旧R1（P13.6074）。全部FULL/独立图/guide及seal通过，analyze_delay_bounds.py核验每个effective值。四电路L对R1二改善二持平、几何改善0.957167%；对P一改善二持平一退化、几何改善0.130945%；对完整U几何退化1.257677%、最差eltwise退化5.180898%。保留opt-in，不凭下界一致性宣称普遍收益。统一observations导出加入retention/bound/layer统计。

## 跨层搜索限制的独立诊断

已核实route_common.cpp load_net_route_bb按端点层范围初始化，bb_factor只扩XY；route_utils.cpp dynamic_update_bounding_boxes也只扩XY；connection_router.tpp只在无path时要求全device重试。attention F/U尾部overuse约230的平台和绝大多数同层owner提示搜索范围值得验证，不自动证明这是失败根因。注意dynamic_update_bounding_boxes的out_bb_updated_nets当前按值传递；本实验不夹带修复，Serial下是否有实际影响另查。

layer_bbox_candidate_01默认off，strict0/1开关只在初始普通网络上把layer_min/max扩至全层，XY/时延/拥塞/STA及clock既有处理不变，记录restricted/expanded数量。make -j8 vpr通过，源码/二进制已独立冻结。layer_bbox_dev_01注册eltwise、attention：F-off完整复现旧F（含失败route/status）后，再同scope对A0(A1)/R1(F1)/U(U1)。K16/4096/.7/opening16/miss2不变，关闭P/L/H，仅精确view优化；单进程1800s64GiB/disk80GiB，顺序运行。启动handle57906；未得出成功率或guide收益结论。正式计时另见FORMAL_TIMING_PROTOCOL.md，runner尚待实现；此方案不限制整个研究。

新增进展：eltwise F-off通过完整route/status/metrics/guide复现；A1/F1/U1均native FULL及独立图审计通过，CPD6.01810/6.20393/6.20393ns，迭代22/19/22。全batch seal仍待attention。analyze_layer_scope.py记录原A0/R1/F无同层端点net跨层绕行，扩层A1/F1/U1分别175/170/147；不能把初始restricted8933和有route的same-layer8921当同一人口。相同scope下R1/U比A0差3.08785%，不能把scope收益写作guide收益。物理连接尾部分析已保存，无identity不匹配；same-layer terminal组不等于route完全平面，不作STA因果推断。

spmv/softmax/bnn同scope迁移已经登记到唯一队列handle26000，等待layer_bbox_dev_01封存；每case F-off先复现对应旧F，再A1/F1/U1，复用匹配A0/R1/U引用。正式计时占用标志active时队列不得启动。新开发实验依据eltwise原生+独立审计结果，不假定attention可成功。

run_formal_timing.py和analyze_formal_timing.py已实现，formal_timing_01准备45个轮换角色。完整输入准入seal、源码/二进制绑定和轮换预检均通过；seccomp现有全工作负载validation passed及执行器摘要已核对。未执行正式计时、未创建其队列：新scope可能改变比较基线，先完成机制验证，避免把旧scope成本结论直接迁移到扩层版本。main.tex本轮编译成功。

## 层边界恢复失败案例：首批完整封存

上一目标轮为实质进展；本轮先用/proc start ticks核对原runner与queue，未重启任何实验。layer_bbox_dev_01已全部终态、独立图/guide审计（适用者）及input seal通过。attention F-off准确复现旧F失败route/status/guide，200轮仍失败；A1/F1/U1均合法，CPD12.6638ns，37/49/49轮，F1与U1最终route body完全相同。637/626/626个同层端点net出现实际跨层绕行，旧A0/R1为零。A1 SB/CB占用740/2307，F1/U1为727/2299。全进程78.306200/83.463456/81.861370s，规划0/1.841520/1.894443s；开发并发数据不作正式速度比。恢复成功属于同输入scope因素，不能归功于guide，也不是总体成功率外推。

eltwise也全部封存：A1/F1/U1=6.01810/6.20393/6.20393ns，22/19/22轮。A1优于同scope guided，F1/U1虽同CPD却route body不同。独立物理路径诊断发现共同最差报告连接n16756的RR延迟0.663513494→0.849339293ns；最差输入startpoint也改变，所检查连接及其net都无直接guide。只作为间接路由影响证据，不宣称单事件因果。物理尾部和全部查询证据保留在critical_path_diagnostics/layer_scope_*。旧冻结比较只支持原terminal-layer搜索范围下的结论，新的更强原生搜索baseline必须同scope比较。

## 原生选择后按过用扩层，以及按关键度分配查询

selective_layer_candidate_01已build/freeze：严格独立开关，在should_route_net已接受后且prune之前检查旧tree，iter>=2、非global、serialclustered、layer interval未覆盖全device且存在实际overcapacity witness时单向扩层。XY/物理Tdel/STA/价格不变，边界永不缩回；rollback保留扩大搜索域，原树/guide/occ事务不动。globalalllayer与selective模式互斥；TBB编译显式拒绝该实验。selective_layer_dev_01已由唯一queue handle54193启动，F/A/U三个关闭控制均完整route/metrics复现；A2/F2/U2和强制rollback X2继续。不要把X2计作方法收益。

query_priority_diagnostic.json显示静态P多pin guide net首pin不是最关键者：spmv7/8、softmax17/28、eltwise12/20、bnn153/237。该诊断不是每个端点预算耗尽的证明。query_priority_candidate_01仅对query/candidate pass做criticality稳定降序，DP仍用原pins顺序，4096/256/slots8不变；没有uncertainty分配、扩层、feedback/H/L组合。已build/freeze并启动P/Cq小pilot handle41204，P必须复现旧优化P。query_priority_expansion队列handle55196等待小pilot seal后对eltwise/bnn运行Cq-only，复用严格匹配封存P/A0/R1，不按旧时间比写加速。

统一分析/导出现在要求每个新执行自己的batch seal，否则合法native/独立审计但未seal显示legal_pending_batch_seal，单独保留native_cpd_ns；失败CPD不进入合法质量比。分析增加选择性scope控制与querypriority配对及预算/回滚一致性核验。正式计时仍prepared未启动，待新scope比较结果决定对象。

selective_layer_dev_01完整审计/封存通过，analyze_selective_layer.py核对expanded net唯一、iter>=2、runtime witness occ>cap、初始层范围受限与单向扩层。日志一致性不冒充独立重建每轮occ。A2/F2/U2 CPD6.22942/5.84702/6.01810ns，20/19/20轮；F2对同策略A2改善6.138613%，U2改善3.392290%，动态反而弱于静态。强制X2一次rollback及最终FULL/独立guide通过，6.10047ns不计方法收益。A2/F2/U2扩大7968/7982/7970个net，占8933初始受限net约89%；大部分6924/6925/6925在iter2触发。不能把收益只解释为稀疏过用筛选。全进程26.367527/26.816533/27.819186s，仍开发观测。

因此已实现delayed_layer_candidate_01：在SerialNetlistRouter的iter2入口一次性扩全net层BB，不强制重布线、不动XY/树/STA/价格；与initial-global及selective互斥。构建/冻结完成，delayed_layer_dev_01排队handle7538；S需完整route/table/scope-events/guide复现F2，再A3/F3/U3区分延迟暴露与过用选择。selective_attention_dev_01已启动handle72247，A2/F2/U2对原失败A0/R1/U与全局合法A1/F1/U1；复用匹配失败状态不以失败CPD算比率。

query_priority_dev_01完整封存，预算/覆盖/控制分析通过。Cq两case完整route都=P，CPD/迭代不变。spmv7/88 plans重排，work371525→371438，coverage相同；softmax25/43重排（首次pin非max只有17，其他8在后续pin顺序变化），work217940→224142，both40→50但informed102→99。规划P/Cq=1.122188/1.109634和1.963362/1.955484s，不宣称速度收益。扩大Cq已执行eltwise native7.47203ns/70轮，差于P6.64602/39；独立审计/全batchseal待完成、bnn继续。下一查询假设应考虑共享source预算均衡与候选排名不确定性，不能从关键度优先推断收益。

新增完整封存：delayed_layer_dev_01的S复现F2完整route/table/扩层事件/guide；A3/F3/U3分别与A2/F2/U2完整route body完全相同，所有FULL/独立图/guide及inputseal通过。因果对照表明eltwise的收益可由延后到iter2开放层范围完整复现，尚未证明过用筛选额外有效。不能把复杂选择策略视为已经更优。

selective_attention_dev_01也全部封存：A2/F2/U2合法12.6638ns，31/32/37轮，扩大21444/21438/21436个net（初始22635），每臂iter2均18416。原A0/R1/U失败状态保留。delayed_attention_dev_01已启动handle65422，S复现F2后A3/F3/U3验证可否简化，不提高route迭代预算。

query_priority_expansion_dev_01已全部审计/封存。eltwise Cq7.47203ns/70轮，差于P6.64602/39；bnn13.5998ns/23轮，比P13.6074小幅改善但仍差于R113.4216。四电路统一Cq对P一改善二持平一退化、几何退化2.957641%、最差退化12.428642%；对R1一改善一持平二退化、几何退化2.105867%。仅按关键度抢先共享预算不作为默认，下一查询方向要用均衡/排名不确定性等可验证依据继续，不能扩查询预算掩盖。

本轮实时交接补充：layer_bbox_expansion的bnn native A1=13.6074ns/18轮、F1=13.5998ns/17轮（比原R113.4216退化），U1仍运行，整批未封存；不提前加入合法聚合。delayed_attention S复现F2已过门，A3/F3 native12.6638ns/31、32轮，U3仍运行；完整独立审计和seal待结束。已核验两个真实VPR PID/start ticks及各自runner。剩余工作不是资源/作者阻碍，研究继续active。


## 五电路全层封存、第二轮简化等价与source预算均分

layer_bbox_expansion_dev_01现全部完成native FULL、独立图/guide审计和input seal。三个F-off控制复现原R1；spmv A1/F1/U1均7.03470ns/16轮，softmax均8.97575/12，bnn13.6074/13.5998/13.5998ns、18/17/17轮。统一五电路初始全层A1/F1/U1全部合法（原A0/R1/U均4合法1失败），F1/U1各对同scope A1一改善三持平一退化，几何退化0.598840%、最差3.087852%。不能把attention恢复归功于guide；bnn相对旧R1退化1.327711%。新增aggregate_scope_development.py固定五电路九角色，核对规范化命令、物理输入/packed/place、scope和guide开关；每次执行自己的seal决定质量资格，失败恢复单列、不使用失败CPD。实际资源从独立audit提取，未封存和缺失保留。

delayed_attention_dev_01全部审计/封存；A3/F3/U3完整route body、metrics、candidate/refresh sequence、guide（适用者）分别等于selective A2/F2/U2。12.6638ns、31/32/37轮，进程76.710983/78.159251/80.311137s。加上eltwise，两个案例都无法证明选择性overuse筛选比iter2统一暴露多收益。delayed_scope_expansion由唯一队列handle88244实际启动：spmv/softmax/bnn，先initial-global R1 F1c复现，再同scope A3/F3/U3，未改变预算。spmv已native/独立审计但batch未seal：A3=7.04234/15，F3/U3=7.28430/16，退化保留、不提前计合法质量。softmax均8.97575/13。bnn继续，不重启原owner。

独立source_share_candidate_01已实现/编译/冻结。VPR_H3D_SOURCE_QUERY_SHARE严格0/1且要求persistent targeted query；每个source call allowance=ceil(剩余lifetime预算/剩余eligible pins)，保留pin/DP顺序和未用预算，原4096/256/slots8不增。reverse始终独立查询，不能沿用旧评分source miss即skip。两侧frontier工作都计入单次和lifetime账本；zero/maximum size_t budget、LRU、cache、memory stop均验证。Floyd oracle共185701shared calls、433124queries、35361certificates、47997evictions、251278memory stops、21541zero shares、104521unused calls，通过但不冒充wrapper或QoR测试。真实wrapper断言与analyze_source_share.py逐事件检查补足。

source_share_dev_01小P/Bq全部审计及input seal。P完整route/table/guide复现旧optimized P。spmv/softmax CPD保持7.04234/8.97575ns，17/13轮。work371525→369932及217940→217041；selected informed96持平、softmax102→99，both42/40持平。Bq107/108calls中19/65共享，source-call charged251613/150541。规划P/Bq1.284890/1.284693和1.983379/1.970107s；全进程19.903104/20.704000和39.689766/39.692449s。不宣称CPD或正式速度收益。

基于共享source复杂度迁移假设而非小样本持平即选优，source_share_expansion_dev_01已注册并实际启动（queue handle96789），eltwise/bnn Bq-only，复用相同命令/packed/place的封存P/A0/R1，保持原端点layer scope、不混入H/L/feedback/Cq。1800s64GiB、80GiBreserve和最多3VPR仍有效；两队列互不重复提交且尊重正式计时active标志。eltwise原生6.64602ns/39轮，待整批封存，bnn继续。

论文main.tex增加五电路同scope表、更新attention简化等价、写入Bq公式/验证/小配对/开放迁移。首次构建发现模板无booktabs，改用既有hline后构建通过；不是最终投稿排版。正式计时仍未启动，需依据新scope公平比较对象重新决定。持续科研目标未完成且无阻碍；本轮为实质进展。


新增只读机制诊断spmv_delayed_paths/connections：对原F、初始全层A1/F1、第二轮A3/F3/U3的最差路径连接并集，核对14条相同source/sink RR身份（84行），物理RR延迟由独立审计提供。F3/U3最差startpoint与A3不同；共同连接$abc$76201$new_n11469 pin3在A3为1.228629892ns、F3为1.607920491ns，该连接及net无guide。并集有3条F3直接guide，不能把这个退化全归为关键连接偏好未采用，也不能从一条物理连接差分推出单事件因果。spmv_U3实际发生30次反馈尝试、13次接受，故相同最终CPD不等于动态机制未执行。diagnostic明确记录新batch未seal，暂不作为正式质量证据。初次用系统python缺lxml，改用项目venv后完成，只读分析无路由重跑。


## Bq四例封存与source测量驱动的reverse重选

上一轮为实质进展。本轮首先通过/proc start ticks核对原source_share_expansion及delayed_scope_expansion owner；未重启审计中的任务。source_share_expansion现seal及所有审计通过，analyze_source_share/analyze_development/aggregate_query_development完成：eltwise Bq6.64602ns/39轮、bnn13.6074ns/20轮；对P四电路CPD全持平，bnn19→20轮。eltwise informed127→126、both34→30，bnn informed1164→1154、both338→335。work517976→504750、4064741→4020316；规划1.372964/13.241443s、全进程27.922483/275.057729s。不从更少work推出加速，均分未证明有效覆盖/QoR收益，不推广。四例对R1几何改善0.827305%，对U退化1.390443%，与P相同。

代码核查发现原P在source query之前选好query_targets，source真实测量/校准之后reverse仍照用旧名单。因此新reverse_rerank_candidate_01默认off严格开关VPR_H3D_REVERSE_RERANK，在source测量后对相同feasible ranked population重算当前混合cost，再调用同一diversify_选相同K个reverse targets。原pin/DP顺序、pool、最终几何兜底及4096/256不变；reverse不因source miss省略。source共享/Cq/H/L/feedback/scope组合全部关闭。记录每pin old/new目标、introduced及source-known，原生断言目标数不变；保留forward/cache/物理Tdel/STA。不是完整排名不确定性算法，也不宣称已经收益。

make -j8 vpr串行配置构建成功、独立stage冻结；原P关闭开关先验证完整route/table/guide，再Rq。小配对已由唯一queue handle82402实际启动，registration/输入/源码/二进制绑定完整，新增analyze_reverse_rerank.py审计target序列/数量/唯一性、budget/counters及独立合法性。spmv P已复现，Rq原生CPD7.04234/17轮但wirelength变化，整批未seal不提前计质量。首次修改命令工作目录写错在读取前失败、仅无变更build；纠正后实际实现再构建，未影响已有候选或运行任务。

更大规模scope验证已登记：scope_gemm_dev_01在五电路两种scope封存后运行gemm F-off控制及A1/F1/U1/A3/F3/U3共七角色。使用独立delayed_layer_candidate_01，不含新查询机制；先核对旧A0/R1、feedback_gemm F与view_gemm V匹配命令/packed/place/独立审计，运行时再次冻结全部物理输入。保留失败/timeout及1800s64GiB80GiBmax3VPR。唯一队列handle39152当前等待，不把待运行实验写成收益，也不按电路挑scope。


Rq小pilot现全部封存，analyze_reverse_rerank与analyze_development通过。spmv/softmax P完整route/table/guide复现旧优化P；Rq CPD仍7.04234/8.97575ns，17/13轮。94/107及75/108个pin的reverse目标序列改变，introduced991/730次候选事件（不是去重物理资源数）。新旧reverse目标的source已知数量750→141、687→108，说明重评分大量转向其他估计候选，不等于不确定性已解决。最终selected informed96→105、102→101；both42→50、40→49。work371525→311905、217940→210286。P/Rq规划1.258554/1.053650和1.942574/1.934336s；全进程19.101733/18.099184和38.652050/38.781477s。仅开发观察，不宣称加速/QoR收益。

据此注册并实际启动reverse_rerank_expansion_dev_01：eltwise/bnn Rq-only，复用严格匹配P/A0/R1参考、sameK16/4096/256/slots8、原pinorder、不混Bq/Cq/H/L/feedback/scope，唯一queue handle41127。检验大图覆盖收益及退化尾部，不能由spmv覆盖提高推断CPD收益。scope_gemm前置输入准入检查已通过，queue39152等待第二轮五电路batchseal；任务有owner且未重复提交。论文已将Rq小试从pending更新为已封存，并保留尚在运行扩大验证的边界。


本轮末实时核验：delayed_scope_expansion所有native已终态，bnn A3/F3/U3=13.2434/13.7856/13.5998ns、18/18/17轮；独立审计/整批seal尚在进行，因此仍不加入合法聚合。原scope拥有的guide优势在更强native基线上不能直接迁移。Rq扩大eltwise native8.21844ns/38轮，对P6.64602明显退化；bnn仍运行。这一信号与小例CPD持平一并保留，不能用spmv覆盖提高作为推广依据。下一可验证假设是source实测后重评分偏向低估的未测source候选，使reverse名单大幅迁移；只是待检验机制，需decision-neutral候选分量/估计trace及独立精确距离对照，不从最终CPD猜因果。研究继续active，无输入/资源阻碍。


## 第二轮scope与Rq扩大封存；独立估计误差诊断

上一轮为实质进展。本轮读取原PID/start ticks后继续原owner，delayed_scope_expansion现所有独立审计/guide和seal通过。五例A3/F3/U3均合法；F3/U3相对同scope A3均一改善二持平二退化，几何退化0.211323%/0.517836%，最差4.094115%/3.435790%。bnn13.2434/13.7856/13.5998ns，18/18/17轮。A1→A3原生五例几何退化0.169797%，F1→F3改善0.216067%，U1→U3退化0.089138%，不能按电路挑scope；聚合脚本保持固定五例。scope_gemm队列39152现已实际启动pid2893673/start1928813720，F-off控制和六个scope×method角色继续，非正式计时。

Rq扩大已全部封存。bnn恢复R113.4216ns/19轮（P13.6074），selected informed1164→1237、both338→365、work4064741→3418133；eltwise6.64602→8.21844ns、39→38轮，informed127→128、both34→39、work517976→462560。四电路对P一改善二持平一退化，几何退化5.090685%、最差23.659574%；对R1退化4.221264%、最差18.045756%。不因覆盖增加和工作减少宣称方法收益，也不停止研究。原CPD/真实物理资源/进程代价完整保留。

estimate_trace_candidate_01已实现、构建及独立冻结。严格VPR_H3D_TRACE_ESTIMATES=0/1记录pre/source/post/table/selected阶段的候选source/sink实际评分分量、exact标记、几何proxy、校准scale、opening/branch、criticality和delayunit。不额外query/recalibrate/排序，不改变代价。独立oracle exact_distances.cpp完全不包含生产搜索头文件，完整Dijkstra在单层图求距、reverse再加一条跨层边。80张随机多层含zero/unreachable图，用虚拟terminal Floyd独立核验21022答案（16886不可达、1145零距离）通过。实际n40RRG的spmv/eltwise P/Rq全部记录将统一核对已测距离和未测估计，并比较单pin surrogate排序；不冒充物理STA或DP共享最优的因果证明。

诊断首批spmv P/Rq已复现并独立审计。eltwise P的route/table/guide/metrics/target counts完全相同，但旧P日志无retain/discards/live_states字段，逐行persistent日志比较拒绝，保留原失败log与estimate_equivalence_initial_schema_rejection.json。恢复脚本resume_estimate_trace.py对每轮共同字段精确比较、另验retain=1/discards=0/live_states<=slots；原输入完整重建hash账本并在末尾全量seal。仅补跑尚未启动的eltwise Rq，不重跑已完成三次native；恢复owner handle89837。oracle队列初次因已终止旧PID拒绝启动，未运行oracle；已改为读取实际recovery_identity，并以唯一owner handle23136等待恢复后的batchseal。原诊断runner及失败记录不覆盖。

run_estimate_oracle.py准备绑定输入graph/exportbin/trace/校准记录，抽取全部候选两侧请求，不按结果抽样。离线oracle1800s/16GiB/80GiB保护，timeout终止其私有进程组；输出由analyze_estimates.py核验已测值、估计误差、单pin排名翻转、old/new reverse目标误差分布。所有trace时间仅属诊断开销；不计方法性能。论文同步已封存scope/Rq结果和诊断方法，实际oracle结论仍pending。


估计诊断最终恢复完成：原四次native和全部route/table/guide/query计数通过，独立图/guide审计及input seal通过。审计目录错误后使用finalize_estimate_trace.py纯审计，无新的route调用；第一次生成finalizer的缩进错误在py_compile阻断，未执行native。完整过程保存在estimate_diagnostics/recovery_history.json。唯一oracle队列最后handle35768，oracle及分析exit0，输入seal通过。

完整Dijkstra处理363个endpoint/direction、208769个唯一候选侧请求、105818025个settled节点，离线耗时24.065581s（不是算法规划时间），全量记录756922条。32197次已测记录、7883个不同已知距离与独立oracle全部吻合。P/Rq选中unknown source estimate/true中位：spmv0.474879/0.500055，eltwise0.509770/0.491006；eltwiseRq source阶段76516条unknown候选中75825低估超过20%。Rq的新reverse目标更常source未测且低估，但最终表单pin mean oracle regret反而下降：spmv7.934058→4.663358%，eltwise6.871737→5.556093%。因此低估确实存在，不能单凭它解释最终CPD退化；单pin surrogate也不等于DP共享objective或STA。

可重现compare_geometry.py用同一oracle/记录比较原unit geometry prior：选中unknown source平均相对绝对误差P/Rq在spmv由0.5161/0.4832降至0.2502/0.2205，eltwise0.4832/0.4719降至0.2526/0.2253。拟合source scales约0.43-0.45，样本校准对未测候选明显过于向下；不从这项回顾性误差对比宣称QoR收益。

据此source_floor_candidate_01已实现/构建/独立冻结：严格VPR_H3D_SOURCE_GEOMETRY_FLOOR开关仅对unknown source采用max(1,source_scale)*geometry；exactsource命中仍直接返回，sink和4096/256查询预算不变。它是估计模型prior，不是可证明lowerbound；后续bound诊断读取的是floor后estimate，避免混淆旧rawscale。P/Sf spmv/eltwise小开发配对已由唯一queue handle10385实际启动。Rq/Bq/Cq/H/L/feedback/layer/estimate_trace均关闭，P完整route/table/guide复现门，允许普通失败但不得把offline误差收益替代最终QoR。分析器analyze_source_floor.py已准备。研究继续active，无外部阻碍。


Sf小配对已全部封存，P控制完整route/table/guide复现。spmv P/Sf CPD7.04234/7.04599ns、17/18轮；eltwise6.64602/7.47203ns、39/70轮。Sf最终source已知107/107及149/149，selected_adjusted=0，代表早期floor排除了unknown并改变query/候选选择，不能解读为开关未生效。sourcefloor工作389861/605281较P371525/517976增加。规划Sf1.134816/1.418285s，进程18.450278/30.023695s；不推广。eltwiseSf完整route body等于旧Cq但finalguide CSV不同，记录观察而不推断单网因果。

为区分局部测量不足与规划surrogate问题，完整距离Ed诊断已登记并实际启动（唯一queue63542）。两例spmv/eltwise复用本轮封存P及旧A0/R1，固定K16和共享objective、原端点layer scope、真实Tdel/STA；关闭Rq/Bq/Cq/Sf/H/L/feedback，采用mixed=1/broadtarget=0，Dijkstra界2*N=2057136覆盖物理节点+虚拟crossing terminals，要求truncated=0及mixed/selected所有candidate双侧已测才解释。内置独立前八endpoint校验同时启用。这不是推广的放大预算方法，也不是最终CPD上界，只是测距完整性与surrogate质量的诊断。保留1800s64GiB80GiBmax3VPR；成本含额外校验，不能作加速比。analyze_complete_distance.py已准备。


完整距离初次配置attempt01两例均在path search前被现有DELAY_BUDGET整数[1,1000000]校验拒绝（2N2057136超界）；原status failed、无CPD、日志/审计/seal完整保留，分类见attempt_review.json，不作方法质量失败解释。随后从绑定exportgraph统计：每层physical514284，forward/reverse候选虚拟terminal最多172760，任何查询可settle状态上限687044。因此无需改旧parser，重新登记独立attempt02 budget1000000已足够穷尽，仍要求truncated0和完整mixed/selected测量才能解释；该证明及binhash在complete_distance_bounds.json。新唯一queue handle75882实际启动，原失败attempt不覆盖。过程没有改科研范围或停止条件。


## 完整距离、DP交互与新的时序引导（持续推进）
complete_distance_dev_02 已完整审计封存：spmv Ed7.03470ns/20，eltwise Ed7.47203ns/70；P为7.04234/17及6.64602/39。混合入表候选43499/78563全部双侧测量、选中107/149全部双侧，查询截断0；各8次独立首查询验证。规划18.398655/26.097110s，进程37.785663/56.818383s（诊断、含验证，不作加速论据）。eltwise完整route body等于Sf。说明补齐图延迟不足以保证最终质量。

distance_dp_dev_01 对相同表/查询改变赋值为independent：spmv Pn7.04234/17，12/107 guide改变；eltwise Pn7.66397/36，37/149 guide改变，SB117→168。完整距离En在两例均与Ed完整route相同，guide分别仅1/107及2/149改变。均已审计封存。原验证器错误要求不同路由迭代数下重复计数日志行数相同；实际表序列完全相同，distinct/final查询计数完全相同。保留initial_gate和原队列失败记录，resume_distance_dp仅复用3个已结束native并补跑1个原来缺失的En，没有重跑路由。

实现timing_regret_candidate_01：VPR_H3D_TIMING_GUIDE_MODE=regret，原coverage为默认。仅选择与替代的双侧真实图距离均已测时，对更慢候选加lambda*min(unit,max(0,alternative-chosen-.02unit))秒；lambda=.25。更快、近似相同、未知候选不加时序项。查询和DP不变，原miss2拥塞/物理Tdel/STA保留。稀疏map按RR id排序，事务guide复制自然带全部数据。10万量纲/单调性/幅度不变量+非法/平局边界检查通过，serial/serial构建成功。原独立冻结代码无变更。P/Hc/Tg同输入实验已登记启动，只有P复现通过后继续，不与scope/feedback/新查询组合。


### Tg首轮封存及扩大适用测量集合验证
P/Hc/Tg spmv/eltwise共6/6合法且inputseal通过，P完整route/table/guide复现。Hc/Tg同表/同查询累计状态/同guide identities。Tg完整route均=P，CPD7.04234/6.64602、17/39轮，尚无收益。spmv0个正差替代，eltwise13guides48pairs，独立oracle+旧P中性trace逐条复算全部48项及测量资格，没有多罚或漏罚；最终连接使用被罚替代0（不是搜索展开计数）。Hc spmv CPD相同但route不同/SB0→1，eltwise route=P。Tg规划1.132742/1.347942s、进程19.009717/27.770430s，均仅开发观察。
启动timing_regret_expansion_dev_01，softmax/bnn原seed11/W100/HybridO/P0，P/Hc/Tg，参数全部不变，不组合其他新机制、不扩大查询预算。依据：bnn已有P双侧选中338，比eltwise34有更大适用集合；是迁移探查，不是成功推广。计划timing_regret_expansion_plan.json。独立时序小试队列已终态0，新队列由handle12935独占提交和监督。


## 实测等价guide与关键路径间接影响
本轮分类：progress。原timing_regret_expansion及scope_gemm owner PID/startticks均现场核验存活，未重启；正在完成bnn时序引导和gemm范围迁移。

独立实现equivalent_guides_candidate_01，环境VPR_H3D_EQUIVALENT_GUIDES=4：保留DP单一选择，只把双侧均已测、总图延迟<=原选择+.02unit、当前negotiated opening charge不更高的候选加入可接受集合，最多3个附加，原空间多样性规则；不加查询，不修改Tdel/STA，不与时序/feedback/scope组合。静态独立试验开关显式拒绝feedback组合，避免破坏旧单一assignment评价。10万单调性/非更慢非更贵/非法边界检查通过；serial/serial编译通过；冻结到独立stage。

P/Eq spmv/eltwise 4/4合法、独立审计及seal通过；原P route/table/guide精确复现，Eq前置表/查询状态保持一致。spmv1条连接新增3候选；eltwise5条连接新增10候选，所有候选的已测资格、oracle延迟、charge及原主选择保留都核验通过。最终使用新增替代的连接数均为0；两例完整route=P，CPD7.04234/6.64602、17/39轮。Eq规划1.289199/1.343702s、进程19.608379/27.819707s，开发时间不能作加速论据。适用群体小且行为未变，不推广该分支，不据此结束研究。

对P/Ed/Pn/En四个已封存eltwise最差时序路径作union连接比对（无新增route），8条跨簇连接全部没有直接guide，所属网络也无guide。new_n16765 pin60的物理RR延迟P0.663513494ns→Ed3.845469080ns，Pn在该连接仍0.663513494ns但整体CPD更差；不同结果的最差start/end发生变化，其他连接亦可能改善。输入packing/placement、原始RR source/sink一致；不能把单条路由延迟直接当作全STA差值或单事件因果。证据critical_path_diagnostics/eltwise_distance_summary.json说明应研究跨网络平面拥塞影响，不能只用guided连接局部ranking或delaycoverage解释最终CPD。

下一步：先解释已运行Tg四电路迁移和gemm公平scope，另一个有依据方向是核查native-selected重布线中的平面过用与现有crossing-overuse/drift/path触发之间的遗漏。当前捕获只把推荐crossing或目的节点过用作为overuse信号，没统计guided分支上的其他planar过用；应先无决策变化采样并复现U，确认额外触发机会和候选价格是否会改变，避免无条件重规划全网。此诊断尚未提交，不能宣称已运行或已获收益。


## Tg迁移封存、平面反馈与出口价格诊断

本轮为实质进展，研究active，旧日期/调用上限/作者信息均不作为停止条件。timing_regret_expansion_dev_01独立审计及输入seal完成，P/Hc/Tg四电路12次均合法。Tg四例完整route均等于P；eltwise48、softmax4、bnn64个正regret候选对确实存在，未由此得到最终QoR收益。Hc只有bnn13.6074→13.5998ns、19→18轮，其余CPD持平，四电路几何改善0.013965916%。没有将微小单例增益推广为稳定候选，物理Tdel和STA不变，正式计时仍未启动。

planar_trace_dev_01封存：trace-on/off均完整复现U的route/table/refresh/guide。eltwise38524次refresh上下文中204次guided路径普通平面过用；现有触发与cooldown之后另有43个机会、31个net、迭代4–14。它们是重复上下文事件，不是独立样本。随后planar_feedback_dev_01独立启用该额外触发，原cooldown3/5%margin/查询评分不变，36次extra attempts中5接受（3clear、2旧代价inf），31拒绝在日志精度下old/new代价相等。整体attempt150→179、accepted87→91；完整最终route仍等于U，CPD6.37264ns/34轮。强制一次事务rollback的X诊断合法7.65785ns/82轮，单独报告，不作为收益，也不声称首次rollback恰在接受新触发之后。

exit_price_dev_01单独验证出口价格（Pl关闭，原U触发）：refresh分支加入opening16*.25*clamp(可达出口最小协商价格-1,0,1)，每分支上限4。复用静态SCC、按leaf/candidate缓存、考虑已拥有节点、物理延迟不变；这是放松的拥塞surrogate，并非联合延迟/拥塞最优，还可能逐leaf重复计算共享出口。initial87个table完全等于U，372查询/1523712settled不变。76个正premium，accepted87→90，最终guide22处变化（19新偏好未采用、3删除），但完整route仍相同6.37264ns/34轮。开发规划1.407556s、全进程35.891453s，对照1.341991/27.216749s，含开发trace、非正式性能证据。不推广加权分支，改查接受的guide变化是否影响native实际待重布线连接。

update_pin_trace_dev_01诊断因错误的retained判断被自检拦下：find_by_isink非空缓存不等同于剪枝后保留，VPR原生用1-indexed get_is_isink_reached位图。保留1失败、1未启动，部分事件不作机制结论；这不是原生路由缺陷，也不自动否定先前在剪枝前完整树上的平面trace。已改为原生bitmap，并仍按实际vector<size_t> remaining_targets检查互斥。attempt02打包误用src/CMakeCache.txt（应src/build/CMakeCache.txt），native调用0、失败日志和attempt_review保留。新独立candidate03/batch03已启动，要求与sealed V/Xp完整route/table/refresh/guide/price一致后才解释。未强迫合法分支重布线。

scope_gemm_dev_01原owner继续执行七角色公平scope验证，不重启或重复audit。当前已到A3；部分原生结果尚未全批seal，不作正式合法聚合。后续按诊断证据决定可作用于实际重布线连接的修改，不盲目提高查询预算或guide权重。


连接适用性diagnostic03最终已seal、所有独立审计和V/Xp完全复现门通过。U382次变化中247retained/135targeted，Xp403中262/141；new/reassign/clear分项及final-unadopted所有匹配事件见update_pin_mechanisms.json。不能把最后匹配事件自动当作best-route对应版本，也不能把全部未采用归因于retained。

据此target_feedback_candidate_01实现并构建冻结（64920c453fd484d97695545c68c38c3a5138819e6964a56cb699957c4764639b）：VPR_H3D_TARGET_FEEDBACK默认off，初始plan不变，refresh只将实际remaining_targets纳入候选/共享DP及同表old/new成本比较；非target完整guide字段及perpin generationcriticality保留并断言。候选池仍可复用旧guide资源，已有retained资源拥塞discount保持；原U net-level触发/cooldown3/margin.05不变，未强制合法分支重布线。非target的历史criticality drift仍可能触发工作，这是需用实测开销评估的明确限制。SCC/距离缓存复用、物理Tdel/STA/完整事务及beststate快照保持。仅测试独立Tf，不混Pl/Xp/mixed/H/scope。

target_feedback_dev_01已由唯一queue handle13170启动V/Tf/X eltwise配对；X强制一次完整事务恢复单独计。验证V完整route/table/refresh/guide复现U、V/Tf首轮87table一致、Tf全部接受偏好变化都属于native target且无retained变更、独立物理和guide审计、输入seal。结果尚未封存，不提前推广。1800s/64GiB/80GiB及max3VPR保护不变。


Tf首例已封存通过：V完整复现U，V/Tf首轮87个table一致；Tf所有115次接受变化均targeted/0retained，非target guide全部字段和generationcriticality生产断言通过。eltwise A0/R1/U/Tf CPD9.93208/6.96208/6.37264/6.20812ns，Tf对U改善2.581662%、对R1改善10.829522%；迭代U34→Tf42，wirelength226840→228420，真实SB84→118、CB972→955，不能只报CPD。Tf191attempts/100accepted（U150/87），查询372→268，settled1523712→1097728；targetpin事件2746、保留pin事件13171，重复事件非独立样本。开发规划1.615785→1.093330s、全进程27.866146→27.310656s，含trace且并发环境，不能当正式加速。X恢复一次guide事务后合法7.50471ns/64轮，排除方法收益；不声称第一次强制恢复发生在接受Tf修改之后。

已登记target_feedback_expansion_dev_01队列handle60808，等待上述seal和target_feedback_mechanisms审计后对spmv/softmax/bnn做V/Tf六次同参数配对；完全复用candidate01，旧U分别来自feedback_dev_01和feedback_bnn_dev_01，packed/place/命令/物理输入严格准入。保持原scope与原U触发，无Pl/Xp/H/mixed组合，不按电路选择参数。记录全部失败/超时/缺失，四电路聚合前不推广，正式计时仍未开始。


## 非目标关键度漂移触发诊断

上一轮为实质进展。本轮以/proc startticks确认scope_gemm(owner2893673)和Tf扩大(owner1715748)仍活跃，继续原owner，未重启native或audit。spmv、softmax Tf/V原生CPD/迭代分别7.04599/19、8.97575/13持平；整批待bnn及seal，暂不按合法聚合。

对sealed eltwise Tf日志新增只读分析：191attempts中100接受，但67次接受没有preferred变化；原V150attempts/87接受中37次无preferred变化。Tf preserves非target的perpin关键度generationstate，而现有gate仍取全网drift，因此可能由retained连接历史状态导致重复工作；这个机制未证明，仅是可检验假设。

target_gate_trace_candidate_01已构建冻结，严格默认off的VPR_H3D_TRACE_TARGET_GATE仅记录每次native-selected refresh上下文：whole-net/actual-target drift、crossing/path/cooldown、eligible/previouslyguidedtarget数量。没有额外query、排序、代价或gate改变。单次T trace run复用sealed target_feedback_dev_01/Tf作为完整route/table/refresh/guide/query/pinchange等价对照，避免重复跑同一个trace-off基准；FULL/独立/guide/inputseal后才解释counterfactual counts。队列handle93623实际启动target_gate_trace_dev_01，1800s64GiB80GiBmax3VPR；不是方法收益实验，不从原轨迹减少的触发数预测改变gate后的CPD或时间。


目标gate诊断现已sealed：trace单次完全复现Tf的完整route/table/refresh/guide/query/pinchanges；39678个上下文与191attempts逐项复算原门通过，输入seal及独立物理/guide审计通过。25次attempt（11net）仅由non-target drift触发，19接受、17接受后无preferred变化，但仍有2个preferred变化；17次没有当前eligible target，18次没有previouslyguided target。不能把无preferred变化等同于状态完全不变，也不能从原轨迹计数预测新gate轨迹。

据此新target_drift_candidate_01默认off严格开关VPR_H3D_TARGET_DRIFT（依赖Tf）仅在关键度drift/newlymissing计算时用实际remainingtargets位图过滤；crossing/path信号、cooldown3、候选/成本/5%margin及物理Tdel/STA不变。新增flag不引入跨net状态；原事务/bestroute snapshots完整保留。目标gate原轨迹trace与该修改互斥，避免混淆全网与targetdrift含义。构建冻结成功，target_drift_dev_01 C/Df配对由唯一handle57728实际启动；C必须完整复现sealed Tf后才跑Df。它是有收益风险的gate消融，不预设保持CPD；现有Tf扩大队列仍复用旧冻结candidate01，不受此修改影响。


Df gate消融已sealed并通过独立审计：C完整复现Tf，Df首轮87table一致、最终完整route仍等于C，CPD6.20812ns/42轮，但finalguide不同。attempt191→171、accepted100→86；查询268→277、settled1097728→1134592，preferred变化115→122（均targeted）。规划1.092664→1.116394s、全进程27.770314→27.872052s，仅开发观察，不宣称效率改善。原Tf轨迹25个non-target-only触发中两次实际变更都是新增guide（net5095pin3iter10、net6719pin35iter13），另外17次同时没有eligible或previouslyguidedtarget；这些事件仍可更新元数据/冷却期，新轨迹work不等于旧轨迹剔除25次。Df目前不推广，不扩大仅凭attempt减少的分支；Tf原冻结候选继续跨电路验证。


Tf三例扩大已全部sealed，analyze_target_feedback/analysis和aggregate_target_feedback通过；四例各A0/R1/U/V/Tf均合法，单seed11/HybridO/P0/W100，samebinary/per-arm环境，不按电路挑参。V→Tf1改善3持平0退化，几何改善0.651759619%；R1→Tf改善2.824837977%；A0→Tf两改善一持平一退化，几何改善11.353545794%、最差spmv退化0.160490142%，不能隐藏旧R1仍不及A0的个例。

spmv Tf7.04599ns/19轮、完整route=V，guides不同，query246→155、plan1.030204→.866985s、process18.298138→18.101729s；softmax8.97575ns/13轮、route和guides均=V、query69不变、plan2.219363→1.963610、process39.490352→39.689406。bnn13.4216ns/19轮持平但route不同，wirelength2075701→2074317，SB94→105、CB5066→5062；query1790→1735、settled7331840→7106560、plan10.604389→10.515153s、process268.992863→266.432539s。三例Tf分别8/2/525次preferred变化全部targeted/0retained。开发时间不得推出正式加速。

真实大扇出机制记录：bnn net8940共2869sinks，Tfiter7实际targets671、其中table仅37eligible leaves/320candidates，原128leaf上限没有改变。这说明restrict-to-target改变可进入共享DP的子问题，不能把收益全归为减少无效guide；后续适合单独消融refresh阶段共享DP而保持initialplan不变。当前不从此单事件推断最终CPD。

已审查并释放target_feedback_scale_dev_01队列55155（release记录绑定aggregate SHA）：同一Tf candidate01、原layer scope、attention/ gemm各V/Tf。attention参考U明确failed200，保留provisionalCPD但不能作合法QoR；V要求完整失败route/decisions/status复现。gemm参考sealed优化V，严格匹配所有输入。保持1800s64GiB80GiBmax3VPR、不启用Df/Pl/Xp/mixed/timing，也不按电路挑scope。只是继续规模/失败检验，非最终候选冻结。

独立精确优化target_membership_candidate_01已构建冻结：接受更新时只建立一次remainingtargets成员位图，取代trace及保留guide断言中反复std::find，成员查找从O(sinks*targets)改为O(sinks+targets)，代价/目标排序/查询/gate不变。Df关闭；不将fastplanner profile之外的全部时间归因于该查找。target_membership_dev_01队列42342在Tf扩大seal+机制检查之后，四例O分别复用sealedTf对照，必须完整route/table/refresh/guide/query/pinchanges及无时间计数字段一致；独立审计和seal后才算等价成立。正式计时仍未启动。


成员位图attempt01在启动native前被环境准入拒绝，native_calls=0：预检比对显式settings与manifest有效环境，而既有io.run统一补OMP_NUM_THREADS/OPENBLAS_NUM_THREADS/MKL_NUM_THREADS=1。已核对运行器源码及差异键，VPR算法参数全一致；新run_target_membership_02.py按同样有效环境合并规则比较，未更改原注册runner/stage。原attempt_review、registration和缺失角色记录保留。target_membership_dev_02由唯一队列handle1772实际运行，同一immutablecandidate01；不构造正式性能结论。scale队列55155已实际运行attention，原scope_gemm已到F3，均由原owner持续管理。


## 反馈阶段共享DP贡献的独立消融与失败资源证据

上一轮为实质进展。本轮以/proc startticks重新确认scope_gemm、target_membership_dev_02、target_feedback_scale三原owner活跃，继续原任务；位图小三例原生复现，bnn与全批seal尚待完成。

refresh_assignment_candidate_01已实现构建冻结：严格VPR_H3D_REFRESH_ASSIGNMENT=inherit/independent，默认inherit。independent仅允许initialshared + targetfeedback，实际刷新有限表才调用既有h3d_plan_independent；初始共享DP、候选生成/查询预算/成本/128leaf高扇出fallback/清除策略不变。oldassignment按同一独立objective逐leaf计算opening+branch，再用原5%margin；不是用共享旧cost与独立新cost比较。记录实际shared/independent刷新求解次数及17位old/newcost，不额外运行第二求解器。原独立求解器函数未改动，既有枚举验证继续适用。

小pilot C/Ri（eltwise seed11/P0/HybridO/W100）已登记queue handle39572，等待membership_dev_02全批seal和exactreproduction分析后运行，以保证通常最多3个活跃VPR批次。C须完整复现sealedTf，首轮87table一致；Ri只改变反馈阶段assignment。后续routing轨迹改变可以导致不同的候选上下文，不要求后续全序列table相同，更不能宣称共享DP在完整物理路由上最优。分析器检查目标连接限制、同objective接受阈值、实际求解器计数、独立组数、FULL/独立/guide/inputseal。物理Tdel/STA和事务机制保持，未启用Df/Pl/Xp/mixed/timing。

新增只读failed_attention_diagnostic_01，handle94225，复用sealed原attention_U失败route及RRG，不发起native route。以既有scoped图审计核查失败文件的树/边/开关/容量，并计算其报告的SB/CB占用和过用资源类型，明确区分saved失败文件与native最后一轮。native failed状态绝不改为合法，原独立审计未覆盖的endpoint/localOPIN/nonconfig/busmux限制保留。离线保护1800s/32GiB/80GiB，原冻结目录不写入。


位图优化target_membership_dev_02全部sealed，analyze_target_membership通过四电路完整route/table/refresh/guide/query/pinchanges以及剔除秒数后的全部计划/查询/反馈/最终计数字段一致。四例均合法，Tf质量结果完全保留。reference→O开发planning秒：spmv.866985→1.139478、softmax1.963610→1.781721、eltwise1.093330→1.104084、bnn10.515153→10.472085；process秒18.101729→19.001584、39.689406→38.337939、27.310656→28.071181、266.432539→271.259808。耗时有升有降，不能从渐近成员查找复杂度改进推断正式端到端加速。保留该精确实现及完整代价，下一正式计时仍须同环境轮换重复。

failed_attention_diagnostic_01已完成并seal，离线分析61.064256s（不是规划或路由加速）。原失败route的实际报告SB175、CB1630、planar wirelength505340；独立scoped审计232条错误均是容量过用，231CHANY+1IPIN，0实际crossentry/0crossdestination过用；原生最后200轮也报告232overused RR，但仅数量一致不证明全部状态快照逐项等同。继续保留nativefailed，原scopedaudit不检查endpoint/localOPIN/nonconfig/busmux的边界不扩大。

classify_failed_attention_paths.py通过额外inputseal：464个net/resource事件、442个不同net、601条不同受影响sink连接，其中592same-layer、9remote，0guided；这442个net也没有任何finalguide。guidecsv84行均nonemptypreferred；以保存失败树的terminalpin标签作对照，不额外声称netlist endpoint认证、unguided的实际criticality或失败单事件因果。index_failed_occupancy.py将同一失败artifact原U及已精确复现的新attention_V按routebody+物理graph+manifest/outputhash绑定复用；export新增独立saved_failed_artifact SB/CB/overuse/source字段，不混合法物理结果，不增加独立观察数量。

代码重新核查route_common.cpp说明原VPR_H3D_LAYER_BB_FEEDBACK已经只在native-selected重布线且pre-prune存在过用节点时扩大z范围；不是所有被选择网络都无条件扩大。不能把普通overuse-triggered层扩展重复提出为新机制。之前A2与A3结果同路由应按这个实际实现解释。已准备target_feedback_layer_combination_plan.json：将四例有效Tf与已单独验证的全层搜索scope组合，使用同scope nativeA1/F1/U1公平对照；尚未提交，待当前Ri与原scope Tf failure/scale结果后审查。失败修复不能全部归因于guide，因为旧nativeA1已可修复attention。

已准备aggregate_scope_six.py，在gemm全批sealed后把其并入固定六电路scope比较，保留原五电路报告，不按电路挑scope。refresh_assignment队列39572已满足membership机制准入，原owner继续运行，未额外复制旧路由实验。


Ri eltwise pilot已sealed，FULL/独立/guide/inputseal及分析全部通过。C完整复现Tf；首轮87table相同，H3D_TABLE共有110条相同前缀（包含前23个refresh表），之后轨迹分叉，不要求全程table相等。C120次共享refresh solve，Ri87次独立solve（无共享refresh），17位cost逐项满足同objective5%接受规则，独立有限解groups=leaves。Ri CPD6.37264ns/34轮，对C6.20812/42轮退化2.65007764%；Ri完整route body回到旧U/V。SB118→84、CB955→972、preferred变化115→124，planning1.136390→1.161224、process28.317328→26.815715s。此单例支持共享refresh对Tf时序收益有贡献，但伴随迭代/资源代价，不推广成全局最优证明。

refresh_assignment_expansion_dev_01唯一queue5184已启动spmv/softmax/bnn Ri-only同参数迁移，严格复用Tf质量对照，默认inherit控制在pilot exactTf，成员位图版本全四例exactTf；这不是所有行同二进制的正式计时。保留完整失败状态和后续轨迹query变化；初始共享table必须相同。准备analyze_refresh_assignment_transfer.py及aggregate_refresh_assignment.py四电路聚合，不因Ri单例退化中止机制研究。

原scope attention_Tf原生仍failed200，CPD12.6638仅是provisional，不纳入合法QoR；完整失败route body与原U、新V都一致。已按相同graph和manifest/outputhash将其加入failed_occupancy_index复用同一个原始失败物理统计，不重复路由或独立计样。整个target_feedback_scale批次仍待gemm与全量seal，不提前作为正式全批结论。

依上述证据，scope_target_feedback_dev_01 C1/Tf1组合试验已登记队列92635，等待Ri迁移全量seal和本地研究release审查后运行；不是等待用户许可。复用target_membership_candidate_01（无Ri变更），同样K16/budget4096/mincrit.7/opening16/miss2，仅initialalllayerBB=1及Tf开关。pilot eltwise/attention严格匹配sealed nativeA1/staticF1/fullU1输入，C1须完整复现U1，再比较Tf1。强原生A1本身修复attention，不能把新增scope的成功归于guide。后续是否扩大看统一scope下质量/尾部/成本，不能逐电路取最好scope。分析器与六电路scope聚合已准备。


## Shared-refresh transfer sealed; uniform-scope combination and path diagnosis

refresh_assignment_expansion_dev_01全量sealed，机制/结果分析及aggregate_refresh_assignment.py通过。四电路A0/R1/Tf/Ri均合法，Ri相对Tf零改善/三持平/eltwise退化2.650077640%，电路几何退化0.656035393%。bnnCPD持平13.4216ns，但19→21轮，SB105→100、CB5062→5067、wirelength2074317→2073244。初始sharedtables保留、独立refresh objective及5%hysteresis逐记录核验；三个迁移控制为严格匹配历史Tf，不作所有行同binary正式计时。保留sharedrefresh候选，Ri不推广。

本地研究审查已写scope_target_feedback_release.json（绑定四电路聚合、运行器、membership候选binary SHA），队列92635启动scope_target_feedback_dev_01，owner3386895/ticks1929748334。统一初始全layer范围C1/Tf1，C1完整复现U1；同scope nativeA1/F1/U1是公平主对照。不是用户审批。

eltwise两个native和独立route/guide审计完成但全批未seal：C1 6.20393ns/22轮，Tf1 6.70679ns/21轮；暂不扩大组合。只读paired_saved_paths.py复用验证过的路径解析/物理delay数据，对A1/C1/Tf1最差STA路径并集匹配8个连接，全部所在net无finalguide。最大RR延迟退化new_n16746 pin13 1.035165092→3.109804885ns，两条route均无crossing；bram_select[2]pin2 1.042804093→1.696745216ns，0→2crossings。saved-route身份与packed/place/arch/netlist/RRG匹配，非完整STA增量/atom-pin认证，也不证明单个refresh导致退化或之前从未guided。诊断输出critical_path_diagnostics/scope_target_eltwise_01；未seal仅探索分析，不纳入正式quality聚合。

论文新增Tf目标范围、触发/cooldown、同目标接受规则、无eligible例外、非target状态保留、事务恢复和高扇出DP适用范围变化的方法说明；新增四电路CPD/iterations标准matplotlib图，输入绑定paper/data/target_feedback_figure.json。图已视觉检查。正式计时仍prepared-only；没有速度声明。新scope组合初步退化表明Tf效果依赖搜索范围，后续先完成attention配对和全批seal，综合关键路径/采用率/共享分组证据再选下一修改；不逐电路选最好scope，不把该分支退化作为整个研究终止条件。


## Combination sealed; pressure-only ablation launched

scope_target_feedback_dev_01已全量sealed，analyze_scope_target_feedback与analysis通过：C1/Tf1 eltwise6.20393→6.70679ns（退化8.105507316%），22→21轮，SB206→253、CB1123→1156；planning1.229603→1.082577s/process26.869642→27.017239s只是开发计时。attention两者12.6638ns/49轮、完整route相同、guide不同，planning1.945885/1.864645、process83.920808/83.549727s。全部更新90/18次都actualtargets、0retained。两例相对C1几何退化3.973798293%，相对同scope原生A1退化5.566872173%；不推广Tf1组合。旧探索路径诊断原文保持，新增seal_review.json绑定通过的seal和机制分析，未改变物理delay/因果限制。

已有证据支持下一独立问题：guide压力是否改变未引导关键连接的拥塞/绕路？guide_pressure_dev_01使用同membership冻结binary，保留Tf1所有参数，仅missweight取0/1，原2复用sealedTf1。W0保留规划但零timing/拥塞guide，必须完整route/CPD/iterations等价同scope nativeA1，W1测试一半压力；两个电路统一配置，不按电路挑最优。初始tables必须与Tf1相同；参考物理输入hash/有效环境/同binary均准入核对。保护1800s64GiB80GiB、最多3owner，输入/完整日志/审计封存。analyze_guide_pressure.py准备，通用比较加入A1/W0/W1、Tf1/W1、U1/W1。

首次启动包装器argv0错误导致Python未使用lxml环境，在registration前失败，native_calls0且无batch目录，guide_pressure_launch_attempt01.json保留原因。使用明确.venv-lazagna/bin/python启动未修改runner，执行handle17277。当前eltwise W0已完成且原生等价gate通过，W1运行；不提前报告全批收益。研究继续，非固定矩阵终点。


## Guide pressure and local-margin diagnostics sealed; exact DP sensitivity prototype

guide_pressure_dev_01全量sealed，机制/结果分析通过。两电路W0完整route/CPD/iterations等价同scope原生A1，不视为独立收益。W1相对Tf1：eltwise6.70679→6.0181ns（10.268548739%），attention12.6638持平；相对A1两例CPD都持平。eltwise相对A1 SB243→194、CB1144→1118、wire222926→222716、iterations22→21；attentionW1完整route=Tf1、49轮，而A1/W0 37轮。W1 plan/process eltwise1.093770/26.914801s、attention1.899762/84.403491s为开发时间。不能将追平强原生CPD称为研究目标完成或正式加速。论文guide_pressure_table及输入hash已生成。

只读pressure_eltwise_01路径比较全sealed，W1 new_n16746 pin13物理RRdelay3.109804885→1.964294087ns，仍高于A1的1.035165092；bram_select[2]pin2两次跨层绕行消失，delay1.696745216→1.228629892与A1相同。CPD相同不等价于所有连接退化消失，仍无单事件因果归因。

guide_margin_candidate_01二进制82ce48937f34eace26de325e6f8b73b094caad5c5b59491a35c68ec320afc3c9；guide_margin_dev_01已sealed，T2/T1完整route/table/refresh/guide/query/pinchanges及所有原非时间计数exact原Tf1/W1。只读finite共享表局部opening+branch差距：weight2共250events/197distinctnetpins，其中109localworse、47tie、94better；weight1 229/214、93worse35tie101better。所有localworse在coassigned>1上；初始149events完全相同。不能用局部独立代价差直接当共享DP可靠性，更不能当物理delay可信度。高扇出fallback不在该finite表诊断覆盖内。无新查询/算法行为改变。

据此新增h3d_partition_sensitivity.h：固定原median hierarchy，存每个node原最优及前两共享候选cost，对每leaf候选排除只沿祖先链改split子树和shared排除选择，得到同finiteDP目标的精确exclusioncost。当前诊断重建一次摘要，未来若用于生产需复用原DP中间结果并验证开销；未采用新的guide可靠性映射。1000随机表/20187exclusions与逐个删除候选重跑原DP比较通过，含1718不可行/14872ties和局部更差但全网margin正的共享反例；优化编译及ASan/UBSan均pass，binding保存source/test/results SHA。

dp_sensitivity_candidate_01已构建（63c2add8661bc515eb6f76dc16a608aa82049587e460a521a48cf3960315a159），dp_sensitivity_dev_01 handle66470正在native等价/独立审计，T2/T1 native已结束，batchseal仍pending。只读计数/记录exclusion和自身计算time，不改变guide/scoring/queries。先analyze_guide_margin.py再analyze_dp_sensitivity.py，比较既有localtrace逐行一致并joinlocal/net-levelmargin，完成后才考虑 bounded reliability映射；不能把unit pass或诊断本身当作QoR收益。原scopegemm与Tfscale原owner继续，未重启。


## Exact DP sensitivity native validation sealed

dp_sensitivity_dev_01完成全部native/independent/guide/inputseal；analyze_guide_margin + analyze_dp_sensitivity + analysis通过。完整route/table/refresh/query/guide/pinchanges/原non-time counters及H3D_GUIDE_MARGIN逐行等价先前T2/T1。T2 250events：104严格exactzero、146positive；101refresh中64exactzero。T1 229events：76exactzero、153positive；80refresh中36exactzero。两条轨迹都各有52个localworse但DPmarginpositive的events，说明不能用局部独立评分差代替共享目标敏感度。所有exclusions都有finitealternative。109finiteplan events的摘要重建+exclusion计算时间T2 .000666052s/T1 .000542891s，不含日志，只能说明此小case诊断测得开销，非formal生产开销或加速。

证据支持新的tie_pressure_plan.json：只在完整共享DP中排除候选的最优cost严格等于basecost时撤去该connection额外miss_weight，positive/infinite保持原weight2；candidate assignment、目标、查询和原生物理delay/STA不变，不用阈值拟合。零margin只证明此finite目标存在替代解，不证明任意无惩罚路由或独立叶选择组合保持目标，因此必须独立pairednative试验。暂未实现/运行此policy，当前src仍诊断版，不能宣称QoR收益。下一步新增opt-in开关及压力状态trace，保留non-target/rollback语义，same-scope eltwise/attention对比sealedTf1、W1、强nativeA1，结果再决定扩大或其他改动。


Scopegemm原owner39152已确认为terminal(returncode1)，非观察超时：7native和7independentrouteaudit全pass，但run_scope_gemm只对A1跳过guideaudit，误要求MODEoff的A3提供guideCSV。原runner/注册/日志/全部结果保留；resume_scope_gemm.py只做post-route recovery，无io.run，native_calls0。按实际manifest MODEoff跳过A1/A3guide审查，对其余guidedarms补齐finalguideaudit，复验所有native输出hash、sharedinput原statidentity及sha、source/runnerbinding，再封存。recovery_identity已记录，handle48229/64GiB1800s80GiB保护，恢复owner确认live。完成后再aggregate_scope_six，不在未seal时推广六例结论；此工具链异常不阻断整体研究。


## Six-circuit closure, sensitivity-pressure outcomes, fixed-parameter transfer (2026-11-13)

Scope gemm post-route recovery completed with seven native runs reused and zero new route calls. The original MODEoff A3 guide-audit error and recovery evidence remain preserved. All six declared seen circuits now have sealed scope comparisons: native initial-global A1/F1/U1 and delayed-global A3/F3/U3 are all 6/6 legal, whereas original-scope A0/R1/U are 5/6 legal. Relative to same-scope native A1, F1/U1 conditional CPD geomeans are -0.4312614%/-0.3252918%; relative to A3, F3/U3 are -0.1760715%/-0.4313440%. No uniform guide advantage or per-circuit scope selection. See scope_six_circuit_summary.json.

Original-scope target feedback scale validation sealed: attention V/Tf remain failed with identical terminal route; failed provisional CPD excluded. Gemm V/Tf both 13.1564 ns, iterations 20→22, different full routes; preference changes 1570/1420, retained changes 457/0. Six-circuit A0/R1/U/V/Tf each have five legal and one failure. Tf vs V: one CPD improvement, four ties, no regression, conditional geomean +0.5217484%; versus R1 +2.2663274%; versus A0 +9.3285139%, worst -0.1604901%. No success gain, no blind or formal timing claim. See target_feedback_six_circuit_summary.json.

Exact-DP tie pressure Z, continuous relative-margin pressure G, and half-strength tie combination H all completed sealed paired validation. Z disables additional congestion guide weight only on strictly exact finite-objective ties; G uses original_weight*gap/(gap+selected standalone leafcost); H combines nominal weight1 with strict-tie suppression. Shared-DP sensitivity oracle tests, positive-sharing/tie/unavailable cases, scaling/base-offset invariance for G, and native target/transaction assertions are preserved. Objective sensitivity is not physical-delay confidence. Z eltwise6.40460ns (6.42229% worse than A1), H6.59052ns (9.51164% worse); both attention12.6638ns/37 have complete native-A1 route identity. G both cases have complete native-A1 route identity, retaining planning overhead without QoR/resource benefit. None promoted. Immutable binaries: Z62bfbb3e4805705bfbde0b6976f74c52422c7969b2e7c32a66592fca1ae47753, G4c394230455a7861fe749eb008ee9cdcd0d10c7eaecd8af91a655e53efb79b74. H reuses Z. Validated unit-source revisions archived by matching historical SHA.

Transfer selection was pinned before new outcome inspection: from 14 exact selected-R1 seed21 HybridO/P0/W100 input pairs, sort by grid side and circuit name, select clstm_like.small and conv_layer (both n60). Conv_layer historical A0/R1 failures are retained, not replaced by a successful input. New arms F/V/Tf use unchanged original-scope target_feedback_candidate_01; A1 is a distinct initial-global native alternative, not a guide-only effect. F must reproduce historical full terminal route/status/CPD/wire/iteration, including failures. No parameter fitting, no query increase.

Attempt01 failed configuration validation before native routing because static F inherited update-pin tracing with feedback off; preserved attempt_review and all receipts, not an algorithm QoR failure. Attempt02 corrects only that instrumentation dependency in a separate runner/directory. clstm all four native and independent audits complete, CPD6.85706ns; F/V/Tf35 iterations, A1 20. Conv_layer F exactly reproduces historical failure; V also fails; remaining runs and final seal still pending at this entry. No batch-level transfer claim yet. Analyzer now validates failed terminal feedback traces instead of skipping them, keeps provisional failed CPD separate, and checks actual configured seed. Generic analysis/export hardcoded seed11 corrected to manifest/registration seed, including seed21; both failed and missing attempts preserved.

Paper methods/results/cost caveats updated and build_pressure_outcomes_transfer.log succeeds. Formal timing remains prepared only. Research active: no date/call/matrix/author blocker. Next read-only failure analysis will distinguish saved failed occupancy and guided descendants before further algorithm changes. Current retained ownership already uses post-prune route tree; do not invent an ownership-staleness bug or equate entry-node ownership with a retained physical crossing.


## Fixed-parameter transfer completed; conditional source-capacity obstruction independently verified

Both transfer batches are sealed and mechanism/general analysis pass. Four pre-ordered seed21 HybridO/P0/W100 circuits retain all A0/R1/F/V/Tf/A1 statuses: each arm is 3 legal/1 failed. clstm F/V/Tf share the complete route, 6.85706ns/35iters; A1 ties CPD at20iters. Robot F/V/Tf13.7339ns/24iters; A1 13.3623ns/17. Tpu F/V/Tf7.81221ns with18/18/20iters and different routes; A1 7.99803ns/17. Tf vsR1/V has three CPDties, no improvement or regression; vsA0 two improvements/one regression, conditional geomean -0.15646225%, worst -2.84021985%. All input order and parameters were pinned; no per-circuit scope/policy winner. Full data: target_feedback_transfer_circuit_summary.json.

Failed convF reproduces originalR1 terminalroute; V/Tf/A1 allfail at200. Failure traces now undergo target-state mechanism validation: V1333preferencechanges853retained, Tf416changes0retained. Failed provisionalCPDs excluded from legal fields. Raw failure physical metrics independently audited with one exact-native-graph stream, failed_transfer_diagnostic_02. First diagnostic attempt incorrectly demanded byte equality between physical-source and imported-native graph encodings and stopped before auditing; artifacts/reason preserved. Attempt02 directly hashes and audits actual --read_rr_graph. All original failures remain. A0/R1/F/V/Tf/A1 overused counts953/954/954/952/952/95. Tf951CHANY+1CHANX;1942affectedconnections1937same-layer5remote,1finalguided. A1all95CHANY,192affected187same-layer5remote,nonefinalguided. Saved SB/CB occupancy A0 292/1296,R1/F290/1303,V323/1307,Tf291/1309,A1 1301/2445. These are failed artifacts, not legalQoR or evidence of an independent timing gain. Separate failed_transfer_occupancy_index.json is merged into exports; legalCPD remains null.

Sample DSP-output conflicts motivated a necessary first-exit capacity test, not another budget increase. Enumerate all outgoing edges of each SOURCE/OPIN closure in the exact native RRG, with no bbox/guide restriction. Capacitated bipartite matching covers21205/21300nets. Aggregate Hall witness:267distinctnets have a complete exit-resource union of172capacity, deficit95net-occupancy units. SOURCE mappings match F/V/Tf/A1. source_escape_diagnostic_01 archives every source/internalclosure/exit and witness. The matching helper agrees with exhaustive assignment on503 small capacitated cases. verify_source_escape_certificate.py uses a different standard-library XML parser and no matching algorithm, rechecks allclosureoutgoingedges/capacities/sourceidentity andinequality; source_escape_verification_01.json passed. This proves an obstruction conditional on recorded SOURCE assignments, not allplacements orpinmappings, and is not independentatom-terminalcertification. A1's95excessoccupancyunits all lie in the cut, attaining this necessary lowerbound; numberof overusednodes is not what Hall deficit generally bounds.

source_escape_controls_01 passed: legal clstm13390,robot12976,tpu22487,attention24371 nets all fullymatch; each has a constructive firstexit assignment from actuallegalroute within capacity. Original failedattention also matches all24371 withidenticalSOURCE map tolegalA1. Thus necessary-cut success is not a routability proof. We keep conv failed in every denominator and continue research on reasonable next mechanisms rather than repeating unchanged routing on its certifiedfixedmap.

Formal same-environment rotated timing is now active, formal_timing_01 owner2043011/start1930328585,handle86556,CPU0. Frozen A0/R1/fullfeedback-with-exact-closure-view (U-view), five mutuallylegal seen circuits, three rotated orders,45roles. This is a separate stable cache/feedback cost study, not a performance claim for later Tf/pressure policies. Eachprocess1800s64GiB80GiB; no concurrent VPR/C++compilation/largegraphaudit while ownerlive. Exactroute+nativeFULL and bound physicalinputs permit reuse of independentcertificates; mismatches retained/gated. Wholeprocess+planning+RSS+allrepeats retained, formal results pending.45roles is not an overallresearchcap or endpoint.

Next algorithm hypothesis saved in retained_prefix_diagnostic_plan.json (designonly, notimplemented): quantify actualpost-prune retainedcrossingedge/sinkreachability/RCprefix versus current source/opening objective, with no newquery orbehaviorchange first. Entryownership alreadycomes fromcurrenttree; CB OPIN may beowned withoutcrossing. setup_net reloads timing beforeplanning, but partial-tree Tdel is not finalSTA or certifiedextensionbound. Afterformalownerfinishes, diagnostic default-off/onmust reproduceTf fullroutes/tables/guides/non-timecounters oneltwise andtpu before any marginal-cost policy. This is an actionable nextmethod path, not a blockedstate. PaperTeX includes4case transfer, failurecutandcontrols, formalstatus. Last PDF build_transfer_result_02.log passed; latesttextadditions awaitpost-timing rebuild. Research active withoutdate/call/matrix/authormetadata limits.


## Retained-prefix diagnostic implemented while exclusive timing proceeds

Previous goal turn classified progress: sealed four-circuit transfer, independently verified source-cut certificate, legal/failure controls and formal timing launch. Current formal owner revalidated by /proc PID/startticks, not merely its marker. No concurrent native routing, C++ compilation or graph audit was launched.

Mutable src now implements opt-in VPR_H3D_TRACE_RETAINED_PREFIX, requiring edge delay scoring, cached closure views, feedback and target restriction. It observes finite tables after the original solve and before hysteresis, including rejected proposals. Per-plan ENTRY records separate retained candidate entry ownership from actual cross-layer child edges; EXIT records contain post-prune partial-tree Tdel/R/C, parent switch and re_expand; REACH uses only lookup into existing immutable sink closure views and const intersection; PAIR records finite branch costs, old/proposed preference and reachable/expandable retained-exit counts. Empty eligibility/high-fanout/non-tree tables are explicit SKIP events. No scoring, ordering, query, guide, congestion, physical delay or transaction logic was changed. Default-off performs none of the diagnostic traversal. Timing cost from tracing is diagnostic overhead, not a production performance claim.

Read source confirms setup_net reloads timing after pruning and h3d_prepare_net runs later. Entry ownership already used the current tree before this change; there is no claimed stale-ownership fix. Retained partial-tree Tdel is not final STA or a certified extension lower bound.

analyze_retained_prefix.py is prepared to require sealed native/independent/finalguide correctness, same binary/environment except trace flag, matching command/private inputs, full route/guide/CPD/iterations, and every original H3D record with time fields normalized. It validates cross-record ownership/exit/reach/decision counts and reports repeated-event coverage. Synthetic test distinguishes owned-but-planar entry from actual reachable retained crossing; one rejected-plan example passes and eight malformed records are rejected. Python syntax/textual checks passed; these do not substitute for C++ compilation or native equivalence.

Status is implemented_unbuilt_unvalidated, with source hashes and patch against relative_pressure_candidate_01 in retained_prefix_implementation.json/retained_prefix_unbuilt.patch. src/vpr/vpr still represents the previous build and must NOT be staged as the new diagnostic. Build and isolated native paired experiments wait for active formal timing to terminate, then follow the unchanged registered diagnostic question on eltwise(seed11) and tpu_like.small.os(seed21). No algorithm QoR benefit or test completion is claimed. Frozen timing source/binaries and original frozen results remain untouched.


## Retained-prefix build/paired workflow queued behind exclusive timing

Previous turn was progress (diagnostic C++/analysis implementation), and this turn adds a reviewable build/freeze/experiment workflow. prepare_retained_prefix_candidate.py runs make -j8 vpr in src with matching PWD (the Makefile uses SOURCE_DIR=$(PWD)), pins source before/after, checks the trace marker in the new binary and VTR_ASSERT_LEVEL=2, and archives build logs/source/cache/binary. Each process retains 1800s/64GiB/80GiB protection; build timeout kills its own process group. No C++ build has started yet.

run_retained_prefix.py uses separate seed-specific batches: eltwise11 and tpu_like.small.os21, fixed original-scope Tf inputs/environment. C first reproduces the frozen Tf route/guide/table/original counters; T differs only in the trace flag and must reproduce all current-binary original records. Both receive native FULL/independent/final-guide audits and inputseal. A failed reproduction preserves the native result and stops dependent arms, with a diagnostic gate reason. A0/R1/Tf references remain explicit and strictly input matched. No claimed QoR experiment has been run by this preparation.

A review found that normalizing every field ending in seconds would also hide physical unit_seconds changes. The analyzer/helper now whitelist known elapsed-time fields by record type; physical unit_seconds and unknown physical-seconds fields remain exact. Synthetic corruption/ownership tests and physical-unit normalization tests pass. No native equivalence is implied. Source and script hashes refreshed before registering the queue.

The single deterministic queue is now SUBMITTED, handle67970, PID2771875/ticks1930476426, verifiedlive with state waiting_for_formal_owner. Identity, archived scripts/source and bindings are under retained_prefix_pipeline_01. Dependency formal2043011/ticks1930328585 remains verifiedlive; 28 formal roles completed when queued status was checked. Queue watches exact owner identity every30s without repeated unchanged log analysis, then requires terminal completion/inputseal before any heavy work. It builds the frozen candidate and executes/analyzes the two deterministic paired cases sequentially. Source/script drift, command failure or equivalence failure preserves records and returns to main-model reasoning; no automatic restart. Luna remains unavailable as previously disclosed; no model switch claimed.

Do not separately launch the planned builder/runners or modify pinned scripts, source or retained_prefix_implementation.json while this queue is live. Further scientific decisions await actual trace evidence. Formal timing still excludes concurrent heavy research work. The pipeline or45-role timing batch finishing will not complete the overall research goal.


## Formal aggregation strengthened without touching measured jobs or queued diagnostic inputs

Both formal owner2043011/start1930328585 and retained-prefix pipeline2771875/start1930476426 were revalidated live; pipeline remains waiting on the exact formal owner. Previous turn was progress (reviewed build/paired workflow actually queued). No native restart, C++ compilation or graph audit was performed during this exclusive timing interval.

Read-only review found analyze_formal_timing omitted already-recorded GNU time memory data and used range(3) for repeat ratios. The old analyzer is archived by SHA44dd5c66bf0b1d78c8d46ed8b87d30d1f9f44a7e65b6cb20e243d1f5c72c0dab. The derived-data analyzer now checks unique registered roles, derives repeat counts from the immutable orders, distinguishes running/not_started/missing or case-gated rows, and preserves native statuses/provisional delays separately from legalCPD. It reads terminal time.txt only with manifest output-hash agreement, records RSS KiB, user/system CPU seconds, child GNU wall, page faults/context switches, environment affinity/load and per-repeat positions. Registered full-process observer wall remains the performance metric; child wall is separate and rounded. RSS is GNU process/children maximum as reported, not a simultaneous process-tree sum. Planning/router times are components, not additive full-process costs.

Complete-arm statistics retain every individual repetition and expose medians/maxima only for wholly legal groups after batch seal. Failed/timeout/running/missing/unsealed groups cannot silently shrink the set. Quality-reuse checks remain required; actual route artifact hashes are rechecked only after measurement seal, avoiding concurrent large route reads. Synthetic tests cover two-repeat schedules, malformed registrations, both GNU elapsed-time forms, RSS units, and incomplete-group exclusion. Tests passed, with scripts/results bound in formal_timing_statistics_binding.json.

A single partial snapshot contains all45registeredroles:29legal_pending_batch_seal,1running,15not_started;29terminalRSSrecords. All formal ratios and legalCPD fields remain unpromoted before seal. This is aggregation verification, not a performance result. The formal runner/binaries/protocol and all pinned retained-prefix pipeline inputs remain unchanged. Paper source explains these comparison/memory conventions; PDF rebuild remains deferred until measurement ends. Research goal active, no new stopping cap.


## Development evidence ledger reconciled with completed v14 experiments (2026-11-13)

Progress this turn: replaced stale operational claims in development-paper claims_evidence.md, mechanisms_and_ablation.md, acceptance_13.md and README.md. Old documents still described DP isolation as unexecuted, imposed a 16-route/12-hour/Nov14 proposal, and said large-file rehash remained incomplete. Historical v13 populations/provenance remain separate; the unexecuted old proposal remains explicitly historical and its date/count/total-time limits revoked. The seven old binding lists already had 3,183 large-file rehashes with zero failures; that limited scope does not include all warehouse files or complete physical semantics. Frozen ROOT/paper/dac2027 and original experiment/code artifacts were not changed. Prior development text is preserved under paper/data/ledger_history_20261113 and README_v13_history.md.

Added C18–C26 for actually completed static/refresh independent-assignment controls, Tf seen/transfer outcomes, native scope effects, exact finite DP sensitivity and non-promoted pressure policies, conditional fixed-SOURCE cut, still-unsealed formal timing, and still-unbuilt retained-prefix instrumentation. Static independent N vs shared F:6declared/5bothlegal,0improve4tie1regress,conditionalgeo−0.842302%; refreshRi vsTf:4bothlegal,0improve3tie1regress,−0.656035%. Localized shared benefit is supported; universal DP or global optimality is not. Tf seen6 has1improve4tie1commonfailure vsV, +0.521748% conditional; transfer4 has3ties1commonfailure vsR1/V and −0.156462% conditional vsA0. No new success. SOURCE obstruction267/172/95 remains conditional on recorded mapping, not all placements; failedattention also passes the necessary test. No new measured-quality or speedup result was invented.

paper/data/evidence_v14_ledger.json binds27small-source artifacts. Reproducible paper/verify_v14_ledger.py validates all source digests,43local links, exact retained aggregate fields and displayed rounded CPD percentages; passed receipt paper/data/evidence_v14_ledger_validation.json. This is small-file/claim verification, not PDF/native/RRG revalidation. Latest paper source has not been rebuilt into PDF during exclusive timing. README now distinguishes current source from last PDF and avoids directing current work to mutate the frozen original paper.

Authoritative process observation: formal2043011/start1930328585 and queued2771875/start1930476426 bothlive;31formal observations completed, latestbnn_r1_R1legal; remaining roles not inferred complete. No formal completion seal. Retained-prefix state remains waiting_for_formal_owner. No queued/pinned script/source/implementation binding was edited, no duplicate build/route/audit launched. Keep the pipeline and measured owners. After formal seals, run derived analysis, and let queued default-off/trace-on gates complete before selecting marginal-prefix algorithm changes. Research goal active; this turn is progress, not blocked or complete.


## Retained-prefix interpretation prepared without changing queued inputs (2026-11-13)

Previous turn was progress: paper claim/evidence reconciliation changed authoritative development documents and passed bound checks. This turn exact formal PID2043011/start1930328585 and queued PID2771875/start1930476426 were verified live;32formal roles completed, latestbnn_r1_Ulegal, no completion seal. Queued diagnostic still waits for exact measured owner. No native launch, C++ build or large graph audit was performed.

Source review established a necessary interpretation boundary: H3D_PREFIX_PAIR best_exit_tdel_seconds minimizes over all reachable retained crossing children, including non-expandable ones. In connection_router.tpp, normal tree traversal separately considers re_expand for each node and still traverses descendants; high-fanout insertion additionally filters spatial bins and bounding boxes. Therefore fastest reachable child Tdel is not necessarily a usable expansion-prefix estimate, and direct child re_expand does not certify heap insertion or describe all usable descendants. No bug in physical Tdel or native routing is claimed.

Implemented independent analyze_retained_prefix_costs.py, leaving all queued/pinned code and scripts untouched. After the primary native neutrality receipt passes, this analysis checks its parser/helper hashes and trace/manifest bindings, recomputes its schema summary, and reports candidate events in six ownership/reachability/expansion categories. It separately retains fastest reachable and fastest reachable expandable child delays, partial-tree entry delay normalized by the logged physical unit, source surrogate, and opening-minus-source charge. Summaries separate accepted/rejected, proposed/nonproposed, and measured/estimated source events, retain missing cached views and count distinct nets/plans. No per-leaf reranking, shared-DP counterfactual, confidence interval, QoR prediction or removal of native congestion is inferred. Partial-tree/source discrepancy is not a physical-delay error bound; events are not independent samples.

Synthetic test_retained_prefix_costs.py passed all six states, the faster-nonexpandable exit counterexample, acceptance/source strata, empty summaries, finite JSON and three malformed cost/unit cases. Validation binding retained_prefix_cost_analysis_validation.json; no actual native trace is yet analyzed. After each queued primary analysis succeeds, run the supplemental CLI with --trace <batch>/runs/<trace-role>, --verified-analysis <primary-receipt>, --out <new-result>. Inspect actual candidate prevalence/cost mismatch before deciding any independent marginal-opening or prefix-delay experiment. Formal owner remains exclusive and original queued jobs retained. Research active, no blocking condition or stopping cap introduced.


## 2026-11-13: sealed formal timing and prefix pipeline handoff

All 45 registered rotated A0/R1/full-feedback closure-view U roles completed legal with strict reference route/quality gates; final physical-input seal passed. The final analyzer rehashed every routed artifact and retains all repetitions, GNU time counters, peak RSS, CPD, resources and iterations. Circuit-geometric median process ratios give U/R1=0.789894330936 and U/A0=1.062457264186: 21.010567% lower time than R1 but 6.245726% residual overhead against native A0. All five individual circuits follow both directions. This is seen/mutually legal conditional timing, not a success gain or isolated cache effect; later Tf/pressure/prefix variants excluded. Formal owner terminated normally; existing prefix pipeline automatically started its pinned build. Research remains active. Development TeX/CSV/table/claim ledger updated; latest PDF rebuild still pending.


## Formal timing PDF and retained-prefix native gate

Formal runtime export added to development paper; rebuilt PDF has25 pages with new tableIX on page24, no overfull/undefined warnings, and numeric table text verified. This is a development manuscript, not a page-limit/submission certification. Prefix immutable build succeeded; initial eltwise audit failed because benchmark context was resolved after changing study.BASE. Original attempted logs preserved. Dedicated recovery reuses2 native runs/new0, performs independent graph/guide audits and seals inputs; primary exact reproduction and supplemental cost analysis pass. Scientific note records 154 owned/133 reusable candidate events and conditional marginal-opening/prefix-delay hypotheses. Corrected separate v2 runner launched seed21 TPU pair in retained_prefix_tpu_dev_02, handle32722; original scripts and completed evidence remain intact.


## TPU prefix confirmation and independent opening-credit hypothesis

TPU seed21 pair completed/sealed, default-off reproduces original Tf and trace preserves complete route, guide, original counters. Primary and supplemental native analyses pass.303 leaf events,260 with retained reachable options;89286 candidate events,270 owned269 reusable. Accepted-proposed reusable59events allsource-measured with zero entry-tree/source discrepancy. Neither case shows faster-nonexpandable mismatch. This favors testing baseline opening credit first; prefix-delay substitution remains separate. Implemented default-off VPR_H3D_RETAINED_OPENING_CREDIT alpha[0,1], refresh-only ownedentry credit alpha*min(1,negotiated). Acc/present premiums, physical/native costs and branch/source scores unchanged. Same opening function feeds ranking/DP/prior hysteresis. Candidate build started; not yet native-validated or promoted.


## Full credit and strength probes sealed

Both full-credit pairs sealed with exact disabled controls, FULL/independent route/guide audits. Eltwise CPD22.082853% worse, TPU identical final Tf route; full credit notpromoted. Alpha.25/.5 probes separately registered before TPU outcome inspection and run serially with exact existing C reuse, zero new control routes. Both sealed and formula-audited. Strength results: {".25": {"status": "legal", "cpd": 6.20812, "iterations": 42, "comparison": {"both_legal": true, "cpd_improvement_pct": 0.0, "same_route": true}, "resources": {"planar_wirelength_excluding_sb_half_nodes": 228420, "sb_pairs_used": 118, "sb_pair_net_occupancy": 118, "cb_crossing_output_sources_used": 955, "cb_crossing_output_source_net_occupancy": 955, "actual_crossing_edge_traversals": {"OPIN->CHANX": 554, "CHANX->CHANX": 118, "OPIN->CHANY": 453}, "qualification": "CB edges share source OPIN and destination channel capacity; no independent per-edge via count"}, "mechanism": {"entry_table_records": 3220, "owned_entry_table_records": 57, "credited_entry_table_records": 57, "negotiated_premium_records": 0, "formula_passed": true, "scope": "Unique plan/entry records; repeated trajectory observations, not independent samples."}}, ".5": {"status": "legal", "cpd": 6.20812, "iterations": 42, "comparison": {"both_legal": true, "cpd_improvement_pct": 0.0, "same_route": true}, "resources": {"planar_wirelength_excluding_sb_half_nodes": 228420, "sb_pairs_used": 118, "sb_pair_net_occupancy": 118, "cb_crossing_output_sources_used": 955, "cb_crossing_output_source_net_occupancy": 955, "actual_crossing_edge_traversals": {"OPIN->CHANX": 554, "CHANX->CHANX": 118, "OPIN->CHANY": 453}, "qualification": "CB edges share source OPIN and destination channel capacity; no independent per-edge via count"}, "mechanism": {"entry_table_records": 3220, "owned_entry_table_records": 57, "credited_entry_table_records": 57, "negotiated_premium_records": 0, "formula_passed": true, "scope": "Unique plan/entry records; repeated trajectory observations, not independent samples."}}}
Old analyzer source preserved by digest before reuse extension. All raw records, states and development times retained; no formal speedup inference. Full-credit paper/claim source updated, latest PDF rebuild and strength synthesis remain next work. Research active; no current heavy process.


## Final-guide agreement and separate retained-source ablation

Read-only sealed guide comparison: alpha.25/.5 change20/24 shared pin preferences; their agreement on changed pins rises0->11/0->15, with3addedguidepins each, yet complete final routes identical. Fullcredit changes23shared preferences, agreement0->21; only5ofthese have changed actual crossing sets, despite CPDregression. Finalguide overlap is agreement, not causal search adoption. New source inspection: legacy untimed branch source proxy has floor2 even for retained OPIN currentTdel0; this was absent from prior opening-source discrepancy summaries. Implemented independent refresh-only source cost from finite nonnegative currentTdel/unit for re_expand retainedentries, both opening and source part of branchfallback. No openingcredit, sinkcost, querybudget, initialplanning, feasibility, nativeTdel/STA changes. Built immutable retained_source_candidate_01; registered sourceexperiment and launched eltwise C/Ps pair (60646). Native analyzer prepared to check exactdisabledcontrol, sameinitialtables, effective source trace formula and full opening-price conservation, thenallQoR statuses/audits/seal. No source scoring gain claim pending pair.


## Retained source pilot sealed, transfer running

Eltwise C/Ps pair passed exact disabled reproduction, initialtable equality, independent route/guide audits, physical-input seal, and native source/opening-price formula checks. Ps35retained expandable entry records,35differfromgeometrybranchsource,only2differfromlegacyopeningsource. CPD6.20812->7.00702ns (12.868630% worse), iterations42->30. Notpromoted; a current-tree source estimate alone does not establish better final timing. Pre-registered TPU seed21 sameparamspair launched to test transfer of this tradeoff. No ownershipcredit, increasedqueries, nativephysicalTdel/STA changes. Paper adoption/sourcehypothesis source updated and build_adoption_result_01 succeeded; latestpilot numericalresult stillneedsincorporation. Research active.


## Source transfer negative; early-criticality layer scope begins

TPU source pair sealed; effective-source/full-opening formulas pass and C exactly reproduces Tf. CPD7.81221->7.86071ns (0.620823% worse), iters20->18. Both source cases worseCPD/feweriters, geomeanCPDdegradation6.568919%; no promotion. Preserve1st-source artifacts. Existing nativeA1 global scope independently recoversattention; already-existing pre-prune overuse scope is not novel. New registered trigger expands only z for native-selected nets with actual remaining target criticality>=.9, aftercriticalitycomputation. Domains persist as native recovery; XY/nativecost/transactions/STA untouched. Guide-off C/O/Z/K pilot: C absentfeature/feedback0 exactA0; O existingoveruseonly; Z threshold0+overuse mustexactA1; Kthreshold.9+overuse. Failedcritical_scope_candidate_01 build preserved (vector<int> prototype vs actual vector<size_t>), correctednew02build passed; no routes onfailedstage. Eltwise4arm pilot launched; no qualityclaim pendingC/Zgates and audits. Researchactive.

2026-11-13: critical_scope eltwise sealed: C/Z exact gates, all4 new legal, K6.40159 vs O6.22942/A1 6.01810; no promotion. Original attention owner preserved. Native count2 control registered and submitted as single dependency-bound pipeline46106/PID3950106/start1932416241; no new candidate code or parameter combination. Source confirms sWNS-based early exit and slack-first best-route selection; count2 is only an upper limit, not guaranteed CPD benefit. Mutable paper and source ledger updated.

2026-11-13: attention critical-scope sealed, all gates passed; C failed200, O legal12.6638/31, Z=A1 exact12.6638/37, K legal12.6638/62, SB697/CB2297. Both pilot cases now sealed: 7/8 new roles legal, one expected exact A0 failure; K one CPD tie/one regression vs both O and A1, not promoted. Native count2 pipeline transitioned from exact dependency wait to live A0 arm. Initial analyzer has a known display-only router_seconds key mismatch; v2 prepared separately without editing queue-bound scripts. Corrected analysis will reuse the same native receipts after initial pipeline terminates, preserving the first analysis.

2026-11-13: uniform native count2 study sealed4/4legal, all first-legal numeric-prefix gates passed. A0 9.93208/43 ->6.01810/68, R1 6.96208/46 ->6.01810/65; Tf6.20812/42 ->same exact final route after62 (second legal ~6.390 correctly rejected); A1 same exact6.01810 after23 with early exit. Restored SB/CB A0 30/968,R1 39/969,Tf118/955,A1243/1144. This changes the strong comparison; no broad Tf timing superiority. Initial analysis preserved, display-only router_seconds typo corrected with v2 and same native receipts. Failed attention resource diagnostic sealed with0newroute, failed A0/R1/C231overused mostlysame-layer nonguided. Post-legal guide-use release registered, implemented defaultoff, built stage01; paired runner6004 active, disabled control already exactly reproduces count2 Tf complete route/guides/original records. No planning-freeze combined.

2026-11-13: independent post-legal release P sealed with all gates:6.20393ns/67,SB38CB966, tiny0.067492%vsTf but3.087852%worse nativecount2. Independent planning-freeze F also sealed with all11gates:6.19629ns/62,SB30CB968,0.190557%vsTf but2.960901%worse nativecount2. F skips28774preparecalls, refresh389->191,query362->268, development planning2.320655->1.179399s/process38.043944->36.079993s (no formal speedup claim). Neither promoted/combined. Uniform count2 extension preregistered forspmv/softmax/bnn and submitted single pipeline10533/PID400835; currentlyspmv_count2, all binaries/oldcount1 inputs matched and pinned, exactprefix/audits required. No research blockers or global stop conditions.

2026-11-13: spmv count2 extension sealed4/4legal and all prefix gates passed; all four full routes/CPDs equal their count1 control, native heuristic exits after one extra iteration. This differs from eltwise, so no extrapolation of the large native refinement gain. Extension pipeline10533 continues softmax thenbnn. Latest paper PDF26pages built; key numeric text and build-log scan pass, no overfull/fatal/undefined lines; not visual or DAC page-limit certification.

2026-11-13: native count2 extension softmax sealed4/4legal, all fullroutes and CPDs unchanged (one extra early-exit iteration), asspmv. Four-case aggregator implemented and first partial snapshot explicitly retains bnn pending (no final population claim). New path-witness diagnostic preregistered and implemented defaultoff: optional parent/edge weights from already settled legacy Dijkstra nodes, 2m cached records/50k emitted side events, no new searches or scores. Core100randomgraphs×25epochs verifies2500querypairs/9433parentsteps/3110terminals, UBSan+libstdc++assertions, 4GiB/60s protection; native RR mapping/equivalence still pending. Single pipeline87452/PID1278629/start1932725031 submitted, waits exact existing extension owner400835/start1932548087 then aggregates, builds stage01, runsC/T, streams actual native RR-edge/weight and proxy-formula audit, analyzes. Its implementation/scripts and mutable C++ source are PINNED: do not edit/restart while queued/running. Unit archive copies match tested bytes. No QoR claim or research stop.

2026-11-13: four-case reconvergence aggregate SEALED32legal (16newcount2+16matchedreusedcount1), all prefixes passed. Tf vsR1 count1+2.824838% ->count2-.780191%(0W3T1L); vsA0/A1 count2-.474666%, worst-3.157475%,1W1T2L. Bnn allarmsCPDsame count1/2, legal-cycle/route identity maydiffer; original attention failure andgemmcount2missing stillexplicit. CSV/TeX/reportbindings exported; mainpaper/table+claimC33 updated, PDF numeric checks passed (actualpagecount invalid forsubmissionclaim). Pathwitnessstage01 BUILT and C/T+graphedge/Tdel+proxyformula audits pass with exactlysame Tfroute6.20812/62,query362. Initial50000rows include11866measured/38134unknown, omit62704later sideevents; canonicalgeometry1853paths/2999plan-side snapshots/4371weightededges. Loggingcensor motivates stage02, notnewbudget: unknownsaggregated, fullrowscountonlymeasured, samequery4096/cache2m/cap50000. Stage02built and pipeline37509 launched forC/T/RRaudit/analyzer; no automaticreroute or QoRinference. MutableCppnotpinnedafterstage02freeze, immutable stage02 andv2scripts remainpinnedbynewpipeline.

2026-11-13: witnessloggingv2 pipeline37509 SEALED and terminal. C/T exactTf6.20812/62, alllegacy query/table/guide/prefix gates and independent physical/proxy audit pass. All26900measured of112704side requests emitted,0trace/cacheomission,2482unique staticpaths/6070plan-side snapshots. Exploratorycoverage:56352candidate-leaf events557both,24190sourceonly,1596sinkonly,30009neither;704proposals only36both(11inacceptedplans). Of25fullyknownproposed+alternative events,11lower localproxyprice(5accepted),7alsolowerindependentcharge; NOT sharedDPdominance. Fixed-budget candidate-directed path-query prototype registered next, notimplemented/submitted: no enlargedlegacy4096, separate256newexpansions/selectedrefresh matchedQ0/Qh/Qpquery-onlycontrols, validpathUB vsprovedexactdistinctions, currentprice snapshot caches, actualremainingtargets+criticality/rankuncertainty. Nextgoalturn must implement/test primitive then native integration, not wait on completed pipelines or stopresearch.


候选路径与评分封存：60,000核心随机查询核对通过；原生查询四臂及真实RR物理核对通过。固定每规划256新增展开，Q0/Qh/Qp有效路径0/47/53，全部完整route与guide一致6.20812ns/62。校准评分S0/S1全原生/物理复用严格条件及独立公式/指纹/DP/滞回检查通过；4814成本变化和48额外DP未改变任何提议、接受及最终route。新观测没有同叶候选对照，75/79评分叶数值退化为几何缩放。旧完整逆侧缓存合并可使81叶事件有至少两条路径（75仅靠旧缓存即有），是覆盖机会而非收益。已登记candidate_path_cached_score_experiment_01.json并构建独立candidate_path_cached_stage_01：静态父路径捕获与verbose追踪分离，原生查询工作不变，当前快照重新计价；K0捕获不使用对照旧S1，K1合并缓存观测。批次candidate_path_cached_eltwise_dev_01由唯一runner执行，句柄38235；研究目标持续active，不设全局日期/调用上限。

缓存合并K0/K1批次结束，native/independent/final-guide/inputseal均通过。独立cached_score_analysis.json通过：710条缓存+53新路径，81叶有>=2观测，8规划提议变化（5接受），接受变化0，完整route相同但最终guide两条不同。CPD6.20812/62，SB118CB955不变，不能宣称QoR。保留两次审计脚本错误attempt01/02：不存在sink_known字段及local_gap反推chosen歧义，修正为既有完整见证路径/快照一致性和完整原始query/RRG身份条件下策略证据复用；全部物理边与公式/共享目标重新核对。压缩缓存已登记，10000随机查询/13692终端路径通过UBSan/断言，完整401509父记录压至56114，原查询/父路径均相同；原生独立构建句柄41778，待构建后等价配对。

压缩缓存原生精确等价封存：compact_witness_eltwise_dev_01/compact_analysis.json passed，1482752→580273条记录(-60.865135%)，0skip，全非计时/前缀/路径/定价/评分/DP/guide/route一致；旧物理/目标证据只在原始全部记录与RRG严格相同下复用。开发进程38.488834→38.835669s，不作加速/RSS主张。继续物理sink-delay隔离分支，登记candidate_path_delay_experiment_01.json，候选candidate_path_delay_stage_01构建完成：P旧price1 delay0复现；D0/D1同price0，D1 delayalpha.25，用缓存已确定真实sink距离逐候选替换并校准未知，source/opening不变、物理UB不冒充最短。唯一runner工具句柄37450，全局研究仍active。

逐候选物理sink-delay配对及审计结束，全部native/independent/guide/inputseal通过。P精确压缩price版；D0原生route和前缀精确query-only。D1price0 delay.25新增5312校正（710精确/4602估计），525精确sink对应未知source，说明局部覆盖利用门槛已改变；24提议变化其中3接受、接受决定变化0、guide三条不同，物理完整route仍相同6.20812/62/SB118CB955。独立fresh RR/价格/搜索工作+逐叶median/签名校正+290DP/指纹/同目标滞回通过。两次审计脚本失败均保留attempt01/02：首轮比较需显式零摘要，新汇总需取最后累计值；不是native算法失败。无QoR推广；仍弱于强count2 A0/R1(6.0181)。已登记下一guide_influence_experiment_01.json只读实际连接引导影响诊断，尚未实现/提交，作为下一可执行研究步骤。所有本轮native/build/audit进程均已terminal，无活动source pin；研究active无阻碍。

开发结果已统一导出candidate_path_development_summary_01.json（17legal=13new+4严格匹配复用），完整CSV保留所有角色实际资源/迭代/规划/router/process，论文选8行展示，正式计时仍引用原sealed45角色而不以此开发计时造速度比。论文C35-C39更新并编译27页，数字和无overfull/fatal/undefined日志检查通过；不视为最终DAC篇幅/视觉认证。CONTINUATION/live_handoff更新为最新物理delay验证源码、所有句柄terminal、无队列无阻碍。下一明确动作先复验source-empty reverse skip在新评分下是否仍合理（登记source_empty_reverse_score_experiment_01.json），再独立做实际guide搜索影响追踪（guide_influence_experiment_01.json）。两者只登记，未实现/未提交，无虚构后台任务。科研目标active，旧日期/总route/固定矩阵/作者条件均不恢复。


新目标回合前轮分类progress：源代码与candidate_path_delay_stage_01全部绑定一致，开始source-empty reverse登记复验。source_empty_reverse_stage_01独立构建，C/R均legal且完整路由/guide/所有评分相同；source_empty_analysis.json实际RR及逐叶评分/DP审计通过。但source-empty requests=0，独立源为空oracle集合为空，不能把通过视为原覆盖数优化得到验证。source_empty_exercise_classification_01.json明确标为zero_exercise_scope_correction。重新读取用户补充包EXPERIMENT_PROTOCOL.md第3节，原优化是available<min(K,ranked.size)，当前D/src和冻结vendor都未启用该available门槛，且最新用户已撤销该包旧全局次数/日期/矩阵停止条件。上轮登记只覆盖全source-map为空，范围较窄，已纠正而不扩跑同一零触发分支。
另登记source_coverage_gate_experiment_01.json四臂：F/G分别复现当前physical.25与原cost规则physical0（price均0），E为G启用真实available/need reverse门槛，N为F启用同门槛；source-empty入场始终关。源码只在原reverse块内skip，保留后续candidate选择/pool/DP，显式计unmeasured；输出跳过ranked候选及source-known标志，后续独立实际RR forward4096 Dijkstra验证每个source覆盖标记。source_coverage_gate_stage_01已构建；唯一native批次source_coverage_gate_eltwise_dev_01，工具句柄9968，F已完成，后续同owner依次执行。普通研究决策自主推进，研究active无阻碍。

原available/need门槛四臂已封存：source_coverage_gate_eltwise_dev_01全native/independent/finalguide/inputseal通过，source_coverage_analysis.json独立真实RR/全forward oracle及逐叶物理/共享目标全部passed。98源端点、765936重复candidate source-known flags验证；每处理臂853检查651skip，distinct legacy查询362→185，settled1482752→757760(-48.895028%)，缓存父记录580273→291379无保护触发。旧cost规则G/E全部base/prefix表/决策/guide/完整route一致；新sink scorer F/N精确观测710→98、校正5312→1168，5提议变化2被接受、接受决定变化0，base/prefix表和finalguide均不同，物理完整route依然相同6.20812/62/SB118CB955。故旧gate不能视为新score等价优化。新priced查询53→67有效上界、同62967工作，不能替代缺失物理测量。source_coverage_gate_summary_01.json及全10角色CSV(6新+4匹配原生参考)封存；详细候选日志下F/G/E/N开发进程38.590899/39.085446/38.437730/39.791280s，仅原始费用，不作正式加速比。
论文C40/C41与方法机制/主结果/消融/费用同步，编译27页，数字与无overfull/fatal/undefined检查通过。source_coverage_protocol_reconciliation_01.json绑定原协议原始段落并声明旧全局上限失效。所有本轮native/build/audit句柄terminal、D/src与最新stage逐文件一致、无活跃/排队作业。next_guide_quality_decision_01.json明确下一优先实际关键连接guide影响追踪（成本raw/加权贡献、三focus连接当前树状态）；根据测量再实现可靠性加权有界soft timing或修正retained-tree指导语义，不能只优化尚无QoR的新scorer。lazy_reverse_experiment_01.json另登记按相同优先级延迟不被消费reverse、保持原完整新评分；未实现/提交，与实际guide机制独立。研究持续active，无研究阻碍，不因本轮平局或旧日期/次数/矩阵/作者信息终止。


当前目标回合前轮分类progress，已核验D/src逐文件等于source_coverage_gate_stage_01，旧原冻结树未动。实现guide_influence_stage_01只读实际连接搜索追踪，固定分组最多10000原始边行、每宽度试验重置、三focus连接现有树上下文。guide_influence_eltwise_dev_01 C/T均legal6.20812/62，默认off复现完整原F且trace-on保持所有原非计时/前缀/原生迭代行/guide/完整route精确相同；guide_influence_analysis.json独立实际RR有向边/switch类型/Tdel/原始float乘数/解析关键度贡献、3729边行与31树上下文全部passed，1941种有向边。全35448次guided crossing评估，31719原始行按预定quota省略，所有桶累计计数保留。focus4674/pin9和pin21在iter17的12/18评估均miss、附加费用中位9.4857/2.6263图delay units，已有sink-layer reexpand节点；不能推导候选可行性不足或唯一因果。4675/pin23六个guided连接尝试完全没有guided crossing评估，九次context均已有sink层reexpand节点。比“criticality削弱所以需盲目加大”更支持有界化附加方法压力、区分已有树复用。
已预登记bounded_critical_guide_experiment_01.json并实现bounded_critical_stage_01：三臂physical/price额外score均0，C原miss2，Z实际c>=.9f时仅移除方法附加拥塞，T同Z再加beta.25*sidecoverage*unit秒的setup搜索项（实际乘criticality）。保留native原get_rr_cong_cost/pres/history、physicalTdel/STA、RCV、事务；coverage是源/汇精确legacy距离是否已测的半权均值，非QoR概率；新priced UB不算精确。新属性存guide全状态，加入非target保留断言和final best guide日志。200000随机helper案例通过UBSan/断言/nativebase/cap/disabled/RCV/浮点threshold边界，1200+有效应用。新stage独立构建完成并启动唯一三臂native批次bounded_critical_eltwise_dev_01；工具句柄以本轮live_handoff后续记录为准，不依赖猜测。等待C默认off精确D0门后才看Z/T，不将C->Z抑制收益冒称T秒项收益。

本轮19新路由角色均legal且原生/full-independent/finalguide/inputseal通过；source/成本/覆盖审计全部通过，8严格匹配原生reference另列（count1和count2分开），统一guide_policy_development_01.json及CSV/9行停止规则表绑定。bounded_critical all-stage beta.25 count2 C/Z/T=6.20812/6.38975/6.01810，iters62/65/78，T仅持平强A0/R1/A1；traceoff三臂原全状态/route/guide复现。进一步完整count1 C/Z/T=6.20812/6.76259/8.25683，iters42/39/57，T比C退化33.000490%、比旧R1退化18.597172%；与对应count2 firstlegal前缀精确匹配，故不能推广count2单点正结果。
后legal policy C/P0/P count2=6.20812/6.20393/6.20393，iters62/76/64，前42迭代cost/query/heap/prefix完全相同，phase仅nativelegal hook激活，best保存阶段明确；独立368端点方向/2076测量flags核对通过。P1 count1完整route/guide/STA/iters/原cost状态复现C，best时inactive。此phase避免早期伤害但未追平强native，不推广。
cap-only.25以native float c*penalty为上限，低于bound保留旧操作；500000核心兼容+非放大性质案例passed。actualRR/445endpoint oracle/2120flags及operator/finalguide通过。cap K count2=6.01810/78、count1=8.25683/57，完整final route和原guideCSV分别等于fixed.25，不能把这解释为完整搜索或策略属性等价（应用总数13049 vs13053）。当前不接受“单是早期放大导致退化”的充分解释，四分之一cap仍扰动大多数critical额外成本。
已预登记bounded_cap_range_experiment_01.json：同binary beta.5/1分别count1/2共4角色，借较保守cap保留更多原操作，明确比较默认firstlegal与最终质量，不扩query预算、无新source/build必要；未实现/未提交。下一步优先执行这一固定开发范围；若仍无稳健收益，应实质改进规划候选相对当前pruned-tree多源搜索的相关性或不确定性，而不是只整理负结果或等待作者。lazy_reverse独立优化仍只登记。论文C42-C45覆盖方法/主结果/消融/机制/费用，编译28页数字与无overfull/fatal/undefined检查通过，非最终DAC篇幅认证。所有本轮进程terminal，D/src逐文件等于bounded_cap_stage_01，冻结原v13/原结果/原论文未改。研究active，无阻碍。


2026-11-13 研究继续active，本轮分类progress，无输入/资源/作者阻碍。bounded_cap_range原setup01在0native时因A0无guide文件失败留存；02四native完成后原runner漏pair_check导致收尾失败，凭持久化runtime/private输入与原sealed控制恢复，未重复路由；审计468端点方向/4242flags/3588有向边通过，同beta首次合法前缀精确复现。L2/H2/L1/H1=6.01810/6.83185/8.44266/7.85132ns，iters58/59/39/32；L2仅持平强A0/R1/A1，L1比C差35.993827%，不推广。物理worst-path并集核对quarter11连接88行、bracket15连接90行无歧义，最大退化均可出现在整网无guide的连接，不能推导单事件因果。
只读search_domain_stage_01编译因t_bb前置声明/edge_sink_node API错误失败封存，修正独立02成功。search_domain_eltwise_dev_01两臂原非时间cost/query/heap/prefix/实际influence/route/guide精确复现；独立实际RRG核对3830搜索行(3809guided)、1156seed raw及31完整focus组，无search行省略。2835guided实际push sink层种子，27guided无preferred源/头通过当前native drivepoint BB；树re_expand存在不再代替入堆事实，BB admission不代替可达性。
box_guide_stage_01独立实现只在本次实际BB排除全部preferred边时撤去search-local软guide，RCV不动，每retry重判、不改guide快照/physicalTdel/STA/native拥塞/事务。C2/B2/B1三臂均legal、FULL/独立/guide/seal及27实际RRG判定passed，B1首次合法精确B2；5nets触发27次，最终route/guide/6.20812ns/SB118CB955均与对应C相同，iters62/42。原cost/influence/数值轨迹存在差异，不称全程等价；没有QoR改进，不推广。新配对times仅详细顺序开发费用。
继续实质机制：复用31完整实际种子组做residual_seed_oracle_01，无native route。输入4994132有向边zeroRC核对，18离线Dijkstra共3475516settlements；30/31组有有限同层walk，10guided全部有，6/10不劣最佳恰一推荐cross，4/10仍cross更好。iter17 pin21(no-cross3.611143 vs preferred1.172490ns)反驳直接按sink层source存在撤guide。原4096逆查询仅settle23/565重复sink层seed，单缓存既有普通标签覆盖不足。注意walk未验证避开未记录非seed树分支、不计native拥塞，非合法extension或STA预测。下一residual_multitarget_query_experiment_01.json已登记未实施/提交：固定shared256预算，用真实queued source集合/seedTdel为多目标，空间vs零启发查询；先离线真实path/UB/exact验证后native只读再评分，不增加旧预算、不假造队列，不因本轮平局终止科研。
论文C46-C50及主方法/实验/消融/机制/费用CSV同步，29页working draft，数字及无overfull/fatal/undefined检查passed；ledger188来源/128本地链接核对passed，非最终DAC篇幅认证。所有本轮native/build/audit/oracle/TeX句柄terminal；当前D/src39绑定文件精确box_guide_stage_01，所有存在原对应文件的baseline哈希不变。CONTINUATION/live_handoff标记active下一多目标查询，无后台或排队任务。旧日期/次数/矩阵/作者限制继续撤销。


2026-11-13 本研究回合为progress，保持active；前回合真进展(9native与物理路径机制)，本轮先新核验旧owner均terminal、D/src以box_guide_stage_01为父，未重跑旧任务。实现residual_query_offline_01，直接复用原H3dCandidatePath C++generic引擎，真实sink层queued多源带当前seedTdel虚拟terminal，固定256/16384labels/65536heap，不改变真实RRG。31focus组Q0零启发0path/7936展开；Qh空间13path/6843，其中10guided只有2path，全部UB无exact。真实有向边/BB/currentprefix与完整oracle核对；180随机图+dense资源stop×3budget共1086适配答案独立Floyd passed，含zero cycle/source==seed/无源/layer/BB/工作内存终止。
residual_path_reuse_offline_01时间序列物理suffix缓存不存动态prefix/price，pool和skip-known两臂都19/31path、5/10guided。skip21query/4544展开，对比always31query/6843展开；cache54/56witness无cap。仅固定contexts离线counterfactual，不冒充native。
原生只读集成复用已有H3dDelayPlan reverse index。stage01因t_bb声明编译失败留存native0；stage02构建完成后审查cache early-skip计数元数据，未提交；修正stage03独立冻结后4臂C/Q0/Qh/Qs全部legal，完整route/guide/oldcost/query/heap/prefix/数值行/实际influence精确C，CPD6.20812/62/SB118CB955。3809guided请求，974无sink层source skip；Q0/Qh/Qs fresh2835/2835/1654，paths687/1376/1595，展开725760/530656/364731，Qs比Qh少31.267902%新增工作。1181cache hits、2012static witnesses，无cache/pathoutput/seedcap触发。11427attempt、7324lower、354sinkBB oracle组/132634普通settlements、30完整seed组、20同输入离线匹配、2349实际有向边/weight/BB与因果cache全部passed。所有native路径仍UB，query结果不改成本或guide，故无QoR收益；新增路径可能交其他非seed树枝，未认证合法extension。API probe1.305621/1.093254/.642077s不含源收集去重trace；完整过程C/Q0/Qh/Qs38.688073/39.766775/41.642259/38.391025s全部保留，顺序开发不作正式speedup。
代价/置信局限：Qs对Qh两者有path的1376场景好145/同1097/更差134，最坏UB2.298914x；新增219path。不能拿cachehit当物理最优或QoR置信。已据此登记retained_outside_experiment_01.json(未实施/提交)：先只读验证当前pruned tree合法suffix/currentBB/expandableanchor/Tdel/currentprices且无额外query，若有价值再把无新增cross作为明确DP叶outsidecost，sameobjective旧assignment重评、eta0精确旧控制/eta.25限制代理收益、intentional empty-guide元数据/事务/冷却滞回及count1/2试验；否则按具体路径交树/锚失效原因改查询目标，而非强行清guide。route_net.tpp实际setup/prune在h3d_prepare_net之前，当前树校验有明确位置。禁止只因sink层seed存在就撤guide。
论文C51-C54及主方法/实验/机制/消融/资源费用CSV同步，29页working PDF数字/无overfull/fatal/undefined通过；ledger203来源/139本地链接；不是最终DAC篇幅认证。所有本轮build/native/offline/audit/TeX句柄terminal，无活跃或排队作业；D/src39绑定文件精确residual_native_stage_03、存在原对应的baseline哈希全不变。目标active，没有旧全局日期/调用总数/矩阵/作者阻碍。


2026-11-13 本目标回合分类progress，先新核验旧Qs owner terminal/seal，并确认D/src等于residual_native_stage_03。实现retained_outside_trace_stage_01只读当前树/价格观察(无新查询)，C0/D1均合法且完整route/guide/旧cost/query/heap/prefix/数值行/actualinfluence/残余query非时间decision/cache精确Qs，仍6.20812ns/62/SB118CB955；FULL/独立route/guide/inputseal passed。333finite table(246refresh)/853叶事件；3663缓存witness，3544anchor_absent、1tree_intersection、118valid，覆盖106叶事件/11网，71叶best raw低于当前physical standalone。37458完整当前树行/37354 nativefloat前缀Tdel、11933 price边snapshot、3663因果来源、704refresh standalone、8173树edge/switch、1099suffix edge/weight核对通过，无guard/trace省略。Root源及sinkpin RR对应固定pair final trace，当前price公式/容量/同plan snapshot核对；非all-net occupancy历史重放，local tree/graph extension也非global容量或STA承诺。
锚点原因另核实：3544当前缺失中1622其他net静态query、1589同网query中间节点、333曾为同网真实queued source；不能把所有缺失归因为剪枝。118有效中116旧真实source/1同网中间节点/1跨网witness。保持静态suffix池并按当前可扩展树节点过滤查索引有证据，盲删中间/跨网路径无证据。
隔离outside_dp_core_01/src实现显式单叶outside_cost、sentinel kind=opening.size()(不是RR resource)、无新cross群、sameobjective prior assignment及shared/independent求解。320随机表×3版本×2solvers=1920答案用独立所有hierarchy cuts穷举验证，640eta0 pair cost/assignment精确旧解，含空候选/纯outside/零cost/ties/invalid prior，UBSan/stdassert passed。尚未拷进mutable router，必须连native类型/元数据一起处理，避免sentinel流入channels_[table[c]]或probe_candidates_。
全246真实refresh表反事实回放：baseline optimum/assignment/currentprior/5%acceptance精确原生，eta0全部精确；eta.25 outsideCost=max(raw,.75*bestStandalone)使14提议变化且14均从旧拒绝变接受、20outside叶。是固定contexts counterfactual，不是真实新reroutes或CPD收益。下一retained_outside_experiment_01.json phase2及outside_native_integration_notes_01.json具体覆盖显式kind、先原physical candidate query后extended solver、当前prioroutside重评、intentional empty guide metadata、失效/过用时仅VPR已选remainingtargets触发冷却refresh、非target/transaction/best完整恢复、eta0 nativegate及eta.25 count1/count2 pilots，不扩budget。
论文C55-C57与主方法/机制/消融/候选全排除原因/actual资源和费用CSV同步，working PDF30页实际验证记录为准，数字/无overfull/fatal/undefined通过。ledger来源218/链接150以validation为准；非最终DAC篇幅认证。所有本轮build/native/audit/unit/replay/TeX句柄terminal，无活跃或排队任务；D/src39文件精确retained_outside_trace_stage_01，23原对应baseline源文件哈希不变。完整目标继续active，无科研输入/资源/作者阻碍，旧日期/调用上限/固定矩阵终止条件仍撤销。


2026-11-13 本轮progress，outside从隔离core真正接入native，source outside_native_stage_01独立冻结构建44.442476s。显式outside kind不做RR下标、原physical candidate queries先执行再extended DP，max(raw,.75standalone)，sameobjective prioroutside重评；intentional empty元数据/当前anchor-BB-tree校验、projected suffix过用和失效仅对VPR已选remainingtargets触发cooldown反馈，物理Tdel/STA/nativecongestion不动。非target新字段断言、wholevector best/rollback快照及最终outside专用描述完成。
C2/Z2控制native均legal且所有旧记录/guide/route精确，原comparator未排9903新FINAL_OUTSIDE_STATE行误报，证据已定位，只过滤新descriptor后旧记录完全精确；旧attempt01及其缺失roles保留，02严格复用两控制，仅补跑N2/N1，没有重跑路由控制。N2/N1均FULL/独立route/guide/input/全部local树价格/extended-DP-state passed，N1 firstlegal全新记录前缀精确N2。CPD均6.20812/62或42/SB118CB955、完整route同C，逐迭代nativeheap计数同C；35448→35352 guided-crossing评估、planning/query不同，不称全轨迹等价。N2 242refresh tables/105valid witness/5accepted plans中7outside叶；N1 120tables/3plans中4outside叶；各9903SAVE和FINAL完整元数据hash核对，最终各3outside。Z2 246actual extended tables全部outside0和9903full-state hashes独立核对。未改善质量，不推广，不把继承Tf对旧R1的收益归功新outside。
Xnew/Xret两test-only角色实际各拒绝一次变化元数据：prior无/current有outside、prior有/current已改变outside，恢复expected/restored摘要一致；两者最终legal6.20812/62，native图/guide/input/fullcurrenttree/DP/prior/state/best证明passed。测试角色不混入quality样本或正式速度比，immutable staticpathcache可留但动态prefix/price每次重评。
用户询问收尾/耗时/GitHub：已现场核查远端main仅b132a1d(11/9)，paper/research/gpt本地未提交，明确回复此前封存只是共享盘本地。四主角色full process40.847070/41.142620/42.595828/29.223656，router25.29/25.04/27.08/13.79，planning2.955286/2.828174/2.951390/1.544859，probeAPI.658143/.666044/.655114/.170727；规划/query为router子项不重复加，非router约15.5s；人工/审计/打包缺统一timer，不编造完整cycle占比。预计阶段快照30-60分钟，长期科研不等全部完成再快照。
Git源码快照主patch43变更文件已独立应用于upstream0b912并核对Git树/全部变化blob；原external dirs无.git，首attempt误读父HEAD已记录纠正，verified版仅证明2878依赖文件同原服务器baseline，不伪称上游gitlink内容认证。rawRRG/route/日志/二进制/大JSON留服务器，选择小证据与论文的local review清单约4660files/121MiB，待最终刷新。GitHub connector实查仓库是PUBLIC，与旧默认private说明不符；当前用户是状态询问而未明确公开未投稿稿范围，先完成本地review commit后需用户决定公开范围，不把此事当整个科研阻碍。
论文C58-C60和资源/费用CSV/控制恢复与两种回滚证据同步，working PDF30页数字/日志passed，非最终DAC篇幅认证。新当前guide资格方向已单独登记未实施：453/3809实际guide-search c<计划nativefloat.7，search-local不改存储guide/预算，控制off及两停止规则，RCV与native物理拥塞不动；是可验证假设，不是本轮CPD因果证明。所有native/build/audit/TeX owner terminal；mutable39文件与outside_native_stage_01匹配、23原文件baseline哈希不变；目标active，无日期/route总数/固定矩阵/作者阻碍。
