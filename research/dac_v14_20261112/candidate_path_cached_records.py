"""Exact non-time records for cached-score controls; preserve physical seconds."""
import re
from candidate_path_records import records as previous_records

def records(lines,allowed_prefixes=None):
    result=[]
    for line in previous_records(lines,allowed_prefixes):
        if line.startswith('H3D_CANDIDATE_PATH_CAPTURE '):continue
        if line.startswith('H3D_PATH_PRICE_SCORE_SUMMARY '):
            line=re.sub(r'\b(score_seconds|resolve_seconds)=\S+',r'\1=<elapsed>',line)
        result.append(line)
    return result
