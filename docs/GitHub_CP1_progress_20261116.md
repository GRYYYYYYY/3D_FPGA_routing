# CP1 固定确认版本、owner 取舍与六页正文09

研究保持 active，以 `9734eee` 为公开证据基点；本次增量接续 `171af5a`，保留本地 HEAD、索引、未发布更新和所有原实验规则。没有重跑已完成批次，也没有新增原生实验。

## 统一方法及冻结边界

当前 STA 与树结构选择事务组 → 跨层保留共享域 → 单网络搜索失败释放 → 根据容量阻塞及当前余量提出 owner 协调 → 对完整合法事务执行固定根预算接受 → 重观测与独立终结选点 → 当前 STA 时序修复。中间模块不要求各自改善 CPD；完整候选才接受或回滚。

[CP1 封存回执](../research/dac_v14_20261112/confirmation_release_cp1_01/completion.json)将上述关系、触发规则、候选顺序、接受与终结规则、依赖及阶段二进制摘要固定下来。116个运行时源文件与已在项目外执行的 dev03 核心逐字节一致，整体绑定1289个文件。新入口绑定 packing 来源和常量网解释，拒绝省略历史 `merge_constant_generators off`、改变阈值/终结规则/owner机会或不匹配的两臂收敛设置。

[23项检查](../research/dac_v14_20261112/confirmation_release_cp1_01/validation.json)和[整包解压移位验证](../research/dac_v14_20261112/confirmation_release_cp1_01/archive_relocation.json)通过，包含实际项目外 CLI、捆绑扩展库导入与1289文件完整性验证。新运行边界以显式 exec 截获检查，未冒充新原生运行。先前项目外 native 观测、R1 owner 事务及 tiny 整方法已实际通过；tiny 无正向提交，不能证明正向整合路径。

[公开源码包](../research/dac_v14_20261112/confirmation_release_cp1_01/current_sta_cp1_source.tar.gz)及[使用说明](../research/dac_v14_20261112/confirmation_release_cp1_01/README.md)供审查。公开源码包不含 NumPy/lxml/shared libraries；不能直接当作完整运行包。完整本地包25,180,971字节，含已绑定依赖且移位准入通过。两个包均在[归档记录](../research/dac_v14_20261112/confirmation_release_cp1_01/archives.json)记录摘要；原生二进制、查询程序和物理输入为显式外部依赖。运行环境为 CPython3.10/Linux x86_64，NumPy2.2.6/lxml6.1.3，非纯标准库。

冻结的是未来确认所用的源码和规则。尚无 CP1 独立确认结果，正向自动 owner 提交后重选及正向完整 timing feedback 仍待验证。原开发批次继续原版本，不追认为确认。后续变化须新版本、新登记输入队列。

## 新证据及归因

本次新增的是可移位固定版本和证据整合，独立物理输入结果新增0。既有不同实际 robot 布局与显式 SDC 对照无收益；attention 两臂初始路由失败，仍保留。相同树不同 seed 不增独立起点。

[robot owner 对照](../research/dac_v14_20261112/robot_owner_scope_pair_01/verification.json)两臂均 unrestricted、关闭 failure release，故只归因协调范围。owner-minus-target 为 CPD 不变、wire+12、SB+0、CB+1，setup31改善/0退化、无新增hold违例。端点接受允许该候选，固定资源规则拒绝两候选；原 actor 没有提交。155.10秒是共享导入配对总费，不是任一候选单独费用或完整冷启动费用。R1 native/domain owner 同结果仍归于协调范围，不能声称额外域收益。

robot no-release 同23连接请求在首连接九次尝试后失败并精确回滚，支持失败释放的操作作用；不能推出全局无路由。BNN固定三网组合通过 FULL/STA，34个延迟预测精确匹配；完整终结选点配置节省24wire，但属于同输入取舍，不是普遍算法收益。

CLSTM及robot p1原四臂均在 packed-netlist 加载时报未知 `$undef`，未进入初始路由。完整失败费用分别107.00/106.48秒、102.93/102.90秒。原回执保留，不能算拥塞失败。修正输入契约后的新登记配对仍等待原串行队列，不能提前宣称 native 修复成功。

## 完整代价及执行状态

原完整BNN N/D仍为7933.25/9754.31秒，约+22.95%；CPD同13.228145690ns，wire2059631/2061417，SB82/43，CB5062/5060。SB减少47.56%，SB+CB减少约0.797%，分母分别报告。资源节省是固定器件占用改善，不推断面积、功耗或跨输入可布通性。

完整原生 terminal-wire 为7351.26秒、2059607wire/82SB/5062CB。匹配GNU-time7351/7247秒，增加104秒；旧观察者/PSS缺口和短暂共享主机重叠保留，不称加速。domain 工程臂尚未闭合，不能更新22.95%开销；稳定同环境交错计时待后续执行。

2026-11-16 04:40 UTC 实时核验：BNN domain 工程 owner2252200存活，随后 reduction1002060、修正clstm1628082、修正robot p1 1665631按原依赖等待；PID均与登记start ticks匹配。[当前状态](../research/dac_v14_20261112/CURRENT_STATUS.md)保存时点回执，不能把旧页面的“运行中”当永久实时状态。普通负结果用于调整方向，不触发研究 Goal 完成。

## 正文与主张

[六页正文09](../research/dac_v14_20261112/paper_snapshots/current_owner_contract_20261116/build/current_repair_main.pdf)按问题—机制—完整结果—多目标取舍—消融—开销与适用范围组织。[证据绑定](../research/dac_v14_20261112/owner_contract_paper_binding_09.json)核验六页、31个完整尝试（4路由失败、4输入加载失败）和2个局部条目；33行不等于33独立样本。两幅图、九项相关工作、原22行及后续5行完整结果保留；逐页渲染检查无裁切/重叠，字号页边距不变。

主文支持具体完整成本、固定图垂直资源界、局部域/释放/owner机制及接受规则取舍。它不主张统一控制器普遍优越、统计加速、外部应用时序闭合或广泛架构泛化。历史局部轨迹、导入组合费用和恢复审计留在补充材料；所有原历史版本及回执继续保留。
