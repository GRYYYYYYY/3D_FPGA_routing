#!/usr/bin/env python3
"""Paired metrics only after legality and provenance validation; no pooled replicates."""
from collections import defaultdict
import math
from pathlib import Path
import re
import statistics

from lazagna_common import ROOT,sha256,utc,write_json
from three_baseline_common import read
from run_vpr import parse_metrics
from run_h3d_delay_study import option,route_body_hash

BASE=ROOT/'results/h3d_delay_20261027_v2'
ARMS=['legacy','delay','critical','delay_critical']


def geometric_change(ratios):
    return 100.*math.expm1(statistics.mean(math.log(x) for x in ratios)) if ratios else None


def last_stats(log,tag):
    lines=re.findall(r'^'+tag+r' (.*)$',log,re.M)
    return dict(re.findall(r'(\w+)=([^\s]+)',lines[-1])) if lines else {}


def main():
    assert not (BASE/'analysis.json').exists()
    validation=read(BASE/'validation.json');assert validation['passed']
    protocol=read(BASE/'protocol.json')
    audits={a['name']:a for a in validation['audits']}
    results=[read(BASE/'runs'/j['name']/'result.json') for j in protocol['jobs']]
    mainruns=defaultdict(dict); serial=defaultdict(list)
    for r in results:
        if r['native_legal']:
            assert audits[r['name']]['passed']
            r['physical_metrics']=audits[r['name']]['route']
        log=(Path(r['directory'])/'stdout.log').read_text(errors='replace')
        for tag in ['H3D_PLAN','H3D_TREE']:
            r['stats'][tag]=last_stats(log,tag)
        time=(Path(r['directory'])/'time.txt').read_text()
        match=re.search(r'Maximum resident set size \(kbytes\): (\d+)',time)
        r['peak_rss_kib']=int(match[1]) if match else None
        if r['phase']=='main':mainruns[r['fixture']][r['arm']]=r
        elif r['phase']=='serial':serial[(r['fixture'],r['arm'])].append(r)
    pairs=[];equivalence=[]
    reference_bindings={}
    def reference_log(directory):
        logpath=directory/('stdout.log' if (directory/'stdout.log').exists() else 'vpr.log')
        recordpath=directory/('result.json' if (directory/'result.json').exists() else 'manifest.json')
        record=read(recordpath)
        for path in [recordpath,directory/'manifest.json',logpath,directory/'routed.route']:
            reference_bindings[str(path)]=sha256(path)
            expected=record.get('outputs',{}).get(path.name)
            if expected:assert reference_bindings[str(path)]==expected['sha256'],path
        log=logpath.read_text(errors='replace')
        assert parse_metrics(log)['critical_path_ns']==record['metrics']['critical_path_ns']
        return log
    for fixture,arms in mainruns.items():
        source=read(protocol['fixtures'][fixture]); command=source['command']
        family,case=fixture.split('_',1)
        a3dir=(ROOT/'results/three_baselines_20261027/runs'/('a3_'+case) if family=='w300'
               else ROOT/'results/runs'/f'koios_a0a4_seed1_{case}_a3')
        a0dir=Path(option(command,'--route_file')).parent
        a0cpd=parse_metrics(reference_log(a0dir)).get('critical_path_ns')
        moderncpd=None
        if family=='w300':
            moderndir=ROOT/'results/three_baselines_20261027/runs'/('modern_'+case)
            moderncpd=parse_metrics(reference_log(moderndir))['critical_path_ns']
        a3log=reference_log(a3dir)
        eq=dict(fixture=fixture,archived_a3=str(a3dir),
            legacy_route_equal=arms['legacy']['native_legal'] and arms['legacy']['route_body_sha256']==route_body_hash(a3dir/'routed.route'),
            legacy_cpd_equal=arms['legacy']['metrics'].get('critical_path_ns')==parse_metrics(a3log).get('critical_path_ns'))
        equivalence.append(eq)
        for arm in ARMS:
            r=arms[arm];baseline=arms['legacy']
            paired=baseline['native_legal'] and r['native_legal']
            item=dict(fixture=fixture,family=family,case=case,arm=arm,paired_legal=paired,
                baseline_legal=baseline['native_legal'],treatment_legal=r['native_legal'],stats=r['stats'])
            if paired:
                cpd=r['metrics']['critical_path_ns'];bc=baseline['metrics']['critical_path_ns']
                item.update(cpd_ns=cpd,legacy_cpd_ns=bc,a0_cpd_ns=a0cpd,cpd_ratio=cpd/bc,
                    cpd_ratio_to_a0=cpd/a0cpd,
                    planar_ratio=r['physical_metrics']['horizontal_track_length']/baseline['physical_metrics']['horizontal_track_length'],
                    vertical_ratio=r['physical_metrics']['vertical_channel_net_occupancy']/baseline['physical_metrics']['vertical_channel_net_occupancy'])
                report=r['outputs'].get('report_timing.setup.rpt')
                reference_report=baseline['outputs'].get('report_timing.setup.rpt')
                item['worst_setup_report_equal_legacy']=(report['sha256']==reference_report['sha256']
                    if report and reference_report else None)
                if moderncpd is not None:
                    item.update(modern_cpd_ns=moderncpd,cpd_ratio_to_modern=cpd/moderncpd)
            pairs.append(item)
    summaries=[]
    for family in ['w100','w300']:
        for arm in ARMS:
            rows=[p for p in pairs if p['family']==family and p['arm']==arm]
            legal=[p for p in rows if p['paired_legal']]
            summaries.append(dict(family=family,arm=arm,registered_pairs=len(rows),legal_pairs=len(legal),
                improved=sum(p['cpd_ratio']<1. for p in legal),unchanged=sum(p['cpd_ratio']==1. for p in legal),
                worsened=sum(p['cpd_ratio']>1. for p in legal),
                identical_worst_setup_reports=sum(p['worst_setup_report_equal_legacy'] is True for p in legal),
                **{key+'_geomean_change_pct':geometric_change([p[key] for p in legal])
                   for key in ['cpd_ratio','cpd_ratio_to_a0','planar_ratio','vertical_ratio']}))
            if family=='w300':
                summaries[-1]['cpd_ratio_to_modern_geomean_change_pct']=geometric_change([p['cpd_ratio_to_modern'] for p in legal])
    timing=[]
    for (fixture,arm),runs in serial.items():
        good=[r for r in runs if r['native_legal']]
        main_reference=mainruns[fixture]['legacy' if arm=='archived_a3' else arm]
        item=dict(fixture=fixture,arm=arm,repeats=len(runs),legal=len(good),
            deterministic_route=len({r.get('route_body_sha256') for r in good})==1,
            matches_main_route=all(r['route_body_sha256']==main_reference['route_body_sha256'] for r in good))
        for key, getter in {
            'wall_seconds':lambda r:r['wall_seconds'],
            'router_seconds':lambda r:r['metrics']['router_seconds'],
            'init_seconds':lambda r:float(r['stats']['H3D_INIT']['init_seconds']),
            'planning_seconds':lambda r:float(r['stats']['H3D_PLAN']['planning_seconds']),
            'peak_rss_kib':lambda r:r['peak_rss_kib'],
        }.items():
            samples=[getter(r) for r in good]
            item['samples_'+key]=samples
            item['median_'+key]=statistics.median(samples) if samples else None
        timing.append(item)
    timing_comparisons=[]
    for item in timing:
        if item['arm']=='archived_a3':continue
        for reference_arm in ['archived_a3','legacy']:
            if item['arm']==reference_arm:continue
            reference=next(t for t in timing if t['fixture']==item['fixture'] and t['arm']==reference_arm)
            timing_comparisons.append(dict(fixture=item['fixture'],arm=item['arm'],reference=reference_arm,
                **{key+'_change_pct':100.*(item['median_'+key]/reference['median_'+key]-1.)
                   for key in ['wall_seconds','router_seconds','init_seconds','planning_seconds','peak_rss_kib']}))
    off=[dict(name=r['name'],route_matches_a0=r['matches_archived_a0_route']) for r in results if r['arm']=='off']
    assert all(e['legacy_route_equal'] and e['legacy_cpd_equal'] for e in equivalence),equivalence
    assert all(e['route_matches_a0'] for e in off)
    assert all(t['deterministic_route'] and t['matches_main_route'] for t in timing)
    write_json(BASE/'analysis.json',dict(utc=utc(),validation_sha256=sha256(BASE/'validation.json'),
        registered=len(results),success=sum(r['native_legal'] for r in results),
        equivalence=equivalence,off_controls=off,summaries=summaries,pairs=pairs,timing=timing,
        timing_comparisons=timing_comparisons,
        reference_bindings=reference_bindings,
        three_baselines=dict(B1='Published VTR8.1 LaZagna aggregate ratios lack a common denominator and per-circuit absolute timing; no numeric superiority claim.',
            B2='Archived modern LaZagna results on the same packing/placement, different graph and toolchain: conditional system comparison.',
            B3='Native VTR9 A0; legacy equality and off controls verify the new build preserves the existing controlled comparison.'),
        note='Geometric means over circuits within each width cohort. Three timing repeats are not independent circuit samples; shared-host serial observations, no new placement seeds.'))
    for row in summaries:print(row)
    for row in timing:print(row)


if __name__=='__main__':main()
