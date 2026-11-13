# DAC2027 注册信息与投稿判断

## 可用于注册的题目和摘要

**Reachability-Constrained Shared-Crossing Planning for 3D FPGA Routing**

Vertical connectivity complicates timing-driven FPGA routing because feasible crossings differ across sinks and architectures. We develop a reachability-constrained planner that compares shared and split crossing assignments on a finite terminal hierarchy, then softly guides VTR routing. Controlled experiments separate routing, placement, and toolchain effects across three architectures. On complete dual-baseline cohorts of two to four circuits, timing changes range from a 0.64% regression to a 1.32% improvement; larger individual gains coexist with regressions and failures. All ten valid serial timing groups incur overhead. Mechanism analysis exposes sparse delay coverage and motivates a controlled test of the planner's independent contribution.

摘要99词，依据当前严格结果；最终注册前由作者确认。它没有宣称加速、普遍时序优势或架构排名反转。

## 时间核对

[DAC2027官方研究稿件要求](https://dac.com/2027/program/research-manuscript-submissions)于本轮核验：摘要截止为2026-11-11 17:00 PST，即北京时间 **11月12日09:00**；稿件截止为2026-11-18 17:00 PST，即北京时间 **11月19日09:00**。用户内部节点早于官方截止，继续执行内部节点，不据此推迟。

| 北京时间内部节点 | 应交付物 | 当前情况 |
| --- | --- | --- |
| 11月10日 | 主张—证据表、摘要、完整初稿 | 本轮已形成源码、99词摘要、完整正文及PDF |
| 11月11日晚 | 注册题目、摘要、作者与投稿信息 | 题目摘要可供作者审阅；作者/COI信息待填写；未代提交 |
| 11月14日晚 | 完整稿、主要证据、明确投稿评估 | 先使用现有严格结果；宽度结果已接入；完成最终审计；不新增大规模调参 |
| 11月18日 | 最终核对版本 | 数值/引用/匿名/页数/清单最终检查，留出上传余量 |

## 提交信息清单

| 项目 | 当前内容或缺口 |
| --- | --- |
| Track | Research manuscript；建议主方向Electronic Design Automation，最终topic按投稿系统实际选项确认 |
| Keywords | Physical Design；FPGA Systems；Chiplets, Interconnects and 3D Integration（建议） |
| Title / Abstract | 上述版本与abstract.txt；后续数值变化需同步两处 |
| 全部作者与顺序 | 待作者提供，不能由仓库账号推断 |
| 单位、邮箱、通讯作者、ORCID等 | 待作者填写系统要求的字段 |
| COI | 待所有作者核对TPC相关冲突，并按官方要求填写 |
| 相关未发表/审稿中论文 | 待作者确认；可能相关稿件需按官方要求披露 |
| PDF | 本地编译初稿正文6页+仅参考文献1页；提交前再核字体、可读性与最终版本 |
| 匿名性 | 正文匿名；内部证据文档含绝对路径与仓库身份，不能直接作为匿名补充材料上传 |
| 工件可用性 | 已有公开仓库属于项目历史；匿名评审引用方式待作者选择，避免在稿内暴露账号 |
| 投稿系统账户与回执 | 未登录、未注册、未提交；交付文件不等于投稿成功 |

官方要求IEEE模板、双栏、9或10pt，正文最多6页，附加1页只能放参考文献，采用双盲评审。初稿采用10pt IEEEtran并将参考文献独立放到第7页；最终页数仍需随编辑重查。[官方要求](https://dac.com/2027/program/research-manuscript-submissions)

## 当前投稿评估

**可以推进注册材料；当前证据不足以支持“显著优于现有路由器”的强性能论文定位，按现状提交DAC研究轨道风险较高。** 主要问题是DP独立贡献未隔离，平均时序收益小且成功集合窄，正式计时没有加速，架构排序只有一个共同完整电路。宽度诊断能解释条件敏感性，但不保证补足算法新颖性或因果证据。

当前最可信的定位是“可达性约束的跨层共享规划方法及其受控评估”，用有利与不利证据共同说明方法边界。11月14日应明确判断：若有限消融能建立额外机制证据且不破坏冻结主结果，可增强贡献；若没有，保持局限并由作者决定是否以此窄定位投稿。不能把负结果改写为成功，也不能靠不断追加案例拖延收束。
