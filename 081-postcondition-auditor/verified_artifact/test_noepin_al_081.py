from dataclasses import replace
import unittest
from noepin_al_081_postcondition_auditor import *


def base():
    return (
        default_request(), default_intent(), default_permit(), default_receipt(),
        default_policy(), default_conditions(), default_observed_state(), default_diff()
    )


def neg(t, z):
    t.assertFalse(z.permission_granted)
    t.assertFalse(z.rollback_executed)
    t.assertFalse(z.state_committed)
    t.assertFalse(z.external_write_performed)
    t.assertFalse(z.action_executed)
    t.assertFalse(z.receipt_promoted_to_truth)
    t.assertFalse(z.world_truth_proven)
    t.assertFalse(z.safety_proven)
    t.assertFalse(z.action_success)


class T(unittest.TestCase):
    def test_001_default_allow(self):
        z=evaluate(*base()); self.assertEqual(z.decision,Decision.ALLOW); self.assertEqual(z.success_state,SuccessState.SUCCESS); self.assertTrue(z.next_gate_candidate); self.assertTrue(z.atomic_publish_candidate); neg(self,z)
    def test_002_required_unmet_deny(self):
        q,i,p,r,pol,c,s,d=base(); s=(s[0],replace(s[1],value='bad'),s[2]); z=evaluate(q,i,p,r,pol,c,s,d); self.assertEqual(z.decision,Decision.DENY); self.assertIn('C-HASH',z.unmet_conditions); neg(self,z)
    def test_003_required_unobserved_hold(self):
        q,i,p,r,pol,c,s,d=base(); s=(s[0],replace(s[1],observed=False),s[2]); z=evaluate(q,i,p,r,pol,c,s,d); self.assertEqual(z.decision,Decision.HOLD); self.assertEqual(z.success_state,SuccessState.UNKNOWN); neg(self,z)
    def test_004_missing_required_fact_hold(self):
        q,i,p,r,pol,c,s,d=base(); z=evaluate(q,i,p,r,pol,c,(s[0],s[2]),d); self.assertEqual(z.decision,Decision.HOLD); neg(self,z)
    def test_005_critical_unexpected_deny(self):
        q,i,p,r,pol,c,s,d=base(); x=DiffEffect('D-X','outside',None,'x',True,False,Severity.CRITICAL,pol.binding,pol.state_epoch); z=evaluate(q,i,p,r,pol,c,s,d+(x,)); self.assertEqual(z.decision,Decision.DENY); self.assertTrue(z.rollback_candidate); self.assertFalse(z.rollback_executed); neg(self,z)
    def test_006_high_unexpected_hold(self):
        q,i,p,r,pol,c,s,d=base(); x=DiffEffect('D-X','outside',None,'x',True,False,Severity.HIGH,pol.binding,pol.state_epoch); z=evaluate(q,i,p,r,pol,c,s,d+(x,)); self.assertEqual(z.decision,Decision.HOLD); neg(self,z)
    def test_007_medium_unexpected_hold(self):
        q,i,p,r,pol,c,s,d=base(); x=DiffEffect('D-X','outside',None,'x',True,False,Severity.MEDIUM,pol.binding,pol.state_epoch); self.assertEqual(evaluate(q,i,p,r,pol,c,s,d+(x,)).decision,Decision.HOLD)
    def test_008_low_unexpected_hold(self):
        q,i,p,r,pol,c,s,d=base(); x=DiffEffect('D-X','outside',None,'x',True,False,Severity.LOW,pol.binding,pol.state_epoch); self.assertEqual(evaluate(q,i,p,r,pol,c,s,d+(x,)).decision,Decision.HOLD)
    def test_009_diff_incomplete_hold(self):
        q,i,p,r,pol,c,s,d=base(); self.assertEqual(evaluate(replace(q,diff_complete=False),i,p,r,pol,c,s,d).decision,Decision.HOLD)
    def test_010_unobserved_effect_hold(self):
        q,i,p,r,pol,c,s,d=base(); dd=(replace(d[0],observed=False),)+d[1:]; self.assertEqual(evaluate(q,i,p,r,pol,c,s,dd).decision,Decision.HOLD)
    def test_011_receipt_false_does_not_override_observation(self):
        q,i,p,r,pol,c,s,d=base(); z=evaluate(q,i,p,replace(r,claimed_success=False),pol,c,s,d); self.assertEqual(z.decision,Decision.ALLOW); self.assertTrue(any('RECEIPT_FAILURE' in x for x in z.reasons)); neg(self,z)
    def test_012_receipt_success_contradicted(self):
        q,i,p,r,pol,c,s,d=base(); s=(s[0],replace(s[1],value='bad'),s[2]); z=evaluate(q,i,p,r,pol,c,s,d); self.assertIn('SUCCESS_RECEIPT_CONTRADICTED_BY_OBSERVATION',z.reasons)
    def test_013_unobserved_receipt_not_success_authority(self):
        q,i,p,r,pol,c,s,d=base(); z=evaluate(q,i,p,replace(r,observed=False),pol,c,s,d); self.assertEqual(z.decision,Decision.ALLOW); neg(self,z)
    def test_014_invalid_permit_hold(self):
        q,i,p,r,pol,c,s,d=base(); self.assertEqual(evaluate(q,i,replace(p,valid=False),r,pol,c,s,d).decision,Decision.HOLD)
    def test_015_unobserved_permit_hold(self):
        q,i,p,r,pol,c,s,d=base(); self.assertEqual(evaluate(q,i,replace(p,observed=False),r,pol,c,s,d).decision,Decision.HOLD)
    def test_016_revocation_unchecked_hold(self):
        q,i,p,r,pol,c,s,d=base(); self.assertEqual(evaluate(q,i,replace(p,revocation_checked=False),r,pol,c,s,d).decision,Decision.HOLD)
    def test_017_unobserved_intent_hold(self):
        q,i,p,r,pol,c,s,d=base(); self.assertEqual(evaluate(q,replace(i,observed=False),p,r,pol,c,s,d).decision,Decision.HOLD)
    def test_018_request_binding_hold(self):
        q,i,p,r,pol,c,s,d=base(); self.assertEqual(evaluate(replace(q,binding='BAD'),i,p,r,pol,c,s,d).decision,Decision.HOLD)
    def test_019_intent_binding_hold(self):
        q,i,p,r,pol,c,s,d=base(); self.assertEqual(evaluate(q,replace(i,binding='BAD'),p,r,pol,c,s,d).decision,Decision.HOLD)
    def test_020_permit_binding_hold(self):
        q,i,p,r,pol,c,s,d=base(); self.assertEqual(evaluate(q,i,replace(p,binding='BAD'),r,pol,c,s,d).decision,Decision.HOLD)
    def test_021_receipt_binding_hold(self):
        q,i,p,r,pol,c,s,d=base(); self.assertEqual(evaluate(q,i,p,replace(r,binding='BAD'),pol,c,s,d).decision,Decision.HOLD)
    def test_022_condition_binding_hold(self):
        q,i,p,r,pol,c,s,d=base(); cc=(replace(c[0],binding='BAD'),c[1],c[2]); self.assertEqual(evaluate(q,i,p,r,pol,cc,s,d).decision,Decision.HOLD)
    def test_023_state_binding_hold(self):
        q,i,p,r,pol,c,s,d=base(); ss=(replace(s[0],binding='BAD'),s[1],s[2]); self.assertEqual(evaluate(q,i,p,r,pol,c,ss,d).decision,Decision.HOLD)
    def test_024_diff_binding_hold(self):
        q,i,p,r,pol,c,s,d=base(); dd=(replace(d[0],binding='BAD'),d[1],d[2]); self.assertEqual(evaluate(q,i,p,r,pol,c,s,dd).decision,Decision.HOLD)
    def test_025_duplicate_condition_hold(self):
        q,i,p,r,pol,c,s,d=base(); self.assertEqual(evaluate(q,i,p,r,pol,c+c[:1],s,d).decision,Decision.HOLD)
    def test_026_duplicate_state_hold(self):
        q,i,p,r,pol,c,s,d=base(); self.assertEqual(evaluate(q,i,p,r,pol,c,s+s[:1],d).decision,Decision.HOLD)
    def test_027_duplicate_effect_hold(self):
        q,i,p,r,pol,c,s,d=base(); self.assertEqual(evaluate(q,i,p,r,pol,c,s,d+d[:1]).decision,Decision.HOLD)
    def test_028_unknown_condition_hold(self):
        q,i,p,r,pol,c,s,d=base(); self.assertEqual(evaluate(replace(q,condition_ids=('NOPE',)),i,p,r,pol,c,s,d).decision,Decision.HOLD)
    def test_029_empty_conditions_hold(self):
        q,i,p,r,pol,c,s,d=base(); self.assertEqual(evaluate(replace(q,condition_ids=()),i,p,r,pol,c,s,d).decision,Decision.HOLD)
    def test_030_absent_predicate(self):
        q,i,p,r,pol,c,s,d=base(); cc=(replace(c[0],operator=PredicateOperator.ABSENT,expected_value=None),c[1],c[2]); ss=(replace(s[0],exists=False,value=None),s[1],s[2]); self.assertEqual(evaluate(q,i,p,r,pol,cc,ss,d).decision,Decision.ALLOW)
    def test_031_ne_predicate(self):
        q,i,p,r,pol,c,s,d=base(); cc=(c[0],replace(c[1],operator=PredicateOperator.NE,expected_value='bad'),c[2]); self.assertEqual(evaluate(q,i,p,r,pol,cc,s,d).decision,Decision.ALLOW)
    def test_032_prepared_same(self):
        q,i,p,r,pol,c,s,d=base(); st=prepare_state(pol,q,i,p,r,c,s,d,binding=pol.binding); v=validate_prepared_integrity(st); z1=evaluate(q,i,p,r,pol,c,s,d); z2=evaluate_prepared(st,current_policy_fingerprint=st.policy_fingerprint,current_request_fingerprint=st.request_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=v); self.assertEqual(z1,z2)
    def test_033_prepared_unvalidated_hold(self):
        q,i,p,r,pol,c,s,d=base(); st=prepare_state(pol,q,i,p,r,c,s,d,binding=pol.binding); self.assertEqual(evaluate_prepared(st,current_policy_fingerprint=st.policy_fingerprint,current_request_fingerprint=st.request_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False).decision,Decision.HOLD)
    def test_034_prepared_registry_stale(self):
        q,i,p,r,pol,c,s,d=base(); st=prepare_state(pol,q,i,p,r,c,s,d,binding=pol.binding); self.assertEqual(evaluate_prepared(st,current_policy_fingerprint=st.policy_fingerprint,current_request_fingerprint=st.request_fingerprint,current_registry_fingerprint='BAD',prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_035_tamper_integrity_false(self):
        q,i,p,r,pol,c,s,d=base(); st=prepare_state(pol,q,i,p,r,c,s,d,binding=pol.binding); self.assertFalse(validate_prepared_integrity(replace(st,registry_fingerprint='BAD')))
    def test_036_delta_roundtrip(self):
        q,i,p,r,pol,c,s,d=base(); a=prepare_state(pol,q,i,p,r,c,s,d,binding=pol.binding); b=prepare_state(pol,q,i,p,r,c,(s[0],replace(s[1],value='new'),s[2]),d,binding=pol.binding); self.assertEqual(apply_delta(a,make_delta(a,b)).registry_fingerprint,b.registry_fingerprint)
    def test_037_delta_base_mismatch(self):
        q,i,p,r,pol,c,s,d=base(); a=prepare_state(pol,q,i,p,r,c,s,d,binding=pol.binding); b=prepare_state(pol,q,i,p,r,c,(s[0],replace(s[1],value='new'),s[2]),d,binding=pol.binding); delta=replace(make_delta(a,b),base_fingerprint='BAD'); self.assertRaises(ValueError,apply_delta,a,delta)
    def test_038_missing_sync(self):
        q,i,p,r,pol,c,s,d=base(); st=prepare_state(pol,q,i,p,r,c,s,d,binding=pol.binding); kc=dict(st.condition_fingerprints); ks=dict(st.state_fingerprints); ke=dict(st.effect_fingerprints); ks.pop('artifact.sha256'); plan=missing_only_sync_plan(st,kc,ks,ke); self.assertIn('artifact.sha256',plan.missing_or_changed_state_paths); self.assertFalse(plan.full_resend_required)
    def test_039_scope_exceeds_permit_hold(self):
        q,i,p,r,pol,c,s,d=base(); qq=replace(q,allowed_effect_paths=q.allowed_effect_paths+('outside',)); self.assertEqual(evaluate(qq,i,p,r,pol,c,s,d).decision,Decision.HOLD)
    def test_040_authority_negatives(self):
        z=evaluate(*base()); neg(self,z)


def _gen(k):
    def f(self):
        q,i,p,r,pol,c,s,d=base(); m=k%15
        if m==0: want=Decision.ALLOW
        elif m==1:
            s=(s[0],replace(s[1],value=f'bad-{k}'),s[2]); want=Decision.DENY
        elif m==2:
            s=(s[0],replace(s[1],observed=False),s[2]); want=Decision.HOLD
        elif m==3:
            x=DiffEffect(f'D-X-{k}','outside',None,'x',True,False,Severity.CRITICAL,pol.binding,pol.state_epoch); d=d+(x,); want=Decision.DENY
        elif m==4:
            x=DiffEffect(f'D-X-{k}','outside',None,'x',True,False,Severity.HIGH,pol.binding,pol.state_epoch); d=d+(x,); want=Decision.HOLD
        elif m==5: q=replace(q,diff_complete=False); want=Decision.HOLD
        elif m==6: p=replace(p,valid=False); want=Decision.HOLD
        elif m==7: i=replace(i,observed=False); want=Decision.HOLD
        elif m==8: q=replace(q,condition_ids=('NOPE',)); want=Decision.HOLD
        elif m==9: pol=replace(pol,revoked=True); want=Decision.HOLD
        elif m==10: r=replace(r,claimed_success=False); want=Decision.ALLOW
        elif m==11:
            d=(replace(d[0],observed=False),d[1],d[2]); want=Decision.HOLD
        elif m==12:
            q=replace(q,binding=f'BAD-{k}'); want=Decision.HOLD
        elif m==13:
            cc=(replace(c[0],operator=PredicateOperator.ABSENT),c[1],c[2]); ss=(replace(s[0],exists=False,value=None),s[1],s[2]); c,s=cc,ss; want=Decision.ALLOW
        else:
            cc=(c[0],replace(c[1],operator=PredicateOperator.NE,expected_value='wrong'),c[2]); c=cc; want=Decision.ALLOW
        z=evaluate(q,i,p,r,pol,c,s,d); self.assertEqual(z.decision,want); neg(self,z)
    return f

for k in range(120):
    setattr(T,f'test_regression_{k:03d}',_gen(k))

if __name__=='__main__': unittest.main(verbosity=2)
