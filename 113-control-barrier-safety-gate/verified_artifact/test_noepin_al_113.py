import unittest
from dataclasses import replace
import noepin_al_113_control_barrier_safety_gate as m

class TestAL113(unittest.TestCase): pass

def scenario(k,r):
    q=m.default_request(); b=q.binding; e=q.state_epoch
    if k==0:
        z=m.evaluate(q); return z.decision==m.Decision.ALLOW and z.next_action==m.NextAction.SAFE_ACTION_CANDIDATE and z.safe_set_preserved and z.next_gate_candidate
    if k==1:
        z=m.evaluate(replace(q,candidate_action_id='RISKY_STEP')); return z.decision==m.Decision.DENY and z.escalation==m.Escalation.BARRIER_VIOLATION and z.corrected_action_candidate=='SAFE_STEP'
    if k==2:
        a=replace(q.actions[0],deltas=(('resource',-61.0),('privilege',0.0)),dynamics_fingerprint='LOWM'); qq=replace(q,actions=(a,)+q.actions[1:]); z=m.evaluate(qq); return z.decision==m.Decision.HOLD and z.next_action==m.NextAction.AUTHORITY_REDUCTION_CANDIDATE and z.safe_set_preserved
    if k==3:
        a=replace(q.actions[0],model_uncertainty=0.5,dynamics_fingerprint='UNC'); qq=replace(q,actions=(a,)+q.actions[1:]); z=m.evaluate(qq); return z.decision==m.Decision.HOLD and z.escalation==m.Escalation.MODEL_UNCERTAINTY
    if k==4:
        z=m.evaluate(replace(q,barriers=())); return z.decision==m.Decision.HOLD and z.escalation==m.Escalation.UNKNOWN_STATE
    if k==5:
        br=replace(q.barriers[0],field='missing',barrier_fingerprint='MISS'); z=m.evaluate(replace(q,barriers=(br,)+q.barriers[1:])); return z.decision==m.Decision.HOLD and 'BARRIER_STATE_FIELD_UNKNOWN' in z.reasons
    if k==6:
        z=m.evaluate(replace(q,candidate_action_id='UNKNOWN')); return z.decision==m.Decision.HOLD and 'CANDIDATE_ACTION_UNKNOWN' in z.reasons
    if k==7:
        z=m.evaluate(replace(q,candidate_action_id='RISKY_STEP',allow_correction_search=False)); return z.decision==m.Decision.DENY and not z.correction_available and z.corrected_action_candidate is None
    if k==8:
        bad=replace(q.actions[0],binding='BAD'); z=m.evaluate(replace(q,actions=(bad,)+q.actions[1:])); return z.decision==m.Decision.HOLD and 'ACTION_DYNAMICS_INVALID' in z.reasons
    if k==9:
        br=replace(q.barriers[0],minimum=101.0,maximum=100.0,barrier_fingerprint='BAD'); z=m.evaluate(replace(q,barriers=(br,)+q.barriers[1:])); return z.decision==m.Decision.HOLD and 'BARRIER_BOUNDS_INVALID' in z.reasons
    if k==10:
        z=m.evaluate(q); neg=(z.candidate_promoted_to_permission,z.corrected_action_promoted_to_permission,z.permission_granted,z.approval_executed,z.authority_granted,z.action_executed,z.plan_committed,z.publish_executed,z.external_write_performed,z.world_truth_proven,z.domain_authority_promoted,z.safety_proven,z.action_success); return not any(neg)
    if k==11:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.validate_prepared_integrity(st)
    if k==12:
        st=m.prepare_state(q,binding=b,state_epoch=e); ok=m.validate_prepared_integrity(st); z=m.evaluate_prepared(st,integrity_validated=ok,current_context_fingerprint=st.context_fingerprint,current_dynamics_fingerprint=st.dynamics_fingerprint,current_safety_fingerprint=st.safety_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_evaluation_fingerprint=st.evaluation_fingerprint); return z==m.evaluate(q)
    if k==13:
        st=m.prepare_state(q,binding=b,state_epoch=e); z=m.evaluate_prepared(st,integrity_validated=False,current_context_fingerprint=st.context_fingerprint,current_dynamics_fingerprint=st.dynamics_fingerprint,current_safety_fingerprint=st.safety_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_evaluation_fingerprint=st.evaluation_fingerprint); return z.decision==m.Decision.HOLD
    if k==14:
        st=m.prepare_state(q,binding=b,state_epoch=e); a=replace(q.actions[0],correction_cost=0.3,dynamics_fingerprint='FP-A-SAFE2'); q2=replace(q,actions=(a,)+q.actions[1:]); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); return len(d.changed_actions)==1 and d.changed_actions[0].action_id=='SAFE_STEP'
    if k==15:
        st=m.prepare_state(q,binding=b,state_epoch=e); a=replace(q.actions[0],correction_cost=0.3,dynamics_fingerprint='FP-A-SAFE2'); q2=replace(q,actions=(a,)+q.actions[1:]); st2=m.prepare_state(q2,binding=b,state_epoch=e); sp=m.plan_missing_only(st,st2); return sp.missing_or_changed_record_ids==('ACTION:SAFE_STEP',) and not sp.full_resend_required
    if k==16:
        q2=replace(q,current_state=tuple(reversed(q.current_state)),actions=tuple(reversed(q.actions)),barriers=tuple(reversed(q.barriers))); return m.evaluate(q)==m.evaluate(q2)
    if k==17:
        # correction chooses lowest correction cost among safe alternatives
        safe=replace(q.actions[0],correction_cost=1.0,dynamics_fingerprint='SAFE-COST1'); alt=replace(q.actions[2],correction_cost=0.1,dynamics_fingerprint='CHEAP'); qq=replace(q,candidate_action_id='RISKY_STEP',actions=(safe,q.actions[1],alt)); z=m.evaluate(qq); return z.corrected_action_candidate=='CONSERVATIVE_STEP'
    if k==18:
        br=replace(q.barriers[0],minimum_margin=0.0,barrier_fingerprint='B0'); qq=replace(q,barriers=(br,)+q.barriers[1:]); z=m.evaluate(qq); return z.decision==m.Decision.ALLOW
    if k==19:
        z1=m.default_evaluation(); z2=m.default_evaluation(); return m._canon(z1)==m._canon(z2) and m._fp(z1)==m._fp(z2)
    return False

def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL113,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
