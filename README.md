# H3D-inspired native 3D FPGA routing

[显式I/O配对通过、六页投稿14](docs/GitHub_clma_IO_admission_submission14_20261117.md)：N/D同14.899788070ns、106117wire/1SB/450CB及全端点，完整677.24/681.11秒；无domain增量，覆盖扩大且初始树改变的限制保留。46行表及全部失败照录。下一不同电路s38584.1真实打包/布局及准入过，N→D确认已启动、尚无完整结果。[投稿14 PDF](research/dac_v14_20261112/submission_narrative_14/build/main.pdf)。

[clma显式I/O native整臂与下一独立输入](docs/GitHub_clma_IO_native_next_input_20261117.md)：native完整677.24秒，原核验通过；domain及配对继续。s38584.1（1260锁存器）只排队当前全部必要核验后的实际输入准备，尚无新结果，投稿13保持。

[clma显式I/O覆盖实例已启动](docs/GitHub_clma_IO_coverage_20261117.md)：原实际电路/图/布局，新增20ns+输入/输出max1/min0基准约束；旧330pin slack全部有限，但fresh初始树同时改变、无冗余共享域组。完整N/D及后续准入继续；不是新独立输入，六页投稿13保持。

[clma完整配对通过、六页投稿13](docs/GitHub_clma_admission_submission13_20261117.md)：N/D同14.713963381ns、106127wire/4SB/450CB及全部端点，完整668.98/659.82秒仅单次描述。3组有结构机会但+inf分支slack被原准入排除，没有domain增量。44行表保留全部负结果，[投稿13 PDF](research/dac_v14_20261112/submission_narrative_13/build/main.pdf)可独立审阅。

[clma native整臂结束、原核验通过](docs/GitHub_clma_native_complete_20261117.md)：668.98秒，CPD15.0530→14.7140ns，+100线长，同4SB/450CB，setup2改善/0退化。domain继续；完整raw/配对通过前不进入收益，六页投稿12保持。

[CP1r6报告修复与clma独立输入确认](docs/GitHub_CP1r6_clma_confirmation_20261117.md)：88条原断言及算法规则保持；clma真实1089块两层布局已完成，native资源阶段有3个冗余网但无可选共享域/owner组，后续时序、domain及配对仍按原队列。尚无新增完整收益，[六页投稿12](research/dac_v14_20261112/submission_narrative_12/build/main.pdf)保持。

[LSTM单标志释放消融通过、六页投稿12](docs/GitHub_LSTM_release_submission12_20261117.md)：同源8请求组，关闭释放5/8后回滚，已有开启释放8/8且资源接受；实际释放前轨迹相同。新组件214.45秒与核验1.48秒独立列账，仅支持该组机制归因，不归因完整70SB。42行主表及原费用限制保持。[投稿12 PDF](research/dac_v14_20261112/submission_narrative_12/build/main.pdf)。

[当前完整配对与六页投稿11](docs/GitHub_frisc_admission_submission11_20261117.md)：LSTM整臂通过（少70SB、多2187线长，同CPD/CB；归档干扰费用不作干净比值）；Frisc完整N/D通过但无domain增量。四档代价机制对照已完成。[投稿11 PDF](research/dac_v14_20261112/submission_narrative_11/build/main.pdf) · [42行配对表](research/dac_v14_20261112/submission_narrative_11/COMPLETE_PAIR_TABLE.md)。本批必要核验全部终结；下方运行描述为历史快照，研究继续。

[Frisc独立电路与明确SDC确认](docs/GitHub_frisc_confirmation_20261117.md)：实际529块n25 Hybrid-O布局、共用20ns基准时钟。native资源阶段有256CB源占用但无多跨层冗余组；完整N/D及后续准入仍运行，不新增收益主张。投稿10保持。

[Elliptic完整配对通过、六页投稿10](docs/GitHub_elliptic_admission_submission10_20261117.md)：N/D均为12.419319795ns、37962wire/0SB/0CB，全端点向量一致。两臂共有原生时序收益，但没有跨层域增量；完整286.70/282.94秒仅单次描述。全部40行结果与失败类别保留，[投稿10 PDF](research/dac_v14_20261112/submission_narrative_10/build/main.pdf)可独立作者审阅。以下启动阶段文字为历史记录。

[Elliptic独立电路完整确认已启动](docs/GitHub_elliptic_confirmation_20261117.md)：已核验640块真实打包/布局，固定CP1r5 native→domain及后续三项只读准入。不同公开电路、同Hybrid-O架构族；当前不新增完整质量主张，六页投稿09可独立审阅。下方各实验状态以对应记录时间为准。

## Current research snapshot — 2026-11-17

[CLSTM-SB完整配对通过、六页投稿09](docs/GitHub_CLSTM_SB_admission_submission09_20261117.md)：同6.590324286ns，N/D为234918/941/0与234970/940/0；少1SB、多52wire，配对setup85改善/22退化。完整1430.08/918.13秒为单次描述，无一般加速主张。无释放/owner事件，所有搜索失败及预算拒绝保留。已知CLSTM的不同SB-only图/实际布局，不计新电路家族。[投稿09 PDF](research/dac_v14_20261112/submission_narrative_09/build/main.pdf)；当前两臂与三项准入全部终结，下面运行/阶段描述是历史状态。

[机制适用性与CLSTM-SB资源阶段](docs/GitHub_mechanism_applicability_CLSTM_stage_20261117.md)：已准入配置说明切口数量不足以预测domain增量，预算及实际失败/阻塞条件需分别考虑。CLSTM-SB native资源阶段4组接受、3组合法策略拒绝，234918wire/941SB/0CB、CPD不变；后续时序修复及完整配对仍待原队列终结，不将阶段结果计入正文收益。投稿08保持。

[CLSTM-small SB-only固定确认已启动](docs/GitHub_CLSTM_SB_confirmation_20261117.md)：同已知CLSTM网表，实际SB-only图/2927块坐标不同于历史Hybrid-O，不计新电路或新架构家族。五项字节预检通过；N→D及终结后3项必要只读保持CP1r5规则。native新鲜初始根通过FULL/STA/物理检查：6.590324286ns、234982wire/948SB/0CB，已进入资源修复，尚无新配对质量。投稿08保持；完整ETA待首个native真实终态校准。

[TPU-OS完整配对通过与六页投稿08](docs/GitHub_TPU_OS_admission_submission08_20261117.md)：N/D同7.812205993ns、17SB/1563CB和完整端点向量，线长360117/360121；domain无增量。两臂各4次资源接受，无失败释放/owner事件。完整941.32/944.17秒，仅单次描述；原核验01失败保留，02精确时序worker格式核验及完整配对通过，无native/STA重跑。[投稿08 PDF](research/dac_v14_20261112/submission_narrative_08/build/main.pdf)，原07保留。下面“TPU-OS缺口未闭合”是早期历史状态。

[当前交付：LSTM整臂通过、六页投稿07、TPU-OS附加准入具体缺口](docs/GitHub_LSTM_delivery_TPU_terminal_20261117.md)：LSTM实际配对通过，失败候选未提交；投稿07可独立作者审阅，四档代价对照已完成。TPU-OS原两臂和三项附加只读均已终结，raw因实际时序manifest缺少seed-order字段未通过，质量留空，尚无正式配对。原执行/核验费用照录，旧ETA作废。下方TPU-OS预检/运行描述为历史记录。

[已准入LSTM完整机制归因与TPU-OS输入预检](docs/GitHub_LSTM_mechanisms_TPU_OS_preflight_20261117.md)：guided接受11步为−82SB/+2348wire，native回退5步为−5SB/−152wire，终结选点再−12wire；10个接受guided作用域有释放事件，但没有LSTM同源no-release反事实，不能作因果必要性主张。全候选保留原失败/策略拒绝与预算边界。[完整工作点图](research/dac_v14_20261112/LSTM_admitted_mechanism_synthesis_01/complete_wire_SB_points.pdf)。TPU-OS实际五项字节和4100block坐标预检通过，2.261795秒，无native/STA；尚未启动完整配对，不计新架构或收益。投稿07保持。

[LSTM整臂与实际配对通过、六页投稿07](docs/GitHub_LSTM_admission_submission_20261117.md)：同14.600438192ns，N/D为2388083/492/8316与2390270/422/8316；少70SB、增加2187wire、CB不变，配对setup51改善/23退化、hold新增0。原ctime失败、native回退拒绝和后续轨迹保留；完整7615.07/26657.73秒照录，domain受外部归档干扰，不推算无干扰时间或正式开销比。[PDF](research/dac_v14_20261112/submission_narrative_07/build/main.pdf) · [完整配对表](research/dac_v14_20261112/submission_narrative_07/LSTM_PAIR_TABLE.md) · [作者审阅/证据影响](research/dac_v14_20261112/submission_narrative_07/EXPERIMENT_IMPACT.md)。四档代价对照已经完成并突出为同组CB预算可行性增量，非所有权重/输入优势；CLSTM历史恢复不阻塞主稿。原06和更早版本保留。

以下为历史快照；当前LSTM准入及稿件以上述交付为准。

[六页投稿06、LSTM必要准入与GEMM真实终态](docs/GitHub_GEMM_LSTM_submission_20261117.md)：[投稿PDF](research/dac_v14_20261112/submission_narrative_06/build/main.pdf) · [剩余证据影响](research/dac_v14_20261112/submission_narrative_06/EXPERIMENT_IMPACT.md)。LSTM/native补充完整准入通过，domain仅原失败候选来源通过，尚无完整配对收益；两个419候选分别保留超402的原策略拒绝与超357的原ctime失败。GEMM两臂完整2940.97/2925.41秒后原初始超时，质量为空。CLSTM02来源闭合失败保持，03补齐实际manifest审计后已封存旧23请求真实复用及新候选FULL/STA；历史恢复终态另记，不阻塞六页稿。

[GEMM native原预算超时与CLSTM已登记接续](docs/GitHub_GEMM_native_timeout_20261117.md)：native完整尝试2940.97秒，未获通过FULL/STA的合法根；domain已进入原初始路由。中间零过用打印不计合法候选，不重跑或放宽预算。CLSTM接续02的11项元数据检查通过，实际等待GEMM终结后先复核来源字节，复用既有23条native请求，缺失阶段新执行计费。当前没有新增完整收益；六页投稿05和BNN完整取舍保持。

[CP1r4实际slack修复与GEMM匹配确认启动](docs/GitHub_CP1r4_GEMM_20261117.md)：实际"+inf"故障及双臂完整规划器回放通过，5连接仅为提案；独立冻结和source+固定wheel重建/迁移准入完成。GEMM约13.22GiB字节/实际布局预检及56.26秒输入复制复核通过，native已真实启动、domain随后；不同已知历史电路、同架构族，暂无完整配对收益。CP1r3原失败与六页投稿05保持，软件诊断费用和准备费用均单列。


[四档代价对照独立准入与六页投稿05](docs/GitHub_confirmed_cost_submission_20261117.md)：0/0.5/1/2全部路由合法、完整同组核验通过，但均因CB654>653策略拒绝；1/2另有37项setup退化。测试权重减少SB，却未复现release分支的CB预算内工作点，不外推普遍优势。原四档尝试353.24秒、后续只读核验80.74秒分列，未重跑native/STA。[最新PDF](research/dac_v14_20261112/submission_narrative_05/build/main.pdf) · [剩余证据影响](research/dac_v14_20261112/submission_narrative_05/EXPERIMENT_IMPACT.md)。

reduction原N/D开发接续均终结：同CPD、72SB/3058CB，线长1241199/1241281；各自后缀5161.46/10116.16秒和旧失败费用单列，不以不同前缀的后缀比冒充完整费用。CLSTM既有23连接来源阶段独立审计通过，候选物理/域/STA及完整接续尚未完成；原空回执与失败保留。CP1r3仍无新增完整准入配对，Goal继续。[实际状态](research/dac_v14_20261112/CURRENT_STATUS.md)。

以下为历史发布快照，角色是否终结及当前稿件以上述入口和实际回执为准。

[reduction/native开发恢复完整终结；原domain接续](docs/GitHub_reduction_native_recovered_20261117.md)：12.606378ns、1241199wire/72SB/3058CB，setup1746改善/286退化、hold退化0；恢复后缀5161.46秒与原失败6147.85秒单列。旧269连接原生阶段实际复用、原running manifest不改。不是新鲜完整费用、冻结确认或配对域收益；正文主张保持。

[CLSTM/native与robot-p1历史恢复终态、必要只读核验](docs/GitHub_legacy_recovery_readonly_queue_20261117.md)：后缀费用分别206.33/705.29秒，原失败费用单列，不拼接完整时间或配对收益。CLSTM/domain原空监督回执及失败保留；21项元数据检查通过，完整独立阶段核验已排在三档代价基线只读协调之后。原reduction恢复继续，投稿04稿和主张不变。

[四档跨层代价基线实际执行终结](docs/GitHub_vertical_cost_terminal_20261117.md)：完整尝试353.24秒，0档等价通过；0.5/1/2原独立准入被可变进度摘要拦住，真实候选与原拒绝保留。只读协调已登记并等待原串行槽，不重跑native/STA；正强度结果尚不进入论文主张。

[CP1r3六角色及原准入终结；六页投稿叙事04](docs/GitHub_CP1r3_terminal_submission_20261117.md)：完整质量0/6、配对0/3，所有真实费用及失败保留；新稿仅更新失败覆盖和适用范围，BNN、方法与prior-art不变。原跨层代价0/0.5/1/2队列已进入实际构建，未修改规则。[投稿PDF](research/dac_v14_20261112/submission_narrative_04/build/main.pdf) · [剩余证据影响清单](research/dac_v14_20261112/submission_narrative_04/EXPERIMENT_IMPACT.md)。

以下角色进度入口为历史快照；最新真实状态以上述记录与CURRENT_STATUS为准。

[DLA-small N/D初始路由失败；接续eltwise-SB](docs/GitHub_DLA_initial_failure_20261117.md)：原完整费用709.74/702.41秒，两臂均未获得合法起点，失败路由时序不计QoR；原预算和日志保留。eltwise-SB属于既有电路/架构的新布局；剩余核验及基线队列不变。

[LSTM完整执行与原验证失败；CP1r3接续DLA-small](docs/GitHub_LSTM_complete_execution_20261117.md)：N/D完整命令分别7615.07/26657.73秒，原独立验证均失败，正式配对比例不发布。保存原失败、具体断言定位、完整费用及下一角色状态；六页叙事03和既有收益边界不变。

以下较早进度入口为当时快照；最新角色状态、验证分类和ETA以本入口及CURRENT_STATUS为准。

[Priority05状态入口修正与实际8个owner](docs/GitHub_priority05_status_correction_20261117.md)：修复刷新脚本漏列已排队基线及四个后继owner的问题；实际进程、队列顺序和实验规则未改。最近15步接受前缀及费用、端点变化和条件性ETA均保留，完整LSTM配对仍未准入。

[六页投稿稿的接受条件与覆盖计数澄清](docs/GitHub_submission_clarifications_20261117.md)：另存叙事03版，明确端点域匹配与hold保护，消除搜索失败的可行性预设及覆盖计数歧义；摘要、数值主表、引用、贡献边界不变。原叙事02及投稿候选保留，未加入未完成确认收益。

[LSTM归档干扰更正](docs/GitHub_LSTM_retention_incident_20261117.md)：助手的硬链接归档改变活动下游源文件ctime，造成一次最终封存失败。135项登记摘要与原最终重哈希一致；失败5项仅ctime变化。原失败、费用、预算及回退轨迹保留，不补造成功或重跑查询，运行期停止此类硬链接操作。LSTM完整配对尚未准入。

[依赖感知重构：独立六页叙事稿](research/dac_v14_20261112/submission_narrative_02/build/main.pdf) · [机制图、证据与贡献边界](docs/GitHub_dependency_narrative_20261117.md) · [剩余实验影响清单](research/dac_v14_20261112/submission_narrative_02/EXPERIMENT_IMPACT.md) · [原生回退与最新条件性ETA](research/dac_v14_20261112/LSTM_closing_menu_ETA_01/ETA.md)。新稿按问题—洞察—设计—验证组织；原候选稿和paper19保留。CP1r3原批次继续，[简单跨层搜索代价对照](docs/GitHub_vertical_cost_queue_20261117.md)已按0/0.5/1/2四档实际排在原确认与raw准入之后、历史恢复之前；32项小型检查通过，实际构建与零强度等价尚待执行，不作为论文收益。

[闭菜单阶段费用与后续输入范围](docs/GitHub_closing_menu_inputs_20261117.md)是历史快照：后续第13次接受已重新打开菜单，旧2.9–9.7小时情景不再适用。GEMM-p0来源元数据一致、约13.22GiB，待后续物理准入；TPU-OS和DLA-medium仍按数据流/规模变体记述。

[投稿源包独立重建通过](docs/GitHub_submission_source_export_20261117.md)：三项稿件输入在独立目录生成六页PDF，文本和全部渲染像素与原稿一致；提供108KB最小源包及原PDF，仍需外部TeX工具链。

[已有LSTM合法候选与0.1%边界](docs/GitHub_LSTM_existing_tradeoffs_20261117.md)：419 SB候选自身CPD14.600438191791909ns、线长2390877/CB8316，setup4改善/1退化；路由合法但超原预算402，拒绝保持。与同组native425 SB及共31条已有观察整理取舍图，不重跑查询、不解释为更宽预算完整结果。

[独立六页投稿候选稿](research/dac_v14_20261112/submission_candidate_01/build/main.pdf) · [剩余实验的具体影响](research/dac_v14_20261112/submission_candidate_01/EXPERIMENT_IMPACT.md) · [最新条件性ETA](research/dac_v14_20261112/LSTM_budget_cost_progress_01/ETA.md)。稿件基于paper19已核验证据独立收束，当前实验继续；补充验证已安排在CP1r3确认终结后的首位。

[LSTM已结束事务费用与排程更新](docs/GitHub_LSTM_cost_progress_20261117.md)：20个已结束事务的登记角色native内部计时占事务墙钟0.27%–3.84%，用于定位工程成本，不是完整配对加速或质量收益。CP1r3继续，新增原始证据准入已实际排队。

[最新实验、结论与运行队列总览](docs/GitHub_research_status_20261117.md)：已完成BNN匹配计时、CP1r2确认、局部机制消融与负结果；CP1r3 LSTM/domain正在运行，native原验证失败及真实费用保留，后续审计与接续依次排队。

Research remains active; public evidence base `9734eee`, subsequent `279bdb4` and local development are preserved. [Current status](research/dac_v14_20261112/CURRENT_STATUS.md) · [Closed confirmation, mechanism attribution and running work](docs/GitHub_cohort_mechanism_20261116.md) · [Current six-page paper](research/dac_v14_20261112/paper_snapshots/current_balanced_cost_20261116/build/current_repair_main.pdf) · [Paper evidence binding](research/dac_v14_20261112/balanced_cost_paper_binding_19.json).

[Prior ingredients and contribution scope](docs/GitHub_sharing_prior_art_20261116.md): paper18's literature statement and supplementary attribution map distinguish established sharing/timing-repair primitives from the actual local domain, release and coordination controls. Its source/PDF is preserved; the same prior-art and contribution boundaries and9references continue in paper19.

[CP1r3 native verification failure and independent diagnosis](docs/GitHub_CP1r3_native_failure_20261117.md): LSTM/native completed its actual measured command in7615.074177s, but the frozen whole verifier failed after74.441375s at the preparation-versus-execution owner-registration seal. Its original status remains `execution_or_verification_failed`, quality=null. A separate readonly metadata audit proves exactly two documented pre-execution runtime bindings for all three owners and matches the actual execution seals. This does not complete the remaining full verification or admit a benefit. A separately registered supplemental verifier retains all88original assertions; its original owner is queued immediately after CP1r3. A second read-only admission owner follows it, before historical recovery, and checks actual bytes, complete requests, raw STA, physical proof and paired roots/endpoints. The additional implementation passes46checks; neither supplementary full replay nor raw admission has executed yet. LSTM/domain continues under its original owner and frozen rules.

[Matched costs integrated into paper19](docs/GitHub_balanced_cost_paper_20261116.md): six pages now report the verified BNN balanced mean overhead+24.91% separately from historical22.95%. Two summary rows represent four complete repeats; three earlier engineering rows are retained in the supplement. The main table has42display rows, including all previous failure categories. No new independent input, CP1r3 complete outcome or broader benefit claim is introduced.

[Actual command seed correction](docs/GitHub_input_seed_provenance_20261116.md): CP1r2 conv_hls/TPU use router seed21; Robot's upstream s23 placement uses router seed11. Eight original command manifests are bound in the supplement. All43quantitative rows and existing claim limits remain unchanged; this is no new independent input or benefit result.

[BNN N/D/D/N complete matching and costs](docs/GitHub_BNN_timing03_balanced_20261116.md): all four whole-flow verifiers and trajectory/request/native-work/actual-graph-byte/fresh-root/full-endpoint matching passed. Complete times are7329.044554/9146.351492/9112.139276/7288.184845s. The two D/N ratios are1.24795960/1.25026182; ratio of arm means is1.24910749 (+24.91%). This reproduces the known BNN resource–timing tradeoff with zero new independent inputs; shared-host/cache and memory-sampling limits remain. Historical22.95% overhead and paper18's contribution boundaries are preserved. The original queue has advanced to CP1r3 preparation/confirmation.

[Next fixed-version confirmation protocol](docs/GitHub_CP1r3_distinct_protocol_20261116.md): LSTM and DLA-like.small plus an eltwise SB-only control keep their original fixed protocol. [Priority02 execution handoff](docs/GitHub_confirmation_priority_20261116.md) places CP1r3 preparation/confirmation after the now-complete BNN N/D/D/N batch, before four-arm readonly admission and development recovery; empty-query replay is last. Six unexecuted waiting owners were explicitly cancelled/replaced without changing inputs or fixed method rules. Actual SB placement differs from the older table in1882of1883blocks, with the same declared graph/packing. The eltwise SB input uses an already known circuit and already known architecture family with a different placement. Three inputs/sixroles are not six samples, three new circuits or a new architecture sample. Precision-only CP1r3 packaging, activation and public reconstruction have completed. The original LSTM/native command ended with the independent verification failure above; LSTM/domain is running. No complete verified pair is available. Remaining roles retain their original order and admission gates.

[Remaining interrupted-stage reconciliation](docs/GitHub_interrupted_stages_20261116.md): four CLSTM/reduction arms now have a source-bound stage inventory and a registered readonly audit behind the existing confirmation cohort. Completed native requests and audits are retained. [Four full-flow recovery adapters](docs/GitHub_interrupted_flow_dispatch_20261116.md) are now implemented and registered after that audit: preserve the CLSTM/native closed stages/original timing portfolio, and continue the other three resource prefixes. Five tiny integration checks/20negative guards and four-arm actual metadata/31negative guards pass. Actual serial byte/STA proof and per-arm admission remain required before recovery; no new recovered outcome, native replay or independent result.

[Objective-specific mechanism evidence](docs/GitHub_mechanism_selection_20261116.md):10existing complete configurations cover9declared physical identities, with no new experiment. Identical48SB-only initial cuts lead to different trades under1.00/1.02CPD caps. Complete resource release coverage is BNN9guided roles/0events and robot3roles/5events. Resource-owner scope and positive-conflicting-witness timing-owner triggers are separated; the pure triage prototype is uninstalled and predicts no gain.

The unified method uses current STA and crossing redundancy to choose complete connection groups, applies retained-crossing domains, releases a failed network's restriction and coordinates capacity-blocking owners. Complete physical/capacity/FULL/STA checks precede acceptance under fixed root envelopes; terminal selection and current-STA timing repair are separate. Intermediate modules need not each improve CPD; native receives matching selection, owner and convergence opportunities.

[CP1r2 is independently packaged and fixed](research/dac_v14_20261112/confirmation_release_cp1r2_01/completion.json). Algorithms/rules remain those of CP1; runtime corrections tolerate vanished Linux process records and preserve/check the guard's executable permission. Real process and guard tests pass, including the guard after [public source/wheel reconstruction](research/dac_v14_20261112/confirmation_release_cp1r2_01/public_source_reconstruction.json). Original CP1/dev03/CP1r1 and all failed receipts remain unchanged. No old development result becomes confirmation.

Five development arms reached legal initial routes but were interrupted by a supervisor process-read race. Corrected CLSTM N/D and robot-p1 N therefore establish input compatibility through initial routing, not complete algorithm benefit. Four later CP1r1 attempts failed before VPR because packaging removed the guard's executable bit. Both categories retain actual costs and no complete quality. Paper18 retained43display rows; current paper19 has42display rows with two balanced-cost summary rows and three older engineering rows moved intact to the supplement. Individual failure and recovery evidence remains supplementary.

| Original complete BNN configuration | CPD (ns) | Wire | SB | CB | Complete time (s) |
|---|---:|---:|---:|---:|---:|
| Native | 13.228145690 | 2059631 | 82 | 5062 | 7933.25 |
| Domain-first | 13.228145690 | 2061417 | 43 | 5060 | 9754.31 |

Domain-first spends1786wire and22.95% more complete time for39fewerSB/twofewerCB. SB falls47.56%; SB+CB falls0.797%. Final-arm setup changes are534 improvements/803 regressions with no increased hold violation. These are occupancy savings, not measured area or power savings. Symmetric engineering preserves domain behavior at9116.40s versus9754.31s (single-observation−6.54%); matched N/D/D/N timing is now complete at+24.91% mean overhead, separately qualified above. [Complete paired evidence](research/dac_v14_20261112/complete_resource_timing_full_flow_01/comparison.json) · [Engineering comparison](research/dac_v14_20261112/complete_BNN_domain_engineering_01/comparison.json).

[Verified robot union ablation](research/dac_v14_20261112/robot_union_mechanism_02/verification_v2.json) holds25connections/five nets fixed: native251140/9/654 is legal but exceeds the CB cap; domain/no-release rolls back; domain/release251160/9/653 is resource-accepted at unchanged13.354624073ns, with240setup improvements/32regressions. No actor commit; shared imported cost194.52s is not a whole-method or per-arm cost. Earlier equal native/domain owner outcomes remain coordination-scope attribution. [Four automatic owner reentries](research/dac_v14_20261112/robot_owner_reentry_audit_02/completion.json) on partial robot-p1/native trade68wire for4CB at fixed CPD; existing reload STA matches exactly. These are scoped development evidence.

[First complete CP1r2 pair](research/dac_v14_20261112/cp1r2_cross_circuit_cohort_01/conv_hls_comparison.json): conv_hls N/D have identical fresh roots/full vectors and retain14.351002164ns,84291wire/0SB/37CB, all4491setup/hold components unchanged. Complete times505.17/500.90s are single observations.18critical connections have zero physical gain in capacity-fixed and relaxed queries; seven relaxed witnesses conflict but offer no gain. This is one prospective fixed-menu no-op confirmation; positive integrated benefits remain pending. [Evidence and paper update](docs/GitHub_CP1r2_first_pair_20261116.md).

[Closed CP1r2 cohort](research/dac_v14_20261112/cp1r2_cross_circuit_cohort_01/terminal_evidence_01/completion.json): conv_hls confirms one legal fixed-menu no-op pair; TPU native/domain both hit their original1800-s initial execution limit, at1904.67/1906.23-s complete attempted cost. No legal TPU quality or domain comparison exists; timeout is not an infeasibility certificate. Two distinct known physical inputs are not four independent samples.

The original [balanced BNN timing03](research/dac_v14_20261112/BNN_interleaved_timing_03/plan.json) is complete and its formal matching passed; no BNN role is repeated. The original Priority02 owner runs CP1r3's three-input/six-role cohort unchanged. [Priority04](docs/GitHub_CP1r3_raw_admission_20261117.md) now schedules original-check supplemental replay, then remaining raw admission, before the four-arm readonly audit, robot-p1 prefix pilot and four full-flow recoveries; [empty-query validation](research/dac_v14_20261112/empty_query_patch_validation_01/plan.json) remains last. The original confirmation and supplemental owners are preserved; only unexecuted downstream waiters were explicitly superseded. Supplemental replay and raw admission are queued, not completed. Existing expensive native results must be reused only after complete admission. Timing01/02 never ran. All original costs and failures remain; no publication, matrix completion, fixed date or ordinary negative stops the active research Goal.

<details>
<summary>Historical progress snapshots and earlier paper versions</summary>

The following entries retain their original publication-time wording. Their running/pending labels are historical; use the current status link above for continuation.

## Current snapshot — 2026-11-15 (research active)

[Current six-page manuscript and native ablations](docs/GitHub_native_ablation_progress_20261116.md): the fixed BNN three-net composition passes native FULL/STA and independent physical checks; robot no-release fails with exact rollback. The unified table retains 22 complete-flow rows and adds two explicitly scoped component rows, without attaching old whole-flow costs. [Current PDF](research/dac_v14_20261112/paper_snapshots/current_native_ablation_20261116/build/current_repair_main.pdf) · [Evidence binding](research/dac_v14_20261112/native_ablation_paper_binding_06.json). Complete terminal-wire BNN is running; full frozen-controller confirmation remains pending. Its [qualified completion comparison](docs/GitHub_terminal_comparison_progress_20261116.md) is registered to preserve the old observer loss and compare GNU-time on matching scopes.

[Prospective fixed-dev03 robot p1 pair](docs/GitHub_robot_p1_registration_20261116.md): verified different actual packing and block-coordinate mapping from modern robot p0, with the same circuit and architecture. Two full-method arms share dev03 and owner opportunities, start fresh routing and are queued after existing work. No native execution or new independent outcome yet; known historical input, not an unseen holdout.

[Missing domain engineering arm registered](docs/GitHub_domain_engineering_registration_20261116.md): apply the completed native single-pass/cache/stream implementation to the original full domain configuration after existing cross-input work. No repeated native batch or changed algorithm rule; no new result or revised overhead claim yet.

Earlier [routing contribution comparison](docs/GitHub_routing_position_progress_20261116.md) added five primary references (nine total), credited prior incremental/current-timing routing and separated imported price resets from unvalidated CHANZ scope.

[Robot owner-scope continuation](docs/GitHub_robot_owner_scope_progress_20261116.md): 18 actual residual-capacity queries separate two target-only no-path cases from 16 owner-release local-path cases. A fixed same-root 3-connection/4-connection unrestricted native contrast is queued after existing work; owner reconnection, complete legality and timing remain unverified. [Current concise status](research/dac_v14_20261112/CURRENT_STATUS.md).

[Earlier mechanism/input continuation](docs/GitHub_mechanism_inputs_progress_20261115.md): robot's exact retained-domain/capacity proof separates per-net release from outside-owner coordination. Six historical input records were screened, including one initial routing failure; no new full-method outcome is claimed. A fixed dev03 clstm native/domain pair is queued after the portable whole-method check. [Earlier six-page paper](research/dac_v14_20261112/paper_snapshots/current_mechanism_inputs_20261115/build/current_repair_main.pdf) incorporates the mechanism evidence, retaining the 22 measured rows and explicit pending-ablation limits; [evidence binding](research/dac_v14_20261112/mechanism_inputs_paper_binding_04.json).

Earlier snapshot: [completed results, conclusions and running experiments](docs/GitHub_progress_20261115.md), the [publication-time verified process state](docs/github_progress_status_20261115.json), and the [C221 six-page manuscript](research/dac_v14_20261112/paper_snapshots/current_R1_native_closure_20261115/build/current_repair_main.pdf). All eight original native/domain control menus are closed. New evidence includes 32-SB owner coordination, mixed circuit transfer outcomes, complete BNN costs and the verified single-pass-index full-flow comparison. Later results are explicitly separated from the manuscript's frozen archive and from trials still in progress. This remains a research snapshot, not a complete offsite raw-data backup.

Continuation from public evidence base `9734eee`: [unified-method progress and publication scope](docs/GitHub_unified_progress_20261115.md), [captured process state](research/dac_v14_20261112/CURRENT_STATUS.md), [reorganized six-page manuscript](research/dac_v14_20261112/paper_snapshots/current_unified_archive_20261115/build/current_repair_main.pdf), and [source/evidence binding](research/dac_v14_20261112/unified_archive_paper_binding_03.json). The 22-row main table binds complete costs and full endpoint changes, including two initial-route failures. The integrated development entry and four new paired roles are registered; full outcomes and frozen-controller confirmation remain pending. The completed same-flow cache/stream native control preserves actual quality and work at approximately 7247 GNU-time seconds; observer loss and missing complete PSS remain explicit. The separately packaged native runtime component has passed relocation tests and is not the whole algorithm. Recovery scheduling preserves surviving processes and never-executed tasks.

Latest continuation: [portable selectors, completed grouping controls and live queue](docs/GitHub_portable_selection_progress_20261115.md). Actual outside-project R1 replay preserves all eight owner groups, one sharing scope and STA selection; a no-cut tiny input remains empty. Three completed grouping roles preserve requests, endpoint vectors and route bodies, with no query-count reduction. BNN domain and registered follow-up roles continue. The complete independently executable confirmation method remains pending.

[Archive integration and measurement coverage](docs/GitHub_archive_scope_progress_20261115.md): [671 actual observations](research/dac_v14_20261112/multiobjective_closed_stream_quality_01/verification.json) now include the completed stream flow. There are 34 quality-complete configurations: 33 with complete observer measurements and one with qualified original GNU-time only. No missing PSS/observer wall/CPU is reconstructed; the six-page main distinguishes these coverage counts. These are not independent samples.

[Portable transaction development entry](docs/GitHub_transaction_entry_progress_20261115.md): actual outside-project two-arm owner protocol reconstruction, installed-candidate vectors/physical audit, five-connection request preparation and runtime/command preflight pass. Altered actual gates and wrong complete trees are rejected. No new VPR execution or independent sample is claimed; full method freeze remains pending.

The 2026-11-09 section below is historical.

</details>

## Historical snapshot — 2026-11-09

This repository preserves the current research code, source patches, experiment
protocols, selected evidence and handoff documents. The registered experiment
queue is still running on the original shared-storage environment; this is **not
a final experimental release or a complete raw-data backup**.

Read the [GitHub snapshot guide](docs/GitHub快照说明_2026-11-09.md) and
[current account handoff](docs/账号切换交接_2026-11-07.md) first. Current source
changes, including previously ignored vendor modifications, are preserved in
[verified source patches](patches/snapshot_20261109/manifest.json). The strict
study's [preliminary report](results/architecture_flow_20261027/serial_strict_reexecution_20261103/report.html)
predates the remaining fixed-placement width diagnosis and final acceptance audit.
Results are conditional: they do not establish general routing acceleration or
an architecture ranking reversal. Historical results below describe earlier
experiment matrices, not completion of the current strict study.

## Earlier experiments and project background

Research implementation of timing-driven vertical-channel selection and routing-tree reoptimization on a fixed FPGA routing resource graph (RRG).

For continuing this work in a new conversation, read the [2026-10-25 handoff](docs/交接说明_2026-10-25.md), including the distinction between paper-era LaZagna, its later VTR-9 code migration, and the native A0 baseline.

The [VTR-9-port build and controlled pilot](docs/LaZagna后续分支验证_2026-10-25.md) completed an explicitly patched VPR build, small-graph checks, and nine audited routes. The subsequent [three-baseline comparison](docs/三基线对比_2026-10-27.md) now adds full-size modern VPR PnR and paired native A0/A3 routing: 31 attempts, 30 routes passing FULL and independent audits, and one capacity failure causing two dependent skips. Under the disclosed ideal-clock diagnostic, all ten A3/A0 pairs have identical reported CPD. Both native arms have 0.277% lower geometric-mean CPD than modern LaZagna; that cross-tool difference is not an A3 benefit. Paper-reported results remain a separate reference without a comparable A3 ratio.

Start with [the Chinese research report](docs/研究结论.md) and the
[generated experiment results](docs/实验结果.md). The completed matrix contains 769 route runs: 637 native successful, independently
audited solutions and 132 retained failures. All 90 sequential timing runs pass.
A3 has conditional timing benefits; A4 has no stable overall advantage in this study.

A separate [LaZagna reproduction and graph correspondence report](results/lazagna_reproduction/report.html)
pins the paper-era LaZagna/OpenFPGA/VTR sources, retains strict published-configuration
attempts, and checks DSP exits, planar edges and physical vertical resources.
Its status is recorded separately from the original 769-run matrix.

The baseline is a pinned upstream VTR version with native CHANZ support. Algorithms must retain directed connectivity, per-net resource occupancy, the original timing model, and the same placement/architecture during router comparisons. This is software CAD research; VPR timing results are model-based, not silicon measurements.

See [the implementation and validation plan](docs/implementation_plan.md) for the full task, evidence requirements, and progress. Source modifications will be kept as reviewable patches against the pinned VTR checkout. Downloaded dependencies, builds, and raw runs are kept outside the tracked source files.

The finite model and its limits are described in [planner_model.md](docs/planner_model.md).
Two literature-inspired controls, their explicit formulas, and differences from
the original papers are documented in [literature_controls.md](docs/literature_controls.md).
The imported FLUTE code retains its [BSD-3 license](LICENSES/FLUTE-BSD3.txt).
Build, paired-run and audit commands are in [reproduction.md](docs/reproduction.md).

## Tool choice

AMD Ross Skills and Vivado MCP are considered according to the user's FPGA tool policy. The current implementation phase uses C++/Python and VPR; it does not require a Vivado project or HLS synthesis. If fabric RTL/bitstream validation becomes necessary, inspect the applicable Ross skill and use existing Vivado MCP sessions preferentially. Local Vivado is 2022.2; newer commands require compatibility checks.


最新接续：[失败释放迁移与实际事务执行检查](docs/GitHub_release_execution_progress_20261115.md)。

最新组件：[完整方法迁移、实际反馈验证与整流程执行登记](docs/GitHub_unified_method_progress_20261115.md)。
