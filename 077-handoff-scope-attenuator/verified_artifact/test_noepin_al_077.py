import unittest
from dataclasses import replace
from noepin_al_077_handoff_scope_attenuator import *

def base(): return default_policy(),default_scopes(),default_capabilities(),default_request()
def assert_neg(t,z):
    for k in ('permission_granted','signed_delegation_token_issued','capability_activated','child_agent_created','sender_authority_inherited','sender_intent_inherited','sender_consent_inherited','tool_executed','transaction_committed','external_write_performed','world_truth_proven','safety_proven','action_success'):
        t.assertFalse(getattr(z,k),k)

class T(unittest.TestCase):
    def test_001_normal_shrink_allow(self):
        p,s,c,q=base(); z=evaluate(q,p,s,c); self.assertEqual(z.decision,Decision.ALLOW); self.assertTrue(z.delegation_permit_candidate); assert_neg(self,z)
    def test_002_equal_allow(self):
        p,s,c,q=base(); q=replace(q,child_scope_id='SCOPE-EQUAL',delegation_purpose=('ANALYZE',),required_capabilities=('CAP-ANALYZE',)); z=evaluate(q,p,s,c); self.assertEqual(z.decision,Decision.ALLOW); assert_neg(self,z)
    def test_003_expansion_deny(self):
        p,s,c,q=base(); q=replace(q,child_scope_id='SCOPE-EXPANDED',delegation_purpose=('ANALYZE',),required_capabilities=('CAP-ANALYZE',)); z=evaluate(q,p,s,c); self.assertEqual(z.decision,Decision.DENY); self.assertTrue(z.violation_items); self.assertFalse(z.delegation_permit_candidate); assert_neg(self,z)
    def test_004_parent_unknown_hold(self):
        p,s,c,q=base(); self.assertEqual(evaluate(replace(q,parent_scope_id='MISSING'),p,s,c).decision,Decision.HOLD)
    def test_005_child_unknown_hold(self):
        p,s,c,q=base(); self.assertEqual(evaluate(replace(q,child_scope_id='MISSING'),p,s,c).decision,Decision.HOLD)
    def test_006_parent_unobserved_hold(self):
        p,s,c,q=base(); s=tuple(replace(x,observed=False) if x.scope_id=='SCOPE-PARENT' else x for x in s); self.assertEqual(evaluate(q,p,s,c).decision,Decision.HOLD)
    def test_007_parent_authority_unconfirmed_hold(self):
        p,s,c,q=base(); s=tuple(replace(x,authority_confirmed=False) if x.scope_id=='SCOPE-PARENT' else x for x in s); z=evaluate(q,p,s,c); self.assertEqual(z.decision,Decision.HOLD); self.assertFalse(z.sender_authority_inherited)
    def test_008_child_unobserved_hold(self):
        p,s,c,q=base(); s=tuple(replace(x,observed=False) if x.scope_id=='SCOPE-CHILD' else x for x in s); self.assertEqual(evaluate(q,p,s,c).decision,Decision.HOLD)
    def test_009_depth_mismatch_hold(self):
        p,s,c,q=base(); s=tuple(replace(x,depth=3) if x.scope_id=='SCOPE-CHILD' else x for x in s); self.assertEqual(evaluate(q,p,s,c).decision,Decision.HOLD)
    def test_010_max_depth_deny(self):
        p,s,c,q=base(); p=replace(p,max_depth=1); mid=replace(next(x for x in s if x.scope_id=='SCOPE-CHILD'),authority_confirmed=True); s=tuple(mid if x.scope_id=='SCOPE-CHILD' else x for x in s); q=HandoffRequest('REQ-DEPTH','SCOPE-CHILD','SCOPE-GRANDCHILD',('SUMMARIZE',),('CAP-READ',),p.binding,p.state_epoch); self.assertEqual(evaluate(q,p,s,c).decision,Decision.DENY)
    def test_011_purpose_missing_hold(self):
        p,s,c,q=base(); self.assertEqual(evaluate(replace(q,delegation_purpose=()),p,s,c).decision,Decision.HOLD)
    def test_012_purpose_parent_expansion_deny(self):
        p,s,c,q=base(); q=replace(q,delegation_purpose=('EXPORT',)); z=evaluate(q,p,s,c); self.assertEqual(z.decision,Decision.DENY); self.assertIn('PURPOSE_PARENT:EXPORT',z.violation_items)
    def test_013_purpose_not_child_deny(self):
        p,s,c,q=base(); q=replace(q,child_scope_id='SCOPE-CHILD',delegation_purpose=('ANALYZE',)); z=evaluate(q,p,s,c); self.assertEqual(z.decision,Decision.DENY); self.assertIn('PURPOSE_CHILD:ANALYZE',z.violation_items)
    def test_014_required_cap_parent_deny(self):
        p,s,c,q=base(); q=replace(q,required_capabilities=('CAP-EXPORT',)); self.assertEqual(evaluate(q,p,s,c).decision,Decision.DENY)
    def test_015_required_cap_child_deny(self):
        p,s,c,q=base(); q=replace(q,required_capabilities=('CAP-ANALYZE',)); self.assertEqual(evaluate(q,p,s,c).decision,Decision.DENY)
    def test_016_cap_record_unknown_hold(self):
        p,s,c,q=base(); c=tuple(x for x in c if x.capability_id!='CAP-READ'); self.assertEqual(evaluate(q,p,s,c).decision,Decision.HOLD)
    def test_017_cap_record_unobserved_hold(self):
        p,s,c,q=base(); c=tuple(replace(x,observed=False) if x.capability_id=='CAP-READ' else x for x in c); self.assertEqual(evaluate(q,p,s,c).decision,Decision.HOLD)
    def test_018_cap_action_violation_deny(self):
        p,s,c,q=base(); child=next(x for x in s if x.scope_id=='SCOPE-CHILD'); bad=replace(child,actions=('ANALYZE','READ','SUMMARIZE')); s=tuple(bad if x.scope_id=='SCOPE-CHILD' else x for x in s); z=evaluate(q,p,s,c); self.assertEqual(z.decision,Decision.DENY); self.assertIn('CAPABILITY_ACTION:ANALYZE',z.violation_items)
    def test_019_data_expansion_deny(self):
        p,s,c,q=base(); ch=next(x for x in s if x.scope_id=='SCOPE-CHILD'); ch=replace(ch,data_classes=('PUBLIC','SECRET')); s=tuple(ch if x.scope_id=='SCOPE-CHILD' else x for x in s); self.assertEqual(evaluate(q,p,s,c).decision,Decision.DENY)
    def test_020_target_expansion_deny(self):
        p,s,c,q=base(); ch=next(x for x in s if x.scope_id=='SCOPE-CHILD'); ch=replace(ch,targets=('EXTERNAL-ENDPOINT','WORKSPACE')); s=tuple(ch if x.scope_id=='SCOPE-CHILD' else x for x in s); self.assertEqual(evaluate(q,p,s,c).decision,Decision.DENY)
    def test_021_goal_expansion_deny(self):
        p,s,c,q=base(); ch=next(x for x in s if x.scope_id=='SCOPE-CHILD'); ch=replace(ch,goals=('EXPORT','SUMMARIZE')); s=tuple(ch if x.scope_id=='SCOPE-CHILD' else x for x in s); self.assertEqual(evaluate(q,p,s,c).decision,Decision.DENY)
    def test_022_action_expansion_deny(self):
        p,s,c,q=base(); ch=next(x for x in s if x.scope_id=='SCOPE-CHILD'); ch=replace(ch,actions=('EXTERNAL_SEND','READ','SUMMARIZE')); s=tuple(ch if x.scope_id=='SCOPE-CHILD' else x for x in s); self.assertEqual(evaluate(q,p,s,c).decision,Decision.DENY)
    def test_023_capability_expansion_deny(self):
        p,s,c,q=base(); ch=next(x for x in s if x.scope_id=='SCOPE-CHILD'); ch=replace(ch,capabilities=('CAP-EXPORT','CAP-READ')); s=tuple(ch if x.scope_id=='SCOPE-CHILD' else x for x in s); self.assertEqual(evaluate(q,p,s,c).decision,Decision.DENY)
    def test_024_multihop_shrink_allow(self):
        p,s,c,q=base(); mid=replace(next(x for x in s if x.scope_id=='SCOPE-CHILD'),authority_confirmed=True); grand=next(x for x in s if x.scope_id=='SCOPE-GRANDCHILD'); s=tuple(mid if x.scope_id=='SCOPE-CHILD' else x for x in s); q=HandoffRequest('REQ-MULTI','SCOPE-CHILD','SCOPE-GRANDCHILD',('SUMMARIZE',),('CAP-READ',),p.binding,p.state_epoch); self.assertEqual(evaluate(q,p,s,c).decision,Decision.ALLOW)
    def test_025_multihop_expansion_deny(self):
        p,s,c,q=base(); mid=replace(next(x for x in s if x.scope_id=='SCOPE-CHILD'),authority_confirmed=True); expanded=ScopeSpec('SCOPE-GRAND-EXP',('ANALYZE','SUMMARIZE'),('PUBLIC',),('ANALYZE','READ'),('WORKSPACE',),('CAP-ANALYZE','CAP-READ'),2,True,False,p.binding,p.state_epoch); s=tuple(mid if x.scope_id=='SCOPE-CHILD' else x for x in s)+(expanded,); q=HandoffRequest('REQ-MULTI-X','SCOPE-CHILD','SCOPE-GRAND-EXP',('SUMMARIZE',),('CAP-READ',),p.binding,p.state_epoch); self.assertEqual(evaluate(q,p,s,c).decision,Decision.DENY)
    def test_026_request_binding_hold(self):
        p,s,c,q=base(); self.assertEqual(evaluate(replace(q,binding='BAD'),p,s,c).decision,Decision.HOLD)
    def test_027_policy_revoked_hold(self):
        p,s,c,q=base(); self.assertEqual(evaluate(q,replace(p,revoked=True),s,c).decision,Decision.HOLD)
    def test_028_duplicate_scope_hold(self):
        p,s,c,q=base(); self.assertEqual(evaluate(q,p,s+(s[0],),c).decision,Decision.HOLD)
    def test_029_duplicate_cap_hold(self):
        p,s,c,q=base(); self.assertEqual(evaluate(q,p,s,c+(c[0],)).decision,Decision.HOLD)
    def test_030_capability_evidence_missing_hold(self):
        p,s,c,q=base(); ch=next(x for x in s if x.scope_id=='SCOPE-CHILD'); ch=replace(ch,capabilities=()); s=tuple(ch if x.scope_id=='SCOPE-CHILD' else x for x in s); q=replace(q,required_capabilities=()); self.assertEqual(evaluate(q,p,s,c).decision,Decision.HOLD)
    def test_031_prepare_integrity(self):
        p,s,c,q=base(); st=prepare_state(p,s,c,binding=p.binding); self.assertTrue(validate_prepared_integrity(st))
    def test_032_prepared_semantics(self):
        p,s,c,q=base(); st=prepare_state(p,s,c,binding=p.binding); z1=evaluate(q,p,s,c); z2=evaluate_prepared(q,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True); self.assertEqual((z1.decision,z1.reasons,z1.violation_items),(z2.decision,z2.reasons,z2.violation_items))
    def test_033_prepared_unvalidated_hold(self):
        p,s,c,q=base(); st=prepare_state(p,s,c,binding=p.binding); self.assertEqual(evaluate_prepared(q,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False).decision,Decision.HOLD)
    def test_034_prepared_changed_policy_hold(self):
        p,s,c,q=base(); st=prepare_state(p,s,c,binding=p.binding); self.assertEqual(evaluate_prepared(q,st,current_policy_fingerprint='BAD',current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_035_prepared_changed_registry_hold(self):
        p,s,c,q=base(); st=prepare_state(p,s,c,binding=p.binding); self.assertEqual(evaluate_prepared(q,st,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint='BAD',prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_036_tampered_prepared_false(self):
        p,s,c,q=base(); st=prepare_state(p,s,c,binding=p.binding); self.assertFalse(validate_prepared_integrity(replace(st,registry_fingerprint='BAD')))
    def test_037_delta_roundtrip(self):
        p,s,c,q=base(); a=prepare_state(p,s,c,binding=p.binding); s2=tuple(replace(x,data_classes=('INTERNAL','PUBLIC')) if x.scope_id=='SCOPE-CHILD' else x for x in s); b=prepare_state(p,s2,c,binding=p.binding); d=make_delta(a,b); self.assertEqual(apply_delta(a,d).registry_fingerprint,b.registry_fingerprint)
    def test_038_missing_sync(self):
        p,s,c,q=base(); st=prepare_state(p,s,c,binding=p.binding); ks=dict(st.scope_fingerprints); kc=dict(st.capability_fingerprints); ks.pop('SCOPE-CHILD'); plan=missing_only_sync_plan(st,ks,kc); self.assertIn('SCOPE-CHILD',plan.missing_or_changed_scopes); self.assertFalse(plan.full_resend_required)
    def test_039_invalid_typed_input_hold(self):
        p,s,c,q=base(); self.assertEqual(evaluate({'x':1},p,s,c).decision,Decision.HOLD)
    def test_040_authority_negatives(self):
        p,s,c,q=base(); assert_neg(self,evaluate(q,p,s,c))

def _gen(i):
    def f(self):
        p,s,c,q=base(); m=i%10
        if m==0: want=Decision.ALLOW
        elif m==1: q=replace(q,child_scope_id='SCOPE-EXPANDED',delegation_purpose=('ANALYZE',),required_capabilities=('CAP-ANALYZE',)); want=Decision.DENY
        elif m==2: q=replace(q,parent_scope_id='MISSING'); want=Decision.HOLD
        elif m==3: q=replace(q,binding=f'BAD-{i}'); want=Decision.HOLD
        elif m==4: s=tuple(replace(x,authority_confirmed=False) if x.scope_id=='SCOPE-PARENT' else x for x in s); want=Decision.HOLD
        elif m==5: q=replace(q,child_scope_id='SCOPE-EQUAL',delegation_purpose=('ANALYZE',),required_capabilities=('CAP-ANALYZE',)); want=Decision.ALLOW
        elif m==6: q=replace(q,delegation_purpose=('EXPORT',)); want=Decision.DENY
        elif m==7: c=tuple(x for x in c if x.capability_id!='CAP-READ'); want=Decision.HOLD
        elif m==8: q=replace(q,child_scope_id='MISSING'); want=Decision.HOLD
        else: s=tuple(replace(x,observed=False) if x.scope_id=='SCOPE-CHILD' else x for x in s); want=Decision.HOLD
        z=evaluate(q,p,s,c); self.assertEqual(z.decision,want); assert_neg(self,z)
    return f
for i in range(120): setattr(T,f'test_regression_{i:03d}',_gen(i))
if __name__=='__main__': unittest.main()
