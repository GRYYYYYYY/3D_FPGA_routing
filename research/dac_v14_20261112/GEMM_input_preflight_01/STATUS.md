# GEMM-p0既定候选实际输入预检

五项原声明输入共14,191,639,818字节（约13.22GiB）已实际单次读取比对SHA256：架构、BLIF、RRG、packing、placement均匹配，源dev/inode/size/mtime/ctime前后不变。复用原坐标解析函数读到38567个block，x/y/subblock/layer范围[0,0,0,0]至[195,199,7,1]，语义坐标摘要见completion.json。

完整实测预检命令17.272951748秒，内部17.186164442秒嵌套；PSS46985KiB、内存缺测0，结束无私有后代。native/STA调用0，未导入历史路由，不把输入准备费用当完整算法时间。缓存和共享主机状态未受控，无冷盘声明。

这是与当前矩阵及CP1r3声明网表不同的GEMM电路，但属于已知历史训练来源、同两层edge-encoded Hybrid-O架构族；不是未见输入或新架构。这里只确认实际输入字节及真实坐标读取，尚未完成graph/packing/placement兼容性、合法新鲜路由起点或完整方法配对；不新增确认样本、收益或应用SDC要求。旧GEMM-p1缺少来源的负记录保留，不以换seed替代。

原确认、基线及必要审计已终结后才持有critical_scope_runner.lock执行此预检。下一步先核实隔离planner修复对实际失败token及完整规划器的适用性，固定后续匹配版本并继续GEMM完整物理输入/新鲜起点准入；不改CP1r3历史规则或结果。CLSTM已通过的23连接来源阶段可供另行登记的恢复消费，不能跳过缺失候选物理/domain/STA核验。
