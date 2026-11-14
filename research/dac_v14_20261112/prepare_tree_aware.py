#!/usr/bin/env python3
"""Prepare an isolated tree-aware query experiment; never edit frozen VPR."""
import shutil
from retained_prefix_workflow import D, read, write, sha

registration = D / 'tree_aware_candidate_query_experiment_01.json'
reg = read(registration)
assert all(sha(p) == h for p, h in reg['source_sha256'].items())
b = D / 'tree_aware_candidate_offline_01'
b.mkdir(exist_ok=False)
(b / 'src').mkdir()
base = D / 'preferred_query_certificate_offline_03/src'
for name in ['h3d_candidate_path.h', 'preferred_query_adapter.h']:
    shutil.copy2(base / name, b / 'src' / name)
s = (base / 'preferred_query_adapter.h').read_text()
s = s.replace('PreferredQueryAnswer', 'TreePreferredQueryAnswer').replace('query_preferred(', 'query_tree_preferred(')
s = s.replace('const std::set<size_t>& preferred,', '''const std::set<size_t>& preferred,
                                    const std::set<size_t>& tree,
                                    const std::set<size_t>& inherited,
                                    bool allow_inherited, bool terminal_tree,''')
s = s.replace('if (layer(node)==layer(sink) || !inside(node)) continue;', '''if (!inside(node)) continue;
        if (layer(node)==layer(sink) && !(allow_inherited && inherited.count(node))) continue;''')
s = s.replace('        reverse(node,[&](size_t from, double delay) {', '''        // A fixed-tree extension attaches once. A tree node is either an
        // eligible actual seed goal or a dead end; never traverse through it.
        if (terminal_tree && tree.count(node)) return;
        reverse(node,[&](size_t from, double delay) {''')
s = s.replace('            return std::isfinite(estimate) ? estimate : 0.;', '''            // A sink-layer seed can already satisfy the preferred crossing
            // through its retained root-to-seed ancestry, with no new crossing.
            if (allow_inherited)
                for (auto [seed,delay] : seeds)
                    if (layer(seed)==layer(sink))
                        estimate=std::min(estimate,delay-floor+order_distance(node,seed));
            return std::isfinite(estimate) ? estimate : 0.;''')
s = s.replace('Off-sink-layer seeds admitted', 'Eligible actual seeds admitted')
s = s.replace('Query exactly one preferred crossing using actual queued seed delays.', 'Query a preferred-satisfied extension with optional inherited ancestry and fixed-tree terminals.')
(b / 'src/tree_preferred_query_adapter.h').write_text(s)

driver = (base / 'preferred_query_driver.cpp').read_text()
driver = driver.replace('#include "preferred_query_adapter.h"', '#include "tree_preferred_query_adapter.h"\n#include "tree_lower_audit.h"')
driver = driver.replace('size_t search,sink,num,np;', 'size_t search,sink,num,np,nt,ni;')
driver = driver.replace('>>num>>np;', '>>num>>np>>nt>>ni;')
needle = '        auto inside=[&](size_t k)'
driver = driver.replace(needle, '''        std::set<size_t> tree,inherited;
        for(size_t j=0;j<nt;++j){size_t k;cases>>k;assert(cases&&k<n);tree.insert(k);}
        for(size_t j=0;j<ni;++j){size_t k;cases>>k;assert(cases&&k<n);inherited.insert(k);}
'''+needle)
driver = driver.replace('mode<5', 'mode<4')
old = 'query_preferred(n,sink,seeds,preferred,layer,inside,reverse,order,mode!=0,mode==2,std::stoull(argv[3]),16384,65536,mode==4?selected_crossings:crossings,mode>=3)'
assert old in driver
driver = driver.replace(old, 'query_tree_preferred(n,sink,seeds,preferred,tree,inherited,mode&1,mode&2,layer,inside,reverse,order,true,false,std::stoull(argv[3]),16384,65536,selected_crossings,true)')
needle = '            size_t index=0;'
driver = driver.replace(needle, '''            auto audit_start=std::chrono::steady_clock::now();
            auto checked=verify_tree_lower(nodes,rev,sink,seeds,preferred,tree,inherited,mode,
                xmin,xmax,ymin,ymax,lmin,lmax,r.lower_seconds);
            std::cout<<"LOWER "<<search<<' '<<mode<<' '<<checked<<' '
                <<std::chrono::duration<double>(std::chrono::steady_clock::now()-audit_start).count()<<'\\n';
'''+needle)
(b / 'src/tree_query_driver.cpp').write_text(driver)
write(b / 'registration.json', dict(status='implemented_pending_unit_and_actual_execution',
    native_route_calls=0, parent=str(registration), parent_sha256=sha(registration),
    arms=['P','I','L','IL'], input_cases=3809, budget=reg['budget'], limits=reg['limits'],
    rationale='Fixed-tree and inherited-prefix factors isolated; actual CPD effectiveness is not established by this query experiment.',
    input_sha256=reg['source_sha256']))
print('Prepared isolated adapter and actual-context driver', b)
