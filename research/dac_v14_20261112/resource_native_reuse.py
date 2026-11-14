"""Conservative free-native resource reuse; domain-ON/forced paths never alias OFF."""
from pathlib import Path
from retained_prefix_workflow import read,sha
from current_native_reuse_resource import match

def free_match(role,batches):
    if role.get('crossing_reuse_enabled') or role.get('fixed_target_paths'):
        return None
    hit=match(role,batches)
    if hit is None:return None
    batch=Path(hit['batch']);terminal=read(batch/'completion.json')
    assert terminal['passed'] and all(sha(p)==h for p,h in terminal['source_sha256'].items())
    domain=batch/(hit['role']+'_domain_audit.json');audit=read(domain)
    assert audit['passed'] and not audit['enabled']
    hit['source_sha256'][str(domain)]=sha(domain)
    hit['source_sha256'][str(batch/'completion.json')]=sha(batch/'completion.json')
    return hit
