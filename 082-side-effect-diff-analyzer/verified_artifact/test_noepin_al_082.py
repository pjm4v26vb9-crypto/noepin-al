import unittest
from dataclasses import replace
from noepin_al_082_side_effect_diff_analyzer import *

def base(): return (default_request(),default_policy(),default_before_state(),default_after_state(),default_expected_effects(),default_protected_fields(),default_severity_rules())

def neg(t,z):
    t.assertFalse(z.permission_granted); t.assertFalse(z.rollback_executed); t.assertFalse(z.state_committed); t.assertFalse(z.external_write_performed); t.assertFalse(z.action_executed); t.assertFalse(z.world_truth_proven); t.assertFalse(z.safety_proven); t.assertFalse(z.action_success)

class T(unittest.TestCase):
    def test_001_default_allow(self):
        z=evaluate(*base()); self.assertEqual(z.decision,Decision.ALLOW); self.assertEqual(len(z.expected_diff),2); self.assertEqual(z.unexpected_diff,()); self.assertTrue(z.next_gate_candidate); neg(self,z)
    def test_002_protected_change_deny(self):
        q,p,b,a,e,pr,s=base(); a=(a[0],a[1],replace(a[2],value='CHANGED'),a[3]); z=evaluate(q,p,b,a,e,pr,s); self.assertEqual(z.decision,Decision.DENY); self.assertTrue(z.rollback_candidate); neg(self,z)
    def test_003_major_unexpected_hold(self):
        q,p,b,a,e,pr,s=base(); b=b+(StateField('project/settings/x','a',True,True,'R',p.binding,p.state_epoch),); a=a+(StateField('project/settings/x','b',True,True,'R',p.binding,p.state_epoch),); z=evaluate(q,p,b,a,e,pr,s); self.assertEqual(z.decision,Decision.HOLD); self.assertEqual(z.highest_severity,Severity.HIGH); neg(self,z)
    def test_004_minor_allowed_allow(self):
        q,p,b,a,e,pr,s=base(); b=b+(StateField('logs/trace',None,False,True,'R',p.binding,p.state_epoch),) if not any(x.path=='logs/trace' for x in b) else b; a=tuple(replace(x,value='x',exists=True) if x.path=='logs/trace' else x for x in a); z=evaluate(q,p,b,a,e,pr,s); self.assertEqual(z.decision,Decision.ALLOW); self.assertEqual(z.highest_severity,Severity.LOW); neg(self,z)
    def test_005_incomplete_before_hold(self):
        q,p,b,a,e,pr,s=base(); self.assertEqual(evaluate(replace(q,before_complete=False),p,b,a,e,pr,s).decision,Decision.HOLD)
    def test_006_incomplete_after_hold(self):
        q,p,b,a,e,pr,s=base(); self.assertEqual(evaluate(replace(q,after_complete=False),p,b,a,e,pr,s).decision,Decision.HOLD)
    def test_007_unobserved_before_hold(self):
        q,p,b,a,e,pr,s=base(); b=(replace(b[0],observed=False),)+b[1:]; self.assertEqual(evaluate(q,p,b,a,e,pr,s).decision,Decision.HOLD)
    def test_008_unobserved_after_hold(self):
        q,p,b,a,e,pr,s=base(); a=(replace(a[0],observed=False),)+a[1:]; self.assertEqual(evaluate(q,p,b,a,e,pr,s).decision,Decision.HOLD)
    def test_009_missing_expected_hold(self):
        q,p,b,a,e,pr,s=base(); a=(replace(a[0],value='old'),)+a[1:]; self.assertEqual(evaluate(q,p,b,a,e,pr,s).decision,Decision.HOLD)
    def test_010_unknown_expected_hold(self):
        q,p,b,a,e,pr,s=base(); self.assertEqual(evaluate(replace(q,expected_effect_ids=('NOPE',)),p,b,a,e,pr,s).decision,Decision.HOLD)
    def test_011_unknown_protected_hold(self):
        q,p,b,a,e,pr,s=base(); self.assertEqual(evaluate(replace(q,protected_rule_ids=('NOPE',)),p,b,a,e,pr,s).decision,Decision.HOLD)
    def test_012_duplicate_before_hold(self):
        q,p,b,a,e,pr,s=base(); self.assertEqual(evaluate(q,p,b+b[:1],a,e,pr,s).decision,Decision.HOLD)
    def test_013_duplicate_after_hold(self):
        q,p,b,a,e,pr,s=base(); self.assertEqual(evaluate(q,p,b,a+a[:1],e,pr,s).decision,Decision.HOLD)
    def test_014_duplicate_effect_hold(self):
        q,p,b,a,e,pr,s=base(); self.assertEqual(evaluate(q,p,b,a,e+e[:1],pr,s).decision,Decision.HOLD)
    def test_015_duplicate_protected_hold(self):
        q,p,b,a,e,pr,s=base(); self.assertEqual(evaluate(q,p,b,a,e,pr+pr[:1],s).decision,Decision.HOLD)
    def test_016_duplicate_severity_hold(self):
        q,p,b,a,e,pr,s=base(); self.assertEqual(evaluate(q,p,b,a,e,pr,s+s[:1]).decision,Decision.HOLD)
    def test_017_request_binding_hold(self):
        q,p,b,a,e,pr,s=base(); self.assertEqual(evaluate(replace(q,binding='BAD'),p,b,a,e,pr,s).decision,Decision.HOLD)
    def test_018_before_binding_hold(self):
        q,p,b,a,e,pr,s=base(); b=(replace(b[0],binding='BAD'),)+b[1:]; self.assertEqual(evaluate(q,p,b,a,e,pr,s).decision,Decision.HOLD)
    def test_019_after_binding_hold(self):
        q,p,b,a,e,pr,s=base(); a=(replace(a[0],binding='BAD'),)+a[1:]; self.assertEqual(evaluate(q,p,b,a,e,pr,s).decision,Decision.HOLD)
    def test_020_expected_binding_hold(self):
        q,p,b,a,e,pr,s=base(); e=(replace(e[0],binding='BAD'),)+e[1:]; self.assertEqual(evaluate(q,p,b,a,e,pr,s).decision,Decision.HOLD)
    def test_021_protected_binding_hold(self):
        q,p,b,a,e,pr,s=base(); pr=(replace(pr[0],binding='BAD'),); self.assertEqual(evaluate(q,p,b,a,e,pr,s).decision,Decision.HOLD)
    def test_022_severity_binding_hold(self):
        q,p,b,a,e,pr,s=base(); s=(replace(s[0],binding='BAD'),)+s[1:]; self.assertEqual(evaluate(q,p,b,a,e,pr,s).decision,Decision.HOLD)
    def test_023_policy_revoked_hold(self):
        q,p,b,a,e,pr,s=base(); self.assertEqual(evaluate(q,replace(p,revoked=True),b,a,e,pr,s).decision,Decision.HOLD)
    def test_024_add_expected(self):
        q,p,b,a,e,pr,s=base(); b=b+(StateField('new/file',None,False,True,'R',p.binding,p.state_epoch),); a=a+(StateField('new/file','x',True,True,'R',p.binding,p.state_epoch),); ee=ExpectedEffect('E-NEW','new/file',ChangeKind.ADD,None,'x',True,p.binding,p.state_epoch); q=replace(q,expected_effect_ids=q.expected_effect_ids+('E-NEW',)); z=evaluate(q,p,b,a,e+(ee,),pr,s); self.assertEqual(z.decision,Decision.ALLOW)
    def test_025_remove_expected(self):
        q,p,b,a,e,pr,s=base(); b=b+(StateField('old/file','x',True,True,'R',p.binding,p.state_epoch),); a=a+(StateField('old/file',None,False,True,'R',p.binding,p.state_epoch),); ee=ExpectedEffect('E-OLD','old/file',ChangeKind.REMOVE,'x',None,True,p.binding,p.state_epoch); q=replace(q,expected_effect_ids=q.expected_effect_ids+('E-OLD',)); z=evaluate(q,p,b,a,e+(ee,),pr,s); self.assertEqual(z.decision,Decision.ALLOW)
    def test_026_synth_add_unexpected_hold(self):
        q,p,b,a,e,pr,s=base(); a=a+(StateField('other/new','x',True,True,'R',p.binding,p.state_epoch),); z=evaluate(q,p,b,a,e,pr,s); self.assertEqual(z.decision,Decision.HOLD)
    def test_027_synth_remove_unexpected_hold(self):
        q,p,b,a,e,pr,s=base(); b=b+(StateField('other/old','x',True,True,'R',p.binding,p.state_epoch),); z=evaluate(q,p,b,a,e,pr,s); self.assertEqual(z.decision,Decision.HOLD)
    def test_028_large_diff_hold(self):
        q,p,b,a,e,pr,s=base(); p=replace(p,large_diff_threshold=2); z=evaluate(q,p,b,a,e,pr,s); self.assertEqual(z.decision,Decision.HOLD)
    def test_029_minor_not_allowlisted_hold(self):
        q,p,b,a,e,pr,s=base(); b=b+(StateField('logs/other','a',True,True,'R',p.binding,p.state_epoch),); a=a+(StateField('logs/other','b',True,True,'R',p.binding,p.state_epoch),); z=evaluate(q,p,b,a,e,pr,s); self.assertEqual(z.decision,Decision.HOLD)
    def test_030_expected_protected_is_deny(self):
        q,p,b,a,e,pr,s=base(); b2=tuple(replace(x,value='old') if x.path=='secrets/token' else x for x in b); a2=tuple(replace(x,value='new') if x.path=='secrets/token' else x for x in a); ee=ExpectedEffect('E-SECRET','secrets/token',ChangeKind.CHANGE,'old','new',True,p.binding,p.state_epoch); q=replace(q,expected_effect_ids=q.expected_effect_ids+('E-SECRET',)); z=evaluate(q,p,b2,a2,e+(ee,),pr,s); self.assertEqual(z.decision,Decision.DENY); self.assertTrue(z.rollback_candidate)
    def test_031_prepared_same(self):
        q,p,b,a,e,pr,s=base(); st=prepare_state(p,q,b,a,e,pr,s,binding=p.binding); valid=validate_prepared_integrity(st); self.assertEqual(evaluate(*base()),evaluate_prepared(st,current_policy_fingerprint=st.policy_fingerprint,current_request_fingerprint=st.request_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid))
    def test_032_prepared_unvalidated_hold(self):
        q,p,b,a,e,pr,s=base(); st=prepare_state(p,q,b,a,e,pr,s,binding=p.binding); self.assertEqual(evaluate_prepared(st,current_policy_fingerprint=st.policy_fingerprint,current_request_fingerprint=st.request_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=False).decision,Decision.HOLD)
    def test_033_prepared_stale_policy(self):
        q,p,b,a,e,pr,s=base(); st=prepare_state(p,q,b,a,e,pr,s,binding=p.binding); self.assertEqual(evaluate_prepared(st,current_policy_fingerprint='BAD',current_request_fingerprint=st.request_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_034_prepared_stale_request(self):
        q,p,b,a,e,pr,s=base(); st=prepare_state(p,q,b,a,e,pr,s,binding=p.binding); self.assertEqual(evaluate_prepared(st,current_policy_fingerprint=st.policy_fingerprint,current_request_fingerprint='BAD',current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_035_prepared_stale_registry(self):
        q,p,b,a,e,pr,s=base(); st=prepare_state(p,q,b,a,e,pr,s,binding=p.binding); self.assertEqual(evaluate_prepared(st,current_policy_fingerprint=st.policy_fingerprint,current_request_fingerprint=st.request_fingerprint,current_registry_fingerprint='BAD',prepared_integrity_validated=True).decision,Decision.HOLD)
    def test_036_tamper_integrity_false(self):
        q,p,b,a,e,pr,s=base(); st=prepare_state(p,q,b,a,e,pr,s,binding=p.binding); self.assertFalse(validate_prepared_integrity(replace(st,registry_fingerprint='BAD')))
    def test_037_delta_roundtrip(self):
        q,p,b,a,e,pr,s=base(); st=prepare_state(p,q,b,a,e,pr,s,binding=p.binding); a2=tuple(replace(x,value='v2') if x.path=='config/mode' else x for x in a); st2=prepare_state(p,q,b,a2,e,pr,s,binding=p.binding); self.assertEqual(apply_delta(st,make_delta(st,st2)).registry_fingerprint,st2.registry_fingerprint)
    def test_038_delta_base_mismatch(self):
        q,p,b,a,e,pr,s=base(); st=prepare_state(p,q,b,a,e,pr,s,binding=p.binding); st2=prepare_state(p,q,b,a,e,pr,s,binding=p.binding); d=replace(make_delta(st,st2),base_fingerprint='BAD'); self.assertRaises(ValueError,apply_delta,st,d)
    def test_039_missing_sync(self):
        q,p,b,a,e,pr,s=base(); st=prepare_state(p,q,b,a,e,pr,s,binding=p.binding); kb=dict(st.before_fingerprints); ka=dict(st.after_fingerprints); ke=dict(st.expected_fingerprints); kp=dict(st.protected_fingerprints); ks=dict(st.severity_fingerprints); ka.pop('status'); plan=missing_only_sync_plan(st,kb,ka,ke,kp,ks); self.assertIn('status',plan.missing_or_changed_after_paths); self.assertFalse(plan.full_resend_required)
    def test_040_authority_negatives(self): neg(self,evaluate(*base()))


def _gen(k):
    def f(self):
        q,p,b,a,e,pr,s=base(); m=k%15
        if m==0: want=Decision.ALLOW
        elif m==1:
            a=tuple(replace(x,value='CHANGED') if x.path=='secrets/token' else x for x in a); want=Decision.DENY
        elif m==2:
            b=b+(StateField(f'project/settings/{k}','a',True,True,'R',p.binding,p.state_epoch),); a=a+(StateField(f'project/settings/{k}','b',True,True,'R',p.binding,p.state_epoch),); want=Decision.HOLD
        elif m==3:
            path='logs/trace'; a=tuple(replace(x,value=f'x{k}',exists=True) if x.path==path else x for x in a); want=Decision.ALLOW
        elif m==4: q=replace(q,before_complete=False); want=Decision.HOLD
        elif m==5: q=replace(q,after_complete=False); want=Decision.HOLD
        elif m==6: a=(replace(a[0],observed=False),)+a[1:]; want=Decision.HOLD
        elif m==7: q=replace(q,expected_effect_ids=('NOPE',)); want=Decision.HOLD
        elif m==8: p=replace(p,revoked=True); want=Decision.HOLD
        elif m==9: a=(replace(a[0],value='old'),)+a[1:]; want=Decision.HOLD
        elif m==10:
            b=b+(StateField(f'other/{k}','a',True,True,'R',p.binding,p.state_epoch),); a=a+(StateField(f'other/{k}','b',True,True,'R',p.binding,p.state_epoch),); want=Decision.HOLD
        elif m==11: q=replace(q,binding=f'BAD-{k}'); want=Decision.HOLD
        elif m==12: p=replace(p,large_diff_threshold=2); want=Decision.HOLD
        elif m==13:
            # no-op receipt-like absence: analyzer still uses state only
            want=Decision.ALLOW
        else:
            # expected add
            path=f'new/{k}'; b=b+(StateField(path,None,False,True,'R',p.binding,p.state_epoch),); a=a+(StateField(path,'x',True,True,'R',p.binding,p.state_epoch),); ee=ExpectedEffect(f'E-{k}',path,ChangeKind.ADD,None,'x',True,p.binding,p.state_epoch); e=e+(ee,); q=replace(q,expected_effect_ids=q.expected_effect_ids+(f'E-{k}',)); want=Decision.ALLOW
        z=evaluate(q,p,b,a,e,pr,s); self.assertEqual(z.decision,want); neg(self,z)
    return f
for k in range(120): setattr(T,f'test_regression_{k:03d}',_gen(k))
if __name__=='__main__': unittest.main(verbosity=2)
