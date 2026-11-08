from __future__ import annotations
import unittest
from dataclasses import replace
import noepin_al_065_minimal_change_optimizer as m
NOW=1_800_000_000

def base(): return m.default_request(NOW),m.default_policy(NOW),m.default_changes(),m.default_goals()
def repl(items,key,val,**kw): return tuple(replace(x,**kw) if getattr(x,key)==val else x for x in items)
def ev(req=None,policy=None,changes=None,goals=None,approval=None):
    r,p,c,g=base(); return m.evaluate(req or r,policy or p,changes or c,goals or g,approval,now=NOW)
def no_authority(t,d):
    for k in ('permission_granted','write_performed','patch_committed','deployment_executed','approval_executed','world_truth_proven','safety_proven','action_success'):
        t.assertFalse(getattr(d,k),k)

def sc01(t):
    d=ev(); t.assertEqual(d.decision,m.Decision.ALLOW); t.assertEqual(d.selected_change_candidate,('CHG-MIN',)); t.assertIn('CHG-NOISE',d.excluded_changes); t.assertTrue(d.minimality_confirmed_under_supplied_model); t.assertTrue(d.next_gate_candidate); no_authority(t,d)
def sc02(t):
    r,p,c,g=base(); r=replace(r,candidate_change_ids=('CHG-MIN','CHG-NOISE')); d=ev(req=r); t.assertEqual(d.selected_change_candidate,('CHG-MIN',)); t.assertEqual(d.excluded_changes,('CHG-NOISE',)); no_authority(t,d)
def sc03(t):
    r,p,c,g=base(); r=replace(r,candidate_change_ids=('CHG-PROTECTED','CHG-B')); d=ev(req=r); t.assertEqual(d.decision,m.Decision.DENY); t.assertEqual(d.protected_change_ids,('CHG-PROTECTED',)); no_authority(t,d)
def sc04(t):
    r,p,c,g=base(); r=replace(r,candidate_change_ids=('CHG-NOISE',)); d=ev(req=r); t.assertEqual(d.decision,m.Decision.HOLD); t.assertIn('GOAL_UNREACHABLE',d.reasons); no_authority(t,d)
def sc05(t):
    r,p,c,g=base(); r=replace(r,current_state_facts=('GOAL-A','GOAL-B')); d=ev(req=r); t.assertEqual(d.decision,m.Decision.ALLOW); t.assertEqual(d.selected_change_candidate,()); t.assertTrue(d.next_gate_candidate); no_authority(t,d)
def sc06(t):
    r,p,c,g=base(); r=replace(r,candidate_change_ids=('CHG-TIE-REV','CHG-TIE-IRREV')); d=ev(req=r); t.assertEqual(d.decision,m.Decision.ALLOW); t.assertEqual(d.selected_change_candidate,('CHG-TIE-REV',)); t.assertEqual(d.reversibility_score,1); no_authority(t,d)
def sc07(t):
    r,p,c,g=base(); r=replace(r,candidate_change_ids=('CHG-TIE-REV','CHG-TIE-UNKNOWN')); d=ev(req=r); t.assertEqual(d.decision,m.Decision.HOLD); t.assertIn('TIED_SOLUTION_SAFETY_NOT_COMPARABLE',d.reasons); no_authority(t,d)
def sc08(t):
    r,p,c,g=base(); r=replace(r,candidate_change_ids=('CHG-APPROVAL',)); d=ev(req=r); t.assertEqual(d.decision,m.Decision.HUMAN_APPROVAL); t.assertEqual(d.selected_change_candidate,('CHG-APPROVAL',)); no_authority(t,d)
def sc09(t):
    r,p,c,g=base(); r=replace(r,candidate_change_ids=('CHG-APPROVAL',)); d=ev(req=r,approval=m.default_approval(NOW)); t.assertEqual(d.decision,m.Decision.ALLOW); t.assertTrue(d.next_gate_candidate); no_authority(t,d)
def sc10(t):
    r,p,c,g=base(); p=replace(p,exact_search_limit=2); d=ev(policy=p); t.assertEqual(d.decision,m.Decision.HOLD); t.assertIn('EXACT_MINIMALITY_NOT_CONFIRMED_SEARCH_LIMIT',d.reasons); no_authority(t,d)
def sc11(t):
    r,p,c,g=base(); r=replace(r,expected_policy_version='BAD'); d=ev(req=r); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc12(t):
    r,p,c,g=base(); r=replace(r,binding='BAD'); d=ev(req=r); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc13(t):
    r,p,c,g=base(); r=replace(r,expires_at=NOW-1); d=ev(req=r); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc14(t):
    r,p,c,g=base(); r=replace(r,created_at=NOW+1); d=ev(req=r); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc15(t):
    r,p,c,g=base(); r=replace(r,candidate_change_ids=('CHG-MIN','CHG-MIN')); d=ev(req=r); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc16(t):
    r,p,c,g=base(); r=replace(r,candidate_change_ids=('MISSING',)); d=ev(req=r); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc17(t):
    r,p,c,g=base(); p=replace(p,max_candidate_changes=1); d=ev(policy=p); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc18(t):
    r,p,c,g=base(); c=c+(c[0],); d=ev(changes=c); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc19(t):
    r,p,c,g=base(); g=g+(g[0],); d=ev(goals=g); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc20(t):
    r,p,c,g=base(); c=repl(c,'change_id','CHG-MIN',verified=False); d=ev(changes=c); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc21(t):
    r,p,c,g=base(); c=repl(c,'change_id','CHG-MIN',revoked=True); d=ev(changes=c); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc22(t):
    r,p,c,g=base(); c=repl(c,'change_id','CHG-MIN',binding='BAD'); d=ev(changes=c); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc23(t):
    r,p,c,g=base(); c=repl(c,'change_id','CHG-MIN',policy_version='BAD'); d=ev(changes=c); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc24(t):
    r,p,c,g=base(); c=repl(c,'change_id','CHG-MIN',change_cost=-1.0); d=ev(changes=c); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc25(t):
    r,p,c,g=base(); g=repl(g,'clause_id','G1',verified=False); d=ev(goals=g); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc26(t):
    r,p,c,g=base(); g=repl(g,'clause_id','G1',alternatives=()); d=ev(goals=g); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc27(t):
    r,p,c,g=base(); p=replace(p,revoked=True); d=ev(policy=p); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc28(t):
    r,p,c,g=base(); p=replace(p,cost_weight=-1.0); d=ev(policy=p); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc29(t):
    r,p,c,g=base(); ps=m.prepare_state(p,c,g,binding=r.binding,now=NOW); d=m.evaluate_prepared(r,ps,None,current_policy_fingerprint='BAD',current_registry_fingerprint=ps.registry_fingerprint,prepared_integrity_validated=True,now=NOW); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc30(t):
    r,p,c,g=base(); ps=m.prepare_state(p,c,g,binding=r.binding,now=NOW); d=m.evaluate_prepared(r,ps,None,current_policy_fingerprint=ps.policy_fingerprint,current_registry_fingerprint='BAD',prepared_integrity_validated=True,now=NOW); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc31(t):
    r,p,c,g=base(); ps=m.prepare_state(p,c,g,binding=r.binding,now=NOW); d=m.evaluate_prepared(r,ps,None,current_policy_fingerprint=ps.policy_fingerprint,current_registry_fingerprint=ps.registry_fingerprint,prepared_integrity_validated=False,now=NOW); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc32(t):
    r,p,c,g=base(); r=replace(r,candidate_change_ids=('CHG-APPROVAL',)); ap=replace(m.default_approval(NOW),binding='BAD'); d=ev(req=r,approval=ap); t.assertEqual(d.decision,m.Decision.HUMAN_APPROVAL); no_authority(t,d)

SCENARIOS=[globals()[f'sc{i:02d}'] for i in range(1,33)]
class TestMinimalChange(unittest.TestCase): pass
for rep in range(5):
    for idx,fn in enumerate(SCENARIOS,1):
        def make(f=fn):
            def test(self): f(self)
            return test
        setattr(TestMinimalChange,f'test_{rep*32+idx:03d}',make())

if __name__=='__main__': unittest.main(verbosity=2)
