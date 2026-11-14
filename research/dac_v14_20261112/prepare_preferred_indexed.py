#!/usr/bin/env python3
import shutil
from retained_prefix_workflow import D,read,write,sha
base=D/'preferred_query_certificate_offline_02';assert read(base/'analysis.json')['passed'] and read(base/'control_reproduction.json')['passed']
b=D/'preferred_query_certificate_offline_03';b.mkdir(exist_ok=False);shutil.copytree(base/'src',b/'src')
write(b/'registration.json',dict(status='registered_before_implementation',native_route_calls=0,parent=str(base),question='Can preferred-source adjacency lookup eliminate the full-crossing scan while preserving every targeted-query result and path?',evidence=read(base/'analysis.json')['summaries'],method='Preserve P0/Ph/Pf/Pt exact controls. Pi uses the same tested adapter and targeted heuristic, with static crossings indexed by source. Lookup only the current preferred-source set. The fixed256 expansion cap and labels16384/heap65536 are unchanged. Record examined crossing records separately from core expansions.',qualification='Offline representation optimization; graph-index construction/loading and selected-list construction are outside the core query timer. Record candidate-filter work for Pt and Pi; do not claim a total native speedup from core query time. Production RRG already exposes forward adjacency, but no native integration has occurred.',source_sha256={str(p):sha(p) for p in [base/'analysis.json',base/'control_reproduction.json',base/'execution.json',base/'query_stdout.log',base/'unit_validation.json']}))
p=b/'src/preferred_query_driver.cpp';s=p.read_text();s=s.replace('    assert(f.peek()==std::char_traits<char>::eof());','''    std::map<size_t,std::vector<std::tuple<size_t,size_t,double>>> by_source;
    for (auto e:crossings) by_source[std::get<0>(e)].push_back(e);
    assert(f.peek()==std::char_traits<char>::eof());''',1)
a='        for(int mode=0;mode<4;++mode){';assert a in s;s=s.replace(a,'''        std::vector<std::tuple<size_t,size_t,double>> selected_crossings;
        for (auto node:preferred) {
            auto found=by_source.find(node);
            if (found!=by_source.end()) selected_crossings.insert(selected_crossings.end(),found->second.begin(),found->second.end());
        }
        std::cout<<"WORK "<<search<<' '<<crossings.size()<<' '<<selected_crossings.size()<<'\\n';
        for(int mode=0;mode<5;++mode){''',1)
s=s.replace('crossings,mode==3)','mode==4?selected_crossings:crossings,mode>=3)');p.write_text(s)
s=(D/'run_preferred_targeted.py').read_text().replace("b=D/'preferred_query_certificate_offline_02'","b=D/'preferred_query_certificate_offline_03'")
s=s.replace("for name in ['test_preferred_query','preferred_query_driver']:","for name in ['preferred_query_driver']:")
a=s.index('unit=subprocess.run(');z=s.index("cases=[c for c in read(base/'cases.json')",a)
s=s[:a]+'''unit_source=D/'preferred_query_certificate_offline_02'
assert read(unit_source/'unit_validation.json')['passed']
for name in ['preferred_query_adapter.h','h3d_candidate_path.h','test_preferred_query.cpp']:
 assert sha(b/'src'/name)==sha(unit_source/'src'/name)
shutil.copy2(unit_source/'test_preferred_query',b/'test_preferred_query')
write(b/'unit_validation.json',dict(passed=True,reused=True,source=str(unit_source/'unit_validation.json'),source_sha256=sha(unit_source/'unit_validation.json'),reason='Exact same adapter, core and test source; only offline driver pre-indexes identical edges. Existing5760 Floyd adapter checks retained, not rerun or added as independent samples.'))
'''+s[z:]
s=s.replace("old=(D/'preferred_query_certificate_offline_01/query_stdout.log')","old=(D/'preferred_query_certificate_offline_02/query_stdout.log')")
s=s.replace("  if int(v[2])==3:continue", "  if v[0]=='WORK':continue\n  if int(v[2])==4:continue")
s=s.replace("print(unit.stdout.strip());",'''targeted=[];indexed=[]
for l in new:
 v=l.split()
 if v[0]=='WORK':continue
 if int(v[2]) not in [3,4]:continue
 mode=int(v[2]);v[2]='3'
 if v[0]=='RESULT':v[10]='<elapsed>'
 (targeted if mode==3 else indexed).append(v)
assert targeted==indexed
write(b/'index_reproduction.json',dict(passed=True,scope='Every Pi result/path/non-time counter equals Pt after arm identity normalization; lookup changes only candidate-filter work.'))
print('Strictly reused 5760 adapter checks; all targeted/indexed non-time results and paths exact');''')
s=s.replace('Every P0/Ph/Pf non-time result and physical path record exact; only Pt changes ordering.','Every P0/Ph/Pf/Pt non-time result and physical path record exact; only Pi uses indexed crossing lookup.')
(D/'run_preferred_indexed.py').write_text(s)
print('Prepared static preferred-source lookup, same adapter and query decisions')
