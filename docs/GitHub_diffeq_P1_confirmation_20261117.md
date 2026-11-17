# diffeq P1 新输入与冻结确认

固定公开 VTR `diffeq` 不同电路，377个时钟寄存器；使用现有两层 Hybrid-O 架构族、n25、实际 P1 分区打包与布局。P1 的267个放置块按层0/1为134/133；明确20 ns时钟和输入/输出max1/min0是基准SDC，不是外部应用要求。此预登记不使用路由质量挑选布局，也不将新布局称为新架构。

完整保留三次前置判定：

1. 最初 P1 对现代 `create_clock [get_ports ...]` 语法报错，命令0.267秒，无布局和路由；原成功census pack为0.889秒。
2. 独立后续P1采用旧解析器支持的 `create_clock ... pclk`，其余四条I/O命令和数值不变。实际P1及TritonPart成功，耗时7.079秒；但P1打包164 CLB而普查为168 CLB，不满足原有逐字节聚类语义相同的检查，该次原准备判定仍为失败。
3. 新物理输入单独登记：1974个原子名称／类型多重集相同，P1实际packed/placement通过原生VPR加载及布局一致性检查。原生探针无路由文件，按预期退出1；两次不同常量合并设置的只读探针分别耗时1.821/1.786秒，均不是FULL/STA或合法路由。后续匹配确认使用与P1来源一致的默认合并设置及原规范SDC。

原冻结入口无法解析P1实际命令中的无参数 `--partition_post_pack`，所以首次确认预检拒绝，原始失败保存且未执行任何臂。独立 `current_sta_cp1r6_p1flags` 包仅将该实际无参数开关加入来源命令解析列表；合同、路由代码、预算、接受和终结规则的其他1297项绑定均逐字节不变，旧入口行为、重复选项及缺值拒绝均保留。独立重建副本也应用同一精确改动并核验；不将它称为新的完整源重建。

以该固定解析版本登记一组 native/domain 和原有 native/domain/pair 只读检查；native已启动，domain及后继核验等待。初始路由仍可能失败、无切口、无收益或退化，所有情况保留；未通过实际完整请求、字节、FULL、STA、端点及物理配对前不进入论文收益。[输入准备](../research/dac_v14_20261112/VTR_diffeq_p1_input_03/completion.json) · [解析版本验证](../research/dac_v14_20261112/confirmation_release_cp1r6_p1flags_01/completion.json) · [配对计划](../research/dac_v14_20261112/cp1r6_diffeq_p1fix_pair_01/plan.json) · [投稿16](../research/dac_v14_20261112/submission_narrative_16/build/main.pdf)。

条件性参考：上一个不同电路 s38417 的两臂各约535秒；diffeq的P1打包、实际布线和工作量不同，不能把该参考视为期限或预计结果。研究Goal继续，投稿16不依赖新批次。
