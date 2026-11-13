\
import unittest
from dataclasses import replace
import noepin_al_161_learning_freeze_and_rollback_controller as m
B='DEFAULT-BINDING'; E='EPOCH-1'
NEG=('learning_update_executed','learning_update_committed','freeze_executed','kill_switch_executed','rollback_executed','resume_executed','target_version_restored','model_updated','policy_modified','threshold_modified','trust_modified','hard_constraint_modified','guardrail_modified','deployment_executed','routing_mutated','incident_record_mutated','reviewer_invoked','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','publish_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success')
def neg(r): return [getattr(r,n) for n in NEG]
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_update_fingerprint=st.update_fingerprint,current_safety_fingerprint=st.safety_fingerprint,current_history_fingerprint=st.history_fingerprint,current_rollback_fingerprint=st.rollback_fingerprint,current_resume_fingerprint=st.resume_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint)
def scenario(k,rep):
 q=m.default_request()
 if k==0:
  r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.verdict==m.ControlVerdict.RUN_CANDIDATE and not any(neg(r))
 if k==1:
  s=replace(q.safety,critical_regression=True,safe_state_confirmed=False); r=m.evaluate(replace(q,safety=s)); return r.decision==m.Decision.HOLD and r.rollback_candidate and r.target_version=='model-v7' and not r.rollback_executed
 if k==2:
  s=replace(q.safety,attack_active=True,safe_state_confirmed=False); r=m.evaluate(replace(q,safety=s)); return r.engine_state==m.EngineState.ATTACK_FREEZE_CANDIDATE and r.learning_freeze_candidate and not r.kill_switch_executed
 if k==3:
  s=replace(q.safety,drift_detected=True,safe_state_confirmed=False); r=m.evaluate(replace(q,safety=s)); return r.verdict==m.ControlVerdict.FREEZE_MAINTAIN_CANDIDATE and not r.rollback_executed
 if k==4:
  rb=replace(q.rollback_point,target_available=False); s=replace(q.safety,critical_regression=True,safe_state_confirmed=False); r=m.evaluate(replace(q,rollback_point=rb,safety=s)); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.ROLLBACK_TARGET_UNAVAILABLE and not r.rollback_candidate
 if k==5:
  hist=tuple(replace(v,verified_safe=False) if v.version_id=='model-v7' else v for v in q.version_history); s=replace(q.safety,critical_regression=True,safe_state_confirmed=False); r=m.evaluate(replace(q,version_history=hist,safety=s)); return r.engine_state==m.EngineState.ROLLBACK_TARGET_UNAVAILABLE_CANDIDATE
 if k==6:
  s=replace(q.safety,cause_known=False,safe_state_confirmed=False); r=m.evaluate(replace(q,safety=s)); return r.escalation==m.Escalation.UNKNOWN_CAUSE and r.learning_freeze_candidate
 if k==7:
  u=replace(q.update,verified=False); r=m.evaluate(replace(q,update=u)); return r.decision==m.Decision.HOLD and r.learning_freeze_candidate
 if k==8:
  u=replace(q.update,committed=True); return m.evaluate(replace(q,update=u)).engine_state==m.EngineState.INVALID
 if k==9:
  bad=replace(q.rollback_point,binding='BAD'); return m.evaluate(replace(q,rollback_point=bad)).engine_state==m.EngineState.INVALID
 if k==10:
  st=m.prepare_state(q,B,E); return prep(st)==st.result
 if k==11:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_update_fingerprint=st.update_fingerprint,current_safety_fingerprint=st.safety_fingerprint,current_history_fingerprint=st.history_fingerprint,current_rollback_fingerprint=st.rollback_fingerprint,current_resume_fingerprint=st.resume_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==12:
  a=m.prepare_state(q,B,E); b=m.prepare_state(replace(q,safety=replace(q.safety,drift_detected=True)),B,E); return m.plan_missing_only(a,b).missing_or_changed_record_ids==('SAFETY_SIGNAL',)
 if k==13:
  a=m.prepare_state(q,B,E); b=m.prepare_state(replace(q,rollback_point=replace(q.rollback_point,target_available=False)),B,E); return m.plan_missing_only(a,b).missing_or_changed_record_ids==('ROLLBACK_POINT',)
 if k==14:
  rs=replace(q.resume,independent_review_passed=True,safety_reverified=True,attack_cleared=True,cause_resolved=True); r=m.evaluate(replace(q,resume=rs)); return r.verdict==m.ControlVerdict.RESUME_REVIEW_CANDIDATE and r.resume_review_candidate and not r.resume_executed
 if k==15:
  rs=replace(q.resume,independent_review_passed=True,safety_reverified=False); r=m.evaluate(replace(q,resume=rs)); return r.decision==m.Decision.HOLD and r.resume_review_candidate
 if k==16:
  r=m.default_evaluation(); return 'SAFETY_SIGNAL_IS_EVIDENCE_NOT_TRUTH' in r.reasons and 'KNOWN_SAFE_VERSION_IS_TARGET_CANDIDATE_NOT_ROLLBACK_EXECUTION' in r.reasons and not r.permission_granted
 if k==17:
  rb=replace(q.rollback_point,target_fingerprint='0'*64); s=replace(q.safety,critical_regression=True,safe_state_confirmed=False); r=m.evaluate(replace(q,rollback_point=rb,safety=s)); return r.escalation==m.Escalation.ROLLBACK_TARGET_UNAVAILABLE
 if k==18:
  r=m.default_evaluation(); return r.target_version=='model-v7' and r.fallback_known_safe_candidate and r.next_gate_candidate
 if k==19:
  r=m.default_evaluation(); return r.engine_state==m.EngineState.LEARNING_RUN_CANDIDATE and r.next_action==m.NextAction.CONTINUE_LEARNING_CANDIDATE and not any(neg(r))
 return False
class TestAL161(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL161,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
