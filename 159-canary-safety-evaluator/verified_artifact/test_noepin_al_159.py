import unittest
from dataclasses import replace
import noepin_al_159_canary_safety_evaluator as m
B='DEFAULT-BINDING'; E='EPOCH-1'
NEG=('deployment_executed','promotion_executed','rollback_executed','traffic_routing_mutated','traffic_fraction_mutated','canary_scope_mutated','policy_modified','hard_constraint_modified','guardrail_modified','model_updated','stable_version_mutated','canary_version_mutated','incident_record_mutated','reviewer_invoked','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','publish_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success')
def neg(r): return [getattr(r,x) for x in NEG]
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_versions_fingerprint=st.versions_fingerprint,current_traffic_fingerprint=st.traffic_fingerprint,current_safety_fingerprint=st.safety_fingerprint,current_utility_fingerprint=st.utility_fingerprint,current_incidents_fingerprint=st.incidents_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint)
def scenario(k,v):
 q=m.default_request()
 if k==0:
  r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.verdict==m.CanaryVerdict.PROMOTE_CANDIDATE and r.staged_promotion_candidate and not any(neg(r))
 if k==1:
  inc=m.Incident('INC-1',True,True,'critical',B,E); r=m.evaluate(replace(q,incidents=(inc,))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.CRITICAL_INCIDENT and r.verdict==m.CanaryVerdict.ROLLBACK_CANDIDATE and not r.rollback_executed
 if k==2:
  s=replace(q.safety_metrics[0],canary_value=0.003); r=m.evaluate(replace(q,safety_metrics=(s,)+q.safety_metrics[1:])); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.SAFETY_METRIC_DEGRADATION and r.fallback_known_safe_candidate
 if k==3:
  t=replace(q.traffic,observed_samples=100); r=m.evaluate(replace(q,traffic=t)); return r.decision==m.Decision.HOLD and r.verdict==m.CanaryVerdict.EXTEND_CANDIDATE
 if k==4:
  t=replace(q.traffic,scope_valid=False); r=m.evaluate(replace(q,traffic=t)); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.SCOPE_LEAK
 if k==5:
  t=replace(q.traffic,fraction=0.20); r=m.evaluate(replace(q,traffic=t)); return r.escalation==m.Escalation.SCOPE_LEAK
 if k==6:
  u=replace(q.utility_metrics[0],canary_value=0.825); r=m.evaluate(replace(q,utility_metrics=(u,))); return r.decision==m.Decision.HOLD and r.verdict==m.CanaryVerdict.HOLD_CANDIDATE
 if k==7:
  bad=replace(q.versions,binding='BAD'); return m.evaluate(replace(q,versions=bad)).engine_state==m.EngineState.INVALID
 if k==8:
  return m.evaluate(replace(q,safety_metrics=())).engine_state==m.EngineState.INVALID
 if k==9:
  st=m.prepare_state(q,B,E); return prep(st)==st.result
 if k==10:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_versions_fingerprint=st.versions_fingerprint,current_traffic_fingerprint=st.traffic_fingerprint,current_safety_fingerprint=st.safety_fingerprint,current_utility_fingerprint=st.utility_fingerprint,current_incidents_fingerprint=st.incidents_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==11:
  a=m.prepare_state(q,B,E); b=m.prepare_state(replace(q,traffic=replace(q.traffic,observed_samples=1300)),B,E); return m.plan_missing_only(a,b).missing_or_changed_record_ids==('TRAFFIC_SLICE',)
 if k==12:
  a=m.prepare_state(q,B,E); inc=m.Incident('I',False,True,'x',B,E); b=m.prepare_state(replace(q,incidents=(inc,)),B,E); return m.plan_missing_only(a,b).missing_or_changed_record_ids==('INCIDENTS',)
 if k==13:
  r=m.default_evaluation(); return 'CANARY_EVIDENCE_IS_NOT_TRUTH' in r.reasons and 'PROMOTE_HOLD_ROLLBACK_ARE_CANDIDATES_NOT_EXECUTION' in r.reasons and not r.permission_granted and not r.action_executed
 if k==14:
  p=replace(q.policy,require_safety_non_degradation=False); s=replace(q.safety_metrics[0],canary_value=0.003); r=m.evaluate(replace(q,policy=p,safety_metrics=(s,)+q.safety_metrics[1:])); return r.decision==m.Decision.ALLOW and r.safety_degradation_count==1
 if k==15:
  t=replace(q.traffic,low_risk_only=False); return m.evaluate(replace(q,traffic=t)).escalation==m.Escalation.SCOPE_LEAK
 if k==16:
  p=replace(q.policy,require_low_risk_scope=False); t=replace(q.traffic,low_risk_only=False); return m.evaluate(replace(q,policy=p,traffic=t)).decision==m.Decision.ALLOW
 if k==17:
  vrs=replace(q.versions,canary_version=q.versions.stable_version); return m.evaluate(replace(q,versions=vrs)).engine_state==m.EngineState.INVALID
 if k==18:
  r=m.default_evaluation(); return r.stable_version=='policy-v2' and r.canary_version=='policy-v3-canary' and r.sample_count==1200 and r.safety_degradation_count==0 and r.critical_incident_count==0
 if k==19:
  r=m.default_evaluation(); return r.next_gate_candidate and r.engine_state==m.EngineState.STAGED_PROMOTION_CANDIDATE and not any(neg(r))
 return False
class TestAL159(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL159,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
