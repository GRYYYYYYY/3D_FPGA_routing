"""Compare VPR's six-significant-digit display separately from exact STA identity."""
import math

def check(report_ns, source_manifest_ns, source_vector, observed_vector):
    numbers=[report_ns,source_manifest_ns,source_vector['cpd_s'],observed_vector['cpd_s']]
    assert all(isinstance(x,(int,float)) and math.isfinite(x) and x>0 for x in numbers)
    displayed=lambda ns:float(format(ns,'.6g'))
    expected=displayed(source_vector['cpd_s']*1e9)
    checks=dict(source_manifest_report_consistent=displayed(source_manifest_ns)==expected,
        source_display_matches_observed_report=report_ns==expected,
        observed_full_precision_matches_report=displayed(observed_vector['cpd_s']*1e9)==report_ns,
        full_precision_CPD_exact=source_vector['cpd_s']==observed_vector['cpd_s'])
    for key in ['setup','hold','endpoint_ids','constraints_sha256']:
        checks[key+'_exact']=source_vector[key]==observed_vector[key]
    return dict(passed=all(checks.values()),checks=checks,
        source_full_precision_CPD_s=source_vector['cpd_s'],
        observed_full_precision_CPD_s=observed_vector['cpd_s'],
        displayed_CPD_ns=report_ns,
        qualification='Rounding applies only to displayed/manifest report fields. Actual CPD, setup, hold, identities and constraints must match exactly; no acceptance tolerance is introduced.')
