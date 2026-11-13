import unittest
from dataclasses import replace
import noepin_al_155_adversarial_curriculum_tester as m
B='DEFAULT-BINDING';E='EPOCH-1'
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_observations_fingerprint=st.observations_fingerprint,current_coverage_fingerprint=st.coverage_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint)
def neg(r): return [getattr(r,f.name) for f in m.fields(r) if f.name in {'model_executed','attack_dispatched','fuzz_execution_performed','test_generation_executed','release_executed','promotion_executed','release_block_executed','curriculum_advanced','training_updated','model_updated','policy_modified','guardrail_modified','canary_deployed','shadow_promoted_to_production','rollback_executed','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','publish_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success'}]
def mutate_case(q,idx,**kw):
 o=replace(q.observations[idx],**kw); return replace(q,observations=q.observations[:idx]+(o,)+q.observations[idx+1:])
def scenario(k,cycle):
 q=m.default_request()
 if k==0:
  r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.regression_gate_pass_candidate and r.coverage_ratio>=.95
 if k==1:
  r=m.evaluate(mutate_case(q,0,passed=False)); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.REGRESSION_FAILURE
 if k==2:
  q2=mutate_case(q,5,passed=False,critical=True,known_case=False,regression_case=False); r=m.evaluate(q2); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.CRITICAL_NEW_FAILURE
 if k==3:
  q2=replace(q,observations=tuple(o for o in q.observations if o.threat_category!='MEMORY_POISON')); r=m.evaluate(q2); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.COVERAGE_INSUFFICIENT
 if k==4:
  q2=mutate_case(q,4,passed=False,critical=False,regression_case=False); r=m.evaluate(q2); return r.decision==m.Decision.HOLD and 'GOAL_HIJACK' in r.next_curriculum_categories
 if k==5:
  q2=replace(q,baseline_failure_case_ids=('BASE-OLD-FAIL',)); r=m.evaluate(q2); return r.decision==m.Decision.ALLOW and r.escalation==m.Escalation.IMPROVEMENT_CONFIRMED and r.next_action==m.NextAction.ADVANCE_DIFFICULTY_CANDIDATE
 if k==6:
  sh=replace(q.shadow,safety_regression=True); r=m.evaluate(replace(q,shadow=sh)); return r.decision==m.Decision.DENY and r.engine_state==m.EngineState.REGRESSION_REJECT_CANDIDATE
 if k==7:
  bad=replace(q.policy,max_difficulty=0); return m.evaluate(replace(q,policy=bad)).engine_state==m.EngineState.INVALID
 if k==8:
  bad=replace(q.observations[0],binding='BAD'); return m.evaluate(replace(q,observations=(bad,)+q.observations[1:])).engine_state==m.EngineState.INVALID
 if k==9:
  st=m.prepare_state(q,B,E); return prep(st)==st.result
 if k==10:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_observations_fingerprint=st.observations_fingerprint,current_coverage_fingerprint=st.coverage_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==11:
  a=m.prepare_state(q,B,E); b=m.prepare_state(replace(q,shadow=replace(q.shadow,shadow_version='shadow-v3')),B,E); return m.plan_missing_only(a,b).missing_or_changed_record_ids==('SHADOW_CANARY_STATE',)
 if k==12:
  q2=mutate_case(q,2,passed=False); a=m.prepare_state(q,B,E); b=m.prepare_state(q2,B,E); return m.plan_missing_only(a,b).missing_or_changed_record_ids==('ATTACK_OBSERVATIONS',)
 if k==13:
  r=m.evaluate(q); return 'FAILURE_EVIDENCE_IS_NOT_TRUTH' in r.reasons and 'COVERAGE_IS_NOT_SAFETY_PROOF' in r.reasons and not r.world_truth_proven and not r.safety_proven
 if k==14:
  r=m.evaluate(q); return r.next_action==m.NextAction.CONTINUE_RELEASE_GATE_CANDIDATE and not r.release_executed and not r.promotion_executed and not r.policy_modified
 if k==15:
  r=m.evaluate(mutate_case(q,5,passed=False,critical=True,known_case=False,regression_case=False)); return not r.release_block_executed and not r.stop_executed and not r.action_executed
 if k==16:
  r=m.default_evaluation(); return r.next_difficulty_candidate==4 and r.next_gate_candidate
 if k==17:
  bad=replace(q.coverage,min_coverage_ratio=1.2); return m.evaluate(replace(q,coverage=bad)).engine_state==m.EngineState.INVALID
 if k==18:
  dup=replace(q,observations=q.observations+(q.observations[0],)); return m.evaluate(dup).engine_state==m.EngineState.INVALID
 if k==19:
  r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.next_action==m.NextAction.CONTINUE_RELEASE_GATE_CANDIDATE and r.escalation==m.Escalation.NONE and r.engine_state==m.EngineState.REGRESSION_GATE_PASS_CANDIDATE and r.next_gate_candidate and not any(neg(r))
 return False
class TestAL155(unittest.TestCase):pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL155,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
