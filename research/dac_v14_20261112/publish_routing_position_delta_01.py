"""Prepare or publish an authorized evidence delta without touching the live index/HEAD."""
import argparse,hashlib,json,os,stat,subprocess,tempfile
from datetime import datetime,timezone
from pathlib import Path
from retained_prefix_workflow import D,read,write,sha
ROOT=D.parents[1];BASE='42ae2e406fce51e8bcbbb744e5016cc3439e6ff3';BRANCH='refs/heads/research/dac-snapshot-20261113'
LOCAL=ROOT/'docs/github_routing_position_local_commit_20261116.json'
MANIFEST=ROOT/'docs/github_routing_position_manifest_20261116.json'
PUBLICATION=ROOT/'docs/github_routing_position_publication_receipt_20261116.json'
def git(*args,data=None,env=None):
    return subprocess.run(['git',*args],cwd=ROOT,input=data,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,check=True).stdout
def stamp():return datetime.now(timezone.utc).isoformat()
def remote():return {line.split()[1]:line.split()[0] for line in git('ls-remote','origin',BRANCH,'refs/heads/main').decode().splitlines()}
def prepare():
    assert not LOCAL.exists() and not MANIFEST.exists()
    refs=remote();assert refs[BRANCH]==BASE
    head=git('rev-parse','HEAD').decode().strip();index=ROOT/'.git/index';index_sha=sha(index)
    scratch=Path(tempfile.mkdtemp(prefix='routing-position-publication-',dir='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/publication_snapshots'))
    env=os.environ.copy();env['GIT_INDEX_FILE']=str(scratch/'index');git('read-tree',BASE,env=env)
    selected=set(D.glob('*.py'))|set(D.glob('*.json'))|{D/'CURRENT_STATUS.md',ROOT/'README.md',ROOT/'docs/GitHub_routing_position_progress_20261116.md'}
    dirs=['routing_related_work_01','paper_snapshots/current_routing_position_20261116','unified_confirmation_candidate_01']
    selected.update([D/'paper/current_repair_main.tex',D/'paper/data/evidence_v14_ledger.json'])
    allowed={'.py','.json','.md','.tex','.bib','.cls','.csv','.svg','.png','.pdf','.sdc','.c','.h','.txt'}
    excluded_dirs={'tools','__pycache__','.git','bin','src','build'}
    for name in dirs:
        base=D/name
        if not base.exists():continue
        for current,subdirs,files in os.walk(base):
            subdirs[:]=[n for n in subdirs if n not in excluded_dirs]
            for name in files:
                f=Path(current)/name
                if f.suffix in allowed or f.name in ['seccomp_thread_guard','standalone_native_runtime_component_01.tar.gz']:
                    selected.add(f)
    paper=read(D/'routing_position_paper_binding_05.json');assert paper['passed'] and paper['pages']==6
    selected.add(Path(paper['pdf']))
    for group in ['source_sha256','verified_case_receipts']:
        for name,digest in paper[group].items():
            f=Path(name);assert sha(f)==digest
            if f.is_relative_to(ROOT):selected.add(f)
    included={};omitted={};entries=[]
    for f in sorted(selected):
        if f.is_symlink() or not f.is_file():continue
        rel=str(f.relative_to(ROOT));size=f.stat().st_size
        if size>4*1024**2:omitted[rel]=dict(bytes=size,reason='Large evidence remains on shared storage');continue
        data=f.read_bytes();mode='100755' if f.stat().st_mode&stat.S_IXUSR else '100644'
        blob=git('hash-object','-w','--stdin',data=data).decode().strip()
        included[rel]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),git_blob=blob,mode=mode)
        entries.append(f'{mode} {blob}\t{rel}\0')
    write(MANIFEST,dict(status='immutable_incremental_snapshot',captured_at=stamp(),public_evidence_base='9734eee83b62fc012f0bb137f75aba919df514e4',expected_parent=BASE,
        selected_files=included,omitted_large_files=omitted,raw_data_backup_complete=False,research_complete=False,
        authorization='Explicit user request to publish completed experiments, conclusions and ongoing experiment descriptions; includes prior-authorized manuscript scope.',
        qualification='Inherits all prior public files; only selected file contents updated. Primary-source related-work positioning revised; no external algorithm benchmark reproduced and no new native or complete-method result. Six-page main retains measured rows and figures; detailed local histories move to supplement. Existing experiment versions remain fixed. Active statuses are capture-time observations.'))
    data=MANIFEST.read_bytes();blob=git('hash-object','-w','--stdin',data=data).decode().strip()
    entries.append(f'100644 {blob}\t{MANIFEST.relative_to(ROOT)}\0')
    git('update-index','-z','--index-info',data=''.join(entries).encode(),env=env)
    tree=git('write-tree',env=env).decode().strip()
    commit=git('commit-tree',tree,'-p',BASE,data=b'Clarify routing prior art and contribution scope in six-page manuscript\n',env=env).decode().strip()
    actual={}
    for row in git('ls-tree','-rz',commit).split(b'\0'):
        if not row:continue
        meta,name=row.split(b'\t',1);actual[name.decode()]=meta.decode().split()[2]
    assert all(actual[n]==v['git_blob'] for n,v in included.items())
    assert git('rev-parse','HEAD').decode().strip()==head and sha(index)==index_sha
    changed=git('diff-tree','--no-commit-id','--name-only','-r',BASE,commit).decode().splitlines()
    write(LOCAL,dict(passed=True,status='prepared_verified_not_pushed',commit=commit,parent=BASE,tree=tree,branch=BRANCH,
        selected_files=len(included),payload_bytes=sum(v['bytes'] for v in included.values()),changed_files=len(changed),
        live_head=head,live_index_sha256=index_sha,live_HEAD_unchanged=True,live_index_unchanged=True,
        remote_main_before=refs['refs/heads/main'],manifest_sha256=sha(MANIFEST),scratch=str(scratch),prepared_at=stamp()))
    (scratch/'changed_paths.txt').write_text('\n'.join(changed)+'\n')
    print(read(LOCAL))
def publish():
    assert not PUBLICATION.exists();r=read(LOCAL);assert r['passed'] and sha(MANIFEST)==r['manifest_sha256']
    assert remote()[BRANCH]==r['parent']
    assert git('rev-parse','HEAD').decode().strip()==r['live_head'] and sha(ROOT/'.git/index')==r['live_index_sha256']
    git('push','origin',r['commit']+':'+BRANCH)
    refs=remote();assert refs[BRANCH]==r['commit'] and refs['refs/heads/main']==r['remote_main_before']
    assert git('rev-parse','HEAD').decode().strip()==r['live_head'] and sha(ROOT/'.git/index')==r['live_index_sha256']
    git('update-ref',BRANCH,r['commit'],r['parent'])
    write(PUBLICATION,dict(**{k:v for k,v in r.items() if k!='status'},status='pushed_and_remote_ref_verified',verified_at=stamp(),
        remote_branch_commit=refs[BRANCH],remote_main_unchanged=True,public_evidence_base='9734eee83b62fc012f0bb137f75aba919df514e4',research_complete=False,
        commit_url='https://github.com/GRYYYYYYY/3D_FPGA_routing/commit/'+r['commit']))
    print(read(PUBLICATION))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--push',action='store_true');a=p.parse_args()
    publish() if a.push else prepare()
