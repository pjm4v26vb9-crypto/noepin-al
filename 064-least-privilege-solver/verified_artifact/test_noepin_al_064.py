from __future__ import annotations
import unittest
from dataclasses import replace
import noepin_al_064_least_privilege_solver as m

NOW=1_800_000_000

def base():
    return (m.default_request(NOW),m.default_policy(NOW),m.default_capabilities(NOW),m.default_edges(),m.default_roles(NOW),m.default_actions(),m.default_requirements())

def ev(req=None,p=None,caps=None,edges=None,roles=None,actions=None,reqs=None,approval=None):
    r,p0,c,e,ro,a,q=base()
    return m.evaluate(req or r,p or p0,caps or c,edges or e,roles or ro,actions or a,reqs or q,approval,now=NOW)

def repl(seq,key,val,**kw): return tuple(replace(x,**kw) if getattr(x,key)==val else x for x in seq)

def no_authority(t,d):
    for k in ('permission_granted','token_issued','credential_minted','capability_activated','role_changed','policy_changed','approval_executed','action_executed','world_truth_proven','safety_proven','action_success'):
        t.assertFalse(getattr(d,k),k)

def sc01(t):
    d=ev(); t.assertEqual(d.decision,m.Decision.ALLOW); t.assertEqual(d.minimal_capability_candidate,('CAP_WRITE_SCOPED',)); t.assertEqual(d.excess_capabilities,('CAP_NOTIFY','CAP_READ')); no_authority(t,d)
def sc02(t): no_authority(t,ev())
def sc03(t):
    r,p,c,e,ro,a,q=base(); d=ev(p=replace(p,revoked=True)); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc04(t):
    r,p,c,e,ro,a,q=base(); d=ev(p=replace(p,expires_at=NOW-1)); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc05(t):
    r,p,c,e,ro,a,q=base(); d=ev(req=replace(r,expected_policy_version='BAD')); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc06(t):
    r,p,c,e,ro,a,q=base(); d=ev(req=replace(r,expected_authority_epoch='BAD')); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc07(t):
    r,p,c,e,ro,a,q=base(); d=ev(req=replace(r,created_at=NOW-1000)); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc08(t):
    r,p,c,e,ro,a,q=base(); d=ev(req=replace(r,expires_at=NOW-1)); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc09(t):
    r,p,c,e,ro,a,q=base(); d=ev(req=replace(r,binding='BAD')); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc10(t):
    r,p,c,e,ro,a,q=base(); d=ev(req=replace(r,action_id='MISSING')); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc11(t):
    r,p,c,e,ro,a,q=base(); d=ev(req=replace(r,goal_id='WRONG')); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc12(t):
    r,p,c,e,ro,a,q=base(); d=ev(req=replace(r,role_id='MISSING')); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc13(t):
    r,p,c,e,ro,a,q=base(); ro=repl(ro,'role_id','ROLE_EDITOR',revoked=True); d=ev(roles=ro); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc14(t):
    r,p,c,e,ro,a,q=base(); ro=repl(ro,'role_id','ROLE_VIEWER',parent_role_ids=('ROLE_EDITOR',)); d=ev(roles=ro); t.assertEqual(d.decision,m.Decision.HOLD); t.assertIn('PREPARED_STATE_INVALID',d.reasons[0]); no_authority(t,d)
def sc15(t):
    r,p,c,e,ro,a,q=base(); e=e+(m.CapabilityEdge('EDGE-CYCLE','CAP_READ','CAP_WRITE_SCOPED','LP-BIND',True,False,'LP-POLICY','1','LP-EPOCH'),); d=ev(edges=e); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc16(t):
    r,p,c,e,ro,a,q=base(); d=ev(req=replace(r,requested_capabilities=r.requested_capabilities+('CAP_UNKNOWN',))); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc17(t):
    r,p,c,e,ro,a,q=base(); d=ev(req=replace(r,role_id='ROLE_VIEWER',requested_capabilities=('CAP_WRITE_SCOPED',),expected_role_version='1')); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc18(t):
    r,p,c,e,ro,a,q=base(); q=(m.RequirementClause('REQ-ADMIN','ACT-SAFE',('CAP_ADMIN',),'LP-BIND',True,False),); d=ev(reqs=q); t.assertEqual(d.decision,m.Decision.DENY); t.assertIn('FORBIDDEN_CAPABILITY_REQUIRED',d.reasons); no_authority(t,d)
def sc19(t):
    r,p,c,e,ro,a,q=base(); d=ev(req=replace(r,requested_capabilities=('CAP_READ',))); t.assertEqual(d.decision,m.Decision.HOLD); t.assertIn('CAPABILITY_INSUFFICIENT',d.reasons); no_authority(t,d)
def sc20(t):
    r,p,c,e,ro,a,q=base(); d=ev(p=replace(p,exact_search_limit=2)); t.assertEqual(d.decision,m.Decision.HOLD); t.assertIn('MINIMALITY_UNCONFIRMED_SEARCH_LIMIT',d.reasons); no_authority(t,d)
def sc21(t):
    r,p,c,e,ro,a,q=base(); q=(m.RequirementClause('REQ-ONE','ACT-SAFE',('CAP_NOTIFY','CAP_WRITE_SCOPED'),'LP-BIND',True,False),); rr=replace(r,requested_capabilities=('CAP_NOTIFY','CAP_WRITE_SCOPED')); d=ev(req=rr,reqs=q); t.assertEqual(d.minimal_capability_candidate,('CAP_NOTIFY',)); no_authority(t,d)
def sc22(t):
    r,p,c,e,ro,a,q=base(); rr=replace(r,role_id='ROLE_ADMIN',requested_capabilities=('CAP_READ','CAP_WRITE_SCOPED','CAP_WRITE_GLOBAL','CAP_NOTIFY'),expected_role_version='1'); d=ev(req=rr); t.assertEqual(d.decision,m.Decision.ALLOW); t.assertIn('FORBIDDEN_EXCESS_REMOVED',d.reasons); t.assertNotIn('CAP_WRITE_GLOBAL',d.minimal_capability_candidate); no_authority(t,d)
def sc23(t):
    r,p,c,e,ro,a,q=base(); rr=replace(r,goal_id='GOAL-REVIEW',action_id='ACT-REVIEW',requested_capabilities=('CAP_ELEVATED_REVIEW',)); d=ev(req=rr); t.assertEqual(d.decision,m.Decision.HUMAN_APPROVAL); t.assertTrue(d.approval_required); no_authority(t,d)
def sc24(t):
    r,p,c,e,ro,a,q=base(); rr=replace(r,goal_id='GOAL-REVIEW',action_id='ACT-REVIEW',requested_capabilities=('CAP_ELEVATED_REVIEW',)); d=ev(req=rr,approval=m.default_approval(NOW)); t.assertEqual(d.decision,m.Decision.ALLOW); t.assertTrue(d.next_gate_candidate); no_authority(t,d)
def sc25(t):
    r,p,c,e,ro,a,q=base(); rr=replace(r,goal_id='GOAL-REVIEW',action_id='ACT-REVIEW',requested_capabilities=('CAP_ELEVATED_REVIEW',)); ap=replace(m.default_approval(NOW),role='WRONG'); d=ev(req=rr,approval=ap); t.assertEqual(d.decision,m.Decision.HUMAN_APPROVAL); no_authority(t,d)
def sc26(t):
    r,p,c,e,ro,a,q=base(); rr=replace(r,goal_id='GOAL-REVIEW',action_id='ACT-REVIEW',requested_capabilities=('CAP_ELEVATED_REVIEW',)); ap=replace(m.default_approval(NOW),binding='WRONG'); d=ev(req=rr,approval=ap); t.assertEqual(d.decision,m.Decision.HUMAN_APPROVAL); no_authority(t,d)
def sc27(t):
    r,p,c,e,ro,a,q=base(); q=q+(m.RequirementClause('REQ-BAD','ACT-SAFE',('NOPE',),'LP-BIND',True,False),); d=ev(reqs=q); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc28(t):
    r,p,c,e,ro,a,q=base(); c=repl(c,'capability_id','CAP_WRITE_SCOPED',revoked=True); d=ev(caps=c); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc29(t):
    r,p,c,e,ro,a,q=base(); c=repl(c,'capability_id','CAP_WRITE_SCOPED',expires_at=NOW-1); d=ev(caps=c); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc30(t):
    r,p,c,e,ro,a,q=base(); e=repl(e,'edge_id','EDGE-WRITE-READ',verified=False); d=ev(edges=e); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc31(t):
    r,p,c,e,ro,a,q=base(); ps=m.prepare_state(p,c,e,ro,a,q,binding=r.binding,now=NOW); d=m.evaluate_prepared(r,ps,None,current_policy_fingerprint=ps.policy_fingerprint,current_registry_fingerprint='BAD',prepared_integrity_validated=True,now=NOW); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)
def sc32(t):
    r,p,c,e,ro,a,q=base(); ps=m.prepare_state(p,c,e,ro,a,q,binding=r.binding,now=NOW); d=m.evaluate_prepared(r,ps,None,current_policy_fingerprint=ps.policy_fingerprint,current_registry_fingerprint=ps.registry_fingerprint,prepared_integrity_validated=False,now=NOW); t.assertEqual(d.decision,m.Decision.HOLD); no_authority(t,d)

SCENARIOS=[globals()[f'sc{i:02d}'] for i in range(1,33)]
class TestLeastPrivilege(unittest.TestCase): pass
for rep in range(5):
    for idx,fn in enumerate(SCENARIOS,1):
        def make(f=fn):
            def test(self): f(self)
            return test
        setattr(TestLeastPrivilege,f'test_{rep*32+idx:03d}',make())

if __name__=='__main__': unittest.main(verbosity=2)
