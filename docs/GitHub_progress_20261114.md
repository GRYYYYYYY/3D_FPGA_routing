# 2026-11-14 科研进展公开快照

采集开始（UTC）：2026-11-14T21:53:32.393858+00:00。用户明确要求上传当前进展；沿用已授权的公开完整研究快照范围。本次追加到 `research/dac-snapshot-20261113`，主实验目录和正在运行的任务不切换分支、不停止。

## 入口

- [335条合法观察及强基线联合档案](../research/dac_v14_20261112/multiobjective_complete_resource_timing_01/points.csv)
- [精度完整的档案JSON](../research/dac_v14_20261112/multiobjective_complete_resource_timing_01/points.json)
- [现有6页正文PDF](../research/dac_v14_20261112/paper_snapshots/current_strict_terminal_vector_feedback_20261114/build/current_repair_main.pdf)
- [64页详细证据稿PDF](../research/dac_v14_20261112/paper_snapshots/current_uniform_fused_repair_20261114/build/main.pdf)
- [新增证据与正文集成状态](../research/dac_v14_20261112/paper/DEVELOPMENT_STATUS.md)
- [发布时实验状态](github_progress_status_20261114.json)；[continuation](../research/dac_v14_20261112/CONTINUATION.json)
- [三套可独立还原的源码补丁与校验](../patches/snapshot_20261114_verified/manifest.json)

## 本次证据

同为13.228145689936355ns的实际合法状态：原生对照2059627wire/82SB/5062CB，成对资源引导分支2061389wire/43SB/5060CB；多1762wire换取39SB/2CB减少。两者来自各自完整自动资源阶段后的current-STA修复，不能与旧45SB前缀拼接。相同CPD不代表逐端点支配（成对分支相对原生550setup改善、799退化）。完整冷启动单配置路由加修复时间仍未知，导入、核心、研究流程和中断恢复时间分列。

最新五连接反馈组合已产生合法结果：CPD 13.599797732410934 ns，2061253 wire / 45 SB / 5060 CB；严格与全向量规则均接受，setup 10 改善、0 退化。该独立45SB输入结果尚未加入335条联合档案，也尚未写入C183v2正文；完整原始回执随本快照保留。

正文仍为已封存C183v2，新增335条档案证据在独立delta中，未冒称已更新正文全部图表。旧队列中断原件和缺失最终seal的R1-native四接受checkpoint均保留；恢复任务、终结与等待状态以发布时JSON为准。

## 保存范围与复现限制

包含研究脚本、协议、当前论文与数据、开发/失败/回滚/审查回执、联合档案和版本化源码补丁。每个选中文件按稳定字节复制、校验，动态文件可能对应不同采集时刻；进行中目录不构成新的整批封存。默认单文件2MiB以下；关键档案和指定最新验证/论文文件按需扩展。大型RRG、route、完整STA前沿、二进制、构建树及原始日志保留服务器，清单列出省略路径/范围及可用身份。这是研究证据和源码快照，不是全部原始数据的异地备份。原绝对来源路径保留，不能保证异机直接运行。

源码补丁分别直接应用于VTR `0b912334fdd83bb754b302146ac0d1ec9edc9a0e`，不要叠加；三套补丁均独立apply检查并核对恢复Git树和文件哈希。外部依赖使用原内容哈希，不冒充远端submodule认证。固定架构资源占用减少不等同芯片面积或功耗减少。
