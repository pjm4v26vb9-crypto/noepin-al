import unittest
from dataclasses import replace
from noepin_al_068_evidence_sufficiency_stopper import *

NOW=1_800_000_000

def base(risk=Risk.HIGH):
    return default_policy(NOW), default_claims(), default_sources(), default_evidence(NOW), default_request(NOW,risk)

class T(unittest.TestCase):
    def test_001_sufficient_independent_evidence(self):
        p,c,s,e,r=base(); z=evaluate(r,p,c,s,e,now=NOW); self.assertEqual(z.decision,Decision.ALLOW); self.assertTrue(z.next_gate_candidate); self.assertEqual(z.independent_source_count,3)
    def test_002_duplicate_source_group_not_double_counted(self):
        p,c,s,e,r=base(); z=evaluate(r,p,c,s,e,now=NOW); self.assertEqual(z.independent_source_count,3); self.assertIn("E-A-COPY",z.duplicate_evidence_ids)
    def test_003_old_evidence_decays(self):
        p,c,s,e,r=base(); e=tuple(replace(x,observed_at=NOW-600) if x.evidence_id=="E-C" else x for x in e); z=evaluate(r,p,c,s,e,now=NOW); self.assertEqual(z.stale_source_count,1); self.assertLess(z.evidence_score,2.3175)
    def test_004_high_risk_insufficient_hold(self):
        p,c,s,e,r=base(); e=e[:2]; z=evaluate(r,p,c,s,e,now=NOW); self.assertEqual(z.decision,Decision.HOLD); self.assertIn("INDEPENDENT_SOURCES",z.missing_requirements)
    def test_005_no_evidence_hold(self):
        p,c,s,e,r=base(); self.assertEqual(evaluate(r,p,c,s,(),now=NOW).decision,Decision.HOLD)
    def test_006_expired_evidence_excluded(self):
        p,c,s,e,r=base(); e=tuple(replace(x,expires_at=NOW-1) if x.evidence_id=="E-C" else x for x in e); z=evaluate(r,p,c,s,e,now=NOW); self.assertEqual(z.decision,Decision.HOLD); self.assertIn("E-C",z.excluded_evidence_ids)
    def test_007_low_confidence_excluded(self):
        p,c,s,e,r=base(); e=tuple(replace(x,confidence=.1) if x.evidence_id=="E-C" else x for x in e); self.assertEqual(evaluate(r,p,c,s,e,now=NOW).decision,Decision.HOLD)
    def test_008_contradictory_evidence_hold(self):
        p,c,s,e,r=base(); e=e+(replace(e[0],evidence_id="E-CONTRA",source_id="SRC-C",state=EvidenceState.CONTRADICTS),); z=evaluate(r,p,c,s,e,now=NOW); self.assertEqual(z.decision,Decision.HOLD); self.assertIn("E-CONTRA",z.contradictory_evidence_ids)
    def test_009_medium_sufficient(self):
        p,c,s,e,r=base(Risk.MEDIUM); z=evaluate(r,p,c,s,e[:2],now=NOW); self.assertEqual(z.decision,Decision.ALLOW)
    def test_010_critical_requires_four_sources(self):
        p,c,s,e,r=base(Risk.CRITICAL); self.assertEqual(evaluate(r,p,c,s,e,now=NOW).decision,Decision.HOLD)
    def test_011_critical_sufficient_requires_human(self):
        p,c,s,e,r=base(Risk.CRITICAL); common=dict(binding="ESS-BIND",verified=True,revoked=False,policy_id="ESS-POLICY",policy_version="1",authority_epoch="ESS-EPOCH"); s=s+(SourceMetadata("SRC-D","GROUP-D","AUDIT",**common),); e=e+(EvidenceRecord("E-D","CLAIM-CONFIG-SAFE","SRC-D",EvidenceKind.DIRECT,EvidenceState.SUPPORTS,.95,NOW-5,NOW+1000,**common),); z=evaluate(r,p,c,s,e,now=NOW); self.assertEqual(z.decision,Decision.HUMAN_APPROVAL); self.assertFalse(z.approval_executed)
    def test_012_policy_identity_mismatch(self):
        p,c,s,e,r=base(); r=replace(r,expected_policy_version="X"); self.assertEqual(evaluate(r,p,c,s,e,now=NOW).decision,Decision.HOLD)
    def test_013_binding_mismatch(self):
        p,c,s,e,r=base(); r=replace(r,binding="X"); self.assertEqual(evaluate(r,p,c,s,e,now=NOW).decision,Decision.HOLD)
    def test_014_stale_request(self):
        p,c,s,e,r=base(); r=replace(r,created_at=NOW-9999); self.assertEqual(evaluate(r,p,c,s,e,now=NOW).decision,Decision.HOLD)
    def test_015_unknown_claim(self):
        p,c,s,e,r=base(); r=replace(r,claim_id="NOPE"); self.assertEqual(evaluate(r,p,c,s,e,now=NOW).decision,Decision.HOLD)
    def test_016_prepared_allow(self):
        p,c,s,e,r=base(); st=prepare_state(p,c,s,e,binding=r.binding,now=NOW); self.assertTrue(validate_prepared_integrity(st)); z=evaluate_prepared(r,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True,now=NOW); self.assertEqual(z.decision,Decision.ALLOW)
    def test_017_prepared_integrity_required(self):
        p,c,s,e,r=base(); st=prepare_state(p,c,s,e,binding=r.binding,now=NOW); self.assertEqual(evaluate_prepared(r,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False,now=NOW).decision,Decision.HOLD)
    def test_018_prepared_tamper_detected(self):
        p,c,s,e,r=base(); st=prepare_state(p,c,s,e,binding=r.binding,now=NOW); tam=replace(st,evidence=(replace(st.evidence[0],confidence=.01),)+st.evidence[1:]); self.assertFalse(validate_prepared_integrity(tam))
    def test_019_freshness_recomputed_in_prepared(self):
        p,c,s,e,r=base(); st=prepare_state(p,c,s,e,binding=r.binding,now=NOW); z1=evaluate_prepared(r,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True,now=NOW); z2=evaluate_prepared(r,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True,now=NOW+700); self.assertGreater(z1.evidence_score,z2.evidence_score)
    def test_020_delta_reconstruct(self):
        p,c,s,e,r=base(); s1=prepare_state(p,c,s,e,binding=r.binding,now=NOW); e2=tuple(replace(x,confidence=.91) if x.evidence_id=="E-B" else x for x in e); s2=prepare_state(p,c,s,e2,binding=r.binding,now=NOW); d=make_delta(s1,s2); s3=apply_delta(s1,d,now=NOW); self.assertEqual(s2.registry_fingerprint,s3.registry_fingerprint)
    def test_021_delta_base_mismatch(self):
        p,c,s,e,r=base(); st=prepare_state(p,c,s,e,binding=r.binding,now=NOW); d=replace(make_delta(st,st),base_fingerprint="bad");
        with self.assertRaises(ValueError): apply_delta(st,d,now=NOW)
    def test_022_missing_only_sync(self):
        p,c,s,e,r=base(); st=prepare_state(p,c,s,e,binding=r.binding,now=NOW); remote={"claims":dict(st.claim_fingerprints),"sources":dict(st.source_fingerprints),"evidence":dict(st.evidence_fingerprints)}; remote["evidence"].pop("E-C"); q=missing_only_sync_plan(st,remote); self.assertEqual(q.missing_or_changed_evidence_ids,("E-C",)); self.assertFalse(q.full_resend_required)
    def test_023_authority_false(self):
        p,c,s,e,r=base(); z=evaluate(r,p,c,s,e,now=NOW); self.assertFalse(any((z.permission_granted,z.truth_proven,z.evidence_written,z.approval_executed,z.data_sent,z.action_executed,z.safety_proven,z.action_success)))
    def test_024_invalid_source_hold(self):
        p,c,s,e,r=base(); s=s[:2]+(replace(s[2],revoked=True),)+s[3:]; self.assertEqual(evaluate(r,p,c,s,e,now=NOW).decision,Decision.HOLD)
    def test_025_duplicate_evidence_id_invalid(self):
        p,c,s,e,r=base(); self.assertEqual(evaluate(r,p,c,s,e+(e[0],),now=NOW).decision,Decision.HOLD)

def _gen(i):
    def f(self):
        p,c,s,e,r=base(); m=i%5
        if m==0:
            z=evaluate(r,p,c,s,e,now=NOW); self.assertEqual(z.decision,Decision.ALLOW)
        elif m==1:
            z=evaluate(r,p,c,s,e[:2],now=NOW); self.assertEqual(z.decision,Decision.HOLD)
        elif m==2:
            ee=tuple(replace(x,expires_at=NOW-1) if x.evidence_id=="E-C" else x for x in e); z=evaluate(r,p,c,s,ee,now=NOW); self.assertEqual(z.decision,Decision.HOLD)
        elif m==3:
            rr=replace(r,action_risk=Risk.MEDIUM); z=evaluate(rr,p,c,s,e[:2],now=NOW); self.assertEqual(z.decision,Decision.ALLOW)
        else:
            ee=e+(replace(e[0],evidence_id=f"C{i}",source_id="SRC-C",state=EvidenceState.CONTRADICTS),); z=evaluate(r,p,c,s,ee,now=NOW); self.assertEqual(z.decision,Decision.HOLD)
        self.assertFalse(z.permission_granted); self.assertFalse(z.action_executed); self.assertFalse(z.action_success)
    return f
for i in range(135): setattr(T,f"test_regression_{i:03d}",_gen(i))

if __name__=='__main__': unittest.main()
