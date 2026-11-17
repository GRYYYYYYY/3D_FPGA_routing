# CLSTM-small SB-only：实际不同起点与固定配对确认

现有TPU-OS完整配对已经通过，domain无资源—时序增量，六页投稿08保持。下一项确认检验：在SB-only跨层配置、没有跨层CB替代通路时，完整共享分支重构及共享域是否仍能给出预算内取舍。

选择已存在的CLSTM-small SB-only输入，不重复Hybrid-O历史恢复。原始打包及布局回执一致，五项实际输入字节通过（1,226,820,123字节）；2927个布局块的真实坐标与历史Hybrid-O起点不同。仍是同一个已知CLSTM-small网表，不计新电路、新架构家族或未见留出集。架构配置与布局同时不同，所以未来结果也不能单独归因架构变化。选择依据是物理配置覆盖，不以历史收益筛选。

[输入来源与字节预检](../research/dac_v14_20261112/CLSTM_SB_input_preflight_01/completion.json) · [实际坐标比较](../research/dac_v14_20261112/CLSTM_SB_input_preflight_01/actual_start_comparison.json)

采用原冻结CP1r5，native→domain，两臂保持图、布局、seed21、预算、搜索、接受及终结规则匹配，只有预定domain模式/失败释放处理不同。没有导入旧route，也未重跑已完成的Hybrid-O查询。原源码包重建直接复用。

完整预检2.179744秒、实际输入准备6.306023秒分列于算法时间之外。native实际图索引阶段已完成85.990046秒；新鲜初始根原FULL/STA/物理检查通过：6.590324286ns、234982wire/948SB/0CB，已进入资源修复。初始原生命令68.196597秒包含于后续完整命令。初始根不构成整臂或配对收益。[执行登记](../research/dac_v14_20261112/cp1r5_clstm_sb_pair_01/plan.json) · [实际观察](../research/dac_v14_20261112/cp1r5_clstm_sb_pair_01/initial_root_checkpoint_01.json)

已单独登记并启动等待中的3项必要只读：native、domain和pair；在原配对终结后最高优先执行。沿用已验证的科学门槛及精确timing-worker格式分支，不增加核验框架；无native/STA重跑，未通过原完整检查时保留空质量和具体原因。[后继准入登记](../research/dac_v14_20261112/CLSTM_SB_complete_admission_01/plan.json)

目前原完整角色尚有2项待终结，后继只读3项待执行。这个新SB-only输入的完整耗时未校准；首个native终态后，才用实际完整费用估算domain的条件性ETA。索引费不能拼成完整时间，正常单任务保护不是研究停止条件。无切口、合法无收益、预算拒绝、路由失败、超时和基础设施错误分别保留。

[六页投稿08](../research/dac_v14_20261112/submission_narrative_08/build/main.pdf)无需等待本批。新增确认只更新其支持的实验行及适用范围；Goal保持active。
