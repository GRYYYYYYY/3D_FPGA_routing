#!/usr/bin/env python3
"""Freeze selected research evidence and prepare an isolated-index snapshot commit; never push."""
import hashlib,json,os,re,stat,subprocess,time
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];D=ROOT/'research/dac_v14_20261112'
BRANCH='refs/heads/research/dac-snapshot-20261113';PARENT='7b2834743007b36ce5890320e15a0ffa7dea1eb3'
STAMP=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
SCRATCH=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/publication_snapshots')/STAMP
SCRATCH.mkdir(parents=True,exist_ok=False);PAYLOAD=SCRATCH/'payload';PAYLOAD.mkdir()
def digest(data):return hashlib.sha256(data).hexdigest()
def run(args,*,env=None,input=None):
 r=subprocess.run(args,cwd=ROOT,env=env,input=input,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 if r.returncode:raise RuntimeError(r.stderr.decode(errors='replace'))
 return r.stdout
def git(*args,**kwargs):return run(['git',*args],**kwargs)
def write(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
head=git('rev-parse','HEAD').decode().strip();index=Path(git('rev-parse','--git-path','index').decode().strip());index=index if index.is_absolute() else ROOT/index
index_hash=digest(index.read_bytes());index_entries=digest(git('ls-files','--stage','-z'))
assert git('rev-parse','--verify',BRANCH).decode().strip()==PARENT
remote=git('ls-remote','--heads','origin',BRANCH).decode().strip().split()[0];assert remote==PARENT,'Remote advanced; reconcile instead of force pushing'
old=json.loads((ROOT/'docs/github_progress_manifest_20261114.json').read_text());excluded={ROOT/p for p in old['excluded_server_directory_roots']}
excluded.discard(D/'paper_snapshots')
allowed={'.py','.json','.csv','.txt','.md','.tex','.bib','.cls','.patch','.cpp','.h','.hpp','.tpp','.sh','.tcl','.diff','.pdf','.png','.svg','.log','.toml','.yaml','.yml'}
mandatory={
 'README.md','docs/GitHub_progress_20261115.md','docs/github_progress_status_20261115.json',
 'research/dac_v14_20261112/CURRENT_STATUS.md','research/dac_v14_20261112/CURRENT_STATUS.json',
 'research/dac_v14_20261112/multiobjective_partial_owner_01/points.json',
 'research/dac_v14_20261112/multiobjective_additional_circuits_01/points.json',
 'research/dac_v14_20261112/multiobjective_closed_R1_native_01/points.json',
 'research/dac_v14_20261112/paper_snapshots/current_R1_native_closure_20261115/build/current_repair_main.pdf',
 'research/dac_v14_20261112/paper/current_repair_main.tex',
 'research/dac_v14_20261112/R1_native_closure_paper_binding_01.json',
 'research/dac_v14_20261112/complete_BNN_joint_index_flow_01/comparison.json',
 'patches/snapshot_20261115_verified/manifest.json'}
secrets=[re.compile(rb'\bgh[pousr]_[A-Za-z0-9]{30,}'),re.compile(rb'github_pat_[A-Za-z0-9_]{30,}'),re.compile(rb'\bsk-(?:proj-)?[A-Za-z0-9_-]{40,}'),re.compile(rb'\bAKIA[A-Z0-9]{16}\b'),re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),re.compile(rb'https?://[^\s/:]+:[^\s/@]+@github\.com')]
selected={};omitted={};unstable={};excluded_dirs=[];candidates=set()
for subtree in ['docs','scripts','patches','paper','research/dac_v14_20261112']:
 start=ROOT/subtree
 for base,dirs,files in os.walk(start,followlinks=False):
  here=Path(base);keep=[]
  for name in dirs:
   path=here/name
   # Existing immutable paper snapshots include the PDF under build/.
   in_paper_snapshot=path.is_relative_to(D/'paper_snapshots')
   skip=path.is_symlink() or path in excluded or name in {'.git','__pycache__','.venv','.venv-lazagna','node_modules','bin','source','src'} or '_workspace_' in name or (name=='build' and not in_paper_snapshot) or name.startswith('epoch_')
   if skip:excluded_dirs.append(str(path.relative_to(ROOT)))
   else:keep.append(name)
  dirs[:]=keep
  for name in files:
   path=here/name;relative=str(path.relative_to(ROOT))
   if path.is_symlink() or '\n' in relative or name.startswith('.env') or path.suffix.lower() not in allowed:continue
   if name.startswith('github_progress_manifest_20261115') or name.startswith('github_progress_local_commit_20261115') or name.startswith('github_progress_publication_receipt_20261115'):continue
   size=path.stat().st_size
   limit=512*1024 if path.suffix=='.log' else 2*1024*1024
   if size>limit and relative not in mandatory:
    omitted[relative]=dict(bytes=size,reason='Large raw/evidence artifact retained on server; existing parent history preserved')
    continue
   candidates.add(relative)
for name in ['README.md','.gitignore','requirements.txt','pyproject.toml']:
 if (ROOT/name).exists():candidates.add(name)
candidates.update(mandatory)
for number,relative in enumerate(sorted(candidates),1):
 source=ROOT/relative
 if not source.is_file() or source.is_symlink():
  if relative in mandatory:raise RuntimeError('Missing mandatory publication artifact: '+relative)
  continue
 data=None
 for attempt in range(3):
  try:
   before=source.stat();value=source.read_bytes();after=source.stat()
   if (before.st_ino,before.st_size,before.st_mtime_ns,before.st_ctime_ns)==(after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns) and len(value)==after.st_size:data=value;break
  except FileNotFoundError:pass
 if data is None:
  unstable[relative]='Changed during stable read; active trial not modified'
  if relative in mandatory:raise RuntimeError('Mandatory publication artifact unstable: '+relative)
  continue
 if any(pattern.search(data) for pattern in secrets):
  omitted[relative]=dict(bytes=len(data),reason='Credential-pattern match requires separate review; contents not exported')
  if relative in mandatory:raise RuntimeError('Credential pattern in required artifact; do not publish')
  continue
 if source.suffix=='.json':
  try:json.loads(data)
  except (json.JSONDecodeError,UnicodeDecodeError):
   unstable[relative]='Incomplete/non-JSON file at capture; not exported'
   if relative in mandatory:raise
   continue
 target=PAYLOAD/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
 mode='100755' if before.st_mode&0o111 else '100644'
 selected[relative]=dict(bytes=len(data),sha256=digest(data),git_blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),mode=mode,source_mtime_ns=before.st_mtime_ns)
 if number%5000==0:print(json.dumps({'frozen':number,'candidates':len(candidates)}),flush=True)
assert mandatory<=selected.keys()
manifest=dict(status='immutable_content_snapshot',captured_at_utc=datetime.now(timezone.utc).isoformat(),repository='GRYYYYYYY/3D_FPGA_routing',branch=BRANCH.removeprefix('refs/heads/'),expected_parent=PARENT,authorization='Explicit user request to push completed experiments, conclusions and ongoing experiment descriptions; prior public manuscript/evidence scope preserved.',selected_files=selected,selected_count_including_manifest=len(selected)+1,payload_bytes_excluding_manifest=sum(r['bytes'] for r in selected.values()),omitted_large_or_sensitive_files=omitted,excluded_server_directory_roots=sorted(set(excluded_dirs)),unstable_or_incomplete_files=unstable,raw_data_backup_complete=False,live_trials_not_modified=True,research_complete=False,qualification='Per-file stable frozen copies; completed evidence remains sealed, active status is only a time-stamped observation. Parent tree is preserved and selected current files overlay it. Raw RRG/routes/STA/cache/binary/build artifacts remain on server. Manifest does not hash itself recursively; its committed blob and SHA256 are recorded in local publication receipt. No remote push is performed by this preparer.')
manifest_path=ROOT/'docs/github_progress_manifest_20261115.json';write(manifest_path,manifest);manifest_rel=str(manifest_path.relative_to(ROOT));target=PAYLOAD/manifest_rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(manifest_path.read_bytes());data=target.read_bytes()
selected_with_manifest=dict(selected);selected_with_manifest[manifest_rel]=dict(bytes=len(data),sha256=digest(data),git_blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest(),mode='100644')
env=dict(os.environ,GIT_INDEX_FILE=str(SCRATCH/'index'),GIT_TERMINAL_PROMPT='0')
git('-c','core.splitIndex=false','read-tree',PARENT,env=env)
ordered=sorted(selected_with_manifest);input_paths=''.join(str(PAYLOAD/relative)+'\n' for relative in ordered).encode()
blobs=git('hash-object','-w','--no-filters','--stdin-paths',env=env,input=input_paths).decode().splitlines();assert len(blobs)==len(ordered)
assert all(blob==selected_with_manifest[p]['git_blob'] for p,blob in zip(ordered,blobs))
entries=b''.join((selected_with_manifest[p]['mode']+' '+blob+'\t'+p+'\0').encode() for p,blob in zip(ordered,blobs))
git('-c','core.splitIndex=false','update-index','-z','--index-info',env=env,input=entries)
staged=git('ls-files','--stage','-z',env=env).split(b'\0');mapping={}
for line in staged:
 if not line:continue
 meta,path=line.split(b'\t',1);mode,blob,stage=meta.decode().split();mapping[path.decode()]=(mode,blob,stage)
assert all(mapping[p]==(m['mode'],m['git_blob'],'0') for p,m in selected_with_manifest.items())
tree=git('write-tree',env=env).decode().strip()
message='Publish verified routing progress, completed controls and active experiments\n\nPreserve C221 six-page manuscript, current592-record named archive, completed native/domain controls, mixed circuit-transfer outcomes, owner-scope evidence, full BNN cost and single-pass-index comparison, later budget/strict/combined-engineering receipts, and verified ongoing queue state. Export private source overlays with exact build identities. Raw artifacts stay on server; research remains active.\n'
ident=subprocess.run(['git','var','GIT_AUTHOR_IDENT'],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
if ident.returncode:env.update(GIT_AUTHOR_NAME='Codex',GIT_AUTHOR_EMAIL='codex@openai.com',GIT_COMMITTER_NAME='Codex',GIT_COMMITTER_EMAIL='codex@openai.com')
commit=git('commit-tree',tree,'-p',PARENT,env=env,input=message.encode()).decode().strip()
assert git('rev-parse',commit+'^').decode().strip()==PARENT
assert git('rev-parse','HEAD').decode().strip()==head
assert digest(git('ls-files','--stage','-z'))==index_entries
assert digest(index.read_bytes())==index_hash
changed=git('diff-tree','--no-commit-id','--name-only','-r',PARENT,commit).decode().splitlines()
receipt=dict(passed=True,status='local_snapshot_commit_verified_not_yet_pushed',branch=BRANCH,commit=commit,parent=PARENT,tree=tree,selected_files=len(selected_with_manifest),selected_payload_bytes=sum(v['bytes'] for v in selected_with_manifest.values()),changed_files=len(changed),staged_entries_match_all_frozen_blob_ids=True,all_frozen_payloads_SHA256_recorded=True,live_HEAD_unchanged=True,live_index_unchanged=True,live_head=head,live_index_sha256=index_hash,raw_data_backup_complete=False,research_complete=False,manifest_sha256=digest(manifest_path.read_bytes()),scratch=str(SCRATCH),prepared_at_utc=datetime.now(timezone.utc).isoformat())
write(ROOT/'docs/github_progress_local_commit_20261115.json',receipt);write(SCRATCH/'receipt.json',receipt)
print(json.dumps(receipt,ensure_ascii=False),flush=True)
