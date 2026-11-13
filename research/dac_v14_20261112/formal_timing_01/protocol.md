# 下一正式计时实验：冻结 U + 精确 view 的端到端开销

状态：具体方案已确定，runner/输入准入尚待实现；未启动计时。该实验不冻结整个科研方向，也不设置研究总日期或route次数上限。候选查询P/L等继续作为独立开发分支，不能混入本实验。

## 问题与版本

问题：六电路U开发验证已经结束，精确view也在eltwise、bnn、gemm保持完整路由/决策/guide等价。它是否在同一计时环境下，改善旧R1额外运行开销，并保留相对A0的成本和质量取舍？不以并发开发秒数或旧ptrace结果推算加速比。

三臂：冻结原A0二进制和配置、冻结原R1二进制和选定配置、`closure_view_candidate_01`不可变二进制的完整U反馈加generation/shared/compact/view。新臂保持legacy评分、K16、query4096、criticality0.7、opening16、miss2、cooldown3、完整接受策略；不启用mixed、目标查询、时序额外guide、eligibility trigger或后续实验开关。所有臂保留原生FULL、最终STA和原生拥塞。关闭额外table/final-guide/profile诊断（优先省略开关，而非假定字符串0一定关闭），保留必要统计。

每臂同seed11、Hybrid-O、P0、W100、原相同packed/place/RRG/网表/architecture及route命令。每项参数从原manifest核对，不从历史目录名`c6`推断criticality。父进程清除继承的H3D实验环境变量后，仅注入登记配置。

## 人口与次序

计时人口为spmv、softmax、eltwise_layer、bnn、gemm_layer五个预先确认各臂合法的开发电路。attention失败仍保留在六电路主质量/成功率分母，不因计时人口只含共同合法电路而消失。不得将计时人口称作盲测或全体成功率。

每电路三轮，顺序依次A0/R1/U-view、R1/U-view/A0、U-view/A0/R1，使各臂占每个位置一次；45个登记角色是本项设计，不是整个研究的次数上限或结束条件。保存每次结果，不挑最小运行时间；汇报每电路各臂中位数及全体重复值、配对比值和电路平衡汇总，任何新失败/超时保持原分母并单列。

## 环境与保护

同主机、同seccomp执行器、同单线程配置。在实际允许CPU集合中选择并记录一个固定CPU，通过专用runner的继承affinity约束所有被测进程。记录host、boot id、CPU/cgroup限制、二进制/源码和动态库绑定。运行期间不并发本研究的其他VPR、重编译或大图独立审计；轻量读写/分析可继续。采用明确的正式计时占用标记和唯一owner，后续实验准入须尊重它。

每次计时前顺序读取本案例共享输入作统一文件缓存预热，记录字节和预热时间但不计入VPR进程秒数；不清空系统缓存。计时覆盖完整VPR进程，包括读图、初始化、规划、详细路由与STA；内部planning/router秒分别记录，不能与完整进程秒再相加。每进程沿用1800s、64GiB、disk reserve80GiB。若保护确实影响该案例，保留原记录，并按一致实验目的调整该案例所有臂的新轮配置，不停止整个科研目标。

## 质量准入和证据复用

每次运行核对architecture/netlist/RRG/packed/place及命令配置的摘要；本地copy后的二进制摘要也绑定。原A0、R1各有封存匹配的独立图审计。新U-view的eltwise、bnn、gemm参考分别为closure_view_dev_01/V、view_confirmation_dev_01/V、view_gemm_dev_01/V；spmv、softmax先使用匹配封存的fullU路由作为期望，精确view的首个实测必须证明完整route body相同。

对所有重复执行都要求native FULL和期望的完整route body/CPD/迭代/线长一致。只有同时证明全部物理输入、packed/place及route body一致时，才可复用已有独立图审计作为该重复的证书；新receipt需列出原证书摘要及所有等价检查，而不是伪造一次新图遍历。这样避免每次时间重复后又花数分钟重复扫描完全相同的大图。任一不一致都保存为待诊断样本，停止该案例后续性能解释并运行必要的独立审计，不将其静默计为合法复现。

输出每角色manifest/stdout/time/route及质量复用receipt，统一保留合法/失败/超时/缺失、CPD、物理SB/CB占用与定义、迭代、planning秒、完整进程秒、峰值RSS及环境。计时完成后仍需扩大质量验证、处理退化和继续有依据的算法改进；不标记整个研究完成。
