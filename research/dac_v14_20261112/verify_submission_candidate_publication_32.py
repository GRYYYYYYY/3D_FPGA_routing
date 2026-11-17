"""Verify the actual remote increment and preservation of live/frozen work."""
import hashlib
import subprocess
from datetime import datetime,timezone
from retained_prefix_workflow import D,read,write,sha

repo=D.parents[1]
def git(*args):
    return subprocess.check_output(['git','-c','gc.auto=0',*args],cwd=repo).decode().strip()

prepared=read(repo/'docs/github_submission_candidate_prepared_20261117.json')
manifest=read(repo/'docs/github_submission_candidate_manifest_20261117.json')
plugin=read(repo/'docs/github_submission_candidate_plugin_proof_20261117.json')
commit=plugin['commit'];tree=plugin['tree']
assert plugin['passed'] and plugin['commit']==commit and plugin['report_plugin_readback_exact']
assert git('rev-parse','origin/research/dac-snapshot-20261113')==commit
assert git('ls-remote','origin','refs/heads/research/dac-snapshot-20261113').split()[0]==commit
assert git('rev-parse',commit+'^{tree}')==tree and git('rev-parse',commit+'^')==prepared['parent']
actual={}
for row in git('ls-tree','-r',commit).splitlines():
    meta,path=row.split('\t',1);actual[path]=meta.split()[2]
assert all(actual.get(item['path'])==item['git_blob'] for item in manifest)
request=''.join(item['git_blob']+'\n' for item in manifest).encode()
stream=subprocess.check_output(['git','-c','gc.auto=0','cat-file','--batch'],input=request,cwd=repo)
cursor=0
for item in manifest:
    end=stream.index(b'\n',cursor);header=stream[cursor:end].split();cursor=end+1
    assert header[:2]==[item['git_blob'].encode(),b'blob'];size=int(header[2]);data=stream[cursor:cursor+size]
    assert size==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']
    cursor+=size;assert stream[cursor:cursor+1]==b'\n';cursor+=1
assert cursor==len(stream)
assert git('rev-parse','HEAD')==prepared['live_head'] and sha(repo/'.git/index')==prepared['live_index_sha256']
assert git('ls-remote','origin','refs/heads/main').split()[0]==prepared['remote_main']
for ref in ['9734eee','279bdb4']:
    subprocess.run(['git','-c','gc.auto=0','merge-base','--is-ancestor',ref,commit],cwd=repo,check=True)
assert all(sha(p)==h for p,h in read(D/'confirmation_priority_handoff_02/plan.json')['protected_source_sha256'].items())
claim=read(D/'CP1r3_lstm_native_failure_claim_binding_01.json')
assert claim['quality'] is None and not claim['paper_benefit_claims_authorized']
assert all(sha(p)==h for p,h in claim['source_sha256'].items())
assert read(D/'cp1r3_distinct_input_cohort_01/lstm_results.json')['native']['status']=='execution_or_verification_failed'
candidate=read(D/'submission_candidate_01/verification.json')
assert candidate['passed'] and candidate['pages']==6
assert all(sha(p)==h for p,h in candidate['source_sha256'].items())
assert all(sha(p)==h for p,h in read(D/'confirmation_priority_handoff_03/plan.json')['protected_source_sha256'].items())
import sys
sys.path.insert(0,str(repo/'paper/dac2027/tools/pdf_review'))
import pymupdf
pdf=subprocess.check_output(['git','cat-file','blob',commit+':research/dac_v14_20261112/submission_candidate_01/build/main.pdf'],cwd=repo)
assert len(pymupdf.open(stream=pdf,filetype='pdf'))==6
for snapshot in ['current_balanced_cost_20261116','current_sharing_prior_art_20261116']:
    for suffix in ['current_repair_main.tex','build/current_repair_main.pdf']:
        relative='research/dac_v14_20261112/paper_snapshots/'+snapshot+'/'+suffix
        assert actual[relative]==git('rev-parse',prepared['parent']+':'+relative)
receipt=dict(passed=True,published_at=datetime.now(timezone.utc).isoformat(),repository='GRYYYYYYY/3D_FPGA_routing',
    branch='research/dac-snapshot-20261113',commit=commit,tree=tree,parent=prepared['parent'],
    files=len(manifest),bytes=sum(x['bytes'] for x in manifest),all_selected_blobs_verified=True,
    all_selected_published_bytes_SHA256_verified=True,report_plugin_readback_exact=True,
    live_HEAD_unchanged=True,live_index_unchanged=True,remote_main_unchanged=True,force=False,
    live_experiment_protected_sources_unchanged=True,paper18_and_paper19_source_PDF_unchanged=True,
    original_native_failure_and_quality_null_preserved=True,supplementary_verifier_executed=False,
    supplementary_verifier_queued=True,submission_candidate_pages=6,submission_candidate_verified=True,new_native_or_STA_calls=0,new_complete_verified_pairs=0,
    goal_status='active',public_refs_preserved=['9734eee','279bdb4'],report=plugin['report'],scratch=prepared['scratch'],
    qualification='Published an independently closed six-page submission candidate from paper19 verified evidence, with fixed problem/method/contribution boundaries, unchanged numerical table and references, precise remaining-experiment claim dependencies, role status and conditional ETA. Priority03 places supplementary verification immediately after CP1r3 without changing active experiments. Original failures and incomplete-result admission limits remain. Publication is not research completion.')
write(repo/'docs/github_submission_candidate_publication_receipt_20261117.json',receipt)
write(repo/'docs/github_submission_candidate_readback_20261117.json',dict(passed=True,commit=commit,
    selected_files=len(manifest),all_selected_blobs_verified=True,all_selected_bytes_SHA256_verified=True,
    report_plugin_readback_exact=True,HEAD_index_main_preserved=True,protected_sources_preserved=True,
    original_failure_preserved=True,paper18_and_paper19_unchanged=True))
print(dict(passed=True,commit=commit,selected_files=len(manifest),all_bytes_SHA256_verified=True,
           HEAD_index_main_preserved=True,papers_and_original_failure_preserved=True,goal='active'))
