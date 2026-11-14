"""Freeze a reviewable public progress snapshot without changing live experiments or Git refs."""
import collections
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import time
from retained_prefix_workflow import D,read,write,sha
from seed_census_analysis_pool_v2 import process_identity

ROOT=D.parents[1];parent='f7167bd1fbeb267d7ffc02766eeb2e5966aec387'
gitdir=Path(subprocess.check_output(['git','rev-parse','--absolute-git-dir'],cwd=ROOT,text=True).strip())
out=gitdir/'progress_snapshot_20261114';out.mkdir(exist_ok=False)
payload=out/'payload';payload.mkdir()
now=datetime.now(timezone.utc).isoformat();owners={}
for n in ['completed_resource_timing_recovery_01','vector_feedback_subset_native_recovery_01','stable_seed_transfer_recovery_01',
          'direct_scope_resource_equivalence_recovery_01','native_census_resource_equivalence_recovery_01']:
    q=D/n/'queue';r=read(q/'registration.json');actual=process_identity(r['pid'])
    terminal=read(q/'completion.json') if (q/'completion.json').exists() else None
    owners[n]=dict(registration=str(q/'registration.json'),recorded_pid=r['pid'],recorded_start_ticks=r['start_ticks'],
        live=bool(actual and actual['state']!='Z' and actual['start_ticks']==r['start_ticks']),
        phase=read(q/'status.json') if (q/'status.json').exists() else None,terminal=terminal)
summary=dict(observed_at=now,archive='multiobjective_complete_resource_timing_01',archive_observations=335,
    whole_research_complete=False,owners=owners,public_parent=parent,
    pending_interrupted_private_checkpoint='stable_seed_transfer_dev_01/bnn_R1_native',
    qualification='Publication-time observations supersede historical live-status text. A phase.json may be stale: terminal receipts and verified PID/start identity take precedence. Running trials are captured as partial evidence, not completed scores.')
write(ROOT/'docs/github_progress_status_20261114.json',summary)
feedback=owners['vector_feedback_subset_native_recovery_01']['terminal']
note=''
if feedback and feedback.get('passed'):
    result=feedback['result'];cmp=result['decisions']['endpoint_vector']['timing_decision']['comparison']
    note=(f"最新五连接反馈组合已产生合法结果：CPD {result['CPD_s']*1e9:.15f} ns，"
          f"{result['resources']['wirelength']} wire / {result['resources']['SB_pairs']} SB / {result['resources']['CB_sources']} CB；"
          f"严格与全向量规则均接受，setup {cmp['setup_improved']} 改善、{cmp['setup_regressed']} 退化。"
          '该独立45SB输入结果尚未加入335条联合档案，也尚未写入C183v2正文；完整原始回执随本快照保留。\n')
doc=ROOT/'docs/GitHub_progress_20261114.md'
doc.write_text('# 2026-11-14 科研进展公开快照\n\n'
    f'采集开始（UTC）：{now}。用户明确要求上传当前进展；沿用已授权的公开完整研究快照范围。'
    '本次追加到 `research/dac-snapshot-20261113`，主实验目录和正在运行的任务不切换分支、不停止。\n\n'
    '## 入口\n\n'
    '- [335条合法观察及强基线联合档案](../research/dac_v14_20261112/multiobjective_complete_resource_timing_01/points.csv)\n'
    '- [精度完整的档案JSON](../research/dac_v14_20261112/multiobjective_complete_resource_timing_01/points.json)\n'
    '- [现有6页正文PDF](../research/dac_v14_20261112/paper_snapshots/current_strict_terminal_vector_feedback_20261114/build/current_repair_main.pdf)\n'
    '- [64页详细证据稿PDF](../research/dac_v14_20261112/paper_snapshots/current_uniform_fused_repair_20261114/build/main.pdf)\n'
    '- [新增证据与正文集成状态](../research/dac_v14_20261112/paper/DEVELOPMENT_STATUS.md)\n'
    '- [发布时实验状态](github_progress_status_20261114.json)；[continuation](../research/dac_v14_20261112/CONTINUATION.json)\n'
    '- [三套可独立还原的源码补丁与校验](../patches/snapshot_20261114_verified/manifest.json)\n\n'
    '## 本次证据\n\n'
    '同为13.228145689936355ns的实际合法状态：原生对照2059627wire/82SB/5062CB，'
    '成对资源引导分支2061389wire/43SB/5060CB；多1762wire换取39SB/2CB减少。'
    '两者来自各自完整自动资源阶段后的current-STA修复，不能与旧45SB前缀拼接。'
    '相同CPD不代表逐端点支配（成对分支相对原生550setup改善、799退化）。'
    '完整冷启动单配置路由加修复时间仍未知，导入、核心、研究流程和中断恢复时间分列。\n\n'
    +note+'\n'
    '正文仍为已封存C183v2，新增335条档案证据在独立delta中，未冒称已更新正文全部图表。'
    '旧队列中断原件和缺失最终seal的R1-native四接受checkpoint均保留；恢复任务、终结与等待状态以发布时JSON为准。\n\n'
    '## 保存范围与复现限制\n\n'
    '包含研究脚本、协议、当前论文与数据、开发/失败/回滚/审查回执、联合档案和版本化源码补丁。'
    '每个选中文件按稳定字节复制、校验，动态文件可能对应不同采集时刻；进行中目录不构成新的整批封存。'
    '默认单文件2MiB以下；关键档案和指定最新验证/论文文件按需扩展。'
    '大型RRG、route、完整STA前沿、二进制、构建树及原始日志保留服务器，清单列出省略路径/范围及可用身份。'
    '这是研究证据和源码快照，不是全部原始数据的异地备份。原绝对来源路径保留，不能保证异机直接运行。\n\n'
    '源码补丁分别直接应用于VTR `0b912334fdd83bb754b302146ac0d1ec9edc9a0e`，不要叠加；'
    '三套补丁均独立apply检查并核对恢复Git树和文件哈希。外部依赖使用原内容哈希，不冒充远端submodule认证。'
    '固定架构资源占用减少不等同芯片面积或功耗减少。\n',encoding='utf-8')

selected={};omitted={};skipped=[];excluded_dirs=[];sensitive=[]
extensions={'.py','.cpp','.h','.tpp','.json','.md','.sh','.patch','.tex','.bib','.cls','.csv','.svg','.png','.pdf'}
exclude={'src','source','bin','build','.git','__pycache__','.venv','.venv-lazagna','tools','paper_snapshots','native','candidate_restored','inbox'}
run_names={'manifest.json','pair_check.json','analysis_gate.json','final_guide_audit.json','control_reproduction.json','trace_reproduction.json','first_legal_prefix_reproduction.json','time.txt','disabled_reproduction.json','first_convergence_prefix.json','rollback_reproduction.json'}
patterns=[re.compile(rb'gh[pousr]_[A-Za-z0-9]{30,}'),re.compile(rb'github_pat_[A-Za-z0-9_]{30,}'),
          re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
          re.compile(rb'(?<![A-Za-z0-9])AKIA[A-Z0-9]{16}(?![A-Za-z0-9])'),
          re.compile(rb'\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{32,}'),
          re.compile(rb'["\x27](?:access_token|api_key|client_secret|refresh_token)["\x27]\s*:\s*["\x27][A-Za-z0-9_+./=-]{20,}["\x27]',re.I)]
def add(path,reason,limit=2*1024**2):
    path=Path(path)
    if path.is_symlink() or not path.is_file():return
    rel=str(path.relative_to(ROOT))
    if rel in selected:return
    for _ in range(3):
        before=path.stat()
        if before.st_size>limit:
            omitted[rel]=dict(bytes=before.st_size,reason='large record retained on server',mtime_ns=before.st_mtime_ns);return
        data=path.read_bytes();after=path.stat()
        if (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns):break
    else:skipped.append(dict(path=rel,reason='changed during bounded copy'));return
    if path.suffix=='.json':
        try:json.loads(data)
        except (ValueError,UnicodeDecodeError):skipped.append(dict(path=rel,reason='not complete JSON at capture'));return
    if path.suffix not in {'.pdf','.png'} and any(p.search(data) for p in patterns):
        sensitive.append(rel);omitted[rel]=dict(bytes=len(data),reason='possible credential pattern; held for review, content not printed');return
    dst=payload/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(data)
    os.chmod(dst,stat.S_IMODE(before.st_mode)&0o777)
    selected[rel]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),source_mtime_ns=before.st_mtime_ns,reason=reason)

for cur,dirs,files in os.walk(D):
    base=Path(cur)
    kept=[]
    for n in dirs:
        if n in exclude or '_workspace_' in n or '_candidate_' in n or n.startswith(('job_','epoch_')):
            excluded_dirs.append(str((base/n).relative_to(ROOT)))
        else:kept.append(n)
    dirs[:]=kept
    isrun='runs' in base.relative_to(D).parts
    for n in files:
        p=base/n
        if isrun:
            if n in run_names:add(p,'run identity/check receipt; large route/log/physical records retained on server')
        elif p.suffix in extensions:add(p,'research implementation/protocol/analysis/partial or sealed evidence')
for root in [ROOT/'paper/dac2027',ROOT/'gpt',ROOT/'patches/snapshot_20261114_verified']:
    if not root.exists():continue
    for cur,dirs,files in os.walk(root):
        dirs[:]=[n for n in dirs if n not in exclude]
        for n in files:
            p=Path(cur)/n
            if p.suffix in extensions or (root==ROOT/'gpt' and p.suffix=='.txt'):add(p,'paper/user research instructions/verified source overlays')
for n in ['current_strict_terminal_vector_feedback_20261114','current_uniform_fused_repair_20261114']:
    root=D/'paper_snapshots'/n
    for cur,dirs,files in os.walk(root):
        dirs[:]=[x for x in dirs if x not in {'tools','__pycache__'}]
        for name in files:
            p=Path(cur)/name
            if p.suffix in extensions:add(p,'immutable current focused/evidence manuscript snapshot',limit=16*1024**2)
for p in (D/'multiobjective_complete_resource_timing_01').iterdir():add(p,'full current 335-observation joint archive',limit=16*1024**2)
for p in [D/'CONTINUATION.json',D/'live_handoff.json',D/'RESEARCH_PROTOCOL.md',doc,ROOT/'docs/github_progress_status_20261114.json',
          ROOT/'docs/github_publication_receipt_20261113.json',D/'paper/data/complete_resource_timing_delta_01.json']:
    add(p,'current continuation/protocol/publication state',limit=16*1024**2)
for role in ['native','paired']:
    state=D/'completed_resource_timing_dev_01'/role/'round_002/proposal_01/transaction/current_group_evaluation'
    add(state/'runs/state/independent_audit.json','exact latest independent physical audit',limit=40*1024**2)
    add(state/'endpoint_vector.json','exact latest fixed-endpoint timing vector',limit=40*1024**2)
if feedback and feedback.get('passed'):
    state=Path(feedback['result']['state'])
    for p in [state/'runs/state/independent_audit.json',state/'endpoint_vector.json']:
        add(p,'new feedback actual physical/STA proof, not yet in joint archive',limit=40*1024**2)
for rel in selected:omitted.pop(rel,None)
manifest=dict(status='frozen_local_progress_snapshot_pending_upload',captured_at_utc=now,
    repository='GRYYYYYYY/3D_FPGA_routing',branch='research/dac-snapshot-20261113',expected_parent=parent,
    authorization='Explicit current request to upload current progress; earlier public full-manuscript/evidence scope persists.',
    selected_files=selected,omitted_large_or_sensitive_files=omitted,excluded_server_directory_roots=excluded_dirs,
    unstable_or_incomplete_files=skipped,possible_sensitive_paths=sensitive,
    selected_count=len(selected),selected_bytes=sum(x['bytes'] for x in selected.values()),
    raw_data_backup_complete=False,live_trials_not_modified=True,research_complete=False,
    qualification='Per-file stable snapshots, not a new atomic seal for live cohorts. Historical parent files remain; this commit overlays selected current files. Original raw artifacts stay on server. Any omitted credential-pattern files require separate review before staging.')
mp=ROOT/'docs/github_progress_manifest_20261114.json';write(mp,manifest)
target=payload/mp.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(mp,target)
paths=sorted(selected)+[str(mp.relative_to(ROOT))]
(out/'paths.txt').write_text('\n'.join(paths)+'\n')
write(out/'preparation.json',dict(passed=not sensitive,payload=str(payload),parent=parent,paths=len(paths),
    selected_bytes=manifest['selected_bytes'],possible_sensitive_paths=sensitive,
    skipped=len(skipped),manifest_sha256=sha(mp),completed_at=datetime.now(timezone.utc).isoformat()))
print(dict(paths=len(paths),MiB=round(manifest['selected_bytes']/1024**2,1),sensitive=sensitive,skipped=len(skipped),payload=str(payload)),flush=True)
