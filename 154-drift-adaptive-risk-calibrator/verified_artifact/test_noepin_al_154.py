import unittest
from dataclasses import replace
import noepin_al_154_drift_adaptive_risk_calibrator as m
B='DEFAULT-BINDING'; E='EPOCH-1'
NEG=['adjusted_risk_committed','risk_model_mutated','calibration_model_mutated','production_threshold_mutated','policy_modified','guardrail_modified','restricted_mode_executed','monitor_policy_mutated','canary_deployed','shadow_promoted_to_production','staged_recovery_executed','rollback_executed','model_updated','online_learning_committed','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','publish_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success']
def neg(r): return [getattr(r,x) for x in NEG]
def shifted(q,delta): return replace(q,stream=tuple(replace(r,features=tuple(x+delta for x in r.features)) for r in q.stream))
def relabel(q,n):
 rows=[]
 for i,r in enumerate(q.stream): rows.append(replace(r,outcome_risky=(i<n),risk_prediction=(.8 if i<n else .2)))
 return replace(q,stream=tuple(rows))
def high_calibration_error(q): return replace(q,stream=tuple(replace(r,risk_prediction=(.05 if r.outcome_risky else .95)) for r in q.stream))
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_stream_fingerprint=st.stream_fingerprint,current_baseline_fingerprint=st.baseline_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint)
def scenario(k,j):
 q=m.default_request()
 if k==0:
  r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.engine_state==m.EngineState.STABLE_RISK_CANDIDATE and not r.recalibration_need and r.next_gate_candidate and not any(neg(r))
 if k==1:
  r=m.evaluate(shifted(q,.08)); return r.decision==m.Decision.ALLOW and r.engine_state==m.EngineState.MONITOR_ENHANCED_CANDIDATE and r.escalation==m.Escalation.MINOR_DRIFT and r.recalibration_need and not r.restricted_mode_candidate
 if k==2:
  r=m.evaluate(shifted(q,.18)); return r.decision==m.Decision.HOLD and r.engine_state==m.EngineState.RESTRICTED_MODE_CANDIDATE and r.escalation==m.Escalation.CRITICAL_DRIFT and r.adjusted_risk>=sum(x.risk_prediction for x in q.stream)/len(q.stream)
 if k==3:
  r=m.evaluate(relabel(q,8)); return r.recalibration_need and r.positive_rate_shift>=.3 and r.engine_state in {m.EngineState.RESTRICTED_MODE_CANDIDATE,m.EngineState.MONITOR_ENHANCED_CANDIDATE}
 if k==4:
  r=m.evaluate(shifted(q,.01)); return r.engine_state==m.EngineState.STABLE_RISK_CANDIDATE and r.drift_score<m.DriftPolicy.__annotations__.get('warn_drift_score',float) if False else r.drift_score<q.policy.warn_drift_score
 if k==5:
  r=m.evaluate(replace(q,stream=q.stream[:3])); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.DATA_INSUFFICIENT and r.adjusted_risk>0
 if k==6:
  r=m.evaluate(replace(q,policy=replace(q.policy,policy_verified=False))); return r.engine_state==m.EngineState.INVALID and r.escalation==m.Escalation.POLICY_UNVERIFIED and not r.next_gate_candidate
 if k==7:
  r=m.evaluate(replace(shifted(q,.18),cause_attribution_available=False)); return r.engine_state==m.EngineState.UNKNOWN_CAUSE_HOLD_CANDIDATE and r.next_action==m.NextAction.RAISE_HOLD_THRESHOLD_CANDIDATE and r.hold_threshold_raise_candidate==q.policy.hold_threshold_raise
 if k==8:
  qq=shifted(q,.18); sh=replace(qq.shadow,recalibration_candidate_available=True,recalibration_validation_passed=True); r=m.evaluate(replace(qq,shadow=sh)); return r.decision==m.Decision.ALLOW and r.engine_state==m.EngineState.STAGED_RECOVERY_CANDIDATE and r.staged_recovery_candidate and r.next_gate_candidate
 if k==9:
  sh=replace(q.shadow,safety_regression=True); r=m.evaluate(replace(q,shadow=sh)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.SAFETY_REGRESSION and r.restricted_mode_candidate
 if k==10:
  r=m.evaluate(high_calibration_error(q)); return r.calibration_error>q.policy.calibration_error_limit and r.engine_state==m.EngineState.RESTRICTED_MODE_CANDIDATE
 if k==11:
  st=m.prepare_state(q,B,E); return prep(st)==st.result
 if k==12:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_stream_fingerprint=st.stream_fingerprint,current_baseline_fingerprint=st.baseline_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==13:
  a=m.prepare_state(q,B,E); b=m.prepare_state(replace(q,shadow=replace(q.shadow,shadow_version='shadow-v3')),B,E); return m.plan_missing_only(a,b).missing_or_changed_record_ids==('SHADOW_CANARY_STATE',)
 if k==14:
  a=m.prepare_state(q,B,E); b=m.prepare_state(shifted(q,.02),B,E); return m.plan_missing_only(a,b).missing_or_changed_record_ids==('FEATURE_OUTCOME_STREAM',)
 if k==15:
  bad=replace(q.baseline,feature_scales=(.1,0,.1)); return m.evaluate(replace(q,baseline=bad)).engine_state==m.EngineState.INVALID
 if k==16:
  bad=replace(q.stream[0],features=(.1,.2)); return m.evaluate(replace(q,stream=(bad,)+q.stream[1:])).engine_state==m.EngineState.INVALID
 if k==17:
  r=m.evaluate(q); return 'DRIFT_SCORE_IS_EVIDENCE_NOT_TRUTH' in r.reasons and not r.world_truth_proven and not r.safety_proven
 if k==18:
  r=m.evaluate(shifted(q,.18)); return r.restricted_mode_candidate and not r.restricted_mode_executed and not r.production_threshold_mutated and not r.policy_modified
 if k==19:
  r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.next_action==m.NextAction.CONTINUE_STABLE_CANDIDATE and r.escalation==m.Escalation.NONE and r.engine_state==m.EngineState.STABLE_RISK_CANDIDATE and r.next_gate_candidate and not any(neg(r))
 return False
class TestAL154(unittest.TestCase):pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL154,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
