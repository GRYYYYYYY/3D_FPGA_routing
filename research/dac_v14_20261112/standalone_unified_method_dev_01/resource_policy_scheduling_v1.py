"""Resource-policy execution order; do not compute a losing optional control."""
SKIPPED = 'not_executed_domain_candidate_accepted'

def execution_order(roles):
    names=set(roles)
    assert names in [{'reuse_off'},{'reuse_on','reuse_off'}], names
    return [name for name in ['reuse_on','reuse_off'] if name in names]

def accepted_resource_role(results):
    for name in ['reuse_on','reuse_off']:
        row=results.get(name,{})
        if row.get('status')=='legal_evaluated' and row['policies']['resources_under_timing']['accepted']:
            return name
    return None

def skip_optional_native(name,results):
    return name=='reuse_off' and accepted_resource_role({'reuse_on':results.get('reuse_on',{})})=='reuse_on'
