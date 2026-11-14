"""Acceptance controls for hidden regressions, plateaus and fixed identities."""
import copy
import math
from endpoint_timing_policy import decide

base = dict(cpd_s=6e-9, endpoint_ids=[(1, 2, 'endpoint')], constraints_sha256='fixed',
            setup={'a': -6e-9, 'b': -5e-9}, hold={'a': 1e-9, 'b': 0.})
plateau = copy.deepcopy(base)
plateau['setup']['b'] = -4e-9
assert not decide('strict', base, plateau, True)['accepted']
assert decide('endpoint_vector', base, plateau, True)['accepted']
assert not decide('endpoint_vector', base, base, True)['accepted']
assert not decide('endpoint_vector', base, plateau, False)['accepted']
assert not decide('endpoint_vector', base, plateau, True, True)['accepted']
for field, key in [('cpd_s', None), ('setup', 'a'), ('hold', 'b')]:
    bad = copy.deepcopy(plateau)
    if key is None:
        bad[field] = math.nextafter(base[field], math.inf)
    else:
        bad[field][key] = math.nextafter(base[field][key], -math.inf)
    assert not decide('endpoint_vector', base, bad, True)['accepted'], field
good = copy.deepcopy(base)
good['cpd_s'] -= 1e-10
good['setup']['a'] += 1e-10
assert decide('strict', base, good, True)['accepted']
assert decide('endpoint_vector', base, good, True)['accepted']
trade = copy.deepcopy(good)
trade['setup']['b'] -= 1e-10
assert decide('strict', base, trade, True)['accepted']
assert not decide('endpoint_vector', base, trade, True)['accepted']
for mutation in ['constraint', 'endpoint', 'domains', 'nonfinite']:
    bad = copy.deepcopy(plateau)
    if mutation == 'constraint': bad['constraints_sha256'] = 'different'
    if mutation == 'endpoint': bad['endpoint_ids'].append((3, 4, 'new'))
    if mutation == 'domains': bad['setup']['extra_domain'] = 0.
    if mutation == 'nonfinite': bad['setup']['a'] = 'nan'
    assert not decide('endpoint_vector', base, bad, True)['accepted']
print(dict(passed=True, scope='Strict and Pareto branch differences; even one representable-number regression rejected; fixed constraints/endpoints/domains; invalid/repeated/unknown states rejected.'))
