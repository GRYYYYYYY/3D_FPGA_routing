"""Exact finite bottleneck assignment, a relaxation of shared RR-path routing."""

def assignment_at(matrix, capacities, offsets, threshold):
    slots=[(node,i) for node in sorted(capacities) for i in range(capacities[node])]
    choices={agent:[s for s in slots if s[0] in row and row[s[0]]+offsets[agent]<=threshold] for agent,row in matrix.items()}
    owner={}
    def augment(agent,seen):
        for slot in choices[agent]:
            if slot in seen:continue
            seen.add(slot)
            if slot not in owner or augment(owner[slot],seen):
                owner[slot]=agent;return True
        return False
    for agent in sorted(matrix,key=lambda a:(len(choices[a]),a)):
        if not augment(agent,set()):return None
    result={agent:slot[0] for slot,agent in owner.items()}
    assert len(result)==len(matrix)
    return result

def bottleneck(matrix,capacities,offsets):
    values=sorted({cost+offsets[agent] for agent,row in matrix.items() for node,cost in row.items() if capacities.get(node,0)>0})
    if not values or assignment_at(matrix,capacities,offsets,values[-1]) is None:
        return dict(status='infeasible')
    lo,hi=0,len(values)-1
    while lo<hi:
        mid=(lo+hi)//2
        if assignment_at(matrix,capacities,offsets,values[mid]) is None:lo=mid+1
        else:hi=mid
    match=assignment_at(matrix,capacities,offsets,values[lo])
    assert lo==0 or assignment_at(matrix,capacities,offsets,values[lo-1]) is None
    return dict(status='optimal',objective=values[lo],assignment=match,
                predecessor_threshold=None if lo==0 else values[lo-1])
