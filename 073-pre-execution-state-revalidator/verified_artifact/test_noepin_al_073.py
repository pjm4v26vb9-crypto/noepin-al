import unittest
from dataclasses import replace
from noepin_al_073_pre_execution_state_revalidator import *

NOW=1_800_000_000

def base():
    pol=default_policy(); d=default_decision_snapshot(NOW); p=matching_preexecution_snapshot(d,NOW); keys=default_dependency_keys()
    return pol,d,p,keys

def change_value(p,key,fp=None,version=None,category=None,observed=None):
    vals=[]
    for v in p.values:
        if v.key==key:
            v=replace(v,
                value_fingerprint=v.value_fingerprint if fp is None else fp,
                version=v.version if version is None else version,
                category=v.category if category is None else category,
                observed=v.observed if observed is None else observed)
        vals.append(v)
    return replace(p,values=tuple(vals))

class T(unittest.TestCase):
    def test_001_no_diff(self):
        pol,d,p,k=base(); z=evaluate(d,p,k,pol,now=NOW); self.assertEqual(z.decision,Decision.ALLOW); self.assertTrue(z.next_gate_candidate)
    def test_002_no_authority_promotion(self):
        pol,d,p,k=base(); z=evaluate(d,p,k,pol,now=NOW); self.assertFalse(any((z.permission_granted,z.permit_refreshed,z.snapshot_written,z.state_mutated,z.tool_executed,z.transaction_committed,z.external_write_performed,z.world_truth_proven,z.safety_proven,z.action_success)))
    def test_003_target_header_change(self):
        pol,d,p,k=base(); p=replace(p,target_fingerprint='TGT-FP-2'); z=evaluate(d,p,k,pol,now=NOW); self.assertEqual(z.decision,Decision.HOLD); self.assertTrue(z.recheck_required)
    def test_004_authority_header_change(self):
        pol,d,p,k=base(); p=replace(p,authority_fingerprint='AUTH-FP-2'); self.assertEqual(evaluate(d,p,k,pol,now=NOW).decision,Decision.HOLD)
    def test_005_confidentiality_header_change(self):
        pol,d,p,k=base(); p=replace(p,confidentiality_fingerprint='CONF-FP-2'); self.assertEqual(evaluate(d,p,k,pol,now=NOW).decision,Decision.HOLD)
    def test_006_policy_header_change(self):
        pol,d,p,k=base(); p=replace(p,policy_fingerprint='POL-FP-2'); self.assertEqual(evaluate(d,p,k,pol,now=NOW).decision,Decision.HOLD)
    def test_007_irrelevant_change(self):
        pol,d,p,k=base(); p=change_value(p,'ui_theme',fp='THEME-LIGHT'); z=evaluate(d,p,k,pol,now=NOW); self.assertEqual(z.decision,Decision.ALLOW); self.assertEqual(z.irrelevant_diff_keys,('ui_theme',))
    def test_008_target_value_change(self):
        pol,d,p,k=base(); p=change_value(p,'target',fp='TGT-FP-2'); self.assertEqual(evaluate(d,p,k,pol,now=NOW).decision,Decision.HOLD)
    def test_009_permission_category_change(self):
        pol,d,p,k=base(); p=change_value(p,'ui_theme',fp='X',category='PERMISSION'); self.assertEqual(evaluate(d,p,k,pol,now=NOW).decision,Decision.HOLD)
    def test_010_missing_key(self):
        pol,d,p,k=base(); p=replace(p,values=tuple(v for v in p.values if v.key!='authority')); z=evaluate(d,p,k,pol,now=NOW); self.assertEqual(z.decision,Decision.HOLD); self.assertIn('authority',z.unobservable_keys)
    def test_011_unobserved(self):
        pol,d,p,k=base(); p=change_value(p,'policy',observed=False); self.assertEqual(evaluate(d,p,k,pol,now=NOW).decision,Decision.HOLD)
    def test_012_binding_mismatch(self):
        pol,d,p,k=base(); p=replace(p,binding='OTHER'); self.assertEqual(evaluate(d,p,k,pol,now=NOW).decision,Decision.HOLD)
    def test_013_epoch_mismatch(self):
        pol,d,p,k=base(); p=replace(p,state_epoch='OTHER'); self.assertEqual(evaluate(d,p,k,pol,now=NOW).decision,Decision.HOLD)
    def test_014_permit_mismatch(self):
        pol,d,p,k=base(); p=replace(p,permit_id='OTHER'); self.assertEqual(evaluate(d,p,k,pol,now=NOW).decision,Decision.HOLD)
    def test_015_decision_stale(self):
        pol,d,p,k=base(); d=replace(d,captured_at=NOW-pol.max_decision_age-1); self.assertEqual(evaluate(d,p,k,pol,now=NOW).decision,Decision.HOLD)
    def test_016_preexec_stale(self):
        pol,d,p,k=base(); p=replace(p,captured_at=NOW-pol.max_preexecution_age-1); self.assertEqual(evaluate(d,p,k,pol,now=NOW).decision,Decision.HOLD)
    def test_017_future_snapshot(self):
        pol,d,p,k=base(); p=replace(p,captured_at=NOW+1); self.assertEqual(evaluate(d,p,k,pol,now=NOW).decision,Decision.HOLD)
    def test_018_duplicate_dependency(self):
        pol,d,p,k=base(); self.assertEqual(evaluate(d,p,('target','target'),pol,now=NOW).decision,Decision.HOLD)
    def test_019_duplicate_value(self):
        pol,d,p,k=base(); p=replace(p,values=p.values+(p.values[0],)); self.assertEqual(evaluate(d,p,k,pol,now=NOW).decision,Decision.HOLD)
    def test_020_policy_revoked(self):
        pol,d,p,k=base(); pol=replace(pol,revoked=True); self.assertEqual(evaluate(d,p,k,pol,now=NOW).decision,Decision.HOLD)
    def test_021_prepared_equivalence(self):
        pol,d,p,k=base(); st=prepare_state(pol,d,k,binding=d.binding); valid=validate_prepared_integrity(st); z1=evaluate(d,p,k,pol,now=NOW); z2=evaluate_prepared(p,st,current_policy_fingerprint=st.policy_fingerprint,current_decision_fingerprint=st.decision_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=valid,now=NOW); self.assertEqual((z1.decision,z1.reasons),(z2.decision,z2.reasons))
    def test_022_prepared_tamper(self):
        pol,d,p,k=base(); st=prepare_state(pol,d,k,binding=d.binding); st=replace(st,registry_fingerprint='0'*64); self.assertFalse(validate_prepared_integrity(st))
    def test_023_prepared_policy_stale(self):
        pol,d,p,k=base(); st=prepare_state(pol,d,k,binding=d.binding); z=evaluate_prepared(p,st,current_policy_fingerprint='x',current_decision_fingerprint=st.decision_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True,now=NOW); self.assertEqual(z.decision,Decision.HOLD)
    def test_024_prepared_decision_stale(self):
        pol,d,p,k=base(); st=prepare_state(pol,d,k,binding=d.binding); z=evaluate_prepared(p,st,current_policy_fingerprint=st.policy_fingerprint,current_decision_fingerprint='x',current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True,now=NOW); self.assertEqual(z.decision,Decision.HOLD)
    def test_025_prepared_registry_stale(self):
        pol,d,p,k=base(); st=prepare_state(pol,d,k,binding=d.binding); z=evaluate_prepared(p,st,current_policy_fingerprint=st.policy_fingerprint,current_decision_fingerprint=st.decision_fingerprint,current_registry_fingerprint='x',prepared_integrity_validated=True,now=NOW); self.assertEqual(z.decision,Decision.HOLD)
    def test_026_delta_roundtrip(self):
        pol,d,p,k=base(); st=prepare_state(pol,d,k,binding=d.binding); vals=list(d.values); vals[0]=replace(vals[0],value_fingerprint='NEW'); d2=replace(d,values=tuple(vals),snapshot_id='DEC-SNAP-73B'); st2=prepare_state(pol,d2,k,binding=d.binding); delta=make_delta(st,st2); out=apply_delta(st,delta); self.assertEqual(out.registry_fingerprint,st2.registry_fingerprint)
    def test_027_delta_base_mismatch(self):
        pol,d,p,k=base(); st=prepare_state(pol,d,k,binding=d.binding); delta=make_delta(st,st); bad=replace(delta,base_fingerprint='x'); self.assertRaises(ValueError,apply_delta,st,bad)
    def test_028_missing_sync(self):
        pol,d,p,k=base(); st=prepare_state(pol,d,k,binding=d.binding); remote=dict(st.value_fingerprints); remote.pop('target'); plan=missing_only_sync_plan(st,remote); self.assertEqual(plan.missing_or_changed_keys,('target',)); self.assertFalse(plan.full_resend_required)
    def test_029_header_safety_always_checked_even_if_not_dependency(self):
        pol,d,p,k=base(); p=replace(p,target_fingerprint='TGT-X'); z=evaluate(d,p,('ui_theme',),pol,now=NOW); self.assertEqual(z.decision,Decision.HOLD)
    def test_030_category_mismatch_relevant(self):
        pol,d,p,k=base(); p=change_value(p,'ui_theme',category='TARGET'); z=evaluate(d,p,k,pol,now=NOW); self.assertEqual(z.decision,Decision.HOLD)
    def test_031_value_binding_unobservable(self):
        pol,d,p,k=base(); vals=tuple(replace(v,binding='X') if v.key=='authority' else v for v in p.values); p=replace(p,values=vals); self.assertEqual(evaluate(d,p,k,pol,now=NOW).decision,Decision.HOLD)
    def test_032_empty_dependency_failclosed(self):
        pol,d,p,k=base(); self.assertEqual(evaluate(d,p,(),pol,now=NOW).decision,Decision.HOLD)
    def test_033_version_change_relevant(self):
        pol,d,p,k=base(); p=change_value(p,'policy',version='v8'); self.assertEqual(evaluate(d,p,k,pol,now=NOW).decision,Decision.HOLD)
    def test_034_irrelevant_version_change_allowed(self):
        pol,d,p,k=base(); p=change_value(p,'ui_theme',version='v3'); self.assertEqual(evaluate(d,p,k,pol,now=NOW).decision,Decision.ALLOW)
    def test_035_prepared_malformed_current_snapshot_fails_closed(self):
        pol,d,p,k=base(); st=prepare_state(pol,d,k,binding=d.binding); p=replace(p,values=p.values+(p.values[0],)); z=evaluate_prepared(p,st,current_policy_fingerprint=st.policy_fingerprint,current_decision_fingerprint=st.decision_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=True,now=NOW); self.assertEqual(z.decision,Decision.HOLD)

def _gen(i):
    def f(self):
        pol,d,p,k=base()
        m=i%7
        if m==0:
            want=Decision.ALLOW
        elif m==1:
            p=replace(p,target_fingerprint=f'T-{i}'); want=Decision.HOLD
        elif m==2:
            p=change_value(p,'authority',fp=f'A-{i}'); want=Decision.HOLD
        elif m==3:
            p=change_value(p,'ui_theme',fp=f'UI-{i}'); want=Decision.ALLOW
        elif m==4:
            p=change_value(p,'confidentiality',observed=False); want=Decision.HOLD
        elif m==5:
            p=replace(p,captured_at=NOW-pol.max_preexecution_age-1); want=Decision.HOLD
        else:
            p=replace(p,policy_fingerprint=f'POL-{i}'); want=Decision.HOLD
        z=evaluate(d,p,k,pol,now=NOW)
        self.assertEqual(z.decision,want)
        self.assertFalse(z.permission_granted); self.assertFalse(z.tool_executed); self.assertFalse(z.transaction_committed); self.assertFalse(z.action_success)
    return f

for i in range(125):
    setattr(T,f'test_regression_{i:03d}',_gen(i))

if __name__=='__main__': unittest.main()
