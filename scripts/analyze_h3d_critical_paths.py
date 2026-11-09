#!/usr/bin/env python3
"""Locate reported worst-path atom arcs in their actual packed clusters/dies."""
import re
from pathlib import Path
from lxml import etree
from lazagna_common import ROOT, sha256, utc, write_json
from validate_lazagna_vtr9_pilot import placements

BASE = ROOT/'results/h3d_delay_20261027'


def analyze(directory):
    report=directory/'report_timing.setup.rpt'
    packed=directory/'packed.net'
    if not packed.exists(): packed=directory/'netlist.net'
    place=directory/'fixed.place'
    if not place.exists(): place=directory/'placement.place'
    text=report.read_text();points=[];active=False
    for line in text.splitlines():
        if '[clock-to-output]' in line:active=True
        if line.startswith('data arrival time'):break
        if not active:continue
        match=re.match(r'^(.+?)\s+\((\.[^)]+)\).*?\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*$',line)
        if match:
            pin=match[1].strip();atom,port=pin.rsplit('.',1)
            points.append(dict(atom=atom,port=port,increment_ns=float(match[3]),arrival_ns=float(match[4])))
    assert points,report
    wanted={p['atom'] for p in points};mapping={};stack=[]
    for event,e in etree.iterparse(packed,events=('start','end'),tag='block',huge_tree=True):
        if event=='start':
            stack.append(e.get('name'))
            if e.get('name') in wanted and len(stack)>=2:
                mapping[e.get('name')]=stack[1]
        else:
            stack.pop();e.clear()
            while e.getprevious() is not None:del e.getparent()[0]
    assert wanted<=mapping.keys(),wanted-mapping.keys()
    coords=placements(place);arcs=[]
    for a,b in zip(points,points[1:]):
        if a['atom']==b['atom']:continue
        ca,cb=mapping[a['atom']],mapping[b['atom']]
        assert ca in coords and cb in coords
        kind='within_cluster' if ca==cb else 'cross_die_terminals' if coords[ca][-1]!=coords[cb][-1] else 'same_die_clusters'
        arcs.append(dict(source=a['atom'],sink=b['atom'],source_cluster=ca,sink_cluster=cb,
                         source_location=coords[ca],sink_location=coords[cb],kind=kind,
                         reported_increment_ns=b['increment_ns']))
    return dict(directory=str(directory),inputs={str(p):sha256(p) for p in (report,packed,place)},
                arcs=arcs,counts={k:sum(a['kind']==k for a in arcs) for k in ('within_cluster','same_die_clusters','cross_die_terminals')},
                reported_arrival_ns=points[-1]['arrival_ns'])


def main():
    output=BASE/'critical_path_attribution.json'
    assert not output.exists()
    rows=[]
    for directory in sorted((ROOT/'results/three_baselines_20261027/runs').glob('a0_*')):
        if not (directory/'report_timing.setup.rpt').exists():continue
        row=analyze(directory);row['case']=directory.name[3:]
        other=directory.with_name('a3_'+row['case'])/'report_timing.setup.rpt'
        row['a0_a3_worst_report_identical']=(directory/'report_timing.setup.rpt').read_bytes()==other.read_bytes()
        rows.append(row);print(row['case'],row['counts'],flush=True)
    write_json(output,dict(utc=utc(),rows=rows,scope='One reported worst path at report precision. Atom arcs mapped through packed cluster membership and placement; increments include local delay. Endpoint die changes do not count all physical Z traversals, and no claim is made about other near-critical paths.'))


if __name__=='__main__':main()
