import unittest
from dataclasses import replace
import noepin_al_157_self_evaluation_bias_detector as m
B='DEFAULT-BINDING';E='EPOCH-1'
NEG={'reviewer_invoked','trust_mutated','self_score_mutated','correction_applied','allow_executed','learning_update_committed','model_updated','risk_model_mutated','policy_modified','hard_constraint_modified','guardrail_modified','canary_deployed','shadow_promoted_to_production','fallback_executed','rollback_executed','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','publish_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success'}
def neg(r): return [getattr(r,f.name) for f in m.fields(r) if f.name in NEG]
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_samples_fingerprint=st.samples_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_history_fingerprint=st.history_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint)
def high_samples(q,task=None):
 t=task or q.task_class
 return tuple(replace(s,task_class=t,self_score=min(1.0,s.independent_score+.22)) for s in q.samples)
def low_samples(q):
 return tuple(replace(s,self_score=max(0.0,s.independent_score-.15)) for s in q.samples)
def scenario(k,cycle):
 q=m.default_request()
 if k==0:
  r=m.evaluate(q); return r.decision==m.Decision.ALLOW and abs(r.bias_estimate-.018333)<1e-6 and r.reviewer_requirement==m.ReviewerRequirement.NONE
 if k==1:
  r=m.evaluate(replace(q,samples=high_samples(q))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.OVERCONFIDENCE_BIAS_HIGH and r.reviewer_requirement==m.ReviewerRequirement.INDEPENDENT_REQUIRED and not r.allow_executed
 if k==2:
  h=replace(q.history,historical_bias=-.14); r=m.evaluate(replace(q,samples=low_samples(q),history=h)); return r.decision==m.Decision.ALLOW and r.bias_estimate<0 and r.correction_factor_candidate>1.0
 if k==3:
  other=tuple(replace(s,sample_id='O-'+s.sample_id,task_class='OTHER',self_score=s.independent_score) for s in q.samples)
  r=m.evaluate(replace(q,samples=other+high_samples(q))); return r.sample_count==6 and r.escalation==m.Escalation.OVERCONFIDENCE_BIAS_HIGH
 if k==4:
  r=m.evaluate(replace(q,samples=q.samples[:2])); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.INSUFFICIENT_DATA and r.self_score_weight_candidate<=q.policy.insufficient_data_weight_cap
 if k==5:
  h=replace(q.history,historical_bias=-.20); r=m.evaluate(replace(q,history=h)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.SUDDEN_BIAS_SHIFT and r.trust_adjustment_candidate==-1 and not r.trust_mutated
 if k==6:
  sh=replace(q.shadow,safety_regression=True); r=m.evaluate(replace(q,shadow=sh)); return r.decision==m.Decision.DENY and r.fallback_known_safe_candidate and not r.fallback_executed
 if k==7:
  bad=replace(q.policy,binding='BAD'); return m.evaluate(replace(q,policy=bad)).engine_state==m.EngineState.INVALID
 if k==8:
  bad=replace(q.samples[0],self_score=1.5); return m.evaluate(replace(q,samples=(bad,)+q.samples[1:])).engine_state==m.EngineState.INVALID
 if k==9:
  st=m.prepare_state(q,B,E); return prep(st)==st.result
 if k==10:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_samples_fingerprint=st.samples_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_history_fingerprint=st.history_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==11:
  a=m.prepare_state(q,B,E); b=m.prepare_state(replace(q,shadow=replace(q.shadow,shadow_version='shadow-v3')),B,E); return m.plan_missing_only(a,b).missing_or_changed_record_ids==('SHADOW_CANARY_STATE',)
 if k==12:
  a=m.prepare_state(q,B,E); sm=list(q.samples); sm[0]=replace(sm[0],outcome_score=.5); b=m.prepare_state(replace(q,samples=tuple(sm)),B,E); return m.plan_missing_only(a,b).missing_or_changed_record_ids==('SCORE_SAMPLES',)
 if k==13:
  r=m.default_evaluation(); return 'SELF_SCORE_IS_NOT_TRUTH' in r.reasons and 'REVIEWER_REQUIREMENT_IS_NOT_REVIEWER_INVOCATION' in r.reasons and not r.world_truth_proven and not r.reviewer_invoked
 if k==14:
  sm=tuple(replace(s,self_score=min(1.0,s.independent_score+.08),outcome_score=s.independent_score) for s in q.samples); r=m.evaluate(replace(q,samples=sm)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.OUTCOME_CALIBRATION_GAP
 if k==15:
  sm=tuple(replace(s,self_score=s.independent_score) for s in q.samples); r=m.evaluate(replace(q,samples=sm)); return r.decision==m.Decision.ALLOW and r.bias_estimate==0 and r.engine_state==m.EngineState.CALIBRATED_NORMAL_CANDIDATE
 if k==16:
  sm=tuple(replace(s,independent_score=.60,self_score=.73,outcome_score=.60) for s in q.samples); return m.evaluate(replace(q,samples=sm)).escalation==m.Escalation.OVERCONFIDENCE_BIAS_HIGH
 if k==17:
  h=replace(q.history,task_class='OTHER'); return m.evaluate(replace(q,history=h)).engine_state==m.EngineState.INVALID
 if k==18:
  r=m.default_evaluation(); return r.task_class=='PLAN_REVIEW' and r.sample_count==6 and r.next_action==m.NextAction.CONTINUE_REVIEW_FLOW_CANDIDATE and r.next_gate_candidate
 if k==19:
  r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.escalation==m.Escalation.NONE and not any(neg(r))
 return False
class TestAL157(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL157,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
