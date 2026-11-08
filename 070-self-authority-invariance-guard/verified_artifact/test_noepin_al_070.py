import unittest
from dataclasses import replace
from noepin_al_070_self_authority_invariance_guard import *
NOW=1_800_000_000

def base(req=None):
    p=default_policy(NOW); a=default_authorities()
    r=req or default_request(NOW)
    aps=()
    return p,a,aps,r

class T(unittest.TestCase):
    def test_001_self_degrade_allow(self):
        p,a,aps,r=base(); z=evaluate(r,p,a,aps,now=NOW); self.assertEqual(z.decision,Decision.ALLOW); self.assertEqual(z.removed_capabilities,("WRITE_SCOPED",))
    def test_002_self_elevate_no_approval_deny(self):
        p,a,aps,r=base(replace(default_request(NOW),requested_capabilities=("READ","WRITE_SCOPED","ADMIN"))); z=evaluate(r,p,a,aps,now=NOW); self.assertEqual(z.decision,Decision.DENY)
    def test_003_self_elevate_independent_approval_candidate(self):
        r=replace(default_request(NOW),requested_capabilities=("READ","WRITE_SCOPED","ADMIN"),approval_id="APR-1"); p,a,_,_=base(r); ev=approval_for(r,now=NOW); z=evaluate(r,p,a,(ev,),now=NOW); self.assertEqual(z.decision,Decision.ALLOW); self.assertTrue(z.independent_approval_valid); self.assertFalse(z.permission_granted)
    def test_004_self_approver_deny(self):
        r=replace(default_request(NOW),requested_capabilities=("READ","WRITE_SCOPED","ADMIN"),approval_id="APR-1"); p,a,_,_=base(r); ev=approval_for(r,approver_id="AGENT-1",now=NOW); z=evaluate(r,p,a,(ev,),now=NOW); self.assertEqual(z.decision,Decision.DENY)
    def test_005_unknown_approver_deny(self):
        r=replace(default_request(NOW),requested_capabilities=("READ","WRITE_SCOPED","ADMIN"),approval_id="APR-1"); p,a,_,_=base(r); ev=approval_for(r,approver_id="UNKNOWN",now=NOW); self.assertEqual(evaluate(r,p,a,(ev,),now=NOW).decision,Decision.DENY)
    def test_006_fake_approval_deny(self):
        r=replace(default_request(NOW),requested_capabilities=("READ","WRITE_SCOPED","ADMIN"),approval_id="APR-1"); p,a,_,_=base(r); ev=approval_for(r,now=NOW,signed=False); self.assertEqual(evaluate(r,p,a,(ev,),now=NOW).decision,Decision.DENY)
    def test_007_revoked_approval_deny(self):
        r=replace(default_request(NOW),requested_capabilities=("READ","WRITE_SCOPED","ADMIN"),approval_id="APR-1"); p,a,_,_=base(r); ev=approval_for(r,now=NOW,revoked=True); self.assertEqual(evaluate(r,p,a,(ev,),now=NOW).decision,Decision.DENY)
    def test_008_expired_approval_deny(self):
        r=replace(default_request(NOW),requested_capabilities=("READ","WRITE_SCOPED","ADMIN"),approval_id="APR-1"); p,a,_,_=base(r); ev=replace(approval_for(r,now=NOW),expires_at=NOW-1); self.assertEqual(evaluate(r,p,a,(ev,),now=NOW).decision,Decision.DENY)
    def test_009_delta_mismatch_deny(self):
        r=replace(default_request(NOW),requested_capabilities=("READ","WRITE_SCOPED","ADMIN"),approval_id="APR-1"); p,a,_,_=base(r); ev=replace(approval_for(r,now=NOW),requested_capabilities=("READ",)); self.assertEqual(evaluate(r,p,a,(ev,),now=NOW).decision,Decision.DENY)
    def test_010_proxy_change_valid_approval(self):
        r=AuthorityChangeRequest("REQ-P","AGENT-2","AGENT-1",("READ",),"APR-1",NOW,"SAG-BIND","1","SAG-EPOCH"); p=default_policy(NOW); a=default_authorities(); ev=approval_for(r,now=NOW); z=evaluate(r,p,a,(ev,),now=NOW); self.assertEqual(z.decision,Decision.ALLOW)
    def test_011_proxy_change_no_approval_deny(self):
        r=AuthorityChangeRequest("REQ-P","AGENT-2","AGENT-1",("READ",),None,NOW,"SAG-BIND","1","SAG-EPOCH"); self.assertEqual(evaluate(r,default_policy(NOW),default_authorities(),(),now=NOW).decision,Decision.DENY)
    def test_012_no_change_allow(self):
        r=replace(default_request(NOW),requested_capabilities=("READ","WRITE_SCOPED")); self.assertEqual(evaluate(r,default_policy(NOW),default_authorities(),(),now=NOW).decision,Decision.ALLOW)
    def test_013_target_missing_hold(self):
        r=replace(default_request(NOW),target_id="NOPE"); self.assertEqual(evaluate(r,default_policy(NOW),default_authorities(),(),now=NOW).decision,Decision.HOLD)
    def test_014_policy_revoked_hold(self):
        p=replace(default_policy(NOW),revoked=True); self.assertEqual(evaluate(default_request(NOW),p,default_authorities(),(),now=NOW).decision,Decision.HOLD)
    def test_015_request_stale_hold(self):
        r=replace(default_request(NOW),created_at=NOW-9999); self.assertEqual(evaluate(r,default_policy(NOW),default_authorities(),(),now=NOW).decision,Decision.HOLD)
    def test_016_prepared_allow(self):
        p=default_policy(NOW); a=default_authorities(); r=default_request(NOW); st=prepare_state(p,a,(),binding=r.binding,now=NOW); self.assertTrue(validate_prepared_integrity(st)); z=evaluate_prepared(r,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True,now=NOW); self.assertEqual(z.decision,Decision.ALLOW)
    def test_017_prepared_integrity_required(self):
        p=default_policy(NOW); r=default_request(NOW); st=prepare_state(p,default_authorities(),(),binding=r.binding,now=NOW); z=evaluate_prepared(r,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False,now=NOW); self.assertEqual(z.decision,Decision.HOLD)
    def test_018_prepared_tamper_detected(self):
        p=default_policy(NOW); r=default_request(NOW); st=prepare_state(p,default_authorities(),(),binding=r.binding,now=NOW); tam=replace(st,authorities=(replace(st.authorities[0],capabilities=("READ","ADMIN")),)+st.authorities[1:]); self.assertFalse(validate_prepared_integrity(tam))
    def test_019_registry_mismatch_hold(self):
        p=default_policy(NOW); r=default_request(NOW); st=prepare_state(p,default_authorities(),(),binding=r.binding,now=NOW); z=evaluate_prepared(r,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint="bad",prepared_integrity_validated=True,now=NOW); self.assertEqual(z.decision,Decision.HOLD)
    def test_020_delta_reconstruct(self):
        p=default_policy(NOW); r=default_request(NOW); s1=prepare_state(p,default_authorities(),(),binding=r.binding,now=NOW); aa=list(default_authorities()); aa[1]=replace(aa[1],capabilities=("READ","WRITE_SCOPED")); s2=prepare_state(p,tuple(aa),(),binding=r.binding,now=NOW); s3=apply_delta(s1,make_delta(s1,s2),now=NOW); self.assertEqual(s2.registry_fingerprint,s3.registry_fingerprint)
    def test_021_delta_base_mismatch(self):
        p=default_policy(NOW); r=default_request(NOW); st=prepare_state(p,default_authorities(),(),binding=r.binding,now=NOW); d=replace(make_delta(st,st),base_fingerprint="bad")
        with self.assertRaises(ValueError): apply_delta(st,d,now=NOW)
    def test_022_missing_only_sync(self):
        p=default_policy(NOW); r=default_request(NOW); st=prepare_state(p,default_authorities(),(),binding=r.binding,now=NOW); remote={"authorities":dict(st.authority_fingerprints),"approvals":dict(st.approval_fingerprints)}; remote["authorities"].pop("AGENT-1"); q=missing_only_sync_plan(st,remote); self.assertEqual(q.missing_or_changed_authority_ids,("AGENT-1",)); self.assertFalse(q.full_resend_required)
    def test_023_duplicate_authority_hold(self):
        a=default_authorities(); z=evaluate(default_request(NOW),default_policy(NOW),a+(a[0],),(),now=NOW); self.assertEqual(z.decision,Decision.HOLD)
    def test_024_authority_false(self):
        z=evaluate(default_request(NOW),default_policy(NOW),default_authorities(),(),now=NOW); self.assertFalse(any((z.permission_granted,z.role_changed,z.scope_changed,z.capability_activated,z.credential_issued,z.approval_executed,z.action_executed,z.world_truth_proven,z.safety_proven,z.action_success)))
    def test_025_approval_binding_mismatch_deny(self):
        r=replace(default_request(NOW),requested_capabilities=("READ","WRITE_SCOPED","ADMIN"),approval_id="APR-1"); ev=replace(approval_for(r,now=NOW),binding="OTHER"); z=evaluate(r,default_policy(NOW),default_authorities(),(ev,),now=NOW); self.assertEqual(z.decision,Decision.DENY)

def _gen(i):
    def f(self):
        p=default_policy(NOW); a=default_authorities(); m=i%5
        if m==0:
            r=default_request(NOW); aps=(); want=Decision.ALLOW
        elif m==1:
            r=replace(default_request(NOW),requested_capabilities=("READ","WRITE_SCOPED","ADMIN")); aps=(); want=Decision.DENY
        elif m==2:
            r=replace(default_request(NOW),requested_capabilities=("READ","WRITE_SCOPED","ADMIN"),approval_id="APR-1"); aps=(approval_for(r,now=NOW),); want=Decision.ALLOW
        elif m==3:
            r=replace(default_request(NOW),requested_capabilities=("READ","WRITE_SCOPED","ADMIN"),approval_id="APR-1"); aps=(approval_for(r,approver_id="AGENT-1",now=NOW),); want=Decision.DENY
        else:
            r=replace(default_request(NOW),created_at=NOW-9999); aps=(); want=Decision.HOLD
        z=evaluate(r,p,a,aps,now=NOW); self.assertEqual(z.decision,want); self.assertFalse(z.permission_granted); self.assertFalse(z.role_changed); self.assertFalse(z.action_success)
    return f
for i in range(135): setattr(T,f"test_regression_{i:03d}",_gen(i))

if __name__=="__main__": unittest.main()
