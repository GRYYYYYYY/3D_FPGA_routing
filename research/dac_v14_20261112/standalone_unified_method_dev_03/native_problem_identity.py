"""Exact problem identity for a budget anchor, distinct from version/runtime provenance."""
from pathlib import Path
from retained_prefix_workflow import read, sha
from run_native_scope_policy_v4 import native_config


def problem_identity(run):
    """Require all real problem bytes and effective options; keep backend provenance separately."""
    run = Path(run).resolve()
    m = read(run / 'manifest.json')
    cmd = m['command']
    files = dict(architecture=Path(cmd[1]), circuit=Path(cmd[2]), graph=Path(cmd[cmd.index('--read_rr_graph') + 1]))
    values = {name: sha(path) for name, path in files.items()}
    for name, path in files.items():
        assert str(path) in m['shared_inputs'] and values[name] == m['shared_inputs'][str(path)]['sha256']
    for name in ['packed.net','placed.place']:
        assert sha(run/name)==m['outputs'][name]['sha256'], 'Packing/placement bytes no longer match their sealed output identity'
    values.update(packed=sha(run / 'packed.net'), placed=sha(run / 'placed.place'), effective_options=native_config(run))
    # Runtime libraries, copied observers and historical registration files remain
    # hashed provenance. They are not additional architectural/budget inputs.
    return values


def provenance(run):
    """Retain every backend/runtime/input identity without using it as a false equality key."""
    run = Path(run).resolve()
    m = read(run / 'manifest.json')
    return dict(manifest=str(run / 'manifest.json'), manifest_sha256=sha(run / 'manifest.json'),
                command=m['command'], shared_inputs=m['shared_inputs'])
