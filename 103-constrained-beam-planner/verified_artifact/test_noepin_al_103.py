import unittest
from dataclasses import replace
import noepin_al_103_constrained_beam_planner as m
class TestAL103(unittest.TestCase): pass

def _base(): return m.default_request(), list(m.default_actions()), m.default_policy()
def _scenario(k,v):
    q,aa,p=_base(); b=p.binding; e=p.state_epoch
    if k==0:
        z=m.default_evaluation(); return z.decision==m.Decision.ALLOW and z.top_plans and z.top_plans[0].action_ids==('A-SAFE-1','A-SAFE-2') and ('HARD_CONSTRAINT_VIOLATION',1) in z.pruned_reasons
    if k==1:
        z=m.default_evaluation(); return all('A-DANGER' not in x.action_ids for x in z.top_plans)
    if k==2:
        xs=tuple(replace(a,hard_constraint_passed=False,constraint_reason='BLOCK') for a in aa); z=m.evaluate(q,xs,p); return z.decision==m.Decision.HOLD and z.beam_exhausted and not z.top_plans
    if k==3:
        # Equal rank score/risk: higher reversibility wins.
        xs=(m.BeamAction('RLOW','S0','GOAL',2,.2,.4,True,'PASS','V','F1',True,b,e),m.BeamAction('RHIGH','S0','GOAL',2,.2,.9,True,'PASS','V','F2',True,b,e)); z=m.evaluate(q,xs,p); return z.top_plans[0].action_ids==('RHIGH',)
    if k==4:
        z=m.evaluate(replace(q,beam_width=1),tuple(aa),p); return z.decision==m.Decision.ALLOW and len(z.top_plans)==1
    if k==5:
        z=m.evaluate(replace(q,max_depth=1),tuple(a for a in aa if a.to_state!='GOAL'),p); return z.decision==m.Decision.HOLD and z.depth_limit_reached
    if k==6:
        z=m.evaluate(replace(q,start_state='GOAL'),tuple(aa),p); return z.decision==m.Decision.ALLOW and z.top_plans[0].action_ids==()
    if k==7:
        z=m.evaluate(q,tuple(aa),replace(p,revoked=True)); return z.decision==m.Decision.HOLD
    if k==8:
        bad=aa+[replace(aa[0],to_state='ZZ')]; z=m.evaluate(q,tuple(bad),p); return z.decision==m.Decision.HOLD
    if k==9:
        z=m.evaluate(replace(q,binding='BAD'),tuple(aa),p); return z.decision==m.Decision.HOLD
    if k==10:
        z=m.evaluate(q,tuple(aa),replace(p,max_generated_candidates=1)); return z.decision==m.Decision.HOLD and 'GENERATION_BUDGET_EXCEEDED' in z.reasons
    if k==11:
        z=m.evaluate(replace(q,max_total_risk=.05),tuple(aa),p); return z.decision==m.Decision.HOLD
    if k==12:
        st=m.prepare_state(q,tuple(aa),p,binding=b,state_epoch=e); return m.validate_prepared_integrity(st)
    if k==13:
        st=m.prepare_state(q,tuple(aa),p,binding=b,state_epoch=e); ok=m.validate_prepared_integrity(st); z=m.evaluate_prepared(st,integrity_validated=ok,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_rank_fingerprint=st.rank_fingerprint); return z==m.evaluate(q,tuple(aa),p)
    if k==14:
        st=m.prepare_state(q,tuple(aa),p,binding=b,state_epoch=e); z=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_rank_fingerprint=st.rank_fingerprint); return z.decision==m.Decision.HOLD
    if k==15:
        st=m.prepare_state(q,tuple(aa),p,binding=b,state_epoch=e); aa2=tuple(replace(a,risk_cost=.3) if a.action_id=='A-SAFE-1' else a for a in aa); st2=m.prepare_state(q,aa2,p,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2); return len(d.changed_actions)==1 and d.changed_actions[0].action_id=='A-SAFE-1' and sp.missing_or_changed_action_ids==('A-SAFE-1',)
    if k==16:
        z=m.default_evaluation(); neg=(z.plan_promoted_to_permission,z.permission_granted,z.action_executed,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.world_truth_proven,z.domain_authority_promoted,z.safety_proven,z.action_success); return not any(neg)
    if k==17:
        # deterministic regardless of action input order
        return m.evaluate(q,tuple(aa),p)==m.evaluate(q,tuple(reversed(aa)),p)
    if k==18:
        # High risk plan can become human-review candidate, not approval execution.
        q2=replace(q,risk=m.RiskClass.HIGH,max_total_risk=5); xs=(m.BeamAction('H','S0','GOAL',5,1.2,.9,True,'PASS','V','F',True,b,e),); z=m.evaluate(q2,xs,p); return z.decision==m.Decision.HUMAN_APPROVAL and z.next_action==m.NextAction.HUMAN_REVIEW_CANDIDATE and not z.permission_granted
    if k==19:
        # Larger graph: beam filtering remains bounded and safe.
        xs=[]
        for d in range(12):
            for j in range(16):
                src=f'N{d}_{j}' if d else 'S0'; dst='GOAL' if d==11 else f'N{d+1}_{j}'
                xs.append(m.BeamAction(f'A{d:02d}_{j:02d}',src,dst,1+j/100,.01,j/15 if j else 1,True,'PASS','V',f'F{d}_{j}',True,b,e))
                xs.append(m.BeamAction(f'X{d:02d}_{j:02d}',src,dst,99,9,.1,False,'BLOCK','V',f'X{d}_{j}',True,b,e))
        q2=replace(q,beam_width=8,max_depth=12,max_total_risk=10,min_final_utility=1); z=m.evaluate(q2,tuple(xs),replace(p,max_generated_candidates=10000)); return z.decision==m.Decision.ALLOW and all('X' not in aid for plan in z.top_plans for aid in plan.action_ids)
    return False

def _mk(i):
    def t(self): self.assertTrue(_scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL103,f'test_case_{i:03d}',_mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
