import unittest
from dataclasses import replace
from noepin_al_072_approval_binding_digest import *

NOW=1_800_000_000

def setup(req=None, *, approver='HUMAN-ADMIN', key_id='KEY-HUMAN', key_hex='11'*32):
    p=default_policy(NOW); r=req or default_request(NOW); a=default_authorities(); k=default_keys(NOW)
    apr=reference_approval(r, approver_id=approver, key_id=key_id, key_hex=key_hex, issued_at=NOW)
    return p,r,(apr,),a,k,()

class T(unittest.TestCase):
    def test_001_normal(self):
        p,r,ap,a,k,rr=setup(); z=evaluate(r,'APR-72',p,ap,a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW); self.assertEqual(z.decision,Decision.ALLOW); self.assertTrue(z.next_gate_candidate); self.assertTrue(z.atomic_publish_candidate)
    def test_002_no_permission(self):
        p,r,ap,a,k,rr=setup(); z=evaluate(r,'APR-72',p,ap,a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW); self.assertFalse(any((z.permission_granted,z.tool_executed,z.external_send_performed,z.atomic_publish_performed,z.approval_executed,z.nonce_consumed,z.replay_ledger_written,z.action_success)))
    def test_003_missing_approval(self):
        p,r,ap,a,k,rr=setup(); z=evaluate(r,None,p,ap,a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW); self.assertEqual(z.decision,Decision.HUMAN_APPROVAL)
    def test_004_action_tamper(self):
        p,r,ap,a,k,rr=setup(); r2=replace(r,action='READ'); self.assertEqual(evaluate(r2,'APR-72',p,ap,a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW).decision,Decision.DENY)
    def test_005_target_tamper(self):
        p,r,ap,a,k,rr=setup(); self.assertEqual(evaluate(replace(r,target='RESOURCE-8'),'APR-72',p,ap,a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW).decision,Decision.DENY)
    def test_006_parameter_tamper(self):
        p,r,ap,a,k,rr=setup(); self.assertEqual(evaluate(replace(r,parameters=(("mode","unsafe"),("recursive","false"))),'APR-72',p,ap,a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW).decision,Decision.DENY)
    def test_007_policy_change(self):
        p,r,ap,a,k,rr=setup(); self.assertEqual(evaluate(replace(r,policy_fingerprint='POLICY-FP-8'),'APR-72',p,ap,a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW).decision,Decision.DENY)
    def test_008_nonce_change(self):
        p,r,ap,a,k,rr=setup(); self.assertEqual(evaluate(replace(r,nonce='OTHER'),'APR-72',p,ap,a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW).decision,Decision.DENY)
    def test_009_scope_change(self):
        p,r,ap,a,k,rr=setup(); self.assertEqual(evaluate(replace(r,approval_scope='OTHER'),'APR-72',p,ap,a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW).decision,Decision.DENY)
    def test_010_intent_change(self):
        p,r,ap,a,k,rr=setup(); self.assertEqual(evaluate(replace(r,intent_fingerprint='OTHER'),'APR-72',p,ap,a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW).decision,Decision.DENY)
    def test_011_expired(self):
        p,r,ap,a,k,rr=setup(); self.assertEqual(evaluate(r,'APR-72',p,ap,a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW+301).decision,Decision.HOLD)
    def test_012_replay_digest(self):
        p,r,ap,a,k,rr=setup(); rec=ReplayReceipt(ap[0].approval_digest,'OLD-NONCE','APPROVAL-BIND'); self.assertEqual(evaluate(r,'APR-72',p,ap,a,k,(rec,),current_policy_fingerprint=r.policy_fingerprint,now=NOW).decision,Decision.DENY)
    def test_013_replay_nonce(self):
        p,r,ap,a,k,rr=setup(); rec=ReplayReceipt('other',r.nonce,'APPROVAL-BIND'); self.assertEqual(evaluate(r,'APR-72',p,ap,a,k,(rec,),current_policy_fingerprint=r.policy_fingerprint,now=NOW).decision,Decision.DENY)
    def test_014_replay_unconfirmed(self):
        p,r,ap,a,k,rr=setup(); self.assertEqual(evaluate(r,'APR-72',p,ap,a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW,replay_state_confirmed=False).decision,Decision.HOLD)
    def test_015_bad_mac(self):
        p,r,ap,a,k,rr=setup(); bad=replace(ap[0],mac_hex='00'*32); self.assertEqual(evaluate(r,'APR-72',p,(bad,),a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW).decision,Decision.DENY)
    def test_016_bad_digest(self):
        p,r,ap,a,k,rr=setup(); bad=replace(ap[0],approval_digest='00'*32); self.assertEqual(evaluate(r,'APR-72',p,(bad,),a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW).decision,Decision.DENY)
    def test_017_untrusted_approver(self):
        p,r,ap,a,k,rr=setup(); bad=replace(ap[0],approver_id='STRANGER'); self.assertEqual(evaluate(r,'APR-72',p,(bad,),a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW).decision,Decision.DENY)
    def test_018_revoked_authority(self):
        p,r,ap,a,k,rr=setup(); aa=tuple(replace(x,revoked=True) if x.principal_id=='HUMAN-ADMIN' else x for x in a); self.assertEqual(evaluate(r,'APR-72',p,ap,aa,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW).decision,Decision.DENY)
    def test_019_revoked_key(self):
        p,r,ap,a,k,rr=setup(); kk=tuple(replace(x,revoked=True) if x.key_id=='KEY-HUMAN' else x for x in k); self.assertEqual(evaluate(r,'APR-72',p,ap,a,kk,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW).decision,Decision.DENY)
    def test_020_key_expired(self):
        p,r,ap,a,k,rr=setup(); kk=tuple(replace(x,expires_at=NOW-1) if x.key_id=='KEY-HUMAN' else x for x in k); self.assertEqual(evaluate(r,'APR-72',p,ap,a,kk,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW).decision,Decision.DENY)
    def test_021_request_stale(self):
        r=replace(default_request(NOW),created_at=NOW-1000); p,r,ap,a,k,rr=setup(r); self.assertEqual(evaluate(r,'APR-72',p,ap,a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW).decision,Decision.HOLD)
    def test_022_epoch_mismatch(self):
        p,r,ap,a,k,rr=setup(); self.assertEqual(evaluate(replace(r,approval_epoch='E2'),'APR-72',p,ap,a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW).decision,Decision.DENY)
    def test_023_duplicate_approval(self):
        p,r,ap,a,k,rr=setup(); self.assertEqual(evaluate(r,'APR-72',p,ap+ap,a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW).decision,Decision.DENY)
    def test_024_prepared_match(self):
        p,r,ap,a,k,rr=setup(); st=prepare_state(p,ap,a,k,rr,binding=r.binding); valid=validate_prepared_integrity(st); z=evaluate_prepared(r,'APR-72',st,current_approval_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_bound_policy_fingerprint=r.policy_fingerprint,prepared_integrity_validated=valid,now=NOW); self.assertEqual(z.decision,Decision.ALLOW)
    def test_025_prepared_stale(self):
        p,r,ap,a,k,rr=setup(); st=prepare_state(p,ap,a,k,rr,binding=r.binding); z=evaluate_prepared(r,'APR-72',st,current_approval_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint='bad',current_bound_policy_fingerprint=r.policy_fingerprint,prepared_integrity_validated=True,now=NOW); self.assertEqual(z.decision,Decision.HOLD)
    def test_026_prepared_tamper(self):
        p,r,ap,a,k,rr=setup(); st=prepare_state(p,ap,a,k,rr,binding=r.binding); st2=replace(st,approvals=(replace(ap[0],mac_hex='00'*32),)); self.assertFalse(validate_prepared_integrity(st2))
    def test_027_delta(self):
        p,r,ap,a,k,rr=setup(); st=prepare_state(p,ap,a,k,rr,binding=r.binding); r2=replace(r,request_id='REQ-72B',nonce='NONCE-72B'); ap2=reference_approval(r2,approval_id='APR-72B',issued_at=NOW); st2=prepare_state(p,ap+(ap2,),a,k,rr,binding=r.binding); d=make_delta(st,st2); self.assertEqual(apply_delta(st,d).registry_fingerprint,st2.registry_fingerprint)
    def test_028_missing_sync(self):
        p,r,ap,a,k,rr=setup(); st=prepare_state(p,ap,a,k,rr,binding=r.binding); remote={'approvals':{},'authorities':dict(st.authority_fingerprints),'keys':dict(st.key_fingerprints),'replay':dict(st.replay_fingerprints)}; pl=missing_only_sync_plan(st,remote); self.assertEqual(pl.missing_or_changed_approval_ids,('APR-72',)); self.assertFalse(pl.full_resend_required)
    def test_029_parameter_order_canonical(self):
        r=default_request(NOW); r2=replace(r,parameters=tuple(reversed(r.parameters))); self.assertEqual(request_fingerprint(r),request_fingerprint(r2))
    def test_030_single_use_required(self):
        p,r,ap,a,k,rr=setup(); apr=reference_approval(r,single_use=False,issued_at=NOW); self.assertEqual(evaluate(r,'APR-72',p,(apr,),a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW).decision,Decision.DENY)

    def test_031_current_policy_unconfirmed(self):
        p,r,ap,a,k,rr=setup(); self.assertEqual(evaluate(r,'APR-72',p,ap,a,k,rr,current_policy_fingerprint=None,now=NOW).decision,Decision.HOLD)
    def test_032_current_policy_changed_after_approval(self):
        p,r,ap,a,k,rr=setup(); self.assertEqual(evaluate(r,'APR-72',p,ap,a,k,rr,current_policy_fingerprint='POLICY-FP-NEW',now=NOW).decision,Decision.DENY)
    def test_033_weak_verifier_key_rejected(self):
        p,r,ap,a,k,rr=setup(); kk=tuple(replace(x,verifier_key_hex='11') if x.key_id=='KEY-HUMAN' else x for x in k); self.assertEqual(evaluate(r,'APR-72',p,ap,a,kk,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW).decision,Decision.DENY)
    def test_034_approval_before_request_rejected(self):
        r=replace(default_request(NOW),created_at=NOW); p=default_policy(NOW); a=default_authorities(); k=default_keys(NOW); apr=reference_approval(r,issued_at=NOW-1,expires_at=NOW+200); self.assertEqual(evaluate(r,'APR-72',p,(apr,),a,k,(),current_policy_fingerprint=r.policy_fingerprint,now=NOW).decision,Decision.DENY)

def _gen(i):
    def f(self):
        m=i%6
        if m==0:
            p,r,ap,a,k,rr=setup(); want=Decision.ALLOW
        elif m==1:
            p,r,ap,a,k,rr=setup(); r=replace(r,action=f'TAMPER-{i}'); want=Decision.DENY
        elif m==2:
            p,r,ap,a,k,rr=setup(); ap=(replace(ap[0],mac_hex='ab'*32),); want=Decision.DENY
        elif m==3:
            p,r,ap,a,k,rr=setup(); rr=(ReplayReceipt(ap[0].approval_digest,r.nonce,'APPROVAL-BIND'),); want=Decision.DENY
        elif m==4:
            p,r,ap,a,k,rr=setup(); want=Decision.HOLD
            z=evaluate(r,'APR-72',p,ap,a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW+1000)
            self.assertEqual(z.decision,want); self.assertFalse(z.permission_granted); return
        else:
            p,r,ap,a,k,rr=setup(); want=Decision.HUMAN_APPROVAL
            z=evaluate(r,None,p,ap,a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW)
            self.assertEqual(z.decision,want); self.assertFalse(z.action_success); return
        z=evaluate(r,'APR-72',p,ap,a,k,rr,current_policy_fingerprint=r.policy_fingerprint,now=NOW)
        self.assertEqual(z.decision,want)
        self.assertFalse(z.permission_granted); self.assertFalse(z.tool_executed); self.assertFalse(z.action_success)
    return f

for i in range(126):
    setattr(T,f'test_regression_{i:03d}',_gen(i))

if __name__=='__main__': unittest.main()
