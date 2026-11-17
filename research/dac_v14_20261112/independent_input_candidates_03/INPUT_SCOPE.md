# 后续输入来源与独立性

本清单按来源和物理输入元数据筛选，不读取历史QoR用于选点。当前确认和已登记基线优先，未登记新执行。

| 候选 | 来源状态 | 输入文件总量(GiB) | 可计入的独立性范围 |
|---|---|---:|---|
| gemm_p0 | metadata_consistent_pending_serial_byte_admission | 13.22 | Different declared netlist/workload from the matched matrix and current cohort; known historical training source, not unseen. |
| gemm_p1 | missing_source_provenance | -- | Same-circuit alternate placement candidate; only actual placement/root proof could establish a different start. |
| tpu_os_p0 | metadata_consistent_pending_serial_byte_admission | 1.14 | Different dataflow/netlist from TPU-WS; retain the same TPU workload-family label. Not a new architecture family. |
| dla_medium_p0 | metadata_consistent_pending_serial_byte_admission | 13.08 | Scale variant of active DLA-small; not an independent new workload-family or architecture sample. |

GEMM-p0的声明网表不同于当前匹配矩阵和CP1r3，优先作为后续不同电路候选；其较大输入需要先做串行字节、资源与布局准入。GEMM-p1缺少指定来源，不以同初始树的新seed替代。TPU-OS保留TPU家族标识，DLA-medium保留规模变体标识。以上均未形成新的确认样本，也不增加论文收益或新架构数量。
