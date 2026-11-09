import unittest
from dataclasses import replace
import noepin_al_114_iterative_stability_monitor as m

class TestAL114(unittest.TestCase): pass

def req_from(vals, *, max_iterations=20, stable=0.02, cusum=2.0):
    q=m.default_request(); b=q.binding; e=q.state_epoch
    samples=tuple(m.IterationSample(i,float(v),float(v)*0.5,f'S{i}',f'A{i}','V1',f'FP{i}',b,e) for i,v in enumerate(vals))
    p=replace(q.policy,max_iterations=max_iterations,stable_delta_threshold=stable,cusum_threshold=cusum)
    return replace(q,samples=samples,policy=p)

def scenario(k,r):
    q=m.default_request(); b=q.binding; e=q.state_epoch
    if k==0:
        z=m.evaluate(q); return z.decision==m.Decision.ALLOW and z.stability==m.StabilityClass.CONVERGING and z.next_action==m.NextAction.CONTINUE_CANDIDATE and z.next_gate_candidate
    if k==1:
        z=m.evaluate(req_from((1,2,3,4,5,6,8,10))); return z.decision==m.Decision.HOLD and z.stability==m.StabilityClass.DIVERGING and z.stop_hint and z.replan_hint
    if k==2:
        z=m.evaluate(req_from((5,7,5,7,5,7,5,7))); return z.decision==m.Decision.HOLD and z.stability==m.StabilityClass.OSCILLATING and z.replan_hint
    if k==3:
        z=m.evaluate(req_from((5,5.005,5.004,5.006,5.005,5.004),stable=0.01)); return z.decision==m.Decision.ALLOW and z.stability==m.StabilityClass.STABLE and z.next_action==m.NextAction.MONITOR_CONTINUE_CANDIDATE
    if k==4:
        z=m.evaluate(req_from((5,5.005,5.004,5.006,5.005),max_iterations=5,stable=0.01)); return z.decision==m.Decision.HOLD and z.stability==m.StabilityClass.STABLE and z.stop_hint and not z.stop_executed
    if k==5:
        z=m.evaluate(req_from((4,3,2))); return z.decision==m.Decision.HOLD and z.escalation==m.Escalation.INSUFFICIENT_EVIDENCE
    if k==6:
        s=q.samples[0]; qq=replace(q,samples=(s,replace(q.samples[1],step=s.step),)+q.samples[2:]); z=m.evaluate(qq); return z.decision==m.Decision.HOLD and 'DUPLICATE_SAMPLE_STEP' in z.reasons
    if k==7:
        s=replace(q.samples[0],goal_distance=-1.0); z=m.evaluate(replace(q,samples=(s,)+q.samples[1:])); return z.decision==m.Decision.HOLD and 'SAMPLE_METRIC_INVALID' in z.reasons
    if k==8:
        s=replace(q.samples[0],binding='BAD'); z=m.evaluate(replace(q,samples=(s,)+q.samples[1:])); return z.decision==m.Decision.HOLD and 'SAMPLE_BINDING_INVALID' in z.reasons
    if k==9:
        s=replace(q.samples[0],action_id=''); z=m.evaluate(replace(q,samples=(s,)+q.samples[1:])); return z.decision==m.Decision.HOLD and 'SAMPLE_IDENTITY_INVALID' in z.reasons
    if k==10:
        z=m.evaluate(q); neg=(z.stop_hint_promoted_to_stop_execution,z.replan_hint_promoted_to_permission,z.permission_granted,z.approval_executed,z.authority_granted,z.stop_executed,z.action_executed,z.plan_committed,z.publish_executed,z.external_write_performed,z.world_truth_proven,z.domain_authority_promoted,z.safety_proven,z.action_success); return not any(neg)
    if k==11:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.validate_prepared_integrity(st)
    if k==12:
        st=m.prepare_state(q,binding=b,state_epoch=e); ok=m.validate_prepared_integrity(st); z=m.evaluate_prepared(st,integrity_validated=ok,current_context_fingerprint=st.context_fingerprint,current_history_fingerprint=st.history_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_analysis_fingerprint=st.analysis_fingerprint); return z==m.evaluate(q)
    if k==13:
        st=m.prepare_state(q,binding=b,state_epoch=e); z=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_history_fingerprint=st.history_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_analysis_fingerprint=st.analysis_fingerprint); return z.decision==m.Decision.HOLD
    if k==14:
        st=m.prepare_state(q,binding=b,state_epoch=e); s=replace(q.samples[3],goal_distance=q.samples[3].goal_distance+0.1,sample_fingerprint='CHANGED'); q2=replace(q,samples=q.samples[:3]+(s,)+q.samples[4:]); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); return len(d.changed_samples)==1 and d.changed_samples[0].step==3
    if k==15:
        st=m.prepare_state(q,binding=b,state_epoch=e); s=replace(q.samples[3],goal_distance=q.samples[3].goal_distance+0.1,sample_fingerprint='CHANGED'); q2=replace(q,samples=q.samples[:3]+(s,)+q.samples[4:]); st2=m.prepare_state(q2,binding=b,state_epoch=e); sp=m.plan_missing_only(st,st2); return sp.missing_or_changed_record_ids==('SAMPLE:3',) and not sp.full_resend_required
    if k==16:
        q2=replace(q,samples=tuple(reversed(q.samples))); return m.evaluate(q)==m.evaluate(q2)
    if k==17:
        z=m.evaluate(req_from((10,9,8,7,8,9,10,12),cusum=1.5)); return z.stability==m.StabilityClass.DIVERGING and z.positive_cusum>=1.5
    if k==18:
        z=m.evaluate(req_from((10,9.1,8.4,7.6,7.0,6.1,5.7,4.8))); return z.decision==m.Decision.ALLOW and z.stability==m.StabilityClass.CONVERGING
    if k==19:
        z1=m.default_evaluation(); z2=m.default_evaluation(); return m._canon(z1)==m._canon(z2) and m._fp(z1)==m._fp(z2)
    return False

def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL114,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
