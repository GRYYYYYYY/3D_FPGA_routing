#!/usr/bin/env python3
"""Hold planar fabric/segment weights fixed while varying SB, CB-O and Hybrid-O."""
import argparse
import copy
import xml.etree.ElementTree as ET

from lazagna_common import ROOT,sha256,utc,write_json

BASE=ROOT/'results/architecture_flow_20261027'
SOURCE=ROOT/'vendor/beyond-flatland-src/Architecture_Files'


def canonical(e):
    return e.tag,tuple(sorted(e.attrib.items())),(e.text or '').strip(),tuple(canonical(c) for c in e)


def common_root(family,size):
    root=ET.parse(SOURCE/'sb_architecture.xml').getroot()
    cb=ET.parse(SOURCE/'cb_o_architecture.xml').getroot()
    assert canonical(root.find('models'))==canonical(cb.find('models'))
    assert canonical(root.find('complexblocklist'))==canonical(cb.find('complexblocklist'))
    # Confirm that the intentional pin-layer change does not hide another tile edit.
    a,b=copy.deepcopy(root.find('tiles')),copy.deepcopy(cb.find('tiles'))
    for tiles in (a,b):
        for sub in tiles.findall('tile/sub_tile'):sub.remove(sub.find('pinlocations'))
    assert canonical(a)==canonical(b)
    layout=root.find('layout')
    template=[x for x in layout if x.get('width')=='25' and x.get('height')=='25']
    assert len(template)==1
    fixed=copy.deepcopy(template[0]);fixed.set('name',f'controlled_{size}')
    fixed.set('width',str(size));fixed.set('height',str(size))
    layout.clear();layout.append(fixed)
    root.find("segmentlist/segment[@name='L4']").set('freq','260')
    assert root.find("segmentlist/segment[@name='L16']").get('freq')=='40'
    if family in ('cb_o','hybrid_o'):
        for tile in root.findall('tiles/tile'):
            for sub in tile.findall('sub_tile'):
                path=f"tiles/tile[@name='{tile.get('name')}']/sub_tile[@name='{sub.get('name')}']/pinlocations"
                sub.remove(sub.find('pinlocations'));sub.append(copy.deepcopy(cb.find(path)))
    if family=='cb_o':
        switches=root.find('switchblocklist')
        cross=switches.find("switchblock[@name='3d_subset']")
        assert cross is not None;switches.remove(cross)
    return root


def prepare(size):
    directory=BASE/'controlled_architectures'/f'n{size}'
    directory.mkdir(parents=True,exist_ok=False)
    output={}
    for family in ['sb','cb_o','hybrid_o']:
        root=common_root(family,size);ET.indent(root)
        p=directory/f'{family}.xml';ET.ElementTree(root).write(p,encoding='utf-8',xml_declaration=True)
        output[family]=dict(path=str(p),sha256=sha256(p))
    write_json(directory/'manifest.json',dict(utc=utc(),grid=[size,size,2],architectures=output,
        sources={str(p):sha256(p) for p in [SOURCE/'sb_architecture.xml',SOURCE/'cb_o_architecture.xml']},
        controls='Identical logic, grid, same-layer custom SB rules, L4/L16 frequencies 260/40, wire and switch delays; only SB crossing availability and output-pin inter-layer connectivity vary',
        qualification='Derived controlled architectures, NOT unchanged author XMLs. Hybrid includes additional CB connectivity; no equal physical area/via budget is assumed.'))
    print('Prepared controlled architecture triple',size)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--sizes',type=int,nargs='+',default=[25])
    for size in parser.parse_args().sizes:prepare(size)
