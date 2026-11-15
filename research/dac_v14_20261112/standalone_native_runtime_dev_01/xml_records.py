"""Unchanged bounded-memory XML record stream."""
from lxml import etree
def records(path):
    sections={'rr_nodes','rr_edges','switches','segments','block_types','grid','channels'}
    with open(path,'rb') as stream:
        for _,e in etree.iterparse(stream,events=('end',),huge_tree=True):
            parent=e.getparent()
            if parent is not None and parent.tag in sections:
                yield parent.tag,e
                e.clear()
                while e.getprevious() is not None:
                    del parent[0]
