"""Exercise the two actual planner expressions without executing planner I/O."""
import ast
import datetime
import hashlib
import json
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
start = time.monotonic()
registration = json.loads((HERE / 'registration.json').read_text())
original = Path(registration['original_planner'])
old_text = original.read_text()
new_text = (HERE / 'plan_current_critical_group.py').read_text()
digest = lambda text: hashlib.sha256(text.encode()).hexdigest()
assert digest(old_text) == registration['original_sha256']
assert digest(new_text) == registration['development_planner_sha256']

def expressions(text):
    tree = ast.parse(text)
    compile(tree, '<planner-syntax-only>', 'exec')
    comparison = next(node.test for node in ast.walk(tree)
                      if isinstance(node, ast.Assert)
                      and 'setup_slack_s' in ast.unparse(node)
                      and 'donors' in ast.unparse(node))
    ordering = next(node.value for node in ast.walk(tree)
                    if isinstance(node, ast.Assign)
                    and any(isinstance(target, ast.Name) and target.id == 'ordered'
                            for target in node.targets))
    return tuple(compile(ast.Expression(node), '<actual-planner-expression>', 'eval')
                 for node in [comparison, ordering])

old_compare, old_order = expressions(old_text)
new_compare, new_order = expressions(new_text)

def outcome(code, environment):
    try:
        return dict(value=eval(code, dict(environment)), error=None)
    except (TypeError, ValueError):
        return dict(value=None, error=True)

rows = []
cases = [
    ('legacy_finite_eligible', [-5e-9], True, True),
    ('legacy_finite_worse', [-7e-9], False, True),
    ('legacy_finite_tie', [-6e-9], False, True),
    ('legacy_multiple_eligible', [-5e-9, -1e-9], True, True),
    ('legacy_one_ineligible', [-5e-9, -7e-9], False, True),
    ('legacy_numeric_infinity', [float('inf')], True, True),
    ('legacy_numeric_negative_infinity', [float('-inf')], False, True),
    ('legacy_numeric_nan_rejected', [float('nan')], False, True),
    ('legacy_empty_donors', [], True, True),
    ('numeric_string', ['-5e-9'], True, False),
    ('positive_infinity_string', ['inf'], True, False),
    ('negative_infinity_string', ['-inf'], False, False),
    ('nan_string_donor_rejected', ['nan'], False, False),
    ('none_donor_fails_closed', [None], 'error', False),
    ('unknown_string_fails_closed', ['unconstrained'], 'error', False),
    ('object_donor_fails_closed', [{}], 'error', False),
    ('one_unknown_donor_fails_closed', [-5e-9, 'bad'], 'error', False),
]
for name, values, expected, legacy_equal in cases:
    sta = {(100, i): dict(setup_slack_s=value) for i, value in enumerate(values)}
    environment = dict(sta=sta, donors=set(sta), cone=dict(worst_slack_s=-6e-9))
    old, new = outcome(old_compare, environment), outcome(new_compare, environment)
    if expected == 'error':
        assert new['error'] is True, (name, new)
    else:
        assert new['error'] is None and new['value'] is expected, (name, new)
    if legacy_equal:
        assert old == new, (name, old, new)
    rows.append(dict(name=name, passed=True, legacy_equivalent=legacy_equal,
                     original=old, development=new))

sta = {(100, 0): dict(setup_slack_s=-5e-9)}
environment = dict(sta=sta, donors=set(sta), cone=dict(worst_slack_s='-6e-9'))
assert outcome(new_compare, environment) == dict(value=True, error=None)
rows.append(dict(name='numeric_string_cutoff', passed=True))

def order_case(name, values, expected_indices, legacy_equal=False):
    keys = [(100, i) for i in range(len(values))]
    environment = dict(sta={key: dict(setup_slack_s=value)
                            for key, value in zip(keys, values)},
                       chosen=set(keys), pins=set(keys) | {(200, 7)})
    expected = [keys[i] for i in expected_indices] + [(200, 7)]
    new = outcome(new_order, environment)
    assert new == dict(value=expected, error=None), (name, new)
    if legacy_equal:
        assert outcome(old_order, environment) == new
    rows.append(dict(name=name, passed=True, legacy_equivalent=legacy_equal))

order_case('finite_order_and_tie_break_unchanged', [-1e-9, -4e-9, -4e-9],
           [1, 2, 0], legacy_equal=True)
order_case('numeric_string_order_not_lexical', ['10e-9', '2e-9', '1e-9'], [2, 1, 0])
order_case('mixed_numeric_and_infinite_order', [float('inf'), '-4e-9', -2e-9], [1, 2, 0])
environment = dict(sta={(100, 0): dict(setup_slack_s='bad')},
                   chosen={(100, 0)}, pins={(100, 0)})
assert outcome(new_order, environment)['error'] is True
rows.append(dict(name='malformed_target_order_fails_closed', passed=True))
assert digest(original.read_text()) == registration['original_sha256']
result = dict(observed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              passed=True, tests=len(rows), rows=rows,
              complete_validation_seconds=time.monotonic() - start,
              original_frozen_planner_unchanged=True,
              tested_actual_changed_AST_expressions=True,
              installed_in_running_or_queued_code=False,
              native_calls=0, STA_calls=0, graph_or_raw_vector_reads=0,
              actual_failing_serialized_token_checked=False,
              actual_full_planner_replay_executed=False,
              quality_admission=False,
              qualification='Expression and compatibility guards only. Invalid/NaN donor values produce no positive strict comparison. These checks do not establish that the actual failed donor is a supported numeric string, or that the full planner/candidate/controller succeeds.')
(HERE / 'validation.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({key: value for key, value in result.items() if key != 'rows'}))
