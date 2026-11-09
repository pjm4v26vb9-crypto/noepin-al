import unittest
from dataclasses import replace
import noepin_al_118_rollback_checkpoint_optimizer as m

class TestAL118(unittest.TestCase): pass

def scenario(k,rep):
    q=m.default_request(); b=q.binding; e=q.state_epoch
    if k==0:
        r=m.evaluate(q); neg=(r.checkpoint_promoted_to_permission,r.snapshot_executed,r.rollback_executed,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success)
        return r.decision==m.Decision.ALLOW and 'S3' in r.checkpoint_locations and r.high_risk_checkpoint_coverage_complete and r.next_gate_candidate and not any(neg)
    if k==1:
        plan=tuple(replace(s,failure_probability=.1,reversible=True) for s in q.plan); r=m.evaluate(replace(q,plan=plan)); return r.decision==m.Decision.ALLOW and r.high_risk_checkpoint_coverage_complete
    if k==2:
        plan=list(q.plan); plan[3]=replace(plan[3],failure_probability=.7,reversible=False); r=m.evaluate(replace(q,plan=tuple(plan))); return r.decision==m.Decision.ALLOW and 'S4' in r.checkpoint_locations
    if k==3:
        plan=tuple(replace(s,snapshot_cost=1000,state_full_bytes=100000000,shared_base_bytes=90000000,delta_bytes=5000000) for s in q.plan); r=m.evaluate(replace(q,plan=plan)); return r.decision==m.Decision.ALLOW and len(r.checkpoint_locations)<=3
    if k==4:
        plan=list(q.plan); plan[2]=replace(plan[2],snapshot_possible=False,reversible=False,failure_probability=.8); r=m.evaluate(replace(q,plan=tuple(plan))); return r.decision==m.Decision.HUMAN_APPROVAL and not r.next_gate_candidate
    if k==5:
        plan=[]
        for i in range(40): plan.append(m.PlanStep(f'L{i}',1+(i%3),.03 if i%11 else .4,1,True,i%11!=0,200000,150000,20000,1,b,e))
        r=m.evaluate(replace(q,plan=tuple(plan))); return r.decision==m.Decision.ALLOW and r.high_risk_checkpoint_coverage_complete
    if k==6:
        plan=list(q.plan); plan[1]=replace(plan[1],failure_probability=None); r=m.evaluate(replace(q,plan=tuple(plan))); return r.decision==m.Decision.ALLOW and r.escalation==m.Escalation.UNKNOWN_RISK and 'UNKNOWN_RISK_CONSERVATIVE_ESTIMATE_USED' in r.reasons
    if k==7:
        plan=(q.plan[0],replace(q.plan[0],failure_probability=.2)); return m.evaluate(replace(q,plan=plan)).decision==m.Decision.HOLD
    if k==8:
        plan=list(q.plan); plan[0]=replace(plan[0],failure_probability=1.2); return m.evaluate(replace(q,plan=tuple(plan))).decision==m.Decision.HOLD
    if k==9:
        p=replace(q.policy,max_checkpoint_interval=0); return m.evaluate(replace(q,policy=p)).decision==m.Decision.HOLD
    if k==10:
        st=m.prepare_state(q,binding=b,state_epoch=e); ok=m.validate_prepared_integrity(st); r=m.evaluate_prepared(st,integrity_validated=ok,current_context_fingerprint=st.context_fingerprint,current_plan_fingerprint=st.plan_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_optimization_fingerprint=st.optimization_fingerprint); return r==m.evaluate(q)
    if k==11:
        st=m.prepare_state(q,binding=b,state_epoch=e); r=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_plan_fingerprint=st.plan_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_optimization_fingerprint=st.optimization_fingerprint); return r.decision==m.Decision.HOLD
    if k==12:
        st=m.prepare_state(q,binding=b,state_epoch=e); r=m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint='bad',current_plan_fingerprint=st.plan_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_optimization_fingerprint=st.optimization_fingerprint); return r.decision==m.Decision.HOLD
    if k==13:
        st=m.prepare_state(q,binding=b,state_epoch=e); q2=replace(q,plan=(replace(q.plan[0],step_cost=9),)+q.plan[1:]); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); return len(d.changed_steps)==1 and d.changed_steps[0].step_id=='S1'
    if k==14:
        st=m.prepare_state(q,binding=b,state_epoch=e); q2=replace(q,plan=(replace(q.plan[0],step_cost=9),)+q.plan[1:]); st2=m.prepare_state(q2,binding=b,state_epoch=e); sp=m.plan_missing_only(st,st2); return sp.missing_or_changed_record_ids==('STEP:S1',) and not sp.full_resend_required
    if k==15:
        s=replace(q.plan[2],snapshot_cost=100,state_full_bytes=100000000,shared_base_bytes=1000,delta_bytes=1000); r=m.evaluate(replace(q,plan=q.plan[:2]+(s,)+q.plan[3:])); return any(c.before_step_id=='S3' and c.reconstruction_mode=='DCSR_SHARED_BASE_DELTA' for c in r.checkpoints)
    if k==16:
        s=replace(q.plan[2],snapshot_cost=.01,shared_base_bytes=1000000,delta_bytes=1000000); r=m.evaluate(replace(q,plan=q.plan[:2]+(s,)+q.plan[3:])); return any(c.before_step_id=='S3' and c.reconstruction_mode=='FULL_SNAPSHOT' for c in r.checkpoints)
    if k==17:
        plan=list(q.plan); plan[2]=replace(plan[2],reversible=True,failure_probability=.2); r=m.evaluate(replace(q,plan=tuple(plan))); return r.decision==m.Decision.ALLOW
    if k==18:
        s=replace(q.plan[0],failure_probability=.9,reversible=False,snapshot_possible=False); r=m.evaluate(replace(q,plan=(s,)+q.plan[1:])); return r.decision==m.Decision.ALLOW and r.high_risk_checkpoint_coverage_complete
    if k==19:
        a=m.default_evaluation(); b2=m.default_evaluation(); return m._canon(a)==m._canon(b2) and m._fp(a)==m._fp(b2)
    return False

def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL118,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
