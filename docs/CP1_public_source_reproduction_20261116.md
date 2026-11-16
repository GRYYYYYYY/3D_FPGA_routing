# 从公开源码恢复 CP1 固定依赖

CP1 的公开源码包不含 NumPy/lxml，但现在已有[实际重建验证](../research/dac_v14_20261112/cp1_public_source_restoration_01/completion.json)：从公开源码归档及两个固定 wheel 恢复1166个依赖文件后，全部1289个封存文件的SHA256一致；实际扩展库导入和项目外固定入口检查通过。未使用完整本地运行包或已安装运行时目录。

要求 CPython3.10、Linux x86_64，以及所列 manylinux wheel 兼容的系统库。依赖为NumPy2.2.6、lxml6.1.3。执行以下命令（输出目录必须尚不存在，位于历史项目之外）：

```bash
python3.10 -m pip download --require-hashes --no-deps --only-binary=:all: --index-url https://pypi.org/simple --dest /tmp/cp1-wheels -r research/dac_v14_20261112/confirmation_cp1_wheels_requirements.txt
python3.10 research/dac_v14_20261112/restore_confirmation_cp1_dependencies.py --source-archive research/dac_v14_20261112/confirmation_release_cp1_01/current_sta_cp1_source.tar.gz --wheel-dir /tmp/cp1-wheels --output /tmp/cp1-rebuilt
```

恢复脚本自身只用标准库、不联网、不修改已有目录。它验证源码归档、release manifest和两个wheel的固定摘要，只恢复manifest要求的依赖文件，再检查完整文件集合和摘要；已有输出拒绝覆盖。wheel中的一个预编译字节码缓存不在封存清单内，明确排除。不要用未验证的最新版依赖替换固定文件。

[wheel来源与摘要](../research/dac_v14_20261112/cp1_public_source_restoration_01/wheel_sources.json)已核对公开PyPI发行元数据。此次pip使用下载缓存，随后逐文件验证；不称从零网络下载。带 `--require-hashes` 的下载命令已实际通过。

恢复后按[固定CP1说明](../research/dac_v14_20261112/confirmation_release_cp1_01/README.md)配置显式物理输入和阶段二进制。输入配置必须绑定重建目录中的manifest/contract路径及原摘要，不复用旧绝对路径；实际验证只重绑定了这些发布位置和packing来源文件位置，机制规则未变。

原生二进制、容量查询程序、architecture/RRG/BLIF/packing/placement及必要SDC仍是显式外部前提。此次入口检查没有声称大物理输入准入、原生二进制重新编译或新完整实验通过；新增native调用0、独立结果0。封存CP1及已排队的两输入四臂确认不改动，开发队列也保持原版本。
