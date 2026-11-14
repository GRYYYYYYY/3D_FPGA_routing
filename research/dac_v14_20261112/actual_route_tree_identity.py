"""Order/header independent identity of actual serialized trees and terminals."""
import collections
import hashlib
import json
from coordinated_repair_tree import from_trace
from resource_opportunity_census import stream_trace

def tree_identity(path):
    result = {}
    for record in stream_trace(path):
        net = record['net']
        assert net not in result, 'Duplicate serialized net'
        tree = from_trace(record['trace'], collections.defaultdict(float)) if record['trace'] else None
        payload = None if tree is None else [tree['root'],
            sorted((node, edge[0], edge[1]) for node, edge in tree['edges'].items()),
            sorted(tree['sinks'].items())]
        result[net] = hashlib.sha256(json.dumps(payload, separators=(',', ':')).encode()).hexdigest()
    return result

def same_actual_trees(left, right):
    return tree_identity(left) == tree_identity(right)
