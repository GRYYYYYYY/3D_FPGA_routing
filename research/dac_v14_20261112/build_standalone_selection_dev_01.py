"""Extract exact selection kernels and carry the full serial pool into a new package."""
import ast
import shutil
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha

source = D/'standalone_observation_dev_02'
out = D/'standalone_selection_dev_01'
assert not out.exists()
manifest = read(source/'artifact_manifest.json')
assert all(sha(source/n) == h for n,h in manifest['sha256'].items())
shutil.copytree(source, out, ignore=shutil.ignore_patterns('__pycache__'))
(out/'artifact_manifest.json').rename(out/'observation_artifact_manifest.json')
origins = {}
for name in ['current_sta_selector.py', 'current_resource_bundle_v2.py', 'seed_census_analysis_pool_v2.py']:
    shutil.copy2(D/name, out/name)
    origins[name] = dict(origin=str(D/name), sha256=sha(D/name), transformation='byte_exact')

# No repository-relative sys.path; each original scientific function is exact.
p = D/'resource_opportunity_census.py'
t = ast.parse(p.read_text())
functions = [n for n in t.body if isinstance(n, ast.FunctionDef)]
text = 'import collections, math\nfrom pathlib import Path\nfrom check_route import NET_RE, NODE_RE, TraceNode, coordinates\n\n'
text += '\n\n'.join(ast.get_source_segment(p.read_text(), n) for n in functions)+'\n'
(out/p.name).write_text(text)
assert [ast.dump(n) for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)] == [ast.dump(n) for n in functions]
origins[p.name] = dict(origin=str(p),sha256=sha(p),transformation='all_function_AST_exact_without_repository_import_path')

def kernel(filename, name, first, last, signature, preamble, result):
    p=D/filename; text=p.read_text(); module=ast.parse(text)
    f=next(n for n in module.body if isinstance(n,ast.FunctionDef) and n.name=='select')
    start=next(i for i,n in enumerate(f.body) if ast.get_source_segment(text,n).startswith(first))
    stop=next(i for i,n in enumerate(f.body) if ast.get_source_segment(text,n).startswith(last))
    body=f.body[start:stop+1]
    rendered='\n\n'+signature+'\n'+preamble
    for n in body:
        rendered+='\n'.join('    '+line for line in ast.unparse(n).splitlines())+'\n'
    rendered+='    return '+result+'\n'
    new=ast.parse(rendered).body[0]
    offset=len(ast.parse(preamble.strip()).body) if preamble.strip() else 0
    assert [ast.dump(n) for n in new.body[offset:-1]] == [ast.dump(n) for n in body]
    origins[name]=dict(origin=str(p),sha256=sha(p),transformation='contiguous_scientific_body_AST_exact',first_statement=first,last_statement=last,statements=len(body))
    return rendered

code='''"""Current-STA selectors over explicit observations. No historical state aliases.

These functions only propose scopes. No native feasibility, acceptance or timing
benefit is inferred. Admission and physical/native verification belong to caller.
"""
import collections, json
from fractions import Fraction
from pathlib import Path
import numpy as np
from immutable_rr_audit_cache import KINDS
from resource_opportunity_census import stream_trace, tree_data, release_scope, pin_screen, wire_units
from current_resource_bundle_v2 import serialize_request
'''
code += kernel('current_crossing_share_selector_v2.py','crossing_kernel',
    'for line in', 'actual=',
    'def crossing_scopes(run, vector, cache, minimum_margin_s=.2e-9):',
    '    rd=Path(run);v=vector;g=cache.g;pins=collections.defaultdict(dict)\n',
    "dict(candidates=candidates, actual_resources=actual, multi_crossing_nets=multiple)")
code += kernel('current_escape_owner_selector_v1.py','owner_kernel',
    'g = cache.g', "groups.sort(",
    'def owner_scopes(run, vector, cache, minimum_margin_ns=.2):',
    '    run=Path(run)\n',
    'dict(certificates=certificates, screens=screens, groups=groups, classifications=classifications, routed_nets=total_nets, positive_excess_same_layer_target_nets=len(potentials))')
(out/'selection_kernels.py').write_text(code)
for p in out.glob('*.py'):compile(p.read_text(),str(p),'exec')
write(out/'selection_source_provenance.json',dict(files=origins,native_calls_new=0,full_method_frozen=False,
    pool='Full byte-exact NativeAnalysisPool, replacing the process_identity-only observation stub in this new package only.',
    qualification='Scientific loop bodies exact; state/proof/path admission is intentionally outside the kernels. No registered package or running actor changed.'))
print(dict(package=str(out),scientific_kernels_AST_exact=True,full_serial_pool_byte_exact=True))
