"""Schematic dependency diagram bound to completed mechanism evidence."""
import os
from pathlib import Path
from retained_prefix_workflow import D, read, write, sha
out=D/'submission_narrative_02'
os.environ['MPLCONFIGDIR']=str(out/'.mplconfig')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,FancyArrowPatch

plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8,'pdf.fonttype':42})
fig,axes=plt.subplots(1,3,figsize=(7.15,2.00))
blue='#225b9c';orange='#b65319';green='#2a7951';gray='#62666a'
def node(ax,xy,label,color=blue,r=.055):
    ax.add_patch(Circle(xy,r,facecolor='white',edgecolor=color,lw=1.4,zorder=4))
    ax.text(*xy,label,ha='center',va='center',fontsize=8,color=color,zorder=5)
def edge(ax,a,b,color=blue,dashed=False,curve=0):
    ax.add_patch(FancyArrowPatch(a,b,arrowstyle='-|>',mutation_scale=8,lw=1.4,
        color=color,linestyle='--' if dashed else '-',connectionstyle=f'arc3,rad={curve}',zorder=2))
for ax in axes:ax.set(xlim=(0,1),ylim=(0,1));ax.axis('off')
a=axes[0];a.set_title('(a) Complete shared branch',fontsize=9,pad=3)
for xy,label in [((.10,.48),'s'),((.37,.72),'r'),((.37,.23),'q'),((.84,.83),'a'),((.84,.58),'b'),((.84,.18),'c')]:node(a,xy,label)
for u,v in [((.15,.50),(.32,.69)),((.15,.45),(.32,.26)),((.42,.74),(.79,.82)),((.42,.70),(.79,.59)),((.42,.22),(.79,.18))]:edge(a,u,v)
edge(a,(.42,.26),(.79,.56),green,True,curve=.12)
edge(a,(.42,.28),(.80,.80),green,True,curve=-.16)
a.text(.34,.89,'shared r',ha='center',color=blue,fontsize=7)
a.text(.32,.07,'retained q',ha='center',color=green,fontsize=7)
a.text(.51,.96,'',ha='center')
a.text(.53,.43,'move both a,b',ha='center',color=green,fontsize=7)
a.text(.50,-.05,'Moving a alone keeps r occupied.',ha='center',fontsize=7)
b=axes[1];b.set_title('(b) Domain obstruction / release',fontsize=9,pad=3)
for xy,label in [((.11,.25),'s'),((.29,.74),'q'),((.69,.74),'v'),((.88,.25),'t')]:node(b,xy,label,color=orange if label=='v' else blue)
edge(b,(.13,.30),(.27,.69));edge(b,(.34,.74),(.64,.74));edge(b,(.71,.69),(.86,.30),orange,True)
b.plot([.65,.83],[.46,.53],color=orange,lw=2)
b.text(.54,.90,'retained q allowed',ha='center',fontsize=7,color=blue)
b.text(.64,.41,'v initially excluded',ha='center',fontsize=7,color=orange)
b.text(.50,.10,'relax this net to permit v',ha='center',fontsize=7,color=green)
b.text(.50,-.05,'Other nets keep their domains.',ha='center',fontsize=7)
c=axes[2];c.set_title('(c) Coordinate blocking owner',fontsize=9,pad=3)
for xy,label,col in [((.10,.56),'s',blue),((.47,.56),'e',orange),((.88,.56),'t',blue),((.47,.16),'o',orange),((.84,.16),'u',orange)]:node(c,xy,label,col)
edge(c,(.15,.56),(.42,.56));edge(c,(.52,.56),(.83,.56));edge(c,(.47,.21),(.47,.50),orange)
edge(c,(.52,.16),(.79,.16),green,True)
c.text(.49,.85,'owner o occupies exit e',ha='center',fontsize=7,color=orange)
c.text(.49,.75,'capacity(e) = 1',ha='center',fontsize=7)
c.text(.69,.31,'reroute owner',ha='center',fontsize=7,color=green)
c.text(.50,-.05,'Accept target + owner together.',ha='center',fontsize=7)
fig.subplots_adjust(left=.025,right=.985,top=.82,bottom=.15,wspace=.13)
fig.savefig(out/'data/dependency_mechanisms.pdf',bbox_inches='tight',pad_inches=.03)
fig.savefig(out/'data/dependency_mechanisms.png',dpi=180,bbox_inches='tight',pad_inches=.03)
sources=['shared_crossing_scopes_01/completion.json','robot_union_mechanism_02/verification_v2.json','R1_owner_release_joint_probe_01/verification.json']
assert all(read(D/n)['passed'] for n in sources)
write(out/'mechanism_figure_binding.json',dict(passed=True,source_sha256={str(D/n):sha(D/n) for n in sources},
    figure_sha256=sha(out/'data/dependency_mechanisms.pdf'),schematic_not_device_coordinates=True,
    claims=['Complete dependent branch removal is needed to free a shared resource.',
    'Robot fixed-scope no-release fails; release permits a different CB tradeoff than unrestricted.',
    'R1 native/domain identical after owner expansion; coordination receives attribution.'],
    no_new_experiment=True,not_a_claim_of_universal_gain=True))
