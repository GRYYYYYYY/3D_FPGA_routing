"""Prepare paper19 and selected original evidence without staging the live tree."""
import base64
import hashlib
import subprocess
import tempfile
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

repo = D.parents[1]


def git(*args):
    return subprocess.check_output(['git', '-c', 'gc.auto=0', *args], cwd=repo).decode().strip()


parent = git('rev-parse', 'origin/research/dac-snapshot-20261113')
assert parent == 'd0c217dba874f4ab045685514b3a2608c42a1b3c'
for ref in ['9734eee', '279bdb4']:
    subprocess.run(['git', '-c', 'gc.auto=0', 'merge-base', '--is-ancestor', ref, parent], cwd=repo, check=True)
binding = read(D / 'balanced_cost_paper_binding_19.json')
assert binding['passed'] and binding['pages'] == 6 and binding['table_rows'] == 42
assert binding['new_independent_inputs'] == 0 and binding['prior_art_and_contribution_boundaries_unchanged']
assert all(sha(p) == h for p, h in binding['source_sha256'].items())
prefix = read(D / 'CP1r3_lstm_native_progress_01/completion.json')
assert prefix['passed'] and not prefix['complete_confirmation_passed']
assert all(sha(p) == h for p, h in prefix['source_sha256'].items())
priority = read(D / 'confirmation_priority_handoff_02/plan.json')
assert all(sha(p) == h for p, h in priority['protected_source_sha256'].items())
files = [repo / n for n in ['README.md', 'docs/GitHub_balanced_cost_paper_20261116.md',
    'docs/github_BNN_timing03_balanced_publication_receipt_20261116.json',
    'docs/github_BNN_timing03_balanced_readback_20261116.json']]
files += [D / n for n in ['CURRENT_STATUS.json', 'CURRENT_STATUS.md', 'refresh_current_status_20261114.py',
    'render_current_status_md_v1.py', 'update_balanced_cost_paper_19.py', 'seal_balanced_cost_paper_19.py',
    'balanced_cost_paper_binding_19.json', 'snapshot_CP1r3_lstm_native_progress_01.py',
    'prepare_balanced_cost_paper_publication_29.py', 'paper/current_repair_main.tex',
    'paper/current_repair_balanced_cost_19.tex', 'paper/data/evidence_v14_ledger.json']]
for directory in [D / 'balanced_cost_paper_evidence_19', D / 'CP1r3_lstm_native_progress_01']:
    files += [p for p in directory.rglob('*') if p.is_file()]
snapshot = Path(binding['snapshot'])
files += [p for p in snapshot.rglob('*') if p.is_file() and (p.suffix != '.png' or p.name == 'contact.png')]
build = D / 'paper/build_balanced_cost_19_r2'
files += [build / n for n in ['current_repair_balanced_cost_19.pdf', 'current_repair_balanced_cost_19.log',
    'compiler_stdout.log', 'build_receipt.json', 'render_receipt.json']]
for q in [D / 'BNN_interleaved_timing_03/queue', *[Path(s['new_queue']) for s in priority['stages']]]:
    files += [q / n for n in ['registration.json', 'status.json', 'completion.json'] if (q / n).exists()]
scratch = Path(tempfile.mkdtemp(prefix='balanced-cost-paper19-',
    dir='/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/publication_snapshots'))
known = {row.split()[2] for row in git('ls-tree', '-r', parent).splitlines()}
entries, manifest, binaries = [], [], {}
reused = 0
for source in sorted(set(files)):
    assert source.stat().st_size < 4 * 1024**2, 'Only selected proofs and publication assets'
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
        try:
            if source.suffix in ['.pdf', '.png', '.zip', '.gz']:
                raise UnicodeDecodeError('utf-8', data, 0, 1, 'binary publication asset')
            entry['content'] = data.decode('utf-8')
        except UnicodeDecodeError:
            entry['sha'] = blob
            binaries[blob] = dict(sha=blob, content=base64.b64encode(data).decode(), source=relative)
    entries.append(entry)
    manifest.append(dict(path=relative, git_blob=blob, sha256=sha(target), bytes=len(data)))
write(scratch / 'payload.json', dict(parent=parent, base_tree=git('rev-parse', parent + '^{tree}'),
    entries=entries, binary_uploads=list(binaries.values())))
info = dict(parent=parent, base_tree=git('rev-parse', parent + '^{tree}'), scratch=str(scratch),
    selected_files=len(manifest), payload_bytes=sum(x['bytes'] for x in manifest),
    reused_existing_blobs=reused, novel_binary_blobs=len(binaries), live_head=git('rev-parse', 'HEAD'),
    live_index_sha256=sha(repo / '.git/index'), remote_main=git('ls-remote', 'origin', 'refs/heads/main').split()[0])
write(repo / 'docs/github_balanced_cost_paper_prepared_20261116.json', info)
write(repo / 'docs/github_balanced_cost_paper_manifest_20261116.json', manifest)
print(dict(info, payload_json_chars=len((scratch / 'payload.json').read_text())))
