import json
from pathlib import Path
from retained_prefix_workflow import read,sha
def native_config(run):
    cmd = list(read(run / 'manifest.json')['command'])
    cmd[0] = 'FROZEN_NATIVE_OBJECTIVE_BINARY'
    if '--route' in cmd:
        cmd.remove('--route')
    assert '--analysis' in cmd
    cmd[cmd.index('--timing_report_npaths') + 1] = '10'
    if '--verify_route_file_switch_id' not in cmd:
        cmd += ['--verify_route_file_switch_id', 'on']
    else:
        cmd[cmd.index('--verify_route_file_switch_id') + 1] = 'on'
    for (option, name) in [('--net_file', 'PACKED'), ('--place_file', 'PLACED'), ('--route_file', 'ROUTE')]:
        cmd[cmd.index(option) + 1] = name
    return json.dumps(cmd)

def run_dir(state):
    return Path(read(state / 'completion.json')['run'])

def input_identity(run):
    manifest = read(run / 'manifest.json')
    shared = sorted(((Path(p).name, v['sha256']) for (p, v) in manifest['shared_inputs'].items() if not (Path(p).name == 'registration.json' and str(p) not in manifest['command'])))
    return [sha(run / 'packed.net'), sha(run / 'placed.place'), shared]
