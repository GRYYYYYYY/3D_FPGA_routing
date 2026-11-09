#!/usr/bin/env python3
"""Final evidence closure for the separate LaZagna reproduction study."""
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote, urlparse
from lxml import html
from lazagna_common import BASE, ROOT, PAPER, sha256, utc, write_json


def read(p):return json.loads(Path(p).read_text())


def main():
    data=read(BASE/'analysis.json');assert data['complete']
    assert len(data['rows'])==126
    assert all(r['state'] not in ('queued','running','supervisor_error') for r in data['rows'])
    legal=[r for r in data['rows'] if r['native_full']]
    assert all(r['native_full'] or 'critical_path_ns' not in r for r in data['rows'])
    assert all(r['independent_audit'] and r['classification']=='legal_audited' for r in legal)
    assert data['audits']['count']==len(legal) and data['audits']['passed']
    assert all(data['protected_files_unchanged'].values())
    cache={}
    def digest(p):
        key=str(Path(p).resolve())
        if key not in cache:cache[key]=sha256(key)
        return cache[key]
    for p,h in read(BASE/'protocol.json')['protected_files'].items():assert digest(p)==h
    exceptions=[];manifest_count=0;route_bindings=[]
    for row in data['rows']:
        directory=BASE/'runs'/row['name'];receipt=directory/'manifest.json'
        if not receipt.exists():
            assert not row['native_full'];continue
        m=read(receipt);manifest_count+=1
        assert m['status'] in ('failed','completed','timeout')
        for path,expected in m['inputs'].items():
            if digest(path)!=expected:
                exception=directory/'input_registration_race.json'
                assert exception.exists() and row['classification']=='excluded_input_registration_race'
                e=read(exception)
                assert e['manifest_sha256']==digest(receipt) and not e['loaded_placement']
                assert '# Load Placement' not in (directory/'stdout.log').read_text(errors='replace')
                exceptions.append({'run':row['name'],'path':path,'expected':expected,'actual':digest(path),'evidence':str(exception)})
        if m.get('supervisor_adopted') and m['status']=='timeout' and m['wall_seconds']<m['timeout_seconds']:
            observation=read(directory/'timeout_timing_observation.json')
            assert observation['original_manifest_sha256']==digest(receipt)
            assert observation['observed_wall_seconds_upper_bound']>=m['timeout_seconds']
        if row['native_full']:
            result=read(directory/'result.json')
            for output in result['outputs'].values():assert digest(output['path'])==output['sha256']
            audit=read(BASE/'audits'/(row['name']+'.json'));assert audit['passed']
            route=directory/'routed.route'
            assert audit['inputs']['route_sha256']==digest(route)
            assert audit['inputs']['rr_graph_sha256']==digest(audit['inputs']['rr_graph'])
            if row['family']=='paper':
                vertical=read(BASE/f'vertical_paper_100_w{row["width"]}.json')
                assert audit['inputs']['resource_map_sha256']==digest(vertical['resource_map'])
            with route.open() as stream:header=stream.readline().strip()
            expected=result['outputs']['fixed.place']['sha256']
            assert expected in header,(row['name'],header,expected)
            route_bindings.append({'run':row['name'],'route_sha256':digest(route),
                                   'placement_sha256':expected,'route_header':header})
    assert len(exceptions)==1
    for prefix in ('route','clock_diagnostic','native_compat','repaired_pnr','guardfix_pnr'):
        summary=read(BASE/f'{prefix}_audit_summary.json')
        assert summary['passed']
        for record in summary['results']:assert digest(record['audit'])==record['sha256']
    graph_checks={}
    for width in (100,300):
        dsp=read(BASE/f'dsp_correspondence_100_w{width}.json')
        assert dsp['passed'] and dsp['common_opins']==2548*74
        assert dsp['left']['graph_sha256']==digest(dsp['left']['graph'])
        assert dsp['right']['graph_sha256']==digest(dsp['right']['graph'])
        graph_checks[f'dsp_w{width}']=True
        for family in ('paper','native'):
            vertical=read(BASE/f'vertical_{family}_100_w{width}.json')
            assert vertical['passed']
            graph=BASE/'runs'/(f'paper_sb_100_w{width}_p50' if family=='paper' else f'native_graph_100_w{width}')/'rr_graph.xml'
            assert vertical['graph_sha256']==digest(graph)
            graph_checks[f'vertical_{family}_w{width}']=True
    for name in ('paper','native','paper_table'):
        clock=read(BASE/f'clock_{name}_w300.json')
        assert clock['complete_graph_scan'] and clock['bram_clock_ipins']==2352
        assert clock['zero_fanin_clock_ipins']==2352 and clock['incoming_edges']==0
        assert digest(clock['graph'])==clock['sha256']
    for family in ('paper','native'):
        proof=read(BASE/f'dsp_cuts_{family}_w100.verified.json')
        assert proof['passed'] and len(proof['certificates'])==344
        assert digest(proof['input'])==proof['input_sha256']
    assert read(BASE/'clock_graph_mode_complete.json')['completed']
    clock_ideal=read(BASE/'clock_all_native_ideal_40_w100.json')
    clock_route=read(BASE/'clock_all_native_route_40_w100.json')
    assert clock_ideal['types']['clb']['clock_ipins']==clock_ideal['types']['clb']['zero_fanin']==2128
    assert clock_route['types']['clb']['zero_fanin']==0 and clock_route['types']['clb']['incoming_edges']==29792
    clock_full=read(BASE/'clock_all_native_ideal_100_w300.json')
    assert clock_full['types']['clb']['clock_ipins']==clock_full['types']['clb']['zero_fanin']==14308
    assert digest(clock_full['graph'])==clock_full['graph_sha256']
    modes=read(BASE/'native_clock_graph_mode_comparison.json')['comparison']
    assert set(modes['edge_classes']['only_left'])==set(modes['edge_classes']['only_right'])=={'CHANX->IPIN','CHANY->IPIN'}
    assert read(BASE/'guardfix_input_equivalence.json')['passed']
    source=read(BASE/'protocol.json')['sources'];repositories={'lazagna':PAPER,'openfpga':PAPER/'OpenFPGA','vtr':PAPER/'OpenFPGA/vtr-verilog-to-routing'}
    versions={k:subprocess.check_output(['git','-C',str(p),'rev-parse','HEAD'],text=True).strip() for k,p in repositories.items()}
    assert all(versions[k]==source[k] for k in repositories)
    original_vtr_clean=not subprocess.check_output(['git','-C',str(repositories['vtr']),'status','--porcelain','--untracked-files=no'],text=True).strip()
    assert original_vtr_clean
    native_source=ROOT/'vendor/vtr/vpr/src/place/move_utils.cpp'
    upstream_source=subprocess.check_output(['git','-C',str(ROOT/'vendor/vtr'),'show','HEAD:vpr/src/place/move_utils.cpp'])
    assert native_source.read_bytes()==upstream_source
    for name in ('final_lazagna_unit_tests','final_route_audit_unit_tests','guardfix_unit_compile_v2','guardfix_unit_test_v2'):
        m=read(BASE/'runs'/name/'manifest.json');assert m['status']=='completed' and m['returncode']==0
    report=BASE/'report.html';tree=html.fromstring(report.read_text());broken=[]
    for href in tree.xpath('//a/@href'):
        parsed=urlparse(href)
        if not parsed.scheme and parsed.path and not (report.parent/unquote(parsed.path)).exists():broken.append(href)
    assert not broken,broken
    assert len(tree.xpath('//*[@id="runs"]/tbody/tr'))==len(data['rows'])
    write_json(BASE/'validation.json',{'utc':utc(),'passed':True,'run_rows':len(data['rows']),
        'executed_attempt_manifests':manifest_count,'legal_routes':len(legal),'audited_legal_routes':len(legal),
        'unique_files_rehashed':len(cache),'input_hash_exceptions_excluded':exceptions,
        'graph_checks':graph_checks,'source_versions':versions,'original_vtr_tracked_source_clean':original_vtr_clean,
        'native_a0_placement_source_matches_upstream_head':True,'matched_guardfix_controls':3,
        'route_placement_bindings':route_bindings,'protected_files_unchanged':data['protected_files_unchanged'],
        'analysis_sha256':sha256(BASE/'analysis.json'),'report_sha256':sha256(report),
        'scope':'All planned states terminal; every legal route passed FULL and independent checks. One cancelled pre-placement metadata-race attempt excluded. Four adopted timeout timings use transparent observer upper bounds. No algorithm-only, exact author-experiment, silicon, or bitstream equivalence claim.'})
    print('Final LaZagna validation passed:',len(legal),'legal routes;',len(cache),'unique files rehashed',flush=True)


if __name__=='__main__':main()
