import unittest
from dataclasses import replace
import noepin_al_152_guardrailed_online_threshold_tuner as m
B='DEFAULT-BINDING'; E='EPOCH-1'
def q0(): return m.default_request()
def neg(r): return [r.threshold_mutated,r.policy_modified,r.guardrail_modified,r.canary_deployed,r.shadow_promoted_to_production,r.rollback_executed,r.model_updated,r.online_learning_committed,r.tool_invoked,r.file_write_executed,r.network_send_executed,r.dcsr_reconstruction_created_fact,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success]
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_outcome_fingerprint=st.outcome_fingerprint,current_threshold_fingerprint=st.threshold_fingerprint,current_cost_fingerprint=st.cost_fingerprint,current_guardrail_fingerprint=st.guardrail_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_outcome_result_fingerprint=st.outcome_result_fingerprint)
def scenario(k,j):
    q=q0()
    if k==0:
        r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.engine_state==m.EngineState.CANARY_PROPOSAL_CANDIDATE and r.proposed_threshold>r.current_threshold and r.expected_gain>0 and r.canary_candidate and r.next_gate_candidate and not any(neg(r))
    if k==1:
        g=replace(q.guardrails,min_samples=99); r=m.evaluate(replace(q,guardrails=g)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.DATA_INSUFFICIENT and r.proposed_threshold==r.current_threshold
    if k==2:
        s=replace(q.shadow,distribution_shift=.9); r=m.evaluate(replace(q,shadow=s)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.DISTRIBUTION_SHIFT
    if k==3:
        s=replace(q.shadow,evaluation_passed=False); r=m.evaluate(replace(q,shadow=s)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.SHADOW_FAILED
    if k==4:
        g=replace(q.guardrails,policy_verified=False); r=m.evaluate(replace(q,guardrails=g)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.POLICY_UNVERIFIED
    if k==5:
        g=replace(q.guardrails,min_expected_gain=999); r=m.evaluate(replace(q,guardrails=g)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.NO_GAIN
    if k==6:
        t=replace(q.threshold,current=.8); r=m.evaluate(replace(q,threshold=t)); return r.engine_state==m.EngineState.INVALID
    if k==7:
        o=replace(q.outcomes[0],binding='BAD'); r=m.evaluate(replace(q,outcomes=(o,)+q.outcomes[1:])); return r.engine_state==m.EngineState.INVALID
    if k==8:
        c=replace(q.costs,false_allow_cost=-1); r=m.evaluate(replace(q,costs=c)); return r.engine_state==m.EngineState.INVALID
    if k==9:
        st=m.prepare_state(q,B,E); return prep(st)==st.result
    if k==10:
        st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_outcome_fingerprint=st.outcome_fingerprint,current_threshold_fingerprint=st.threshold_fingerprint,current_cost_fingerprint=st.cost_fingerprint,current_guardrail_fingerprint=st.guardrail_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_outcome_result_fingerprint=st.outcome_result_fingerprint); return r.engine_state==m.EngineState.INVALID
    if k==11:
        st=m.prepare_state(q,B,E); q2=replace(q,shadow=replace(q.shadow,distribution_shift=.1)); st2=m.prepare_state(q2,B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('SHADOW_CANARY_STATE',)
    if k==12:
        st=m.prepare_state(q,B,E); q2=replace(q,threshold=replace(q.threshold,current=.55)); st2=m.prepare_state(q2,B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('CURRENT_THRESHOLDS',)
    if k==13:
        st=m.prepare_state(q,B,E); q2=replace(q,outcomes=q.outcomes+(m.Outcome('OX',.1,False,False,1,B,E),)); st2=m.prepare_state(q2,B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('OUTCOME_STREAM',)
    if k==14:
        r=m.default_evaluation(); return r.bound_check and r.fallback_threshold==r.current_threshold and not any(neg(r))
    if k==15:
        r=m.evaluate(q); return r.proposed_critical_false_allow<=r.current_critical_false_allow
    if k==16:
        return 'SHADOW_CANARY_STATE' in m.plan_missing_only(m.prepare_state(q,B,E),m.prepare_state(replace(q,shadow=replace(q.shadow,shadow_version='s3')),B,E)).missing_or_changed_record_ids
    if k==17:
        r=m.evaluate(q); return 'SHADOW_CANARY_HAVE_NO_PRODUCTION_AUTHORITY' in r.reasons
    if k==18:
        r=m.evaluate(q); return r.current_threshold==q.threshold.current and q.threshold.current==.5
    if k==19:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.next_action==m.NextAction.CONTINUE_CANARY_CANDIDATE and r.escalation==m.Escalation.NONE and r.engine_state==m.EngineState.CANARY_PROPOSAL_CANDIDATE and r.next_gate_candidate and not any(neg(r))
    return False
class TestAL152(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL152,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
