import unittest
from dataclasses import replace
import noepin_al_106_local_plan_repair_search as m
class TestAL106(unittest.TestCase): pass

def _base(): return m.default_request(),list(m.default_plan()),m.default_diff(),list(m.default_candidates()),m.default_policy()
def _scenario(k,v):
    q,plan,diff,cands,p=_base(); b=p.binding; e=p.state_epoch
    if k==0:
        z=m.default_evaluation(); return z.decision==m.Decision.ALLOW and z.next_action==m.NextAction.LOCAL_REPAIR_CANDIDATE and z.chosen_candidate=='BUILD-SAFE' and z.affected_range==('BUILD','TEST','PUBLISH')
    if k==1:
        z=m.default_evaluation(); return z.chosen_candidate!='BUILD-RISKY' and any(x[0]=='BUILD-UNKNOWN-GLOBAL' for x in z.rejected_candidates)
    if k==2:
        d=replace(diff,global_constraint_changed=True); z=m.evaluate(q,tuple(plan),d,tuple(cands),p); return z.decision==m.Decision.HOLD and z.full_replan_required and z.next_action==m.NextAction.FULL_REPLAN_CANDIDATE
    if k==3:
        d=replace(diff,global_impact_known=False); z=m.evaluate(q,tuple(plan),d,tuple(cands),p); return z.decision==m.Decision.HOLD and z.full_replan_required
    if k==4:
        z=m.evaluate(replace(q,max_affected_steps=2),tuple(plan),diff,tuple(cands),p); return z.decision==m.Decision.HOLD and z.full_replan_required
    if k==5:
        xs=tuple(replace(c,hard_constraint_passed=False) for c in cands); z=m.evaluate(q,tuple(plan),diff,xs,p); return z.decision==m.Decision.HOLD and z.next_action==m.NextAction.HOLD_NO_ALTERNATIVE
    if k==6:
        xs=tuple(c for c in cands if c.candidate_id=='BUILD-BROKEN'); z=m.evaluate(q,tuple(plan),diff,xs,p); return z.decision==m.Decision.HOLD and any(r[1]=='DOWNSTREAM_POSTCONDITION_INCOMPATIBLE' for r in z.rejected_candidates)
    if k==7:
        good=replace(cands[0],risk=.9,candidate_id='BUILD-REVIEW',candidate_fingerprint='R'); p2=replace(p,human_review_risk_increase=.1); z=m.evaluate(q,tuple(plan),diff,(good,),p2); return z.decision==m.Decision.HUMAN_APPROVAL and z.next_action==m.NextAction.HUMAN_REVIEW_CANDIDATE and not z.permission_granted
    if k==8:
        z=m.evaluate(replace(q,failed_step_id='NOPE'),tuple(plan),diff,tuple(cands),p); return z.decision==m.Decision.HOLD
    if k==9:
        z=m.evaluate(q,tuple(plan),diff,tuple(cands),replace(p,revoked=True)); return z.decision==m.Decision.HOLD
    if k==10:
        st=m.prepare_state(q,tuple(plan),diff,tuple(cands),p,binding=b,state_epoch=e); return m.validate_prepared_integrity(st)
    if k==11:
        st=m.prepare_state(q,tuple(plan),diff,tuple(cands),p,binding=b,state_epoch=e); ok=m.validate_prepared_integrity(st); z=m.evaluate_prepared(st,integrity_validated=ok,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_boundary_fingerprint=st.boundary_fingerprint); return z==m.evaluate(q,tuple(plan),diff,tuple(cands),p)
    if k==12:
        st=m.prepare_state(q,tuple(plan),diff,tuple(cands),p,binding=b,state_epoch=e); z=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_boundary_fingerprint=st.boundary_fingerprint); return z.decision==m.Decision.HOLD
    if k==13:
        st=m.prepare_state(q,tuple(plan),diff,tuple(cands),p,binding=b,state_epoch=e); cs=tuple(replace(c,risk=c.risk+.01) if c.candidate_id=='BUILD-SAFE' else c for c in cands); st2=m.prepare_state(q,tuple(plan),diff,cs,p,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2); return len(d.changed_candidates)==1 and sp.missing_or_changed_record_ids==('CANDIDATE:BUILD-SAFE',)
    if k==14:
        z=m.default_evaluation(); neg=(z.repair_promoted_to_permission,z.permission_granted,z.action_executed,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.world_truth_proven,z.global_constraint_proven,z.domain_authority_promoted,z.safety_proven,z.action_success); return not any(neg)
    if k==15:
        return m.evaluate(q,tuple(plan),diff,tuple(cands),p)==m.evaluate(q,tuple(plan),diff,tuple(reversed(cands)),p)
    if k==16:
        # lower residual risk wins even if cost is higher
        a=replace(cands[0],candidate_id='A',risk=.20,cost=2.0,candidate_fingerprint='A'); b2=replace(cands[0],candidate_id='B',risk=.21,cost=.1,candidate_fingerprint='B'); z=m.evaluate(q,tuple(plan),diff,(b2,a),p); return z.chosen_candidate=='A'
    if k==17:
        # removed prerequisite invalidates local candidate
        d=replace(diff,removed_facts=('source_ready',)); z=m.evaluate(q,tuple(plan),d,tuple(cands),p); return z.decision==m.Decision.HOLD
    if k==18:
        st=m.prepare_state(q,tuple(plan),diff,tuple(cands),p,binding=b,state_epoch=e); z=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint='BAD',current_frontier_fingerprint=st.frontier_fingerprint,current_boundary_fingerprint=st.boundary_fingerprint); return z.decision==m.Decision.HOLD and z.full_replan_required
    if k==19:
        # failed step not global-sensitive, global change but downstream global-sensitive means still full replan
        z=m.evaluate(q,tuple(plan),replace(diff,global_constraint_changed=True),tuple(cands),p); return z.full_replan_required
    return False

def _mk(i):
    def t(self): self.assertTrue(_scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL106,f'test_case_{i:03d}',_mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
