"""Conservative observed-state dominance; no missing-time substitution."""
def dominates(a,b,with_time=False,interval=True):
 names=['wirelength','SB_pairs','CB_sources']+(['complete_single_configuration_seconds'] if with_time else [])
 if any(a[k] is None or b[k] is None or a[k]>b[k] for k in names):return False
 identical=a['route_body_sha256']==b['route_body_sha256'] and a['binary_sha256']==b['binary_sha256']
 if interval and not identical:
  if a['CPD_interval_ns'][1]>b['CPD_interval_ns'][0]:return False
  strict=a['CPD_interval_ns'][1]<b['CPD_interval_ns'][0]
 else:
  if a['CPD_ns']>b['CPD_ns']:return False
  strict=a['CPD_ns']<b['CPD_ns']
 return strict or any(a[k]<b[k] for k in names)

def annotate(points):
 for b in points:
  b.update(quality_dominated_by=[],nominal_quality_dominated_by=[],matched_time_dominated_by=[])
  matched=[]
  for a in points:
   if a['id']==b['id'] or a['quality_cohort']!=b['quality_cohort']:continue
   if dominates(a,b):b['quality_dominated_by'].append(a['id'])
   if dominates(a,b,interval=False):b['nominal_quality_dominated_by'].append(a['id'])
   if a['timing_cohort'] and a['timing_cohort']==b['timing_cohort'] and a['convergence']==b['convergence'] and a['complete_single_configuration_seconds'] is not None and b['complete_single_configuration_seconds'] is not None:
    matched.append(a)
    if dominates(a,b,True):b['matched_time_dominated_by'].append(a['id'])
  b['quality_projection_retained']=not b['quality_dominated_by']
  b['quality_status']='dominated' if b['quality_dominated_by'] else 'uncertain_due_to_CPD_precision' if b['nominal_quality_dominated_by'] else 'nondominated_in_collected_population'
  b['candidate_retention']='dominated_in_matched_five_dimensions' if b['matched_time_dominated_by'] else 'retained_on_matched_five_dimensional_frontier' if matched else 'retained_pending_comparable_complete_runtime'
  b['archive_retained']=not b['matched_time_dominated_by'];b['record_preserved']=True;b['five_dimensional_comparison_count']=len(matched)
  b['retention_qualification']='Observation-level development archive, not configuration selection or statistical timing dominance. Formal configuration timing summaries use all matched repeats; no fastest-repeat or per-circuit historical-best configuration is nominated. Missing comparable complete algorithm time remains unknown. Four quality axes omit endpoint-vector differences.'
 return points
