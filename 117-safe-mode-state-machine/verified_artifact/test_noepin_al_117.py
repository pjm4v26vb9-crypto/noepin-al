import unittest
from dataclasses import replace
import noepin_al_117_safe_mode_state_machine as m

class TestAL117(unittest.TestCase): pass

def scenario(k,j):
    q=m.default_request(); b=q.binding; e=q.state_epoch
    if k==0:
        z=m.evaluate(q); return z.decision==m.Decision.ALLOW and z.safety_mode_candidate==m.SafetyMode.NORMAL and z.next_gate_candidate
    if k==1:
        ev=replace(q.risk_events[0],severity=m.RiskSeverity.HIGH,evidence_fingerprint='HIGH'); z=m.evaluate(replace(q,risk_events=(ev,))); return z.decision==m.Decision.HOLD and z.safety_mode_candidate==m.SafetyMode.RESTRICTED
    if k==2:
        z=m.evaluate(replace(q,trust=0.3)); return z.decision==m.Decision.HOLD and z.safety_mode_candidate==m.SafetyMode.READ_ONLY
    if k==3:
        z=m.evaluate(replace(q,connectivity=m.Connectivity.OFFLINE)); return z.decision==m.Decision.HOLD and z.safety_mode_candidate==m.SafetyMode.OFFLINE
    if k==4:
        ev=replace(q.risk_events[0],severity=m.RiskSeverity.CRITICAL,evidence_fingerprint='CRIT'); z=m.evaluate(replace(q,risk_events=(ev,))); return z.decision==m.Decision.DENY and z.safety_mode_candidate==m.SafetyMode.EMERGENCY_STOP and not z.stop_executed
    if k==5:
        z=m.evaluate(replace(q,operator_signals=(m.OperatorSignal.EMERGENCY_STOP,))); return z.safety_mode_candidate==m.SafetyMode.EMERGENCY_STOP and z.decision==m.Decision.DENY
    if k==6:
        qr=replace(q,current_mode=m.SafetyMode.RESTRICTED,operator_signals=(m.OperatorSignal.RECOVERY_REQUEST,),stable_windows=5,trust=.95,connectivity=m.Connectivity.TRUSTED); z=m.evaluate(qr); return z.decision==m.Decision.HUMAN_APPROVAL and z.safety_mode_candidate==m.SafetyMode.NORMAL and z.recovery_candidate and not z.permission_granted
    if k==7:
        qr=replace(q,current_mode=m.SafetyMode.RESTRICTED,operator_signals=(m.OperatorSignal.RECOVERY_REQUEST,),stable_windows=1,trust=.95); z=m.evaluate(qr); return z.decision==m.Decision.HOLD and z.safety_mode_candidate==m.SafetyMode.RESTRICTED
    if k==8:
        qr=replace(q,current_mode=m.SafetyMode.RESTRICTED,operator_signals=(m.OperatorSignal.RECOVERY_REQUEST,m.OperatorSignal.EMERGENCY_STOP)); z=m.evaluate(qr); return z.safety_mode_candidate==m.SafetyMode.EMERGENCY_STOP and z.decision==m.Decision.DENY
    if k==9:
        z=m.evaluate(replace(q,connectivity=m.Connectivity.UNKNOWN)); return z.decision==m.Decision.HOLD and z.safety_mode_candidate==m.SafetyMode.READ_ONLY
    if k==10:
        z=m.evaluate(q); neg=(z.capability_matrix_promoted_to_permission,z.mode_change_executed,z.permit_issued,z.permission_granted,z.approval_executed,z.authority_granted,z.stop_executed,z.action_executed,z.plan_committed,z.publish_executed,z.external_write_performed,z.world_truth_proven,z.domain_authority_promoted,z.safety_proven,z.action_success); return not any(neg)
    if k==11:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.validate_prepared_integrity(st)
    if k==12:
        st=m.prepare_state(q,binding=b,state_epoch=e); ok=m.validate_prepared_integrity(st); z=m.evaluate_prepared(st,integrity_validated=ok,current_context_fingerprint=st.context_fingerprint,current_event_fingerprint=st.event_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_transition_fingerprint=st.transition_fingerprint); return z==m.evaluate(q)
    if k==13:
        st=m.prepare_state(q,binding=b,state_epoch=e); z=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_event_fingerprint=st.event_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_transition_fingerprint=st.transition_fingerprint); return z.decision==m.Decision.HOLD
    if k==14:
        st=m.prepare_state(q,binding=b,state_epoch=e); ev=replace(q.risk_events[0],severity=m.RiskSeverity.MEDIUM,evidence_fingerprint='CHANGED'); st2=m.prepare_state(replace(q,risk_events=(ev,)),binding=b,state_epoch=e); d=m.make_delta(st,st2); return len(d.changed_events)==1 and d.changed_events[0].event_id=='HEALTH'
    if k==15:
        st=m.prepare_state(q,binding=b,state_epoch=e); ev=replace(q.risk_events[0],severity=m.RiskSeverity.MEDIUM,evidence_fingerprint='CHANGED'); st2=m.prepare_state(replace(q,risk_events=(ev,)),binding=b,state_epoch=e); sp=m.plan_missing_only(st,st2); return sp.missing_or_changed_record_ids==('EVENT:HEALTH',) and not sp.full_resend_required
    if k==16:
        ev2=m.RiskEvent('SECOND',m.RiskSeverity.LOW,True,'SYSTEM','V1','FP2',b,e); q2=replace(q,risk_events=(q.risk_events[0],ev2)); return m.evaluate(q2)==m.evaluate(replace(q2,risk_events=tuple(reversed(q2.risk_events))))
    if k==17:
        ev2=replace(q.risk_events[0],evidence_fingerprint='DUP'); z=m.evaluate(replace(q,risk_events=(q.risk_events[0],ev2))); return z.decision==m.Decision.HOLD and 'DUPLICATE_EVENT_ID' in z.reasons
    if k==18:
        z=m.evaluate(replace(q,trust=None)); return z.decision==m.Decision.HOLD and z.safety_mode_candidate==m.SafetyMode.READ_ONLY
    if k==19:
        z1=m.default_evaluation(); z2=m.default_evaluation(); return m._canon(z1)==m._canon(z2) and m._fp(z1)==m._fp(z2)
    return False

def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL117,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
