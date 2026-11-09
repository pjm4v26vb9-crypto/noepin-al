import unittest
from dataclasses import replace
import noepin_al_108_cost_risk_pareto_planner as m
class TestAL108(unittest.TestCase): pass

def _scenario(k,variant):
    p=m.default_policy(); q=m.default_request(); plans=list(m.default_plans()); b=p.binding; e=p.state_epoch
    if variant%2: q=replace(q,request_id=f'REQ-108-{variant}')
    if k==0:
        z=m.evaluate(q,tuple(plans),p); return z.decision==m.Decision.ALLOW and z.selected_plan=='PLAN-SAFE' and len(z.pareto_frontier)>=3 and not z.permission_granted
    if k==1:
        dominant=m.CandidatePlan('BEST',1,1,.1,.99,1,True,True,True,'V1','BEST',b,e); z=m.evaluate(q,(dominant,replace(dominant,plan_id='WORSE',total_cost=2,plan_fingerprint='W')),p); return z.selected_plan=='BEST' and z.dominated_plans==('WORSE',)
    if k==2:
        z=m.evaluate(q,tuple(plans),replace(p,priority_order=())); return z.decision==m.Decision.HUMAN_APPROVAL and z.selected_plan is None
    if k==3:
        bad=tuple(replace(x,hard_constraint_passed=False) for x in plans); z=m.evaluate(q,bad,p); return z.decision==m.Decision.HOLD
    if k==4:
        a=m.CandidatePlan('A',5,5,.5,.9,.8,True,True,True,'V1','A',b,e); c=replace(a,plan_id='C',plan_fingerprint='C'); pol=replace(p,priority_order=(m.Objective.RISK,)); z=m.evaluate(q,(a,c),pol); return z.decision==m.Decision.HUMAN_APPROVAL and z.reasons==('POLICY_TIE_UNRESOLVED',)
    if k==5:
        pol=replace(p,priority_order=(m.Objective.COST,)); z=m.evaluate(q,tuple(plans),pol); return z.selected_plan=='PLAN-CHEAP'
    if k==6:
        pol=replace(p,priority_order=(m.Objective.TIME,)); z=m.evaluate(q,tuple(plans),pol); return z.selected_plan=='PLAN-FAST'
    if k==7:
        pol=replace(p,priority_order=(m.Objective.REVERSIBILITY,)); z=m.evaluate(q,tuple(plans),pol); return z.selected_plan=='PLAN-SAFE'
    if k==8:
        z=m.evaluate(replace(q,max_total_risk=.3),tuple(plans),p); return z.decision==m.Decision.HOLD
    if k==9:
        z=m.evaluate(q,tuple(plans),replace(p,revoked=True)); return z.decision==m.Decision.HOLD
    if k==10:
        st=m.prepare_state(q,tuple(plans),p,binding=b,state_epoch=e); return m.validate_prepared_integrity(st)
    if k==11:
        st=m.prepare_state(q,tuple(plans),p,binding=b,state_epoch=e); ok=m.validate_prepared_integrity(st); z=m.evaluate_prepared(st,integrity_validated=ok,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_selection_fingerprint=st.selection_fingerprint); return z==m.evaluate(q,tuple(plans),p)
    if k==12:
        st=m.prepare_state(q,tuple(plans),p,binding=b,state_epoch=e); z=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_selection_fingerprint=st.selection_fingerprint); return z.decision==m.Decision.HOLD
    if k==13:
        st=m.prepare_state(q,tuple(plans),p,binding=b,state_epoch=e); p2=tuple(replace(x,total_risk=x.total_risk+.01) if x.plan_id=='PLAN-SAFE' else x for x in plans); st2=m.prepare_state(q,p2,p,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2); return len(d.changed_plans)==1 and sp.missing_or_changed_record_ids==('PLAN:PLAN-SAFE',)
    if k==14:
        z=m.default_evaluation(); neg=(z.plan_promoted_to_permission,z.permission_granted,z.authority_granted,z.action_executed,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.world_truth_proven,z.domain_authority_promoted,z.safety_proven,z.action_success); return not any(neg)
    if k==15:
        return m.evaluate(q,tuple(plans),p)==m.evaluate(q,tuple(reversed(plans)),p)
    if k==16:
        z=m.evaluate(replace(q,min_success_probability=.95),tuple(plans),p); return all(x.plan_id!='PLAN-SAFE' for x in z.pareto_frontier)
    if k==17:
        z=m.evaluate(replace(q,min_reversibility=.9),tuple(plans),p); return all(x.reversibility>=.9 for x in z.pareto_frontier)
    if k==18:
        st=m.prepare_state(q,tuple(plans),p,binding=b,state_epoch=e); z=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint='BAD',current_frontier_fingerprint=st.frontier_fingerprint,current_selection_fingerprint=st.selection_fingerprint); return z.decision==m.Decision.HOLD
    if k==19:
        # unique Pareto winner is selectable even without policy priority because no unresolved trade-off remains
        a=m.CandidatePlan('A',1,1,.1,.99,1,True,True,True,'V1','A',b,e); c=m.CandidatePlan('C',2,2,.2,.9,.8,True,True,True,'V1','C',b,e); z=m.evaluate(q,(a,c),replace(p,priority_order=())); return z.decision==m.Decision.ALLOW and z.selected_plan=='A'
    return False

def _mk(i):
    def t(self): self.assertTrue(_scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL108,f'test_case_{i:03d}',_mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
