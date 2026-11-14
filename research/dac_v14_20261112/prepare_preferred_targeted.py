#!/usr/bin/env python3
import shutil
from retained_prefix_workflow import D,read,write,sha
base=D/'preferred_query_certificate_offline_01';assert read(base/'unit_validation.json')['passed'];assert (base/'execution.json').exists()
b=D/'preferred_query_certificate_offline_02';b.mkdir(exist_ok=False);shutil.copytree(base/'src',b/'src')
write(b/'registration.json',dict(status='registered_before_implementation',native_route_calls=0,parent='preferred_query_certificate_offline_01',evidence='Initial fixed256 replay: all10 prefix floors zero, P0 no paths, Ph/Pf3paths, no exact/no-cross-dominance certificates. Independent physical audit runs separately; no quality claim.',question='Does explicitly ordering toward the mandatory preferred crossing improve candidate-path coverage under the same256-expansion/storage caps?',method='Retain P0/Ph/Pf as exact non-time control reproductions. Pt orders sink-layer reverse nodes by min over actual preferred crossing edges of head distance estimate + switchdelay + best source-layer seed-prefix estimate. On the prefix side use the existing seed-directed ordering. Values order expansion only; exact/lower certificate remains min pending g.',input='Same10guided complete queued-seed contexts, same sealed binary graph and existing unlimited physical oracle.',limits=dict(expansions_per_query=256,labels=16384,heap_entries=65536,seconds=1800,memory_bytes=24*1024**3,disk_reserve_bytes=80*1024**3),qualification='Adaptive offline mechanism change after first replay, not a preregistered blind test or native integration. Query budgeting unchanged per arm; no claim about overall online combined-query overhead. No-cross UB vs preferred LB only within the fixed one-cross walk model; native prices/tree validity remain separate.',source_sha256={str(p):sha(p) for p in [base/'registration.json',base/'execution.json',base/'query_stdout.log',D/'residual_seed_oracle_01/analysis.json',D/'residual_path_reuse_offline_01/analysis.json']}))
p=b/'src/preferred_query_adapter.h';s=p.read_text();a='size_t budget, size_t labels=16384, size_t heap=65536) {';assert a in s;s=s.replace(a,'size_t budget, size_t labels=16384, size_t heap=65536,\n                                    const std::vector<std::tuple<size_t,size_t,double>>& crossings={},\n                                    bool target_crossing=false) {',1)
a='    auto heuristic=[&](size_t node) {';assert a in s;s=s.replace(a,'''    // Mandatory-crossing geometry is an ordering estimate, never a lower bound.
    std::vector<std::pair<size_t,double>> suffix_targets;
    if (target_crossing) {
        for (auto [from,to,delay] : crossings) {
            if (!preferred.count(from) || !inside(from) || !inside(to)
                || layer(from)==layer(sink) || layer(to)!=layer(sink)) continue;
            double prefix=std::numeric_limits<double>::infinity();
            for (auto [seed,seed_delay] : seeds)
                if (layer(seed)==layer(from))
                    prefix=std::min(prefix,seed_delay-floor+order_distance(from,seed));
            if (std::isfinite(prefix)) suffix_targets.emplace_back(to,delay+prefix);
        }
    }
'''+a,1)
a='        double estimate=std::numeric_limits<double>::infinity();';assert s.count(a)==1;s=s.replace(a,a+'''
        if (target_crossing && layer(node)==layer(sink)) {
            for (auto [head,prefix] : suffix_targets)
                estimate=std::min(estimate,prefix+order_distance(node,head));
            return std::isfinite(estimate) ? estimate : 0.;
        }
''',1);p.write_text(s)
p=b/'src/preferred_query_driver.cpp';s=p.read_text();s=s.replace('    std::vector<std::vector<Edge>> rev(n);','    std::vector<std::vector<Edge>> rev(n);\n    std::vector<std::tuple<size_t,size_t,double>> crossings;',1)
s=s.replace('rev[v].push_back({u,w});}','rev[v].push_back({u,w});if(nodes[u].layer!=nodes[v].layer)crossings.emplace_back(u,v,w);}',1)
s=s.replace('mode<3','mode<4');s=s.replace('mode==2,std::stoull(argv[3]))','mode==2,std::stoull(argv[3]),16384,65536,crossings,mode==3)');p.write_text(s)
p=b/'src/test_preferred_query.cpp';s=p.read_text().replace('mode<3','mode<4');s=s.replace('limited?3:16384,limited?6:65536);','limited?3:16384,limited?6:65536,edges,mode==3);');p.write_text(s)
runner=(D/'run_preferred_certificate.py').read_text().replace("b=D/'preferred_query_certificate_offline_01'","b=D/'preferred_query_certificate_offline_02'")
runner=runner.replace("print(unit.stdout.strip());",'''# Only the fourth ordering arm is new. Every old non-time field/path must match.
old=(D/'preferred_query_certificate_offline_01/query_stdout.log').read_text().splitlines()
new=(b/'query_stdout.log').read_text().splitlines()
def normalized(lines):
 result=[]
 for line in lines:
  v=line.split()
  if int(v[2])==3:continue
  if v[0]=='RESULT':v[10]='<elapsed>'
  result.append(v)
 return result
control=normalized(old)==normalized(new);write(b/'control_reproduction.json',dict(passed=control,scope='Every P0/Ph/Pf non-time result and physical path record exact; only Pt changes ordering.'))
assert control
print(unit.stdout.strip());''')
(D/'run_preferred_targeted.py').write_text(runner)
print('Prepared targeted ordering, fixed original query/storage budgets')
