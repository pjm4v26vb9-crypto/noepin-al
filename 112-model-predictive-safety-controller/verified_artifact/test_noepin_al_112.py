import unittest
from dataclasses import replace
import noepin_al_112_model_predictive_safety_controller as m

class TestAL112(unittest.TestCase): pass

def base(): return m.default_request()
def run_prepared(st,ok=True,**changes):
    args=dict(integrity_validated=ok,current_context_fingerprint=st.context_fingerprint,current_dynamics_fingerprint=st.dynamics_fingerprint,current_constraint_fingerprint=st.constraint_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_frontier_fingerprint=st.frontier_fingerprint); args.update(changes); return m.evaluate_prepared(st,**args)

def scenario(k,variant):
    q=base(); b=q.binding; e=q.state_epoch
    if k==0:
        z=m.evaluate(q); neg=(z.action_promoted_to_permission,z.permission_granted,z.approval_executed,z.authority_granted,z.action_executed,z.plan_committed,z.publish_executed,z.external_write_performed,z.world_truth_proven,z.domain_authority_promoted,z.safety_proven,z.action_success); return z.decision==m.Decision.ALLOW and z.next_action==m.NextAction.SAFE_ACTION_CANDIDATE and z.selected_action_candidate=='SAFE_ADJUST' and z.safe_trajectory_found and z.hard_constraints_preserved and z.constraint_margin>=q.minimum_constraint_margin and not any(neg)
    if k==1:
        z=m.evaluate(replace(q,actions=())); return z.decision==m.Decision.HOLD and 'ACTIONS_MISSING' in z.reasons
    if k==2:
        z=m.evaluate(replace(q,actions=q.actions+(q.actions[0],))); return z.decision==m.Decision.HOLD and 'DUPLICATE_ACTION_ID' in z.reasons
    if k==3:
        z=m.evaluate(replace(q,current_state=q.current_state+(q.current_state[0],))); return z.decision==m.Decision.HOLD and 'CURRENT_STATE_INVALID' in z.reasons
    if k==4:
        z=m.evaluate(replace(q,constraints=())); return z.decision==m.Decision.HOLD and 'CONSTRAINTS_MISSING' in z.reasons
    if k==5:
        a=replace(q.actions[0],deltas=(('load',0.0),('reserve',0.0),('temperature',1000.0)),effect_fingerprint='BADSAFE'); z=m.evaluate(replace(q,actions=(a,))); return z.decision==m.Decision.HOLD and z.escalation==m.Escalation.NO_SAFE_TRAJECTORY and not z.action_executed
    if k==6:
        a=replace(q.actions[0],model_uncertainty=2.0,effect_fingerprint='UNC2'); z=m.evaluate(replace(q,actions=(a,))); return z.decision==m.Decision.HOLD and z.escalation==m.Escalation.MODEL_UNCERTAINTY and z.next_action==m.NextAction.SAFE_MODE_CANDIDATE
    if k==7:
        a=replace(q.actions[0],model_uncertainty=0.4,effect_fingerprint='UNC04'); z=m.evaluate(replace(q,actions=(a,))); return z.safe_trajectory_found and z.horizon_shortened and z.horizon_used==2 and 'HORIZON_SHORTENED_FOR_MODEL_UNCERTAINTY' in z.reasons
    if k==8:
        z=m.evaluate(replace(q,minimum_constraint_margin=25.0)); return z.decision==m.Decision.HUMAN_APPROVAL and z.next_action==m.NextAction.AUTHORITY_REDUCTION_CANDIDATE and z.authority_reduced and not z.authority_granted
    if k==9:
        c=replace(q.constraints[2],maximum=80.0,constraint_fingerprint='C-BOUND'); z=m.evaluate(replace(q,constraints=q.constraints[:2]+(c,),minimum_constraint_margin=1.0)); return z.safe_trajectory_found and z.constraint_margin==0.0 and z.decision==m.Decision.HUMAN_APPROVAL
    if k==10:
        st=m.prepare_state(q,binding=b,state_epoch=e); return m.validate_prepared_integrity(st)
    if k==11:
        st=m.prepare_state(q,binding=b,state_epoch=e); return run_prepared(st)==st.precomputed_result
    if k==12:
        st=m.prepare_state(q,binding=b,state_epoch=e); return run_prepared(st,False).decision==m.Decision.HOLD
    if k==13:
        st=m.prepare_state(q,binding=b,state_epoch=e); return run_prepared(st,current_frontier_fingerprint='BAD').decision==m.Decision.HOLD
    if k==14:
        st=m.prepare_state(q,binding=b,state_epoch=e); a=replace(q.actions[0],risk_cost=0.3,effect_fingerprint='FP-A-SAFE2'); q2=replace(q,actions=(a,)+q.actions[1:]); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); return len(d.changed_actions)==1 and d.changed_actions[0].action_id=='SAFE_ADJUST'
    if k==15:
        st=m.prepare_state(q,binding=b,state_epoch=e); a=replace(q.actions[0],risk_cost=0.3,effect_fingerprint='FP-A-SAFE2'); q2=replace(q,actions=(a,)+q.actions[1:]); st2=m.prepare_state(q2,binding=b,state_epoch=e); sp=m.plan_missing_only(st,st2); return sp.missing_or_changed_record_ids==('ACTION:SAFE_ADJUST',) and not sp.full_resend_required
    if k==16:
        q2=replace(q,current_state=tuple(reversed(q.current_state)),actions=tuple(reversed(q.actions)),goals=tuple(reversed(q.goals)),constraints=tuple(reversed(q.constraints))); return m.evaluate(q)==m.evaluate(q2)
    if k==17:
        a=replace(q.actions[0],binding='BAD'); z=m.evaluate(replace(q,actions=(a,)+q.actions[1:])); return z.decision==m.Decision.HOLD and 'ACTION_INVALID' in z.reasons
    if k==18:
        z=m.evaluate(replace(q,horizon=0)); return z.decision==m.Decision.HOLD and 'HORIZON_INVALID' in z.reasons
    if k==19:
        z1=m.default_evaluation(); z2=m.default_evaluation(); return m._canon(z1)==m._canon(z2) and m._fp(z1)==m._fp(z2)
    return False

def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL112,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
