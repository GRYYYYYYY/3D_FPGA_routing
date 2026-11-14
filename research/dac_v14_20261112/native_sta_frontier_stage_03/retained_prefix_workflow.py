"""Shared admission and identity helpers for the retained-prefix diagnostic."""
from pathlib import Path
import hashlib
import json
import re

D = Path(__file__).resolve().parent


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def require_formal_terminal():
    marker = D / 'formal_timing_active.json'
    if not marker.exists():
        raise RuntimeError('Expected formal timing identity is absent; inspect authoritative state first')
    state = read(marker)
    proc = Path('/proc') / str(state['pid']) / 'stat'
    if proc.exists() and proc.read_text().split(') ', 1)[1].split()[19] == state['start_ticks']:
        raise RuntimeError('Formal timing owner is live; heavy diagnostic work must wait')
    batch = Path(state['out'])
    if not (batch / 'completion.json').exists() or not (batch / 'input_seal.json').exists():
        raise RuntimeError('Formal timing is unresolved; diagnose its terminal state before heavy work')
    assert read(batch / 'input_seal.json')['passed']


def normalized_command(command):
    result = list(command[1:])
    for option in ['--net_file', '--place_file', '--route_file']:
        result[result.index(option) + 1] = '<paired-private-file>'
    return result


def route_body(path):
    digest = hashlib.sha256()
    started = False
    with Path(path).open('rb') as stream:
        for line in stream:
            if line.startswith(b'Net '):
                started = True
            if started:
                digest.update(line)
    assert started
    return digest.hexdigest()


def original_records(lines, allowed_prefixes=None):
    # Physical delay-unit fields also end in "seconds" and must stay exact.
    elapsed_fields = {
        'H3D_INIT': ['init_seconds'],
        'H3D_PLAN': ['planning_seconds'],
        'H3D_FEEDBACK': ['check_seconds'],
        'H3D_REACH_PROFILE': ['seconds'],
        'H3D_PLAN_PROFILE': [name + '_seconds' for name in [
            'candidates', 'distance', 'eligibility', 'output', 'prior',
            'select', 'solve', 'source', 'table', 'total']],
    }
    result = []
    for line in lines:
        if not line.startswith('H3D_') or line.startswith('H3D_PREFIX_'):
            continue
        prefix = line.split()[0]
        if allowed_prefixes is not None and prefix not in allowed_prefixes:
            continue
        fields = elapsed_fields.get(prefix, [])
        if fields:
            line = re.sub(r'\b(' + '|'.join(fields) + r')=\S+', r'\1=<elapsed>', line)
        result.append(line)
    return result


def source_files():
    root = D / 'src'
    files = list((root / 'vpr/src/route').glob('h3d*'))
    files += [root / 'vpr/src/route' / name for name in [
        'connection_router.tpp', 'route_net.tpp', 'route_net.cpp', 'route_tree.h',
        'SerialNetlistRouter.tpp', 'route.cpp', 'route_common.cpp', 'route_common.h']]
    return {str(p.relative_to(root)): sha(p) for p in files if p.is_file()}
