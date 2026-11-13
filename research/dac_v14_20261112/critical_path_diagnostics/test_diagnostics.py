from inspect_paths import report_points
from compare_connections import extract
from check_route import TraceNode
text='''Point       Incr      Path
clock clk (rise edge) 0.000 0.000
clk.inpad[0] (.input) 0.000 0.000
a.Q[0] (.latch) [clock-to-output] 0.151 0.231
b.in[2] (.names) 1.292 1.523
data arrival time 1.523
clock clk (rise edge) 0.000 0.000
b.clk[0] (.latch) 0.080 0.080
'''
points=report_points(text)
assert [p['pin'] for p in points]==['clk.inpad[0]','a.Q[0]','b.in[2]']
assert points[-1]['increment_ns']==1.292
# Branch one crosses layers; branch two reuses the root and remains planar.
def node(i,kind,xy,sw,pin=None):return TraceNode(i,kind,xy,xy,sw,pin)
trace=[node(0,'SOURCE',(1,1,0),4),node(1,'OPIN',(1,1,0),5),node(2,'SINK',(2,2,1),-1,1),node(0,'SOURCE',(1,1,0),6),node(3,'SINK',(3,3,0),-1,2)]
a=extract({'trace':trace},(2,2,0,1));b=extract({'trace':trace},(3,3,0,0))
assert a==[dict(sink=2,nodes=[2,1,0],switches=[5,4],crossings=[1])]
assert b==[dict(sink=3,nodes=[3,0],switches=[6],crossings=[])]
assert extract({'trace':trace},(9,9,0,0))==[]
print('timing table boundary and branch-specific RR switch path checks passed')
