# TPU-OS整臂判定与完整配对

**实际配对：未通过。**

| 角色 | 质量准入 | CPD(ns) | 线长/SB/CB | 自身根setup改善/退化/hold新增 | 完整命令(s) | PSS(GiB) |
|---|---|---:|---:|---:|---:|---:|
| native | not_passed | — | — | — | 941.321435 | 2.808 |
| domain | not_passed | — | — | — | 944.174382 | 2.831 |

具体缺口：
{'arm': 'native', 'status': 'raw_admission_requires_reconciliation', 'reason': 'Traceback (most recent call last):\n  File "/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_routing/research/dac_v14_20261112/admit_cp1r5_tpu_os_pair_01.py", line 112, in role\n    result=audit.case(target,original,out)\n  File "/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_routing/research/dac_v14_20261112/admit_cp1r5_tpu_os_pair_01.py::original_case_entry", line 25, in case\n    COHORT = D/\'cp1r3_distinct_input_cohort_01\'\n  File "/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_routing/research/dac_v14_20261112/cp1r3_raw_admission_v1.py", line 226, in transaction\n    assert env[\'VPR_JOINT_NATIVE_SEED_ORDER\'] == role[\'seed_order\']\nKeyError: \'VPR_JOINT_NATIVE_SEED_ORDER\'\n'}
{'arm': 'domain', 'status': 'raw_admission_requires_reconciliation', 'reason': 'Traceback (most recent call last):\n  File "/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_routing/research/dac_v14_20261112/admit_cp1r5_tpu_os_pair_01.py", line 112, in role\n    result=audit.case(target,original,out)\n  File "/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_routing/research/dac_v14_20261112/admit_cp1r5_tpu_os_pair_01.py::original_case_entry", line 25, in case\n    COHORT = D/\'cp1r3_distinct_input_cohort_01\'\n  File "/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_routing_acceleration/3D_FPGA_routing/research/dac_v14_20261112/cp1r3_raw_admission_v1.py", line 226, in transaction\n    assert env[\'VPR_JOINT_NATIVE_SEED_ORDER\'] == role[\'seed_order\']\nKeyError: \'VPR_JOINT_NATIVE_SEED_ORDER\'\n'}

原独立检查及后续只读费用另列：
- native原检查：11.896343640983105秒。
- domain原检查：11.670919381082058秒。
- native只读阶段：22.034798秒，raw_admission_requires_reconciliation。
- domain只读阶段：21.227776秒，raw_admission_requires_reconciliation。
- pair只读阶段：0.155744秒，pair_not_admitted。

TPU-OS是不同于TPU-WS的数据流/网表，仍属同TPU工作负载家族和两层Hybrid-O架构；无新架构、未见留出集或应用SDC主张。原失败、拒绝及费用保留。只有本次实际准入支持的表格和适用性可更新，投稿07在此之前保持。
