#!/usr/bin/env python3
"""Check literal Table III 260/40 tracks separately from released XML 280/40."""
import xml.etree.ElementTree as ET
from lazagna_common import BASE,ROOT,PAPER,PYTHON,run,sha256,utc,write_json


def main():
    protocol=BASE/'table_tracks_protocol.json'
    if protocol.exists():raise RuntimeError('Table sensitivity already registered')
    src=BASE/'architectures/paper_100.xml';root=ET.parse(src).getroot()
    root.find("segmentlist/segment[@name='L4']").set('freq','260')
    arch=BASE/'architectures/paper_table_100.xml';ET.indent(root);ET.ElementTree(root).write(arch,encoding='utf-8',xml_declaration=True)
    write_json(protocol,{'utc':utc(),'source':str(src),'source_sha256':sha256(src),'architecture':str(arch),'sha256':sha256(arch),
        'change':'L4:L16 frequency weights 280:40 to 260:40; all other published architecture settings, toolchain and SB generator unchanged.',
        'scope':'Literal paper Table III sensitivity graph, separate from the as-released-XML primary. Inspect actual tracks and BRAM clock connectivity; do not assume the author used this corrected XML.'})
    binary=ROOT/'artifacts/bin/lazagna-paper/vpr';circuit=PAPER/'benchmarks/and2/and2.blif'
    base=BASE/'runs/paper_table_graph_100_w300/rr_graph.xml';graph=BASE/'runs/paper_table_sb_100_w300_p50/rr_graph.xml'
    r=run('paper_table_graph_100_w300',[binary,arch,circuit,'--pack','--route_chan_width',300,'--num_workers',1,'--clock_modeling','route','--write_rr_graph',base],inputs=[binary,arch,circuit],timeout=1800)
    if r['status']!='completed':raise RuntimeError('Table base graph failed')
    creator=PAPER/'scripts/3d_sb_creator.py'
    r=run('paper_table_sb_100_w300_p50',[PYTHON,creator,'-f',base,'-o',graph,'-p',.5,'-c','subset','-a',arch,'-vp',1,'--sb_location_pattern','repeated_interval'],inputs=[creator,base,arch],timeout=1800)
    if r['status']!='completed':raise RuntimeError('Table SB graph failed')
    for script,output in [('check_lazagna_clock_pins.py','clock_paper_table_w300.json'),('audit_lazagna_vertical.py','vertical_paper_table_100_w300.json')]:
        r=run('table_'+script[:-3],[PYTHON,ROOT/'scripts'/script,'--graph',graph,'--output',BASE/output],inputs=[graph],timeout=1800)
        if r['status']!='completed':raise RuntimeError('Table graph audit failed')
    write_json(BASE/'table_tracks_complete.json',{'utc':utc(),'graph':str(graph),'sha256':sha256(graph),'completed':True})


if __name__=='__main__':main()
