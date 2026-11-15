"""Exact XML stream and native float32 conversion, without old experiment CLI."""
import struct
from lxml import etree

def graph_records(path):
    # Independent of the C++ RR reader and existing route-audit adapters.
    with path.open('rb') as stream:
        for _,element in etree.iterparse(stream,events=('end',),huge_tree=True):
            parent=element.getparent()
            if parent is not None and parent.tag in ['rr_nodes','rr_edges','switches']:
                yield parent.tag,element
                element.clear()
                while element.getprevious() is not None:del parent[0]

def f32(value):return struct.unpack('f',struct.pack('f',float(value)))[0]
