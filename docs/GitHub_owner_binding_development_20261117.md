# 独立开发修正与已结束观测费用

投稿候选稿、paper19及当前CP1r3确认/补充核验队列保持原版本。本次没有新的完整配对收益，不安装开发补丁，不重跑native或STA。

## 修正准备登记的生命周期

[独立开发副本](../research/dac_v14_20261112/owner_registration_development_fix_02/source_patch.json)将runtime绑定移到owner准备封存之前；调用阶段只验证已经封存的owner登记。普通尚未封存的作用域仍可在首次调用前绑定。已有执行登记、runtime字节漂移、不同路径、封存后登记变化、未成功准备或旧版未绑定owner都会在启动前拒绝。原冻结核验器的准备哈希断言保持原样。

[12项检查](../research/dac_v14_20261112/owner_registration_development_fix_02/validation.json)覆盖成功路径、原断言、共享字典角色记录保持、普通作用域幂等及异常拒绝。首次检查发现deepcopy保留共享字典关系，使新增顶层绑定也修改角色来源表；[原失败](../research/dac_v14_20261112/owner_registration_development_fix_01/preflight_failure.json)及当时源码完整保留。第二版先分离顶层来源表再绑定，检查通过。

这是未来发布版本的准备登记修正，尚未完成完整原生流程验证或安装。它不改写LSTM/native原失败，不替代当前已排队的原检查重审与原始证据准入，也不构成速度或方法收益。后续完整封装和端到端验证应在单独版本进行。

## 工程费用定位

[19个已结束普通事务、35次观测的费用分层](../research/dac_v14_20261112/LSTM_observation_cost_layers_01/ENGINEERING_SCOPE.md)进一步区分了准备、原生进程封装、独立物理审计及未细分工作。新候选评估中，两臂原生进程封装均值约107–109秒、独立审计约70秒、准备约39–40秒。原生进程时间包含监督启动/等待/observer停止，不能当作纯搜索或纯STA；角色内部timer已嵌套其中。未细分工作不能全部归于Python或哈希。复用的历史候选FULL/STA不重复计费，owner事务因回调范围不同排除。

该证据将下一步工程定位细化为原生初始化/加载/STA和封装准备/候选审计。未来有效优化仍须保留全部门槛，对native/domain对称应用，并实测完整流程；当前不报告加速。

截至01:30 UTC，LSTM/domain第十次资源提交已完成（530.26秒，当前线长预算余量329），第十一轮FULL/STA外层评估正在运行。native命令已结束但原独立验证失败，质量尚未准入；其余四角色待执行。当前条件性排程仍约3.4–11.2小时，额外原始证据准入耗时未知、另计；不是期限或研究停止条件。

新增证据只进入补充工程记录与状态说明。[六页投稿稿件](../research/dac_v14_20261112/submission_candidate_01/build/main.pdf)及[具体实验影响清单](../research/dac_v14_20261112/submission_candidate_01/EXPERIMENT_IMPACT.md)保持不变。研究Goal继续active。
