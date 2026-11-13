from routing_log_metrics import last_iteration
row=' 200    4.3  1000.0    0 1.1e+07     432     635     231 ( 0.010%)  505116 (36.9%)   12.664'
assert last_iteration([row]) is None
assert last_iteration(['Iter Time Overused RR Nodes',row,'Final critical path delay: 12.6 ns'])==dict(iteration=200,rerouted_nets=432,rerouted_connections=635,overused_rr_nodes=231)
assert last_iteration(['Iter Time Overused RR Nodes','[ -1.3e-08: -1.1e-08) 7 (0.0%)']) is None
print('failure iteration parsing and unrelated numeric-line rejection passed')
