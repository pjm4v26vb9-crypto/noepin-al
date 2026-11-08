import unittest
from dataclasses import replace
from noepin_al_071_policy_immutability_kernel import *
NOW=1_800_000_000

def setup(req=None):
    p=default_kernel_policy(NOW); cur=default_snapshot(); auth=default_authorities(); vers=default_versions(); r=req or default_request(NOW); sig=signature_for(r,cur,now=NOW); return p,cur,auth,(sig,),vers,r

class T(unittest.TestCase):
    def test_001_normal_update_allow_candidate(self):
        p,c,a,s,v,r=setup(); z=evaluate(r,p,c,a,s,v,now=NOW); self.assertEqual(z.decision,Decision.ALLOW); self.assertEqual(z.proposed_version,8); self.assertFalse(z.policy_update_committed)
    def test_002_execution_agent_direct_update_deny(self):
        r=replace(default_request(NOW),actor_id="AGENT-1"); p,c,a,_,v,_=setup(r); s=(signature_for(r,c,signer_id="HUMAN-ADMIN",now=NOW),); self.assertEqual(evaluate(r,p,c,a,s,v,now=NOW).decision,Decision.DENY)
    def test_003_signature_tamper_deny(self):
        p,c,a,s,v,r=setup(); s=(replace(s[0],signed_policy_hash="tampered"),); self.assertEqual(evaluate(r,p,c,a,s,v,now=NOW).decision,Decision.DENY)
    def test_004_version_conflict_hold(self):
        r=replace(default_request(NOW),expected_version=6); p,c,a,_,v,_=setup(r); s=(signature_for(r,c,now=NOW),); self.assertEqual(evaluate(r,p,c,a,s,v,now=NOW).decision,Decision.HOLD)
    def test_005_valid_rollback_append_only_candidate(self):
        r=ChangeRequest("RB","SECURITY-ADMIN",7,"hash-v5","ROLLBACK",5,"SIG-71",NOW,"POL-BIND","POL-EPOCH"); p,c,a,_,v,_=setup(r); s=(signature_for(r,c,candidate_hash="hash-v5",signer_id="SECURITY-ADMIN",now=NOW),); z=evaluate(r,p,c,a,s,v,now=NOW); self.assertEqual(z.decision,Decision.ALLOW); self.assertEqual(z.proposed_version,8); self.assertEqual(z.rollback_target_version,5)
    def test_006_rollback_target_unverified_deny(self):
        r=ChangeRequest("RB","SECURITY-ADMIN",7,"hash-v5","ROLLBACK",5,"SIG-71",NOW,"POL-BIND","POL-EPOCH"); p,c,a,_,v,_=setup(r); v=tuple(replace(x,verified=False) if x.version==5 else x for x in v); s=(signature_for(r,c,candidate_hash="hash-v5",signer_id="SECURITY-ADMIN",now=NOW),); self.assertEqual(evaluate(r,p,c,a,s,v,now=NOW).decision,Decision.DENY)
    def test_007_signature_missing_deny(self):
        r=replace(default_request(NOW),signature_id=None); p,c,a,_,v,_=setup(r); self.assertEqual(evaluate(r,p,c,a,(),v,now=NOW).decision,Decision.DENY)
    def test_008_signature_unknown_deny(self):
        r=replace(default_request(NOW),signature_id="NOPE"); p,c,a,_,v,_=setup(r); self.assertEqual(evaluate(r,p,c,a,(),v,now=NOW).decision,Decision.DENY)
    def test_009_signer_untrusted_deny(self):
        p,c,a,_,v,r=setup(); s=(signature_for(r,c,signer_id="AGENT-1",now=NOW),); self.assertEqual(evaluate(r,p,c,a,s,v,now=NOW).decision,Decision.DENY)
    def test_010_updater_unknown_deny(self):
        r=replace(default_request(NOW),actor_id="OUTSIDER"); p,c,a,_,v,_=setup(r); s=(signature_for(r,c,signer_id="SECURITY-ADMIN",now=NOW),); self.assertEqual(evaluate(r,p,c,a,s,v,now=NOW).decision,Decision.DENY)
    def test_011_signature_expired_deny(self):
        p,c,a,s,v,r=setup(); s=(replace(s[0],expires_at=NOW-1),); self.assertEqual(evaluate(r,p,c,a,s,v,now=NOW).decision,Decision.DENY)
    def test_012_signature_revoked_deny(self):
        p,c,a,s,v,r=setup(); s=(replace(s[0],revoked=True),); self.assertEqual(evaluate(r,p,c,a,s,v,now=NOW).decision,Decision.DENY)
    def test_013_signature_unverified_deny(self):
        p,c,a,s,v,r=setup(); s=(replace(s[0],verified=False),); self.assertEqual(evaluate(r,p,c,a,s,v,now=NOW).decision,Decision.DENY)
    def test_014_request_fingerprint_mismatch_deny(self):
        p,c,a,s,v,r=setup(); s=(replace(s[0],request_fingerprint="bad"),); self.assertEqual(evaluate(r,p,c,a,s,v,now=NOW).decision,Decision.DENY)
    def test_015_signature_version_mismatch_deny(self):
        p,c,a,s,v,r=setup(); s=(replace(s[0],expected_version=6),); self.assertEqual(evaluate(r,p,c,a,s,v,now=NOW).decision,Decision.DENY)
    def test_016_authority_epoch_mismatch_deny(self):
        r=replace(default_request(NOW),expected_authority_epoch="OLD"); p,c,a,_,v,_=setup(r); s=(signature_for(r,c,now=NOW),); self.assertEqual(evaluate(r,p,c,a,s,v,now=NOW).decision,Decision.DENY)
    def test_017_current_policy_inactive_hold(self):
        p,c,a,s,v,r=setup(); c=replace(c,active=False); self.assertEqual(evaluate(r,p,c,a,s,v,now=NOW).decision,Decision.HOLD)
    def test_018_current_version_hash_mismatch_hold(self):
        p,c,a,s,v,r=setup(); c=replace(c,policy_hash="bad"); s=(signature_for(r,c,now=NOW),); self.assertEqual(evaluate(r,p,c,a,s,v,now=NOW).decision,Decision.HOLD)
    def test_019_request_stale_hold(self):
        r=replace(default_request(NOW),created_at=NOW-9999); p,c,a,_,v,_=setup(r); s=(signature_for(r,c,now=NOW),); self.assertEqual(evaluate(r,p,c,a,s,v,now=NOW).decision,Decision.HOLD)
    def test_020_prepared_allow(self):
        p,c,a,s,v,r=setup(); st=prepare_state(p,c,a,s,v,binding=r.binding,now=NOW); self.assertTrue(validate_prepared_integrity(st)); z=evaluate_prepared(r,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True,now=NOW); self.assertEqual(z.decision,Decision.ALLOW)
    def test_021_prepared_integrity_required(self):
        p,c,a,s,v,r=setup(); st=prepare_state(p,c,a,s,v,binding=r.binding,now=NOW); self.assertEqual(evaluate_prepared(r,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False,now=NOW).decision,Decision.HOLD)
    def test_022_prepared_tamper_detected(self):
        p,c,a,s,v,r=setup(); st=prepare_state(p,c,a,s,v,binding=r.binding,now=NOW); tam=replace(st,authorities=(replace(st.authorities[0],capabilities=("EXECUTE","POLICY_UPDATE")),)+st.authorities[1:]); self.assertFalse(validate_prepared_integrity(tam))
    def test_023_registry_mismatch_hold(self):
        p,c,a,s,v,r=setup(); st=prepare_state(p,c,a,s,v,binding=r.binding,now=NOW); self.assertEqual(evaluate_prepared(r,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint="bad",prepared_integrity_validated=True,now=NOW).decision,Decision.HOLD)
    def test_024_delta_reconstruct(self):
        p,c,a,s,v,r=setup(); s1=prepare_state(p,c,a,s,v,binding=r.binding,now=NOW); a2=a+(AuthorityRecord("ADMIN-X",("POLICY_SIGN",),"POL-BIND","POL-EPOCH",True,False),); s2=prepare_state(p,c,a2,s,v,binding=r.binding,now=NOW); s3=apply_delta(s1,make_delta(s1,s2),now=NOW); self.assertEqual(s2.registry_fingerprint,s3.registry_fingerprint)
    def test_025_missing_only_sync(self):
        p,c,a,s,v,r=setup(); st=prepare_state(p,c,a,s,v,binding=r.binding,now=NOW); remote={"authorities":dict(st.authority_fingerprints),"signatures":dict(st.signature_fingerprints),"versions":dict(st.version_fingerprints)}; remote["authorities"].pop("AGENT-1"); q=missing_only_sync_plan(st,remote); self.assertEqual(q.missing_or_changed_authority_ids,("AGENT-1",)); self.assertFalse(q.full_resend_required)
    def test_026_duplicate_authority_hold(self):
        p,c,a,s,v,r=setup(); self.assertEqual(evaluate(r,p,c,a+(a[0],),s,v,now=NOW).decision,Decision.HOLD)
    def test_027_duplicate_signature_hold(self):
        p,c,a,s,v,r=setup(); self.assertEqual(evaluate(r,p,c,a,s+(s[0],),v,now=NOW).decision,Decision.HOLD)
    def test_028_duplicate_version_hold(self):
        p,c,a,s,v,r=setup(); self.assertEqual(evaluate(r,p,c,a,s,v+(v[0],),now=NOW).decision,Decision.HOLD)
    def test_029_authority_outputs_false(self):
        p,c,a,s,v,r=setup(); z=evaluate(r,p,c,a,s,v,now=NOW); self.assertFalse(any((z.policy_update_committed,z.policy_store_written,z.permission_granted,z.role_changed,z.capability_activated,z.signature_created,z.approval_executed,z.action_executed,z.world_truth_proven,z.safety_proven,z.action_success)))
    def test_030_rollback_hash_mismatch_deny(self):
        r=ChangeRequest("RB","SECURITY-ADMIN",7,"wrong","ROLLBACK",5,"SIG-71",NOW,"POL-BIND","POL-EPOCH"); p,c,a,_,v,_=setup(r); s=(signature_for(r,c,candidate_hash="wrong",signer_id="SECURITY-ADMIN",now=NOW),); self.assertEqual(evaluate(r,p,c,a,s,v,now=NOW).decision,Decision.DENY)

def _gen(i):
    def f(self):
        m=i%5
        if m==0:
            p,c,a,s,v,r=setup(); want=Decision.ALLOW
        elif m==1:
            r=replace(default_request(NOW),actor_id="AGENT-1"); p,c,a,_,v,_=setup(r); s=(signature_for(r,c,now=NOW),); want=Decision.DENY
        elif m==2:
            r=replace(default_request(NOW),expected_version=6); p,c,a,_,v,_=setup(r); s=(signature_for(r,c,now=NOW),); want=Decision.HOLD
        elif m==3:
            p,c,a,s,v,r=setup(); s=(replace(s[0],verified=False),); want=Decision.DENY
        else:
            r=ChangeRequest(f"RB{i}","SECURITY-ADMIN",7,"hash-v4","ROLLBACK",4,"SIG-71",NOW,"POL-BIND","POL-EPOCH"); p,c,a,_,v,_=setup(r); s=(signature_for(r,c,candidate_hash="hash-v4",signer_id="SECURITY-ADMIN",now=NOW),); want=Decision.ALLOW
        z=evaluate(r,p,c,a,s,v,now=NOW); self.assertEqual(z.decision,want); self.assertFalse(z.policy_update_committed); self.assertFalse(z.action_success)
    return f
for i in range(130): setattr(T,f"test_regression_{i:03d}",_gen(i))

if __name__=="__main__": unittest.main()
