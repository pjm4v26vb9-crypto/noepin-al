import unittest
from dataclasses import replace
import noepin_al_116_risk_budget_allocator as m
class TestAL116(unittest.TestCase): pass

def scenario(k,r):
    q=m.default_request(); b=q.binding; e=q.state_epoch
    if k==0:
        z=m.evaluate(q); return z.decision==m.Decision.ALLOW and z.next_gate_candidate and z.allocated_total<=z.allocatable_remaining+1e-9 and not z.permission_granted
    if k==1:
        ss=tuple(replace(s,risk_estimate=0.10,priority=1.0,critical=False) for s in q.subtasks); z=m.evaluate(replace(q,subtasks=ss)); vals=[a.budget_candidate for a in z.allocations]; return z.decision==m.Decision.ALLOW and max(vals)-min(vals)<1e-9
    if k==2:
        ss=list(q.subtasks); ss[0]=replace(ss[0],risk_estimate=0.70,priority=2.0); z=m.evaluate(replace(q,subtasks=tuple(ss))); d={a.subtask_id:a for a in z.allocations}; return d['RESEARCH'].budget_candidate>=d['BUILD'].budget_candidate
    if k==3:
        ss=tuple(replace(s,consumed_risk=0.40) for s in q.subtasks); z=m.evaluate(replace(q,subtasks=ss)); return z.decision==m.Decision.HOLD and z.overrun_alert and z.escalation==m.Escalation.TOTAL_OVERRUN
    if k==4:
        z=m.evaluate(q); d={a.subtask_id:a for a in z.allocations}; return d['PUBLISH-CHECK'].unknown_risk and d['PUBLISH-CHECK'].budget_candidate<=q.total_risk_budget*q.policy.unknown_step_cap_fraction+1e-12
    if k==5:
        ss=list(q.subtasks); ss[1]=replace(ss[1],risk_estimate=0.01,priority=20.0); z=m.evaluate(replace(q,subtasks=tuple(ss))); d={a.subtask_id:a for a in z.allocations}; return d['VERIFY'].budget_candidate<=q.total_risk_budget*q.policy.critical_step_cap_fraction+1e-12
    if k==6:
        ss=list(q.subtasks); ss[0]=replace(ss[0],completed=True,previous_budget=0.20,consumed_risk=0.05); z=m.evaluate(replace(q,subtasks=tuple(ss))); return 0<z.redistribution_pool<=q.total_risk_budget*q.policy.redistribution_cap_fraction+1e-12
    if k==7:
        ss=list(q.subtasks); ss[0]=replace(ss[0],completed=True,previous_budget=0.20,consumed_risk=0.05); p=replace(q.policy,allow_redistribution=False); z=m.evaluate(replace(q,subtasks=tuple(ss),policy=p)); return z.redistribution_pool==0
    if k==8:
        ss=tuple(replace(s,consumed_risk=0.225) for s in q.subtasks); z=m.evaluate(replace(q,subtasks=ss)); return z.decision==m.Decision.HOLD and z.escalation==m.Escalation.INSUFFICIENT_BUDGET and not z.additional_budget_granted
    if k==9:
        ss=tuple(replace(s,completed=True) for s in q.subtasks); z=m.evaluate(replace(q,subtasks=ss)); return z.decision==m.Decision.ALLOW and not z.allocations and z.remaining_budget>=0
    if k==10:
        z=m.evaluate(q); neg=(z.allocation_promoted_to_permission,z.additional_budget_granted,z.permission_granted,z.approval_executed,z.authority_granted,z.stop_executed,z.action_executed,z.plan_committed,z.publish_executed,z.external_write_performed,z.world_truth_proven,z.domain_authority_promoted,z.safety_proven,z.action_success); return not any(neg)
    if k==11:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.validate_prepared_integrity(st)
    if k==12:
        st=m.prepare_state(q,binding=b,state_epoch=e); ok=m.validate_prepared_integrity(st); z=m.evaluate_prepared(st,integrity_validated=ok,current_context_fingerprint=st.context_fingerprint,current_subtask_fingerprint=st.subtask_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_allocation_fingerprint=st.allocation_fingerprint); return z==m.evaluate(q)
    if k==13:
        st=m.prepare_state(q,binding=b,state_epoch=e); z=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_subtask_fingerprint=st.subtask_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_allocation_fingerprint=st.allocation_fingerprint); return z.decision==m.Decision.HOLD
    if k==14:
        st=m.prepare_state(q,binding=b,state_epoch=e); s=replace(q.subtasks[1],risk_estimate=0.13,evidence_fingerprint='CHANGED'); q2=replace(q,subtasks=(q.subtasks[0],s)+q.subtasks[2:]); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); return len(d.changed_subtasks)==1 and d.changed_subtasks[0].subtask_id=='VERIFY'
    if k==15:
        st=m.prepare_state(q,binding=b,state_epoch=e); s=replace(q.subtasks[1],risk_estimate=0.13,evidence_fingerprint='CHANGED'); q2=replace(q,subtasks=(q.subtasks[0],s)+q.subtasks[2:]); st2=m.prepare_state(q2,binding=b,state_epoch=e); sp=m.plan_missing_only(st,st2); return sp.missing_or_changed_record_ids==('SUBTASK:VERIFY',) and not sp.full_resend_required
    if k==16:
        return m.evaluate(q)==m.evaluate(replace(q,subtasks=tuple(reversed(q.subtasks))))
    if k==17:
        ss=list(q.subtasks); ss[0]=replace(ss[0],risk_estimate=1.2); z=m.evaluate(replace(q,subtasks=tuple(ss))); return z.decision==m.Decision.HOLD and 'RISK_ESTIMATE_INVALID' in z.reasons
    if k==18:
        ss=list(q.subtasks); ss[1]=replace(ss[1],subtask_id=ss[0].subtask_id); z=m.evaluate(replace(q,subtasks=tuple(ss))); return z.decision==m.Decision.HOLD and 'DUPLICATE_SUBTASK_ID' in z.reasons
    if k==19:
        z1=m.default_evaluation(); z2=m.default_evaluation(); return m._canon(z1)==m._canon(z2) and m._fp(z1)==m._fp(z2)
    return False

def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL116,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
