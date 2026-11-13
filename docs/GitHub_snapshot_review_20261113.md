# 2026-11-13 阶段快照（本地待确认公开范围）

当前仓库 GRYYYYYYY/3D_FPGA_routing 经实时 GitHub 元数据核对为 **public**。旧 2026-11-09 说明中的“默认私有”不能作为本次发布依据。此清单和本地提交不代表已推送或已授权公开当前未投稿稿；远端 main 在核对时仍为 b132a1d。

本批 outside DP 四个 quality/control 角色全部合法，首次合法和两次收敛均保持现有完整路由、6.20812ns CPD 与 SB/CB118/955。两类真实变化元数据的强制回滚也通过。新方法没有质量收益，不推广；研究目标仍持续，不受旧日期/总调用/固定矩阵或作者资料限制。当前论文更新到 C60。

保存代码、实验协议、状态/耗时/资源表、封存检查、所有小型分析结果、输入输出哈希、失败/缺失记录，以及原v13和独立开发稿。大型 RRG、route、实时/完整日志、二进制和外部依赖树不上传，原件保留共享盘；较大分析JSON在清单中列出路径/大小，若已有封存hash则一并列出。该Git快照是证据摘要及可还原主源码，不是所有原始数据的异地完整备份。

源码从 patches/snapshot_20261113_verified/architecture_outside_native.patch 独立应用于 VTR 0b912334fdd83bb754b302146ac0d1ec9edc9a0e，并核对43个变更文件和恢复Git树。不要叠加旧 architecture_r1.patch。原环境第三方目录没有自己的Git元数据，清单只证明2878个文件与原服务器/研究baseline一致，不冒充远端submodule commit内容认证；异机需取得匹配依赖并核对hash。

研究入口：research/dac_v14_20261112/RESEARCH_LOG.md、CONTINUATION.json、paper/claims_evidence.md。最新结果及分项时间：outside_quality_summary_01.json、outside_quality_timing_01.json、paper/data/outside_quality_v14.csv。原CSV/审计保留绝对来源路径，以免破坏封存身份；不能宣称任意目录开箱即跑。

规划和残余query计时是router阶段子项，不重复相加；非router部分含加载、初始化、输出/检查/退出。人工推理/完整审计/打包缺统一阶段timer，不编造整个科研周期耗时占比，也不将单次顺序开发时间当正式加速比。
