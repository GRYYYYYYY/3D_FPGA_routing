#!/usr/bin/env python3
"""Describe candidate/delay coverage without treating planning counts as QoR."""
from collections import defaultdict
from statistics import fmean


def summarize(rows):
    groups=defaultdict(list)
    for row in rows:
        if row['configuration']['router']=='R1':
            groups[row['phase'],row['family'],row['flow'],row['role']].append(row)
    output=[]
    for (phase,family,flow,role),members in sorted(groups.items()):
        legal=[r for r in members if r['status']=='legal']
        rates=defaultdict(list);counts=defaultdict(int)
        for row in legal:
            score=row.get('guide_coverage',{});search=row.get('delay_search',{})
            for name in ['eligible','skipped','delay_scored','unmeasured']:counts[name]+=score.get(name,0)
            for name in ['queries','settled','truncated','cache_hits']:counts[name]+=search.get(name,0)
            if score.get('eligible',0)+score.get('skipped',0)>0:
                rates['selected_pin_fraction'].append(score['eligible']/(score['eligible']+score['skipped']))
            if score.get('delay_scored',0)+score.get('unmeasured',0)>0:
                rates['fully_delay_scored_pin_fraction'].append(score['delay_scored']/(score['delay_scored']+score['unmeasured']))
            if search.get('queries',0)>0:rates['truncated_query_fraction'].append(search['truncated']/search['queries'])
        output.append(dict(phase=phase,family=family,flow=flow,role=role,registered_roles=len(members),legal_roles=len(legal),
            count_totals=dict(counts),run_mean_fractions={k:dict(mean=fmean(v),valid_runs=len(v)) for k,v in rates.items()}))
    return dict(groups=output,
        scope='Descriptive arithmetic mean of legal-run fractions, with valid-run and registered-role counts; not CPD statistics. Different roles may alias one actual run.',
        interpretation='Delay-scored pins require enough forward/reverse-covered candidates for K alternatives. No delay query (e.g. geometry variant) is missing/not applicable, not zero coverage. A bounded-search truncation is not an infeasibility certificate.')
