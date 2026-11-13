# DAC 持续开发（本地 v13 派生）

最新状态见 `CONTINUATION.json`、`live_handoff.json` 和 `paper/DEVELOPMENT_STATUS.md`；查询与层范围聚合分别见 `query_circuit_summary.json`、`scope_circuit_summary.json`。以下初期实验条目保留为历史入口，不能用其旧pending描述判断当前状态。

授权与持续研究规则见 RESEARCH_PROTOCOL.md；最新研究记录见 RESEARCH_LOG.md。旧补充包中的日期/route次数/固定矩阵终止条件不再适用。所有新研究为后注册；原代码和结果不覆盖。该目录不是冻结确认版本。

- `origin.json`、`baseline_source_sha256.json`：父源码身份及独立复制范围。
- `v13/`：原稿及审查快照；`paper/`：独立开发稿源文件。
- `src/`：实际开发源码及串行构建；`h1_source/`保留H1源码，`h1.patch`、`h2_dp.patch`绑定后续变更。
- `final_pairs/`：服务器最终A0/R1的252配对只读复算。
- `h1_dev_01/`：线程保护失败的首次尝试，四条均无有效CPD，不覆盖。
- `h1_dev_02/`：H1有效配对、默认关闭复现门、FULL/独立审计及完整输入封存；分析见analysis.md/json。
- `h2_dp_dev_01/`：独立H/N/G对照，状态以manifest及completion.json为准；目录存在不代表完成。

运行入口为 `.venv-lazagna/bin/python research/dac_v14_20261112/run_development.py --out <新目录名>`。默认spmv/softmax及F/H/N/G；所有新目录必须不存在。单线程、1800s、64GiB、80GiB磁盘保留；锁防止重复启动。先核对存活进程和最新manifest，不根据旧日志重复启动。正式计时尚未开始，开发秒数不用于正式加速结论。

H1已测：两电路均合法，spmv退化3.1632%，softmax持平；更多部分测距没有转化成CPD优势。继续独立引导/DP/geometry验证，动态反馈更新及针对候选的查询尚待实现。

`query_prototype/`：独立可恢复候选查询原型及2,000项距离核对；尚未接入VPR，不能作真实路由收益证据。
