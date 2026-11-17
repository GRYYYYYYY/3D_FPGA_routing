# CP1r3 三输入六角色：执行终结，完整质量尚未准入

|输入|角色|完整命令秒|执行与原验证结论|
|---|---|---:|---|
|lstm|native|7615.074177|verification_infrastructure_or_evidence_failure|
|lstm|domain|26657.726866|verification_infrastructure_or_evidence_failure|
|dla_small|native|709.742677|initial_route_failed|
|dla_small|domain|702.413717|initial_route_failed|
|eltwise_sb|native|903.226738|infrastructure_timing_planner_slack_type_error|
|eltwise_sb|domain|1042.857390|infrastructure_timing_planner_slack_type_error|

三个物理输入、六个角色全部执行结束，原队列终结passed=true只表示队列收尾成功。完整质量准入0/6、完整匹配准入0/3；不能计算正式N/D收益或费用比例。没有将失败统称为合法无收益，也没有将SB-only既有电路的新布局称为新电路或新架构。

LSTM两条命令返回0，但原独立验证失败；native为owner登记封存变化，domain首个失败为round013/candidate00原passed=false。DLA-small两臂初始路由都剩525个过用节点，无合法根；不是超时。eltwise-SB两臂资源阶段完成，随后相同planner的str/float TypeError使完整命令失败，不是路由失败。domain资源前缀228059 wire/1026 SB/0 CB、自己的CPD6.1216711699785264ns；它不替代完整结果，不能据此声称泛化收益。

补充验证已由原owner自动启动；随后是原raw准入和已登记跨层代价基线。保持原版本、预算、接受规则及失败记录。确认执行已结束；六角色补充验证规划10–40分钟，含失败检查，实际可更早结束；raw与基线额外耗时尚未校准，不提供整个研究的停止日期。历史回退队列继续保留，不是投稿主稿前置条件。

正文只新增失败覆盖、实际完整尝试费用与适用范围限制；BNN和既有机制结论保持，CP1r3未提供已准入的完整跨输入收益。基础设施细节、哈希和逐阶段轨迹留在补充材料。归档全部采用独立inode，小型来源读取前后dev/inode/size/mtime/ctime完全不变；没有重跑native、STA或昂贵查询。

## 已登记准入也已终结

原补充N/D分别耗时104.039414/142.180702秒，均返回失败。native已写出原核验主体payload，随后因独立输出queue目录缺失而写回执失败；此局部payload不等于补充命令成功。domain仍在原line64失败。raw队列0.159189秒终结，六角色均在原/补充前置检查被拒，未进行昂贵字节/向量准入；它不是完整raw审计通过。0/6角色、0/3配对准入保持。

跨层代价原owner已自动开始实际来源复核和私有构建；来源复核14.894037秒，新费用单列。剩余原补充角色为0，旧10–40分钟情景已结束。构建和后续0/0.5/1/2实际执行尚无完整计时样本，不沿用确认ETA；已登记构建1800秒/链接300秒只是阶段上限，不是研究终止日期或实际预测。
