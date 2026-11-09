import unittest
from dataclasses import replace
import noepin_al_102_safe_astar_action_planner as m

class TestAL102(unittest.TestCase): pass

def _base(): return m.default_request(), list(m.default_actions()), m.default_policy()
def _scenario(k,v):
    q,aa,p=_base(); b=p.binding; e=p.state_epoch
    if k==0:
        z=m.default_evaluation(); return z.decision==m.Decision.ALLOW and z.safe_plan==('A-SAFE-1','A-SAFE-2') and z.hard_constraint_exclusions==1
    if k==1:
        # dangerous shortcut never selected
        z=m.evaluate(q,tuple(aa),p); return 'A-DANGER' not in z.safe_plan and z.total_risk<1
    if k==2:
        xs=tuple(replace(a,hard_constraint_passed=False,constraint_reason='BLOCK') for a in aa); z=m.evaluate(q,xs,p); return z.decision==m.Decision.HOLD and not z.safe_plan
    if k==3:
        # same execution+risk weighted total; lower risk route wins deterministically
        xs=(m.ActionEdge('L1','S0','X',1,.1,True,'PASS','V','F1',True,b,e),m.ActionEdge('L2','X','GOAL',1,.1,True,'PASS','V','F2',True,b,e),m.ActionEdge('H1','S0','Y',1.5,.6,True,'PASS','V','F3',True,b,e),m.ActionEdge('H2','Y','GOAL',.2,.4,True,'PASS','V','F4',True,b,e)); z=m.evaluate(q,xs,p); return z.safe_plan==('L1','L2')
    if k==4:
        z=m.evaluate(replace(q,max_total_cost=1.0),tuple(aa),p); return z.decision==m.Decision.HOLD and z.budget_exceeded
    if k==5:
        z=m.evaluate(replace(q,max_total_risk=.1),tuple(aa),p); return z.decision==m.Decision.HOLD and z.budget_exceeded
    if k==6:
        z=m.evaluate(replace(q,start_state='GOAL'),tuple(aa),p); return z.decision==m.Decision.ALLOW and z.safe_plan==()
    if k==7:
        z=m.evaluate(q,tuple(aa),replace(p,revoked=True)); return z.decision==m.Decision.HOLD
    if k==8:
        bad=aa+[replace(aa[0],to_state='Z')]; z=m.evaluate(q,tuple(bad),p); return z.decision==m.Decision.HOLD
    if k==9:
        z=m.evaluate(replace(q,binding='BAD'),tuple(aa),p); return z.decision==m.Decision.HOLD
    if k==10:
        # expansion budget
        z=m.evaluate(q,tuple(aa),replace(p,max_expansions=1)); return z.decision==m.Decision.HOLD and z.budget_exceeded
    if k==11:
        # risk class cap can hold even request budget is large
        z=m.evaluate(replace(q,risk=m.RiskClass.CRITICAL,max_total_risk=100),tuple(aa),replace(p,critical_risk_cap=.1)); return z.decision==m.Decision.HOLD
    if k==12:
        st=m.prepare_state(q,tuple(aa),p,binding=b,state_epoch=e); return m.validate_prepared_integrity(st)
    if k==13:
        st=m.prepare_state(q,tuple(aa),p,binding=b,state_epoch=e); ok=m.validate_prepared_integrity(st); z=m.evaluate_prepared(st,integrity_validated=ok,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_heuristic_fingerprint=st.heuristic_fingerprint); return z==m.evaluate(q,tuple(aa),p)
    if k==14:
        st=m.prepare_state(q,tuple(aa),p,binding=b,state_epoch=e); z=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_heuristic_fingerprint=st.heuristic_fingerprint); return z.decision==m.Decision.HOLD
    if k==15:
        st=m.prepare_state(q,tuple(aa),p,binding=b,state_epoch=e); aa2=tuple(replace(a,risk_cost=.3) if a.action_id=='A-SAFE-1' else a for a in aa); st2=m.prepare_state(q,aa2,p,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2); return len(d.changed_actions)==1 and d.changed_actions[0].action_id=='A-SAFE-1' and sp.missing_or_changed_action_ids==('A-SAFE-1',)
    if k==16:
        z=m.default_evaluation(); neg=(z.safe_plan_promoted_to_permission,z.permission_granted,z.action_executed,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.world_truth_proven,z.domain_authority_promoted,z.safety_proven,z.action_success); return not any(neg)
    if k==17:
        # no path if graph disconnected
        xs=tuple(a for a in aa if a.action_id!='A-SAFE-2'); z=m.evaluate(q,xs,p); return z.decision==m.Decision.HOLD and not z.safe_plan
    if k==18:
        # deterministic action ordering
        z1=m.evaluate(q,tuple(aa),p); z2=m.evaluate(q,tuple(reversed(aa)),p); return z1==z2
    if k==19:
        # large linear graph remains safe
        xs=[]
        for i in range(250): xs.append(m.ActionEdge(f'G{i:03d}',f'N{i}',f'N{i+1}',.01,.001,True,'PASS','V',f'F{i}',True,b,e))
        q2=replace(q,start_state='N0',goal_state='N250',max_total_cost=10,max_total_risk=10)
        z=m.evaluate(q2,tuple(xs),replace(p,max_expansions=1000)); return z.decision==m.Decision.ALLOW and len(z.safe_plan)==250
    return False

def _mk(i):
    def t(self): self.assertTrue(_scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL102,f'test_case_{i:03d}',_mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
