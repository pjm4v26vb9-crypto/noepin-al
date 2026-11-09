import unittest
from dataclasses import replace
import noepin_al_115_adaptive_action_rate_limiter as m

class TestAL115(unittest.TestCase): pass

def with_last(q, **kw):
    w=replace(q.windows[-1],**kw)
    return replace(q,windows=q.windows[:-1]+(w,))

def scenario(k,r):
    q=m.default_request(); b=q.binding; e=q.state_epoch
    if k==0:
        z=m.evaluate(q); return z.decision==m.Decision.ALLOW and z.next_gate_candidate and 0<z.allowed_rate<=z.requested_rate and not z.permission_granted
    if k==1:
        ws=list(q.windows)
        for i in range(3): ws[-1-i]=replace(ws[-1-i],critical_error=True,error_rate=0.95)
        z=m.evaluate(replace(q,windows=tuple(ws))); return z.decision==m.Decision.HOLD and z.allowed_rate==0 and z.next_action==m.NextAction.RATE_ZERO_KILL_CANDIDATE and not z.stop_executed
    if k==2:
        z=m.evaluate(with_last(q,risk=0.85)); return z.allowed_rate<=z.requested_rate*0.20+1e-12 and z.escalation==m.Escalation.HIGH_RISK
    if k==3:
        z=m.evaluate(with_last(q,trust=0.20)); return z.allowed_rate<=z.requested_rate*q.policy.low_trust_cap_fraction+1e-12 and z.escalation==m.Escalation.LOW_TRUST
    if k==4:
        z0=m.evaluate(q); z=m.evaluate(with_last(q,system_load=0.95)); return z.allowed_rate<z0.allowed_rate
    if k==5:
        z0=m.evaluate(q); z=m.evaluate(with_last(q,error_rate=0.70)); return z.allowed_rate<z0.allowed_rate
    if k==6:
        z=m.evaluate(replace(with_last(q,error_rate=None),high_risk_action=True)); return z.decision==m.Decision.HOLD and z.allowed_rate<=q.policy.low_monitor_rate and z.next_action==m.NextAction.LOW_RATE_HOLD_CANDIDATE
    if k==7:
        z=m.evaluate(with_last(q,system_load=None)); return z.decision==m.Decision.HOLD and z.escalation==m.Escalation.METRIC_UNAVAILABLE
    if k==8:
        # previous window deliberately harsher; current stable may recover only by one configured step.
        ws=list(q.windows); ws[-2]=replace(ws[-2],risk=0.65,error_rate=0.35,system_load=0.80,trust=0.50); ws[-1]=replace(ws[-1],risk=0.10,error_rate=0.02,system_load=0.30,trust=0.95)
        z=m.evaluate(replace(q,windows=tuple(ws))); return z.allowed_rate<z.effective_cap and z.next_action in (m.NextAction.RECOVERY_RATE_CANDIDATE,m.NextAction.RATE_LIMIT_CANDIDATE)
    if k==9:
        ws=list(q.windows); ws[-2]=replace(ws[-2],risk=0.65,error_rate=0.35,system_load=0.80,trust=0.50); ws[-1]=replace(ws[-1],risk=0.30,error_rate=0.12,system_load=0.62,trust=0.70)
        z=m.evaluate(replace(q,windows=tuple(ws))); return z.allowed_rate<=z.effective_cap and 'RECOVERY_WITHHELD_UNTIL_STABLE' in z.reasons
    if k==10:
        z=m.evaluate(q); neg=(z.rate_candidate_promoted_to_permission,z.kill_candidate_promoted_to_stop_execution,z.permission_granted,z.approval_executed,z.authority_granted,z.stop_executed,z.action_executed,z.plan_committed,z.publish_executed,z.external_write_performed,z.world_truth_proven,z.domain_authority_promoted,z.safety_proven,z.action_success); return not any(neg)
    if k==11:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.validate_prepared_integrity(st)
    if k==12:
        st=m.prepare_state(q,binding=b,state_epoch=e); ok=m.validate_prepared_integrity(st); z=m.evaluate_prepared(st,integrity_validated=ok,current_context_fingerprint=st.context_fingerprint,current_metrics_fingerprint=st.metrics_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_limiter_fingerprint=st.limiter_fingerprint); return z==m.evaluate(q)
    if k==13:
        st=m.prepare_state(q,binding=b,state_epoch=e); z=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_metrics_fingerprint=st.metrics_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_limiter_fingerprint=st.limiter_fingerprint); return z.decision==m.Decision.HOLD
    if k==14:
        st=m.prepare_state(q,binding=b,state_epoch=e); w=replace(q.windows[2],risk=0.19,metric_fingerprint='CHANGED'); q2=replace(q,windows=q.windows[:2]+(w,)+q.windows[3:]); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); return len(d.changed_windows)==1 and d.changed_windows[0].window_id==2
    if k==15:
        st=m.prepare_state(q,binding=b,state_epoch=e); w=replace(q.windows[2],risk=0.19,metric_fingerprint='CHANGED'); q2=replace(q,windows=q.windows[:2]+(w,)+q.windows[3:]); st2=m.prepare_state(q2,binding=b,state_epoch=e); sp=m.plan_missing_only(st,st2); return sp.missing_or_changed_record_ids==('WINDOW:2',) and not sp.full_resend_required
    if k==16:
        return m.evaluate(q)==m.evaluate(replace(q,windows=tuple(reversed(q.windows))))
    if k==17:
        z=m.evaluate(with_last(q,risk=1.2)); return z.decision==m.Decision.HOLD and 'METRIC_RANGE_INVALID' in z.reasons
    if k==18:
        w=q.windows[0]; q2=replace(q,windows=(w,replace(q.windows[1],window_id=w.window_id))+q.windows[2:]); z=m.evaluate(q2); return z.decision==m.Decision.HOLD and 'DUPLICATE_WINDOW_ID' in z.reasons
    if k==19:
        z1=m.default_evaluation(); z2=m.default_evaluation(); return m._canon(z1)==m._canon(z2) and m._fp(z1)==m._fp(z2)
    return False

def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL115,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
