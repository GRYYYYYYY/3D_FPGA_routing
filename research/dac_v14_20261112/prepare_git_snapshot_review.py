#!/usr/bin/env python3
"""Explicit local snapshot inventory; no remote mutation."""
import os,time,json,subprocess
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
ROOT=D.parents[1];LIMIT=2*1024**2

def main():
    selected={};omitted={};exclude={'src','source','bin','build','.git','__pycache__','.venv','.venv-lazagna','tools'}
    allowed={'.py','.cpp','.h','.json','.md','.sh','.patch','.tex','.bib','.cls','.csv','.svg','.png','.pdf'}
    run_names={'manifest.json','pair_check.json','final_guide_audit.json','control_reproduction.json','trace_reproduction.json','first_legal_prefix_reproduction.json','time.txt','disabled_reproduction.json','first_convergence_prefix.json','rollback_reproduction.json'}
    def add(p,reason):
        if p.is_symlink() or not p.is_file():return
        rel=str(p.relative_to(ROOT));size=p.stat().st_size
        if size>LIMIT:omitted[rel]=dict(bytes=size,reason='Larger than review snapshot per-file threshold; original retained on shared storage.');return
        if p.name.startswith('.env') or p.suffix in ['.key','.pem']:return
        selected[rel]=dict(bytes=size,sha256=sha(p),reason=reason)
    for current,dirs,files in os.walk(D):
        dirs[:]=[n for n in dirs if n not in exclude];base=Path(current);isrun='runs' in base.relative_to(D).parts
        for name in files:
            p=base/name
            if isrun:
                if name in run_names:add(p,'controlled run receipt/check/time; raw route/log omitted')
            elif p.suffix in allowed:add(p,'development source/protocol/analysis/summary/working-paper evidence')
    for paper in [ROOT/'paper/dac2027',D/'paper']:
        if not paper.exists():continue
        for current,dirs,files in os.walk(paper):
            dirs[:]=[n for n in dirs if n not in exclude and n not in ['archive','archives','releases','submission_packages']];base=Path(current)
            for name in files:
                p=base/name
                if p.suffix in allowed or name in ['README','abstract.txt']:add(p,'frozen-v13 or independent working paper source/data/figures')
        if (paper/'build/main.pdf').exists():add(paper/'build/main.pdf','review PDF; source and validation also included')
    for p in (ROOT/'gpt').rglob('*'):
        if p.suffix in allowed or p.suffix=='.txt':add(p,'user supplied research/supplement package')
    for p in (ROOT/'patches/snapshot_20261113_verified').glob('*'):add(p,'independently apply-checked source patch and dependency hashes')
    stage=D/'outside_native_stage_01'
    for p in [stage/'CMakeCache.txt',D/'outside_dp_core_01/src/h3d_partition_dp.h',D/'outside_dp_core_01/src/h3d_independent_plan.h']:add(p,'current build provenance or independently tested exact solver source')
    ledger=read(D/'paper/data/evidence_v14_ledger.json')
    for rel,expected in ledger['sources_sha256'].items():
        p=D/rel;add(p,'working-paper claim-ledger source')
        key=str(p.relative_to(ROOT))
        if key in omitted:omitted[key]['sealed_sha256']=expected
    doc=ROOT/'docs/GitHub_snapshot_review_20261113.md'
    doc.write_text('''# 2026-11-13 阶段快照（本地待确认公开范围）\n\n当前仓库 GRYYYYYYY/3D_FPGA_routing 经实时 GitHub 元数据核对为 **public**。旧 2026-11-09 说明中的“默认私有”不能作为本次发布依据。此清单和本地提交不代表已推送或已授权公开当前未投稿稿；远端 main 在核对时仍为 b132a1d。\n\n本批 outside DP 四个 quality/control 角色全部合法，首次合法和两次收敛均保持现有完整路由、6.20812ns CPD 与 SB/CB118/955。两类真实变化元数据的强制回滚也通过。新方法没有质量收益，不推广；研究目标仍持续，不受旧日期/总调用/固定矩阵或作者资料限制。当前论文更新到 C60。\n\n保存代码、实验协议、状态/耗时/资源表、封存检查、所有小型分析结果、输入输出哈希、失败/缺失记录，以及原v13和独立开发稿。大型 RRG、route、实时/完整日志、二进制和外部依赖树不上传，原件保留共享盘；较大分析JSON在清单中列出路径/大小，若已有封存hash则一并列出。该Git快照是证据摘要及可还原主源码，不是所有原始数据的异地完整备份。\n\n源码从 patches/snapshot_20261113_verified/architecture_outside_native.patch 独立应用于 VTR 0b912334fdd83bb754b302146ac0d1ec9edc9a0e，并核对43个变更文件和恢复Git树。不要叠加旧 architecture_r1.patch。原环境第三方目录没有自己的Git元数据，清单只证明2878个文件与原服务器/研究baseline一致，不冒充远端submodule commit内容认证；异机需取得匹配依赖并核对hash。\n\n研究入口：research/dac_v14_20261112/RESEARCH_LOG.md、CONTINUATION.json、paper/claims_evidence.md。最新结果及分项时间：outside_quality_summary_01.json、outside_quality_timing_01.json、paper/data/outside_quality_v14.csv。原CSV/审计保留绝对来源路径，以免破坏封存身份；不能宣称任意目录开箱即跑。\n\n规划和残余query计时是router阶段子项，不重复相加；非router部分含加载、初始化、输出/检查/退出。人工推理/完整审计/打包缺统一阶段timer，不编造整个科研周期耗时占比，也不将单次顺序开发时间当正式加速比。\n''')
    add(doc,'snapshot scope, public visibility and reconstruction limitations')
    manifest=ROOT/'docs/github_snapshot_manifest_20261113.json';write(manifest,dict(status='local_review_inventory_not_pushed',created_at=time.time(),repository='GRYYYYYYY/3D_FPGA_routing',verified_visibility='public',remote_main_observed='b132a1d13eec8351cfcdc371bfc03611f678291b',selected_files=selected,omitted_large_files=omitted,selected_count=len(selected),selected_bytes=sum(x['bytes'] for x in selected.values()),claim='No remote publication performed. Confirm publication scope before including unpublished working-paper material in a public branch. Original large records remain on shared storage.'))
    # Include the manifest itself through a path list; self-hash is intentionally not recursive.
    paths=sorted(selected)+[str(manifest.relative_to(ROOT))];(ROOT/'docs/github_snapshot_paths_20261113.txt').write_text('\n'.join(paths)+'\n')
    print(dict(files=len(selected),bytes=sum(x['bytes'] for x in selected.values()),omitted_large=len(omitted),manifest=str(manifest.relative_to(ROOT))))
if __name__=='__main__':main()
