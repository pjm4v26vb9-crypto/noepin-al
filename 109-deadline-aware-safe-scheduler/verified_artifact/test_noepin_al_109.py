import unittest
from dataclasses import replace
import noepin_al_109_deadline_aware_safe_scheduler as m

class TestAL109(unittest.TestCase): pass

def base(): return m.default_request(), list(m.default_tasks()), m.default_policy()

def scenario(k,variant):
    q,t,p=base(); b=p.binding; e=p.state_epoch
    if k==0:
        z=m.evaluate(q,tuple(t),p); return z.decision==m.Decision.ALLOW and z.next_action==m.NextAction.SAFE_SCHEDULE_CANDIDATE and z.deadline_feasible and z.required_safety_preserved and z.next_gate_candidate
    if k==1:
        z=m.evaluate(replace(q,deadline=9.5),tuple(t),p); return z.decision==m.Decision.HUMAN_APPROVAL and z.deadline_feasible and z.escalation==m.Escalation.DEADLINE_TIGHT_CANDIDATE
    if k==2:
        z=m.evaluate(replace(q,requested_omissions=('SECURITY-VERIFY',)),tuple(t),p); return z.decision==m.Decision.HOLD and 'MANDATORY_SAFETY_OMISSION_FORBIDDEN' in z.reasons
    if k==3:
        # dependency conflict / cycle
        tt=list(t); tt[1]=replace(tt[1],dependencies=('PUBLISH',)); z=m.evaluate(q,tuple(tt),p); return z.decision==m.Decision.HOLD and 'DEPENDENCY_CYCLE' in z.reasons
    if k==4:
        z=m.evaluate(replace(q,deadline=8.0),tuple(t),p); return z.decision==m.Decision.HUMAN_APPROVAL and not z.deadline_feasible and z.required_safety_preserved and z.final_finish_time==9.0
    if k==5:
        z=m.default_evaluation(); return z.safe_schedule[0].task_id=='SECURITY-VERIFY' and 'CRITICAL_HIGH_RISK_VERIFICATION_PRIORITIZED' in z.reasons
    if k==6:
        tt=list(t); tt[2]=replace(tt[2],hard_constraint_passed=False); z=m.evaluate(q,tuple(tt),p); return z.decision==m.Decision.HOLD and 'HARD_CONSTRAINT:BUILD' in z.reasons
    if k==7:
        tt=list(t); tt[2]=replace(tt[2],policy_allowed=False); z=m.evaluate(q,tuple(tt),p); return z.decision==m.Decision.HOLD and 'POLICY_DENIED:BUILD' in z.reasons
    if k==8:
        tt=list(t); tt[2]=replace(tt[2],risk=4.5); z=m.evaluate(q,tuple(tt),p); return z.decision==m.Decision.HOLD and 'RISK_LIMIT:BUILD' in z.reasons
    if k==9:
        z=m.evaluate(replace(q,requested_omissions=('PREPARE',)),tuple(t),p); return z.decision==m.Decision.HOLD and 'TASK_OMISSION_REQUIRES_REPLAN' in z.reasons
    if k==10:
        st=m.prepare_state(q,tuple(t),p,binding=b,state_epoch=e); return m.validate_prepared_integrity(st)
    if k==11:
        st=m.prepare_state(q,tuple(t),p,binding=b,state_epoch=e); z=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_schedule_fingerprint=st.schedule_fingerprint); return z==st.precomputed_result
    if k==12:
        st=m.prepare_state(q,tuple(t),p,binding=b,state_epoch=e); z=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint,current_schedule_fingerprint=st.schedule_fingerprint); return z.decision==m.Decision.HOLD
    if k==13:
        st=m.prepare_state(q,tuple(t),p,binding=b,state_epoch=e); t2=tuple(replace(x,duration_estimate=x.duration_estimate+.1) if x.task_id=='BUILD' else x for x in t); st2=m.prepare_state(q,t2,p,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2); return len(d.changed_tasks)==1 and sp.missing_or_changed_record_ids==('TASK:BUILD',)
    if k==14:
        z=m.default_evaluation(); neg=(z.schedule_promoted_to_permission,z.permission_granted,z.authority_granted,z.action_executed,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.world_truth_proven,z.domain_authority_promoted,z.safety_proven,z.action_success); return not any(neg)
    if k==15:
        return m.evaluate(q,tuple(t),p)==m.evaluate(q,tuple(reversed(t)),p)
    if k==16:
        # non-safety task is never silently dropped just to meet deadline
        z=m.evaluate(replace(q,deadline=8.5),tuple(t),p); return z.decision==m.Decision.HUMAN_APPROVAL and len(z.safe_schedule)==len(t)
    if k==17:
        st=m.prepare_state(q,tuple(t),p,binding=b,state_epoch=e); z=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint='BAD',current_frontier_fingerprint=st.frontier_fingerprint,current_schedule_fingerprint=st.schedule_fingerprint); return z.decision==m.Decision.HOLD
    if k==18:
        z=m.evaluate(replace(q,risk_class=m.RiskClass.CRITICAL),tuple(t),p); return z.decision==m.Decision.ALLOW and z.required_safety_preserved
    if k==19:
        z=m.default_evaluation(); ids=[x.task_id for x in z.safe_schedule]; return ids.index('SECURITY-VERIFY')<ids.index('BUILD') and ids.index('PREPARE')<ids.index('BUILD') and ids.index('BUILD')<ids.index('TEST')<ids.index('PUBLISH')
    return False

def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL109,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
