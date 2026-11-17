# LSTM整臂准入与投稿交付；当前队列真实终态

LSTM/domain整臂：**通过**。native/domain实际完整配对：**通过**。
来源、实际状态连续性、最终FULL/原始STA/全端点/物理证据、实际初始树及六项图载荷配对均通过；本次仅复用已有终结回执并复核投稿绑定，没有重跑native或STA。

| 角色 | CPD(ns) | 线长 | SB | CB | 自身根setup改善/退化/hold新增 | 完整原命令(s) |
|---|---:|---:|---:|---:|---:|---:|
| native | 14.600438192 | 2388083 | 492 | 8316 | 20/5/0 | 7615.074177 |
| domain | 14.600438192 | 2390270 | 422 | 8316 | 71/27/0 | 26657.726866 |

D−N为线长+2187、SB−70、CB和CPD不变；完整终点配对setup改善51、退化23，hold新增0。不能将整臂差值全部归于域限制。domain完整费用包含外部归档ctime干扰；不推算无干扰时间，不计算正式完整时间比。BNN已匹配N/D/D/N的24.91%开销是另一项结果。

ctime失败分支round013/candidate00的控制器前后均指向round012/candidate02/reuse_off_evaluation，未提交失败候选。原FULL_STA_failed、合法原生回退的策略拒绝，以及后续round013/014/015的candidate02原生接受均保留；不追认历史completion。

原419SB/2390877wire候选超过原上限402，仍策略拒绝。ctime失败的另一419SB/2390832wire候选超357，自身CPD14.600438191791909ns、CB8316及端点4改善/1退化已独立核验；此记录不改变其原失败或未提交判定。

## 投稿交付

- [六页投稿07 PDF](../research/dac_v14_20261112/submission_narrative_07/build/main.pdf)，由06另存，原06保护不变。
- [完整LSTM配对表](../research/dac_v14_20261112/submission_narrative_07/LSTM_PAIR_TABLE.md)。
- [具体实验影响与作者审阅](../research/dac_v14_20261112/submission_narrative_07/EXPERIMENT_IMPACT.md)。
- [LSTM整臂判定](../research/dac_v14_20261112/LSTM_domain_whole_admission_03/admission_decision.json)。

摘要、表I、§IV-C、适用性及结论已经纳入LSTM。四档跨层代价对照已完成，并在摘要/机制表突出同源固定组上的CB预算可行性增量：0/0.5为251140/9/654，1/2为251125/9/654，均合法但违反CB≤653；共享域加失败释放为251160/9/653。不主张所有权重、所有输入或外部路由器优势。CLSTM历史恢复仍在补充材料，不阻塞作者审阅。

## 当前后继队列与条件性ETA

TPU-OS原native/domain完整命令和原检查均结束；完整命令为941.321435/944.174382秒。后续native/domain/pair三项只读登记也已终结，分别22.034798/21.227776/0.155744秒，等待原队列1231.207077秒单列。

**附加准入未通过，质量保持空，正式配对未准入。** 两臂raw核验均在实际时序事务manifest缺失VPR_JOINT_NATIVE_SEED_ORDER时抛出KeyError。执行结束、原检查通过和补充准入通过是三个不同状态；这不是已证实的路由失败、合法无收益或超时。尚需只针对实际执行命令、日志与冻结二进制默认值核对这一分支，再完成原有门槛。没有以缺省值猜测通过，也没有重跑昂贵查询。

原执行剩余0角色、原登记只读剩余0阶段；先前预测domain终结的ETA已被实际回执替代。缺口修复尚未验证，不能给出可靠剩余秒数。该后继只影响未来TPU-OS表格行和适用性；未进入投稿07，也不阻塞其审阅。

[TPU-OS完整费用与具体缺口](../research/dac_v14_20261112/TPU_OS_complete_admission_01/PAIR_TABLE.md)。Goal保持active，普通失败及Git推送均不构成研究结束。
