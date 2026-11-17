"""Read the previously selected GEMM bytes once, reusing existing hash/layout readers."""
import ast
import fcntl
import hashlib
import json
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

root = D / 'CLSTM_SB_input_preflight_01'


def main():
    started = time.monotonic()
    registration = read(root / 'registration.json')
    assert not (root / 'completion.json').exists(), 'Keep every actual attempt'
    rows = []
    with (D / 'critical_scope_runner.lock').open('r') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            assert all(sha(p) == h for p, h in registration['source_sha256'].items())
            chosen = registration['selected_input']
            assert chosen['id'] == 'clstm_sb_p0'
            assert chosen['not_previously_registered_complete_confirmation']
            for key in ['architecture', 'circuit', 'graph', 'packed', 'placement']:
                item = chosen['physical_files'][key]
                path = Path(item['path'])
                before = path.stat()
                identity = (before.st_dev, before.st_ino, before.st_size,
                            before.st_mtime_ns, before.st_ctime_ns)
                assert before.st_size == item['bytes']
                tick = time.monotonic()
                digest = sha(path)
                after = path.stat()
                assert (after.st_dev, after.st_ino, after.st_size,
                        after.st_mtime_ns, after.st_ctime_ns) == identity
                assert digest == chosen['declared_sha256'][key], key
                rows.append(dict(kind=key, path=str(path), sha256=digest,
                                 bytes=before.st_size, read_seconds=time.monotonic()-tick,
                                 source_metadata_unchanged=True))
                write(root / 'progress.json', dict(status='actual_input_byte_preflight',
                      completed_inputs=rows, elapsed_seconds=time.monotonic()-started))
            reader = D / 'verify_cp1r3_candidate_placement_01.py'
            syntax = ast.parse(reader.read_text())
            function = next(n for n in syntax.body
                            if isinstance(n, ast.FunctionDef) and n.name == 'coordinates')
            namespace = {}
            exec(compile(ast.Module(body=[function], type_ignores=[]), str(reader), 'exec'), namespace)
            coordinates = namespace['coordinates'](Path(chosen['physical_files']['placement']['path']))
            normalized = [[name, *coordinates[name]] for name in sorted(coordinates)]
            layout = dict(placed_blocks=len(coordinates),
                          coordinate_semantic_sha256=hashlib.sha256(json.dumps(normalized, separators=(',', ':')).encode()).hexdigest(),
                          min_coordinates=[min(v[i] for v in coordinates.values()) for i in range(4)],
                          max_coordinates=[max(v[i] for v in coordinates.values()) for i in range(4)],
                          source_reader=str(reader),
                          qualification='Actual block/x/y/subblock/layer records observed; not packing/graph legality or a new routed root.')
            assert all(sha(p) == h for p, h in registration['source_sha256'].items())
            write(root / 'completion.json', dict(passed=True,
                  status='input_bytes_and_actual_coordinates_preflight_passed',
                  physical_inputs=rows, actual_layout=layout,
                  complete_internal_preflight_seconds=time.monotonic()-started,
                  new_native_or_STA_calls=0, new_independent_confirmed_samples=0,
                  source_route_imported=False, source='known historical CLSTM-small on SB-only configuration; same circuit as Hybrid-O recovery, distinct physical configuration, no new architecture family',
                  new_architecture=False, full_input_or_route_admission=False,
                  source_sha256={str(root/'registration.json'): sha(root/'registration.json'), **registration['source_sha256']},
                  qualification='One read of each declared input for byte binding, plus existing coordinate parsing. Full graph/packing/placement compatibility, fresh legal roots, frozen next-version methods and matched full outputs remain required. No QoR selection or application-SDC claim.'))
        except BaseException as exc:
            write(root / 'completion.json', dict(passed=False, status='input_preflight_failed',
                  error=repr(exc), completed_inputs=rows,
                  complete_internal_preflight_seconds=time.monotonic()-started,
                  new_native_or_STA_calls=0, full_input_or_route_admission=False))
            raise


if __name__ == '__main__':
    main()
