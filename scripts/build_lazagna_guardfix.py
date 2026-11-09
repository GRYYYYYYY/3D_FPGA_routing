#!/usr/bin/env python3
"""Build a one-object guard correction without changing published checkouts."""
import difflib
import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
from lazagna_common import BASE,ROOT,PAPER,run,sha256,utc,write_json


def main():
    dest=ROOT/'artifacts/bin/lazagna-guardfix';dest.mkdir(parents=True,exist_ok=True)
    if (dest/'manifest.json').exists():raise RuntimeError('Guardfix already built')
    source=PAPER/'OpenFPGA/vtr-verilog-to-routing/vpr/src/place/move_utils.cpp'
    old=source.read_text();new=old
    guards=[line for line in old.splitlines() if line.strip().startswith('if (') and '!= OPEN' in line and ('compressed_loc.x' in line or 'from_compressed_loc.x' in line)]
    assert len(guards)==2,guards
    for line in guards:new=new.replace(line,line.replace('!= OPEN','== OPEN'),1)
    patch=''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/vpr/src/place/move_utils.cpp',tofile='b/vpr/src/place/move_utils.cpp'))
    patchpath=ROOT/'patches/lazagna-placement-validity-guards.patch';patchpath.write_text(patch)
    patched=dest/'move_utils.cpp';patched.write_text(new)
    def functions(text):
        start=text.index('t_bb get_compressed_grid_target_search_range(')
        end=text.index('bool intersect_range_limit_with_floorplan_constraints(',start)
        return text[start:end]
    test=dest/'guard_behavior_test.cpp'
    test.write_text('''#include <algorithm>\n#include <cassert>\n#include <iostream>\nconstexpr int OPEN=-1;
struct t_physical_tile_loc { int x,y,layer_num; };
struct t_bb { int xmin,xmax,ymin,ymax,layer_min,layer_max; t_bb():xmin(-1),xmax(-1),ymin(-1),ymax(-1),layer_min(-1),layer_max(-1){} t_bb(int a,int b,int c,int d,int e,int f):xmin(a),xmax(b),ymin(c),ymax(d),layer_min(e),layer_max(f){} };
struct t_compressed_block_grid { int get_num_columns(int layer)const {assert(layer>=0&&layer<2);return 40;} int get_num_rows(int layer)const {assert(layer>=0&&layer<2);return 40;} };
namespace released {\n'''+functions(old)+'\n}\nnamespace repaired {\n'+functions(new)+'''\n}
int main(){t_compressed_block_grid g;
 for(int z: {0,1}) { t_physical_tile_loc a{10,12,z},b{20,22,z};
 auto old=released::get_compressed_grid_target_search_range(g,a,3); assert(old.xmin==OPEN);
 auto x=repaired::get_compressed_grid_target_search_range(g,a,3); assert(x.xmin==7&&x.xmax==13&&x.ymin==9&&x.ymax==15&&x.layer_min==z);
 auto old2=released::get_compressed_grid_bounded_search_range(g,a,b,3);assert(old2.xmin==OPEN);
 auto y=repaired::get_compressed_grid_bounded_search_range(g,a,b,3);assert(y.xmin==10&&y.xmax==13&&y.ymin==12&&y.ymax==15&&y.layer_min==z);
 }
 for(auto bad: {t_physical_tile_loc{OPEN,0,0},t_physical_tile_loc{0,OPEN,0},t_physical_tile_loc{0,0,OPEN}}){
 assert(repaired::get_compressed_grid_target_search_range(g,bad,3).xmin==OPEN);
 assert(repaired::get_compressed_grid_bounded_search_range(g,{10,10,0},bad,3).xmin==OPEN);
 }
 std::cout<<"Both original valid-coordinate rejection defects reproduced; corrected functions accept valid locations and reject each invalid coordinate.\\n";
}''')
    r=run('guardfix_unit_compile_v2',['/usr/bin/c++','-std=c++17','-O2',test,'-o',dest/'guard_behavior_test'],inputs=[test],timeout=120)
    assert r['status']=='completed'
    r=run('guardfix_unit_test_v2',[dest/'guard_behavior_test'],inputs=[dest/'guard_behavior_test'],timeout=30)
    assert r['status']=='completed'
    build=PAPER/'OpenFPGA/build/vtr-verilog-to-routing/vpr'
    flagsfile=build/'CMakeFiles/libvpr.dir/flags.make';flags=flagsfile.read_text();args=[]
    for key in ['CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS']:
        args+=shlex.split(re.search(r'^'+key+r' = (.*)$',flags,re.M)[1])
    obj=dest/'move_utils.cpp.o'
    r=run('guardfix_object_compile',['/usr/bin/c++',*args,'-o',obj,'-c',patched],cwd=build,inputs=[source,patched,flagsfile],timeout=600)
    assert r['status']=='completed'
    original=build/'libvpr.a';library=dest/'libvpr.a';shutil.copy2(original,library)
    members=subprocess.check_output(['ar','t',original],text=True).splitlines();assert members.count('move_utils.cpp.o')==1
    r=run('guardfix_archive_replace',['ar','r',library,obj],inputs=[original,obj],timeout=120);assert r['status']=='completed'
    assert subprocess.check_output(['ar','t',library],text=True).splitlines()==members
    linkfile=build/'CMakeFiles/vpr.dir/link.txt';link=shlex.split(linkfile.read_text())
    link[link.index('-o')+1]=str(dest/'vpr');link[link.index('libvpr.a')]=str(library)
    r=run('guardfix_link',link,cwd=build,inputs=[linkfile,library,ROOT/'artifacts/bin/lazagna-paper/vpr'],timeout=300)
    assert r['status']=='completed'
    assert sha256(source)==sha256(dest/'move_utils.cpp') or source.read_text()==old
    write_json(dest/'manifest.json',{'utc':utc(),'binary_sha256':sha256(dest/'vpr'),'original_source':str(source),'original_source_sha256':sha256(source),
        'patched_source':str(patched),'patched_source_sha256':sha256(patched),'patch':str(patchpath),'patch_sha256':sha256(patchpath),
        'scope':'Only move_utils.cpp.o replaced in a copied libvpr.a; all other objects, main object, linked libraries and compile flags reuse the original build. Published source tree and original binary unchanged.',
        'bug_introduced_by':'af5b6a4434','tests':'Extracted original and repaired function bodies compiled and exercised for valid coordinates on both layers and invalid x/y/layer.'})
    print(dest/'vpr',flush=True)


if __name__=='__main__':main()
