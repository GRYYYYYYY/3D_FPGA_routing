"""Close the existing elliptic packing/placement receipts; no native execution."""
import ast
import fcntl
import hashlib
import json
import subprocess
import time
from collections import Counter
from pathlib import Path
from lxml import etree
from retained_prefix_workflow import D, read, write, sha
from seed_census_analysis_pool_v2 import process_identity

ROOT = D / 'VTR_elliptic_input_01'


def reader(path, name):
    node = next(n for n in ast.parse(path.read_text()).body
                if isinstance(n, ast.FunctionDef) and n.name == name)
    namespace = dict(Path=Path, Counter=Counter, etree=etree, hashlib=hashlib)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), 'exec'), namespace)
    return namespace[name]


def main():
    started = time.monotonic()
    assert not (ROOT/'completion.json').exists()
    with (D/'critical_scope_runner.lock').open() as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        source = read(ROOT/'registration.json')
        selected = read(ROOT/'capacity_selection.json')
        place = ROOT/'place_01'
        registration = read(place/'registration.json')
        owner = read(place/'owner.json')
        actual = process_identity(owner['pid'])
        assert not actual or actual['start_ticks'] != owner['start_ticks'] or actual['state'] == 'Z'
        for role in ['pack_04', 'place_01']:
            root = ROOT/role
            terminal = read(root/'execution_completion.json')
            measured = read(root/'measurement/completion.json')
            supervised = read(root/'supervision.json')
            assert terminal['execution_ended'] and terminal['returncode'] == 0
            assert measured['passed'] and not measured['live_descendants_after_command_exit']
            assert supervised['passed'] and not supervised['residual_descendants']
            assert 'VPR succeeded' in (root/'measurement/stdout.log').read_text()
        source_bytes = subprocess.run(['git', '-C', str(D.parents[1]/'vendor/vtr'), 'show',
            source['source_commit']+':'+source['source_path']], check=True, capture_output=True).stdout
        assert hashlib.sha256(source_bytes).hexdigest() == source['actual_source_sha256']
        assert source_bytes == (ROOT/'inputs/elliptic.blif').read_bytes()
        assert sha(place/'registration.json') == owner['registration_sha256']
        assert all(sha(p) == h for p, h in registration['source_sha256'].items())
        assert sha(registration['binary']['path']) == registration['binary']['sha256']
        packed_reader = D.parents[1]/'scripts/run_flatland_pack_census.py'
        coordinate_reader = D.parents[1]/'scripts/validate_lazagna_vtr9_pilot.py'
        packed = reader(packed_reader, 'packed_summary')(place/'packed.net')
        assert packed == selected['actual_packed']
        coords = reader(coordinate_reader, 'placements')(place/'placed.place')
        block_names = [b.get('name') for b in etree.parse(str(place/'packed.net')).getroot().findall('block')]
        assert len(block_names) == len(set(block_names)) == len(coords) == 640
        assert set(block_names) == set(coords)
        assert len(set(coords.values())) == len(coords)
        assert all(0 <= v[0] < 40 and 0 <= v[1] < 40 and v[2] >= 0 and v[3] in [0, 1]
                   for v in coords.values())
        coordinate_sha = hashlib.sha256(json.dumps([[n, *coords[n]] for n in sorted(coords)],
            separators=(',', ':')).encode()).hexdigest()
        physical = dict(architecture=Path(selected['selected_fixture']['architecture']),
                        graph=Path(selected['selected_fixture']['graph']),
                        circuit=ROOT/'inputs/elliptic.blif', packed=place/'packed.net',
                        placement=place/'placed.place')
        # Graph was checked just above; reuse the observed digest rather than another full read.
        physical_rows = {k:dict(path=str(p), bytes=p.stat().st_size,
            sha256=registration['source_sha256'].get(str(p)) or sha(p)) for k,p in physical.items()}
        costs = []
        for name in ['pack', 'pack_02', 'pack_03', 'pack_04', 'place_01']:
            measured = read(ROOT/name/'measurement/completion.json')
            costs.append(dict(stage=name, complete_command_seconds=measured['complete_command_wall_seconds'],
                returncode=measured['returncode'], route_queries=0,
                classification='successful_upstream_preparation' if measured['returncode']==0 else 'preserved_preparation_failure'))
        files = [Path(__file__).resolve(), ROOT/'registration.json', ROOT/'capacity_selection.json',
                 packed_reader, coordinate_reader]
        for name in ['pack', 'pack_02', 'pack_03', 'pack_04', 'place_01']:
            files += [ROOT/name/'execution_completion.json', ROOT/name/'measurement/completion.json']
        files += [place/'registration.json', place/'input_byte_admission.json', place/'supervision.json',
                  place/'measurement/stdout.log']
        binding = {str(p):sha(p) for p in files}
        # Explicit derived adapter, not a fabricated historical execution manifest.
        provenance = dict(format='derived_upstream_receipts_v1', status='completed',
            command=registration['command'], outputs={
                'packed.net':physical_rows['packed'], 'placed.place':physical_rows['placement']},
            original_execution_receipts=[str(ROOT/n/'execution_completion.json') for n in ['pack_04','place_01']],
            source_sha256=binding, historical_manifest_rewritten=False,
            qualification='Derived packing/placement provenance for the existing frozen input contract. Actual commands, stdout, measurement and original failed preparation attempts remain intact. Not routing admission.')
        write(ROOT/'packing_provenance.json', provenance)
        write(ROOT/'completion.json', dict(passed=True, status='actual_upstream_input_preparation_verified',
            physical_files=physical_rows, actual_packed=packed,
            actual_layout=dict(placed_blocks=len(coords), coordinate_semantic_sha256=coordinate_sha,
                layer_block_counts=dict(Counter(v[3] for v in coords.values()))),
            original_owner_terminal_verified=True, source_bytes_equal_pinned_VTR_commit=True,
            actual_block_names_and_unique_coordinates_verified=True,
            costs=costs, complete_readonly_finalization_seconds=time.monotonic()-started,
            source_sha256={**binding, str(ROOT/'packing_provenance.json'):sha(ROOT/'packing_provenance.json')},
            new_native_or_STA_calls=0, route_quality_admitted=False,
            qualification='A distinct mapped sequential circuit and one fresh actual placement, on the existing Hybrid-O architecture family. No explicit application SDC, unseen-input or new-architecture claim. Packing/placement internal STA is upstream. Full initial routing, FULL/STA/physical audit and native/domain matching remain required.'))
        print(json.dumps(dict(passed=True, packed=packed, placed_blocks=len(coords), costs=costs)))


if __name__ == '__main__':
    main()
