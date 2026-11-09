#!/usr/bin/env python3
"""Exact streaming import comparison, with only documented schema exceptions.

Unlike a VPR round trip, our converter preserves all other XML bytes. Comparing
those bytes avoids allocating XML objects for tens of millions of fixed edges.
Locations are compared as attribute maps; unused parser metadata is verified.
"""
from itertools import zip_longest
from pathlib import Path
import re
import xml.etree.ElementTree as ET

ATTR = re.compile(r'(\w+)="([^"]*)"')
LOC = re.compile(r'<loc\s+[^<>]*?(?:/>|></loc>)')


def normalized_lines(path, unused_id=None):
    unused_seen = 0
    with Path(path).open() as stream:
        for line in stream:
            if 'name="unused_native_Z_schema"' in line:
                if unused_id is None: raise ValueError('Unexpected unused schema segment')
                element = ET.fromstring(line)
                assert element.tag == 'segment'
                assert element.attrib == dict(id=str(unused_id),name='unused_native_Z_schema',length='1',res_type='GENERAL')
                assert len(element)==1 and element[0].tag=='timing' and not element[0].attrib
                unused_seen += 1
                assert unused_seen == 1
                continue
            if 'segment_id="' in line and unused_id is not None:
                assert int(dict(ATTR.findall(line))['segment_id']) != unused_id
            if '<loc ' in line:
                matches=list(LOC.finditer(line));assert len(matches)==1
                match=matches[0]
                element = ET.fromstring(match[0])
                assert element.tag=='loc' and len(element)==0
                attributes=dict(element.attrib)
                if 'layer' in attributes:
                    assert 'layer_low' not in attributes and 'layer_high' not in attributes
                    layer=attributes.pop('layer')
                    attributes.update(layer_low=layer,layer_high=layer)
                assert attributes['layer_low']==attributes['layer_high']
                if 'twist' in attributes:
                    assert attributes.pop('twist')=='0'
                yield ('location',line[:match.start()],tuple(sorted(attributes.items())),line[match.end():])
            else:
                yield ('exact_xml_line',line)
    assert unused_seen == (1 if unused_id is not None else 0)


def verify(original, converted, unused_id):
    count=0
    for a,b in zip_longest(normalized_lines(original),normalized_lines(converted,unused_id)):
        if a != b: raise ValueError(f'Import changed graph at compared line {count}')
        count+=1
    return dict(passed=True,exact_compared_lines=count,unused_segment_id=unused_id,
        method='All XML lines exactly equal, except location attributes normalized by independent XML parser and one verified unused segment; reject any node referencing the unused segment')
