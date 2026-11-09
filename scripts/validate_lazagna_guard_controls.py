#!/usr/bin/env python3
"""Check one-code-change causal controls and canonical packed-netlist equality."""
import hashlib
import json
from lxml import etree
from lazagna_common import BASE, ROOT, sha256, utc, write_json


def normalized_command(m):
    command=list(m['command']);command[0]='VPR_BINARY'
    # These output filenames are inherently different between isolated runs.
    for flag in ('--route_file','--net_file','--place_file'):
        i=command.index(flag);command[i+1]=flag+'_OUTPUT'
    return command


def canonical_packing(path):
    tree=etree.parse(str(path));tree.getroot().set('name','PACKED_NETLIST_PATH')
    return hashlib.sha256(etree.tostring(tree,method='c14n')).hexdigest()


def main():
    rows=[]
    for case,prefix in [('bnn','paper_primary_'),('conv_layer','paper_ideal_pnr_'),('dla_like.small','paper_ideal_pnr_')]:
        before=BASE/'runs'/(prefix+case+'_w300')
        after=BASE/'runs'/(('paper_guardfix_route_pnr_' if case=='bnn' else 'paper_guardfix_ideal_pnr_')+case+'_w300')
        a,b=(json.loads((p/'manifest.json').read_text()) for p in (before,after))
        ia={p:h for p,h in a['inputs'].items() if p!=a['command'][0]}
        ib={p:h for p,h in b['inputs'].items() if p!=b['command'][0]}
        ah,bh=(canonical_packing(p/'packed.net') for p in (before,after))
        row={'case':case,'before':str(before),'after':str(after),
             'command_identical_except_binary_and_output_paths':normalized_command(a)==normalized_command(b),
             'identical_architecture_blif_rrg_hashes':ia==ib,
             'identical_environment':a['environment_overrides']==b['environment_overrides'],
             'identical_timeout':a['timeout_seconds']==b['timeout_seconds'],
             'canonical_packing_identical':ah==bh,'canonical_packing_sha256':ah,
             'original_packing_sha256':sha256(before/'packed.net'),'guardfix_packing_sha256':sha256(after/'packed.net')}
        assert all(row[k] for k in ('command_identical_except_binary_and_output_paths','identical_architecture_blif_rrg_hashes',
                                   'identical_environment','identical_timeout','canonical_packing_identical'))
        rows.append(row)
    build=json.loads((ROOT/'artifacts/bin/lazagna-guardfix/manifest.json').read_text())
    assert sha256(build['original_source'])==build['original_source_sha256']
    assert sha256(build['patched_source'])==build['patched_source_sha256']
    assert sha256(ROOT/'artifacts/bin/lazagna-guardfix/vpr')==build['binary_sha256']
    write_json(BASE/'guardfix_input_equivalence.json',{'utc':utc(),'passed':True,'pairs':rows,
        'canonicalization':'Only the root packed.net block name, which contains its output filename, is replaced before C14N hashing. Architecture ID, atom-netlist ID, all blocks, nets, pins and connectivity remain included.',
        'build_manifest_sha256':sha256(ROOT/'artifacts/bin/lazagna-guardfix/manifest.json')})
    print('All three matched controls and canonical packings pass',flush=True)


if __name__=='__main__':main()
