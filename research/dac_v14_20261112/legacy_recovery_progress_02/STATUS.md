# 已登记恢复的两个终态及精确失败原因

|轨迹|自己的已恢复终态|本次后缀费用|边界|
|---|---|---:|---|
|CLSTM/native|6.849416589461ns，226922wire/3SB/915CB，setup153改善/10退化、hold退化0|206.331049秒|原失败641.584947秒另计；不是新完整从头费用或确认配对|
|CLSTM/domain|未执行恢复，quality=null|准入0.005978秒|原独立审计JSONDecodeError保留，无新增native查询|
|robot-p1|11.633691343604ns，231101wire/47SB/6673CB，setup34改善/1退化、hold退化0|705.290739秒|原失败1857.322629秒另计；开发恢复，不是独立输入或冻结确认|

CLSTM/native时序阶段从226894到226922线长（+28），CPD改善0.007638778499ns；原时序阶段与恢复登记的绝对上限逐项相同，为227133wire/3SB/915CB，selected policy均为timing_under_resources。226894是该阶段锚点，不是线长上限；10个setup退化明确保留，不误称端点不退化策略通过。没有移动预算或将旧费用与后缀拼成完整时间。

CLSTM/domain的错误已精确定位到原reuse_on_native_supervision.json零字节文件。原独立审计的实际source_sha256确实绑定其空字节摘要，随后直接进入reduction输入；原函数紧接着对该文件read JSON。配套active记录中的原supervisor和child身份都已不存活，原worker有passed封存回执，但这尚不等于重新通过全部来源、字节、完整请求、FULL、STA、向量和物理门槛。原空文件和失败回执保持，不补造历史supervisor completion。后续只应复用已有23请求原生结果做必要独立审计，不重复昂贵查询。

原队列继续reduction/native；基线0.5/1/2只读协调仍由原session6495等待串行槽，不修改当前规则。此包只更新补充材料的恢复与失败解释，不扩大主稿TableI、摘要或结论；既有native/domain配对资格未改变。上述已知电路/布局均不增加独立输入或架构计数。
