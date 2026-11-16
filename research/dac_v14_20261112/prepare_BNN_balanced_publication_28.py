"""Prepare a selected evidence tree without changing HEAD, index or live jobs."""
import hashlib
import subprocess
import tempfile
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

repo = D.parents[1]


def git(*args):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=repo).decode().strip()


parent = git('rev-parse', 'origin/research/dac-snapshot-20261113')
assert parent == '578bc64877312e6c3d405ce1755ba0880b2fc5da'
for ref in ['9734eee', '279bdb4']:
    subprocess.run(['git', '-c', 'gc.auto=0', 'merge-base', '--is-ancestor', ref, parent], cwd=repo, check=True)
r = read(D / 'BNN_timing03_balanced_receipt_01/completion.json')
assert r['passed'] and r['paired_cost_observation_available'] and r['independent_new_inputs'] == 0
assert all(sha(p) == h for p, h in r['source_sha256'].items())
c = read(D / 'BNN_timing03_balanced_claim_binding_01.json')
assert all(sha(p) == h for p, h in c['source_sha256'].items())
priority = read(D / 'confirmation_priority_handoff_02/plan.json')
assert all(sha(p) == h for p, h in priority['protected_source_sha256'].items())
files = [repo / n for n in ['README.md', 'docs/GitHub_BNN_timing03_balanced_20261116.md',
         'docs/github_BNN_timing03_domain1_publication_receipt_20261116.json',
         'docs/github_BNN_timing03_domain1_readback_20261116.json']]
files += [D / n for n in ['CURRENT_STATUS.json', 'CURRENT_STATUS.md', 'refresh_current_status_20261114.py',
          'render_current_status_md_v1.py', 'snapshot_BNN_timing03_balanced_receipt_01.py',
          'seal_BNN_timing03_balanced_claims_01.py', 'BNN_timing03_balanced_claim_binding_01.json',
          'prepare_BNN_balanced_publication_28.py', 'confirmation_release_cp1r3_01/completion.json']]
files += [p for p in (D / 'BNN_timing03_balanced_receipt_01').rglob('*') if p.is_file()]
batch = D / 'BNN_interleaved_timing_03'
files += [batch / 'comparison.json', *batch.glob('pair_*_final_endpoints.json')]
for name in r['registered_order']:
    case = batch / name
    files += [case / n for n in ['completion.json', 'same_role_equivalence.json', 'own_root_endpoints.json']]
for q in [batch / 'queue', *[Path(s['new_queue']) for s in priority['stages']]]:
    files += [q / n for n in ['registration.json', 'status.json', 'completion.json'] if (q / n).exists()]
cohort = D / 'cp1r3_distinct_input_cohort_01'
files += [p for p in cohort.iterdir() if p.is_file() and p.suffix == '.json']
scratch = Path(tempfile.mkdtemp(prefix='BNN-timing03-balanced-',
    dir='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/publication_snapshots'))
known = {row.split()[2] for row in git('ls-tree', '-r', parent).splitlines()}
entries, manifest, reused = [], [], 0
for source in sorted(set(files)):
    assert source.stat().st_size < 4 * 1024**2, 'Large raw data is retained locally'
    data = source.read_bytes()
    relative = str(source.relative_to(repo))
    target = scratch / 'files' / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
    entry = dict(path=relative, mode='100644', type='blob')
    if blob in known:
        entry['sha'] = blob
        reused += 1
    else:
        entry['content'] = data.decode()
    entries.append(entry)
    manifest.append(dict(path=relative, git_blob=blob, sha256=sha(target), bytes=len(data)))
write(scratch / 'payload.json', dict(parent=parent, base_tree=git('rev-parse', parent + '^{tree}'), entries=entries))
info = dict(parent=parent, base_tree=git('rev-parse', parent + '^{tree}'), scratch=str(scratch),
    selected_files=len(manifest), payload_bytes=sum(x['bytes'] for x in manifest),
    reused_existing_blobs=reused, live_head=git('rev-parse', 'HEAD'),
    live_index_sha256=sha(repo / '.git/index'),
    remote_main=git('ls-remote', 'origin', 'refs/heads/main').split()[0])
write(repo / 'docs/github_BNN_timing03_balanced_prepared_20261116.json', info)
write(repo / 'docs/github_BNN_timing03_balanced_manifest_20261116.json', manifest)
print(dict(info, payload_json_chars=len((scratch / 'payload.json').read_text())))
