"""Replay the two actual failed planners with the registered isolated numeric fix."""
import ast
import fcntl
import gc
import json
import os
import runpy
import subprocess
import sys
import time
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

root = D / 'planner_numeric_slack_replay_02'


def worker(arm):
    registration = read(root / 'registration.json')
    case = registration['roles'][arm]
    planner = Path(registration['development_planner'])
    original = Path(registration['original_planner'])
    assert sha(planner) == registration['development_planner_sha256']
    assert sha(original) == registration['original_planner_sha256']
    old_tree, new_tree = ast.parse(original.read_text()), ast.parse(planner.read_text())
    old_assert = next(n for n in ast.walk(old_tree) if isinstance(n, ast.Assert)
                      and n.lineno == 45)
    new_assert = next(n for n in ast.walk(new_tree) if isinstance(n, ast.Assert)
                      and n.lineno == 45)
    old_expression = compile(ast.Expression(body=old_assert.test), str(original), 'eval')
    new_expression = compile(ast.Expression(body=new_assert.test), str(planner), 'eval')
    observed = []

    def trace(frame, event, arg):
        if frame.f_code.co_filename != str(planner) or frame.f_code.co_name != '<module>':
            return None
        if event == 'line' and frame.f_lineno == new_assert.lineno:
            values = frame.f_locals
            environment = {k: values[k] for k in ['sta', 'donors', 'cone']}
            tokens = []
            for net, pin in sorted(values['donors']):
                value = values['sta'][net, pin]['setup_slack_s']
                if isinstance(value, str):
                    tokens.append(dict(net=net, pin=pin, serialized_slack=value,
                                       normalized_slack_repr=repr(float(value))))
            old_error, old_value = None, None
            try:
                old_value = eval(old_expression, dict(environment))
            except TypeError as error:
                old_error = repr(error)
            observed.append(dict(target=list(values['target']), donors=len(values['donors']),
                                 cutoff=values['cone']['worst_slack_s'],
                                 actual_string_donors=tokens,
                                 original_expression_value=old_value,
                                 original_expression_error=old_error,
                                 development_expression_value=eval(new_expression, dict(environment))))
        return trace

    sys.path.insert(0, str(original.parent))
    sys.modules.pop('retained_prefix_workflow', None)
    import importlib
    runtime_helpers = importlib.import_module('retained_prefix_workflow')
    assert Path(runtime_helpers.__file__).resolve() == original.parent/'retained_prefix_workflow.py'
    assert runtime_helpers.D == original.parent
    sys.argv = [str(planner), *case['arguments']]
    sys.settrace(trace)
    try:
        scope = runpy.run_path(str(planner), run_name='__main__')
        del scope
        gc.collect()
    finally:
        sys.settrace(None)
        write(root / arm / 'actual_token_observations.json', dict(
            observed=observed, diagnostic_line_trace=True, new_native_or_STA_calls=0,
            qualification='Actual original donor sets and serialized values; tracing is diagnostic overhead, not complete-method timing.'))
    assert observed and any(x['original_expression_error'] for x in observed)
    assert all(x['development_expression_value'] for x in observed)


def main():
    registration = read(root / 'registration.json')
    assert not (root / 'completion.json').exists(), 'Preserve attempts'
    started = time.monotonic()
    roles = []
    with (D / 'critical_scope_runner.lock').open('r') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert all(sha(p) == h for p, h in registration['source_sha256'].items())
        for arm, case in registration['roles'].items():
            output = root / arm
            output.mkdir()
            command = [sys.executable, '-B', str(Path(__file__).resolve()), '--worker', arm]
            tick = time.monotonic()
            with (output / 'stdout.log').open('x') as log:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT,
                                        env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, timeout=900)
            row = dict(arm=arm, returncode=result.returncode,
                       complete_replay_command_seconds=time.monotonic()-tick,
                       native_or_STA_calls=0)
            if result.returncode == 0:
                plan = read(output / 'proposal/plan.json')
                new_bindings = plan['source_sha256']
                old_bindings = read(case['original_failed_proposal_registration'])['source_sha256']
                original_path = registration['original_planner']
                development_path = registration['development_planner']
                assert {p:h for p,h in old_bindings.items() if p != original_path} == {
                    p:h for p,h in new_bindings.items() if p != development_path}
                assert sha(case['original_failed_log']) == case['original_failed_log_sha256']
                row.update(passed=plan['passed'], selection=plan['selection'],
                           planned_connections=len(plan['ordered_queries']),
                           exact_original_nonplanner_input_bindings=True,
                           actual_tokens=str(output/'actual_token_observations.json'))
            else:
                row.update(passed=False, status='new_development_replay_failed_original_preserved')
            roles.append(row)
            write(root / 'progress.json', dict(roles=roles))
        assert all(sha(p) == h for p, h in registration['source_sha256'].items())
        write(root / 'completion.json', dict(passed=all(x['passed'] for x in roles), roles=roles,
              complete_replay_scope_seconds=time.monotonic()-started,
              new_native_or_STA_calls=0, original_failures_rewritten=False,
              installed_in_frozen_runtime=False, full_method_admitted=False,
              source_sha256={str(root/'registration.json'):sha(root/'registration.json'), **registration['source_sha256']},
              qualification='Two actual full planner replays with diagnostic line tracing and original inputs/rules. No native transaction, candidate, acceptance, full controller recovery or new independent confirmation is executed.'))
        assert all(x['passed'] for x in roles), 'Diagnostic replay failed; retain original and new failures'


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--worker':
        worker(sys.argv[2])
    else:
        main()
