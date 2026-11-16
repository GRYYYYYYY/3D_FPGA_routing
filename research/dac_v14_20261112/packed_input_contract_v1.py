"""Preserve declared packing-time atom-netlist interpretation in a new input config."""
def preserve_packed_input_options(historical_command, fresh_command):
    result = list(fresh_command)
    inherited = {}
    # This changes atom-netlist identity, not the routing/repair opportunity.
    for flag in ['--merge_constant_generators']:
        assert historical_command.count(flag) <= 1 and result.count(flag) <= 1
        if flag not in historical_command:
            continue
        value = historical_command[historical_command.index(flag)+1]
        assert value in ['on','off']
        if flag in result:
            assert result[result.index(flag)+1] == value, 'Conflicting packed-input interpretation'
        else:
            result.extend([flag,value])
        inherited[flag] = value
    return result,inherited


def classify_initial_failure(manifest, stdout):
    if manifest.get('returncode') and 'Type: Netlist file' in stdout and '.blif and .net do not match' in stdout:
        return 'input_netlist_compatibility_failed'
    if manifest.get('returncode') and ('Routing failed.' in stdout or 'Circuit is unroutable with a channel width factor' in stdout):
        return 'initial_route_failed'
    return 'execution_or_verification_failed'
