from __future__ import annotations
import ast, dataclasses, unittest
from pathlib import Path
import noepin_al_049_model_trust_router as m

NOW=1_800_000_000

def pol(**kw): return dataclasses.replace(m.default_policy(NOW),**kw)
def profs(): return m.default_profiles(NOW)
def req(**kw): return dataclasses.replace(m.default_request(NOW),**kw)

class CoreTests(unittest.TestCase):
    def test_001_default_allow_local(self):
        o=m.evaluate(req(),pol(),profs(),now=NOW); self.assertEqual(o.decision,m.ControlDecision.ALLOW); self.assertEqual(o.selected_location,"LOCAL")
    def test_002_no_permission_execution(self):
        o=m.evaluate(req(),pol(),profs(),now=NOW); self.assertFalse(o.permission_granted or o.model_invoked or o.data_transferred or o.action_success)
    def test_003_no_truth_or_verification_promotion(self):
        o=m.evaluate(req(),pol(),profs(),now=NOW); self.assertFalse(o.trust_truth_established); self.assertFalse(o.verification_pass_proven)
    def test_004_restricted_local_required(self):
        o=m.evaluate(req(sensitivity=m.Sensitivity.RESTRICTED,risk_score=.3),pol(),profs(),now=NOW); self.assertEqual(o.selected_location,"LOCAL")
    def test_005_restricted_cloud_rejected(self):
        o=m.evaluate(req(sensitivity=m.Sensitivity.RESTRICTED),pol(),profs(),now=NOW); self.assertIn("LOCAL_REQUIRED",o.rejected_model_reasons["CLOUD-TRUST-1"])
    def test_006_external_processing_false_blocks_cloud(self):
        pp=tuple(p for p in profs() if p.location==m.ModelLocation.CLOUD); o=m.evaluate(req(external_processing_allowed=False),pol(),pp,now=NOW); self.assertEqual(o.decision,m.ControlDecision.DENY)
    def test_007_cloud_confidential_requires_approval(self):
        pp=(profs()[2],); o=m.evaluate(req(sensitivity=m.Sensitivity.CONFIDENTIAL,risk_score=.3),pol(),pp,now=NOW); self.assertEqual(o.decision,m.ControlDecision.HUMAN_APPROVAL)
    def test_008_cloud_confidential_approval_evidence_candidate(self):
        pp=(profs()[2],); o=m.evaluate(req(sensitivity=m.Sensitivity.CONFIDENTIAL,risk_score=.3,human_approval_evidence_verified=True),pol(),pp,now=NOW); self.assertEqual(o.decision,m.ControlDecision.ALLOW); self.assertFalse(o.permission_granted)
    def test_009_untrusted_provider(self):
        p=dataclasses.replace(profs()[0],provider_id="UNKNOWN"); o=m.evaluate(req(),pol(),(p,),now=NOW); self.assertEqual(o.decision,m.ControlDecision.DENY); self.assertIn("UNTRUSTED_PROVIDER",o.rejected_model_reasons[p.model_id])
    def test_010_revoked_model(self):
        p=dataclasses.replace(profs()[0],revoked=True); o=m.evaluate(req(),pol(),(p,),now=NOW); self.assertEqual(o.decision,m.ControlDecision.DENY)
    def test_011_unverified_model(self):
        p=dataclasses.replace(profs()[0],evidence_verified=False); o=m.evaluate(req(),pol(),(p,),now=NOW); self.assertIn("MODEL_EVIDENCE_UNVERIFIED",o.rejected_model_reasons[p.model_id])
    def test_012_binding_mismatch(self):
        p=dataclasses.replace(profs()[0],evidence_binding="OTHER"); o=m.evaluate(req(),pol(),(p,),now=NOW); self.assertIn("EVIDENCE_BINDING_MISMATCH",o.rejected_model_reasons[p.model_id])
    def test_013_capability_gap(self):
        o=m.evaluate(req(required_capabilities=frozenset({"VISION"})),pol(),profs(),now=NOW); self.assertEqual(o.decision,m.ControlDecision.DENY)
    def test_014_sensitivity_not_supported(self):
        p=dataclasses.replace(profs()[1],allowed_sensitivities=frozenset({m.Sensitivity.PUBLIC})); o=m.evaluate(req(sensitivity=m.Sensitivity.INTERNAL),pol(),(p,),now=NOW); self.assertIn("SENSITIVITY_NOT_SUPPORTED",o.rejected_model_reasons[p.model_id])
    def test_015_trust_below_threshold(self):
        p=dataclasses.replace(profs()[0],trust_score=.69); o=m.evaluate(req(),pol(),(p,),now=NOW); self.assertIn("TRUST_BELOW_SENSITIVITY_THRESHOLD",o.rejected_model_reasons[p.model_id])
    def test_016_high_risk_trust_threshold(self):
        p=dataclasses.replace(profs()[1],trust_score=.89,max_risk=.95); o=m.evaluate(req(risk_score=.8),pol(),(p,),now=NOW); self.assertIn("TRUST_BELOW_HIGH_RISK_THRESHOLD",o.rejected_model_reasons[p.model_id])
    def test_017_model_risk_ceiling(self):
        p=dataclasses.replace(profs()[0],max_risk=.2); o=m.evaluate(req(risk_score=.3),pol(),(p,),now=NOW); self.assertIn("MODEL_RISK_CEILING_EXCEEDED",o.rejected_model_reasons[p.model_id])
    def test_018_policy_binding_id(self):
        o=m.evaluate(req(expected_policy_id="X"),pol(),profs(),now=NOW); self.assertEqual(o.decision,m.ControlDecision.HOLD)
    def test_019_policy_binding_version(self):
        o=m.evaluate(req(expected_policy_version="X"),pol(),profs(),now=NOW); self.assertEqual(o.decision,m.ControlDecision.HOLD)
    def test_020_policy_binding_epoch(self):
        o=m.evaluate(req(expected_authority_epoch=9),pol(),profs(),now=NOW); self.assertEqual(o.decision,m.ControlDecision.HOLD)
    def test_021_policy_revoked(self):
        o=m.evaluate(req(),pol(revoked=True),profs(),now=NOW); self.assertEqual(o.decision,m.ControlDecision.HOLD)
    def test_022_policy_expired(self):
        o=m.evaluate(req(),pol(expires_at=NOW),profs(),now=NOW); self.assertEqual(o.decision,m.ControlDecision.HOLD)
    def test_023_policy_future(self):
        o=m.evaluate(req(),pol(issued_at=NOW+1,expires_at=NOW+100),profs(),now=NOW); self.assertEqual(o.decision,m.ControlDecision.HOLD)
    def test_024_request_invalid_risk(self):
        o=m.evaluate(req(risk_score=1.2),pol(),profs(),now=NOW); self.assertEqual(o.decision,m.ControlDecision.HOLD)
    def test_025_duplicate_model_id(self):
        p=profs()[0]; o=m.evaluate(req(),pol(),(p,p),now=NOW); self.assertEqual(o.decision,m.ControlDecision.HOLD)
    def test_026_too_many_models(self):
        o=m.evaluate(req(),pol(max_models=1),profs(),now=NOW); self.assertEqual(o.decision,m.ControlDecision.HOLD)
    def test_027_prepared_semantic_equality(self):
        ps=profs(); p=pol(); pr=m.prepare_registry(p,ps,now=NOW); self.assertEqual(m.evaluate(req(),p,ps,now=NOW),m.evaluate_prepared(req(),p,ps,pr,now=NOW))
    def test_028_prepared_policy_mismatch(self):
        ps=profs(); p=pol(); pr=m.prepare_registry(p,ps,now=NOW); p2=dataclasses.replace(p,high_risk_min_trust=.91); o=m.evaluate_prepared(req(),p2,ps,pr,now=NOW); self.assertEqual(o.decision,m.ControlDecision.HOLD)
    def test_029_prepared_registry_mismatch(self):
        ps=profs(); p=pol(); pr=m.prepare_registry(p,ps,now=NOW); ps2=(dataclasses.replace(ps[0],trust_score=.95),)+ps[1:]; o=m.evaluate_prepared(req(),p,ps2,pr,now=NOW); self.assertEqual(o.decision,m.ControlDecision.HOLD)
    def test_030_delta_roundtrip(self):
        b=profs(); t=(dataclasses.replace(b[0],trust_score=.95),b[2],dataclasses.replace(b[1],model_id="EDGE-NEW")); d=m.build_registry_delta(b,t); r=m.apply_registry_delta(b,d); self.assertEqual(m.registry_fingerprint(r),m.registry_fingerprint(t))
    def test_031_delta_wrong_base(self):
        b=profs(); t=(dataclasses.replace(b[0],trust_score=.95),)+b[1:]; d=m.build_registry_delta(b,t); bad=(dataclasses.replace(b[0],trust_score=.94),)+b[1:];
        with self.assertRaises(ValueError): m.apply_registry_delta(bad,d)
    def test_032_delta_tamper_target(self):
        b=profs(); t=(dataclasses.replace(b[0],trust_score=.95),)+b[1:]; d=m.build_registry_delta(b,t); d=dataclasses.replace(d,target_fingerprint="0"*64)
        with self.assertRaises(ValueError): m.apply_registry_delta(b,d)
    def test_033_sync_missing_only(self):
        pr=m.prepare_registry(pol(),profs(),now=NOW); known=dict(pr.profile_fingerprints); known.pop("CLOUD-TRUST-1"); s=m.plan_registry_sync(pr,known); self.assertEqual(s.missing_or_changed_model_ids,("CLOUD-TRUST-1",)); self.assertFalse(s.full_resend_required)
    def test_034_sync_no_authority(self):
        pr=m.prepare_registry(pol(),profs(),now=NOW); s=m.plan_registry_sync(pr,{}); self.assertFalse(s.permission_granted or s.model_invocation_authorized or s.data_transfer_authorized)
    def test_035_order_independent_registry_fp(self):
        p=profs(); self.assertEqual(m.registry_fingerprint(p),m.registry_fingerprint(tuple(reversed(p))))
    def test_036_digest_deterministic(self):
        a=[m.evaluate(req(),pol(),profs(),now=NOW) for _ in range(3)]; self.assertEqual(m.assessment_digest(a),m.assessment_digest(a))
    def test_037_public_still_prefers_local_deterministically(self):
        o=m.evaluate(req(sensitivity=m.Sensitivity.PUBLIC),pol(),profs(),now=NOW); self.assertEqual(o.selected_model_id,"LOCAL-TRUST-1")
    def test_038_cloud_disallowed_sensitivity_policy(self):
        p=pol(cloud_allowed_sensitivities=frozenset({m.Sensitivity.PUBLIC}),cloud_approval_sensitivities=frozenset()); pp=(profs()[2],); o=m.evaluate(req(sensitivity=m.Sensitivity.INTERNAL),p,pp,now=NOW); self.assertIn("CLOUD_SENSITIVITY_NOT_ALLOWED",o.rejected_model_reasons[pp[0].model_id])
    def test_039_static_safety(self):
        src=Path(m.__file__).read_text(encoding="utf-8"); tree=ast.parse(src); banned={"subprocess","socket","requests","urllib","shutil"}; imports={n.names[0].name.split('.')[0] for n in ast.walk(tree) if isinstance(n,(ast.Import,ast.ImportFrom)) and getattr(n,'names',None)}; self.assertTrue(banned.isdisjoint(imports)); self.assertNotIn("os.system",src); self.assertNotIn("Popen",src)
    def test_040_license_not_specified(self):
        src=Path(m.__file__).read_text(encoding="utf-8"); self.assertIn("License / Rights: NOT SPECIFIED",src); self.assertNotIn("MIT License",src); self.assertNotIn("Apache License",src)

# 120 deterministic matrix tests: 4 sensitivities x 3 risks x 10 variants.
def _make_matrix(idx,sens,risk,variant):
    def test(self):
        p=pol(); ps=list(profs()); r=req(sensitivity=sens,risk_score=risk)
        if variant==0:
            pass
        elif variant==1:
            ps[0]=dataclasses.replace(ps[0],trust_score=.40)
        elif variant==2:
            ps[1]=dataclasses.replace(ps[1],evidence_verified=False)
        elif variant==3:
            ps[2]=dataclasses.replace(ps[2],provider_id="UNTRUSTED")
        elif variant==4:
            r=dataclasses.replace(r,external_processing_allowed=False)
        elif variant==5:
            ps[0]=dataclasses.replace(ps[0],max_risk=max(0.0,risk-.01))
        elif variant==6:
            ps[0]=dataclasses.replace(ps[0],capabilities=frozenset({"TEXT"}))
        elif variant==7:
            ps[2]=dataclasses.replace(ps[2],evidence_binding="OTHER")
        elif variant==8:
            ps[1]=dataclasses.replace(ps[1],revoked=True)
        elif variant==9:
            r=dataclasses.replace(r,human_approval_evidence_verified=True)
        o=m.evaluate(r,p,tuple(ps),now=NOW)
        self.assertIn(o.decision,{m.ControlDecision.ALLOW,m.ControlDecision.DENY,m.ControlDecision.HOLD,m.ControlDecision.HUMAN_APPROVAL})
        self.assertFalse(o.permission_granted or o.model_invoked or o.data_transferred or o.action_success or o.trust_truth_established or o.verification_pass_proven)
        if o.selected_model_id is not None:
            self.assertIn(o.selected_model_id,o.eligible_model_ids)
    return test

counter=41
for sens in m.Sensitivity:
    for risk in (0.1,0.7,0.95):
        for variant in range(10):
            setattr(CoreTests,f"test_{counter:03d}_matrix_{sens.value}_{str(risk).replace('.','')}_{variant}",_make_matrix(counter,sens,risk,variant)); counter+=1

if __name__=="__main__": unittest.main(verbosity=2)
