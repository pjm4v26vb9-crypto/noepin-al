import unittest
from dataclasses import replace
from noepin_al_087_permit_lease_manager import *

class T(unittest.TestCase):
    def base(self): return default_request(),default_permits(),default_nonce_records(),default_policy()
    def neg(self,z):
        self.assertFalse(z.request_promoted_to_success); self.assertFalse(z.permit_promoted_to_permission); self.assertFalse(z.nonce_store_mutated); self.assertFalse(z.usage_consumed); self.assertFalse(z.permission_granted); self.assertFalse(z.action_executed); self.assertFalse(z.plan_committed); self.assertFalse(z.atomic_publish_executed); self.assertFalse(z.external_write_performed); self.assertFalse(z.receipt_promoted_to_truth); self.assertFalse(z.world_truth_proven); self.assertFalse(z.safety_proven); self.assertFalse(z.action_success)
    def test_001_default_allow(self): z=default_evaluation(); self.assertEqual(z.decision,Decision.ALLOW); self.assertTrue(z.consume_candidate); self.neg(z)
    def test_002_expired(self): r,p,n,pol=self.base(); r=replace(r,now=1063.0); self.assertEqual(evaluate(r,p,n,pol).lease_state,LeaseState.EXPIRED)
    def test_003_exhausted(self): r,p,n,pol=self.base(); p=(replace(p[0],usage_count=3),); n=(replace(n[0],usage_count=3),); r=replace(r,expected_usage_count=3); self.assertEqual(evaluate(r,p,n,pol).lease_state,LeaseState.EXHAUSTED)
    def test_004_state_mismatch(self): r,p,n,pol=self.base(); r=replace(r,current_state_fingerprint='OTHER'); z=evaluate(r,p,n,pol); self.assertEqual(z.decision,Decision.HOLD); self.assertTrue(z.reissue_required)
    def test_005_replay_seen_attempt(self): r,p,n,pol=self.base(); n=(replace(n[0],seen_attempt_nonces=(r.attempt_nonce,)),); z=evaluate(r,p,n,pol); self.assertEqual(z.lease_state,LeaseState.REPLAY); self.assertTrue(z.replay_detected)
    def test_006_clock_before_issue(self): r,p,n,pol=self.base(); r=replace(r,now=997.0); self.assertEqual(evaluate(r,p,n,pol).decision,Decision.HOLD)
    def test_007_signature_unverified(self): r,p,n,pol=self.base(); p=(replace(p[0],signature_verified=False),); self.assertEqual(evaluate(r,p,n,pol).decision,Decision.DENY)
    def test_008_nonce_inactive(self): r,p,n,pol=self.base(); n=(replace(n[0],active=False),); self.assertEqual(evaluate(r,p,n,pol).lease_state,LeaseState.REPLAY)
    def test_009_nonce_unobserved(self): r,p,n,pol=self.base(); n=(replace(n[0],observed=False),); self.assertEqual(evaluate(r,p,n,pol).decision,Decision.DENY)
    def test_010_nonce_missing(self): r,p,n,pol=self.base(); self.assertEqual(evaluate(r,p,(),pol).decision,Decision.DENY)
    def test_011_scope_mismatch(self): r,p,n,pol=self.base(); r=replace(r,current_scope_fingerprint='OTHER'); z=evaluate(r,p,n,pol); self.assertEqual(z.decision,Decision.DENY); self.assertTrue(z.reissue_required)
    def test_012_stale_usage_replay(self): r,p,n,pol=self.base(); p=(replace(p[0],usage_count=1),); n=(replace(n[0],usage_count=1),); r=replace(r,expected_usage_count=0); self.assertEqual(evaluate(r,p,n,pol).lease_state,LeaseState.REPLAY)
    def test_013_expected_usage_ahead(self): r,p,n,pol=self.base(); r=replace(r,expected_usage_count=1); self.assertEqual(evaluate(r,p,n,pol).decision,Decision.HOLD)
    def test_014_store_usage_mismatch(self): r,p,n,pol=self.base(); n=(replace(n[0],usage_count=1),); self.assertEqual(evaluate(r,p,n,pol).decision,Decision.HOLD)
    def test_015_invalid_ttl(self): r,p,n,pol=self.base(); p=(replace(p[0],ttl_seconds=0),); self.assertEqual(evaluate(r,p,n,pol).decision,Decision.HOLD)
    def test_016_invalid_max_usage(self): r,p,n,pol=self.base(); p=(replace(p[0],max_usage_count=0),); self.assertEqual(evaluate(r,p,n,pol).decision,Decision.HOLD)
    def test_017_negative_usage(self): r,p,n,pol=self.base(); p=(replace(p[0],usage_count=-1),); self.assertEqual(evaluate(r,p,n,pol).decision,Decision.HOLD)
    def test_018_usage_over_max(self): r,p,n,pol=self.base(); p=(replace(p[0],usage_count=4),); self.assertEqual(evaluate(r,p,n,pol).decision,Decision.HOLD)
    def test_019_request_binding_mismatch(self): r,p,n,pol=self.base(); r=replace(r,binding='X'); self.assertEqual(evaluate(r,p,n,pol).decision,Decision.HOLD)
    def test_020_permit_epoch_mismatch(self): r,p,n,pol=self.base(); p=(replace(p[0],state_epoch='X'),); self.assertEqual(evaluate(r,p,n,pol).decision,Decision.HOLD)
    def test_021_unknown_permit(self): r,p,n,pol=self.base(); r=replace(r,permit_id='NOPE'); self.assertEqual(evaluate(r,p,n,pol).decision,Decision.DENY)
    def test_022_duplicate_permit(self): r,p,n,pol=self.base(); p=(p[0],p[0]); self.assertEqual(evaluate(r,p,n,pol).decision,Decision.HOLD)
    def test_023_duplicate_nonce_record(self): r,p,n,pol=self.base(); n=(n[0],n[0]); self.assertEqual(evaluate(r,p,n,pol).decision,Decision.HOLD)
    def test_024_nonce_permit_mismatch(self): r,p,n,pol=self.base(); n=(replace(n[0],permit_id='OTHER'),); self.assertEqual(evaluate(r,p,n,pol).decision,Decision.DENY)
    def test_025_policy_revoked(self): r,p,n,pol=self.base(); pol=replace(pol,revoked=True); self.assertEqual(evaluate(r,p,n,pol).decision,Decision.HOLD)
    def test_026_request_unobserved(self): r,p,n,pol=self.base(); r=replace(r,observed=False); self.assertEqual(evaluate(r,p,n,pol).decision,Decision.HOLD)
    def test_027_permit_unobserved(self): r,p,n,pol=self.base(); p=(replace(p[0],observed=False),); self.assertEqual(evaluate(r,p,n,pol).decision,Decision.DENY)
    def test_028_empty_attempt_nonce(self): r,p,n,pol=self.base(); r=replace(r,attempt_nonce=''); self.assertEqual(evaluate(r,p,n,pol).decision,Decision.HOLD)
    def test_029_empty_permit_nonce(self): r,p,n,pol=self.base(); p=(replace(p[0],permit_nonce=''),); self.assertEqual(evaluate(r,p,n,pol).decision,Decision.HOLD)
    def test_030_duplicate_seen_attempt(self): r,p,n,pol=self.base(); n=(replace(n[0],seen_attempt_nonces=('X','X')),); self.assertEqual(evaluate(r,p,n,pol).decision,Decision.HOLD)
    def test_031_prepared_semantic(self):
        x=self.base(); st=prepare_state(*x,binding=x[-1].binding,state_epoch=x[-1].state_epoch); self.assertTrue(validate_prepared_integrity(st)); self.assertEqual(evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True),evaluate(*x))
    def test_032_prepared_stale(self):
        x=self.base(); st=prepare_state(*x,binding=x[-1].binding,state_epoch=x[-1].state_epoch); self.assertEqual(evaluate_prepared(st,current_context_fingerprint='X',current_dependency_fingerprint=st.dependency_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_033_prepared_integrity_required(self):
        x=self.base(); st=prepare_state(*x,binding=x[-1].binding,state_epoch=x[-1].state_epoch); self.assertEqual(evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False).decision,Decision.HOLD)
    def test_034_delta_reconstruction(self):
        x=self.base(); s1=prepare_state(*x,binding=x[-1].binding,state_epoch=x[-1].state_epoch); p=(replace(x[1][0],usage_count=1),); n=(replace(x[2][0],usage_count=1,seen_attempt_nonces=('OLD',)),); r=replace(x[0],expected_usage_count=1,attempt_nonce='NEW'); x2=(r,p,n,x[3]); s2=prepare_state(*x2,binding=x2[-1].binding,state_epoch=x2[-1].state_epoch); self.assertEqual(apply_delta(s1,make_delta(s1,s2)),s2)
    def test_035_missing_only(self):
        r,_,_,pol=self.base(); N=20; p=tuple(PermitLease(f'P{n}',1000,60,3,0,f'N{n}',f'S{n}','SC',True,True,'LEASE-BIND','STATE-EPOCH-1') for n in range(N)); ns=tuple(NonceLeaseRecord(f'N{n}',f'P{n}',True,0,(),True,'LEASE-BIND','STATE-EPOCH-1') for n in range(N)); r=replace(r,permit_id='P0',current_state_fingerprint='S0',current_scope_fingerprint='SC'); st=prepare_state(r,p,ns,pol,binding=pol.binding,state_epoch=pol.state_epoch); kp=dict(st.permit_fingerprints); kn=dict(st.nonce_fingerprints); [kp.pop(f'P{n}') for n in range(5)]; plan=missing_only_sync_plan(st,kp,kn); self.assertEqual(len(plan.missing_or_changed_permit_ids),5); self.assertFalse(plan.full_resend_required)
    def test_036_delta_smaller(self):
        r,_,_,pol=self.base(); N=100; p=tuple(PermitLease(f'P{n}',1000,60,3,0,f'N{n}',f'S{n}','SC',True,True,'LEASE-BIND','STATE-EPOCH-1') for n in range(N)); ns=tuple(NonceLeaseRecord(f'N{n}',f'P{n}',True,0,(),True,'LEASE-BIND','STATE-EPOCH-1') for n in range(N)); r=replace(r,permit_id='P0',current_state_fingerprint='S0',current_scope_fingerprint='SC'); s1=prepare_state(r,p,ns,pol,binding=pol.binding,state_epoch=pol.state_epoch); pp=list(p); pp[0]=replace(pp[0],ttl_seconds=61); s2=prepare_state(r,tuple(pp),ns,pol,binding=pol.binding,state_epoch=pol.state_epoch); self.assertLess(delta_bytes(make_delta(s1,s2)),full_registry_bytes(s2))
    def test_037_authority_flags_false(self): self.neg(default_evaluation())
    def test_038_next_usage(self): self.assertEqual(default_evaluation().next_usage_count,1)
    def test_039_remaining_ttl(self): self.assertEqual(default_evaluation().remaining_ttl,55.0)
    def test_040_consume_is_candidate_only(self): z=default_evaluation(); self.assertTrue(z.consume_candidate); self.assertFalse(z.usage_consumed); self.assertFalse(z.nonce_store_mutated); self.assertFalse(z.permission_granted); self.assertFalse(z.action_executed)

def _gen(k):
    def f(self):
        r,p,n,pol=self.base(); mode=k%12
        if mode==0: want=Decision.ALLOW
        elif mode==1: r=replace(r,now=1064); want=Decision.DENY
        elif mode==2: r=replace(r,current_state_fingerprint='X'); want=Decision.HOLD
        elif mode==3: n=(replace(n[0],active=False),); want=Decision.DENY
        elif mode==4: n=(replace(n[0],seen_attempt_nonces=(r.attempt_nonce,)),); want=Decision.DENY
        elif mode==5: p=(replace(p[0],signature_verified=False),); want=Decision.DENY
        elif mode==6: r=replace(r,current_scope_fingerprint='X'); want=Decision.DENY
        elif mode==7: pol=replace(pol,revoked=True); want=Decision.HOLD
        elif mode==8: p=(replace(p[0],usage_count=3),); n=(replace(n[0],usage_count=3),); want=Decision.DENY
        elif mode==9: r=replace(r,now=999.0); want=Decision.ALLOW
        elif mode==10: r=replace(r,expected_usage_count=1); want=Decision.HOLD
        else: r=replace(r,observed=False); want=Decision.HOLD
        z=evaluate(r,p,n,pol); self.assertEqual(z.decision,want); self.neg(z)
    return f
for k in range(120): setattr(T,f'test_regression_{k:03d}',_gen(k))

if __name__=='__main__': unittest.main(verbosity=2)
