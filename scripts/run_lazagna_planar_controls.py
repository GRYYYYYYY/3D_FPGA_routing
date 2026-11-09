#!/usr/bin/env python3
"""Separate plane switchblock specification from VPR version at W=100."""
import copy
import json
import xml.etree.ElementTree as ET
from lazagna_common import BASE, ROOT, PAPER, PYTHON, run, sha256, utc, write_json


def main():
    registration=BASE/'planar_control_protocol.json'
    if registration.exists():raise RuntimeError('Controls already registered')
    paper=ET.parse(BASE/'architectures/paper_40.xml').getroot()
    native=ET.parse(BASE/'architectures/native_40.xml').getroot()
    custom=copy.deepcopy(paper)
    sb=custom.find('device/switch_block');sb.attrib.clear();sb.set('type','custom')
    custom.append(copy.deepcopy(native.find('switchblocklist')))
    # The new VPR accepts the planar legacy schema after removing the obsolete
    # inter-die connection-block attribute. No plane connectivity is edited.
    wilton=copy.deepcopy(paper)
    wilton.find('device/connection_block').attrib.pop('input_inter_die_switch_name',None)
    arches={}
    for name,root in [('old_custom',custom),('new_wilton',wilton)]:
        path=BASE/'architectures'/f'{name}_40.xml'
        ET.indent(root);ET.ElementTree(root).write(path,encoding='utf-8',xml_declaration=True)
        arches[name]={'path':str(path),'sha256':sha256(path)}
    write_json(registration,{'utc':utc(),'purpose':'2x2 planar controls: old/new VPR and built-in Wilton/custom plane; no vertical resources in these two supplemental graphs.',
                            'grid':[40,40,2],'width':100,'architectures':arches})
    for name in arches:
        binary=ROOT/'artifacts/bin'/('lazagna-paper' if name=='old_custom' else 'baseline')/'vpr'
        arch=arches[name]['path'];circuit=PAPER/'benchmarks/and2/and2.blif'
        runname=f'control_{name}_40_w100';graph=BASE/'runs'/runname/'rr_graph.xml'
        r=run(runname,[binary,arch,circuit,'--pack','--route_chan_width',100,'--write_rr_graph',graph,
                      '--num_workers',1,'--clock_modeling','route'],inputs=[binary,arch,circuit],timeout=1800)
        print(json.dumps({'name':name,'status':r['status']}),flush=True)
    comparisons=[('old_builtin_vs_old_custom','paper_graph_40_w100','control_old_custom_40_w100'),
                 ('old_builtin_vs_new_builtin','paper_graph_40_w100','control_new_wilton_40_w100'),
                 ('old_custom_vs_new_custom','control_old_custom_40_w100','native_graph_40_w100'),
                 ('paper_base_vs_added_z','paper_graph_40_w100','paper_sb_40_w100_p50')]
    for label,left,right in comparisons:
        paths=[BASE/'runs'/n/'rr_graph.xml' for n in [left,right]]
        if not all(p.exists() for p in paths):continue
        r=run('compare_'+label,[PYTHON,ROOT/'scripts/compare_lazagna_graphs.py','--left',paths[0],
              '--right',paths[1],'--output',BASE/(label+'.json')],inputs=paths,timeout=1800)
        print(json.dumps({'comparison':label,'status':r['status']}),flush=True)


if __name__=='__main__':main()
