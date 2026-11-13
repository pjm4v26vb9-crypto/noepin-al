\
import unittest
from dataclasses import replace
import noepin_al_160_shadow_mode_comparison_engine as m
B='DEFAULT-BINDING'; E='EPOCH-1'
NEG=('shadow_permit_issued','deployment_executed','promotion_executed','rollback_executed','routing_mutated','stable_decision_mutated','shadow_decision_mutated','policy_modified','hard_constraint_modified','guardrail_modified','model_updated','secret_exported','reviewer_invoked','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','publish_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success')
def neg(r): return [getattr(r,x) for x in NEG]
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_live_request_fingerprint=st.live_request_fingerprint,current_stable_fingerprint=st.stable_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint)
def scenario(k,v):
 q=m.default_request()
 if k==0:
  r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.verdict==m.ShadowVerdict.CANARY_CANDIDATE and r.canary_candidate and r.next_action==m.NextAction.CONTINUE_CANARY_CANDIDATE and not any(neg(r))
 if k==1:
  s=replace(q.stable,decision=m.Decision.ALLOW,reason_code='OK',risk_score=.2); sh=replace(q.shadow,decision=m.Decision.ALLOW,reason_code='OK',risk_score=.2); r=m.evaluate(replace(q,stable=s,shadow=sh)); return r.verdict==m.ShadowVerdict.MATCH_CANDIDATE and r.engine_state==m.EngineState.MATCHED_SHADOW_CANDIDATE
 if k==2:
  s=replace(q.stable,decision=m.Decision.DENY,reason_code='BLOCK',risk_score=.9); sh=replace(q.shadow,decision=m.Decision.ALLOW,reason_code='ALLOW',risk_score=.1); r=m.evaluate(replace(q,stable=s,shadow=sh)); return r.escalation==m.Escalation.CRITICAL_DECISION_DIFF and r.reviewer_required and not r.reviewer_invoked
 if k==3:
  sh=replace(q.shadow,permit_requested=True); r=m.evaluate(replace(q,shadow=sh)); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.SHADOW_PERMIT_VIOLATION and r.permit_rejected and not r.shadow_permit_issued
 if k==4:
  lr=replace(q.live_request,sensitive=True); r=m.evaluate(replace(q,live_request=lr)); return r.escalation==m.Escalation.SECRET_REQUEST and r.secret_containment_candidate and not r.secret_exported
 if k==5:
  o=replace(q.outcome,safe=False); r=m.evaluate(replace(q,outcome=o)); return r.escalation==m.Escalation.UNSAFE_SHADOW_DIFF and r.reviewer_required
 if k==6:
  sh=replace(q.shadow,reason_code='ALT_REASON',decision=q.stable.decision,risk_score=q.stable.risk_score); r=m.evaluate(replace(q,shadow=sh)); return r.decision==m.Decision.HOLD and r.reviewer_required and r.decision_diff.reason_changed
 if k==7:
  bad=replace(q.shadow,binding='BAD'); return m.evaluate(replace(q,shadow=bad)).engine_state==m.EngineState.INVALID
 if k==8:
  bad=replace(q.policy,canary_gain_threshold=1.5); return m.evaluate(replace(q,policy=bad)).engine_state==m.EngineState.INVALID
 if k==9:
  st=m.prepare_state(q,B,E); return prep(st)==st.result
 if k==10:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_live_request_fingerprint=st.live_request_fingerprint,current_stable_fingerprint=st.stable_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==11:
  a=m.prepare_state(q,B,E); b=m.prepare_state(replace(q,outcome=replace(q.outcome,utility_score=.92)),B,E); return m.plan_missing_only(a,b).missing_or_changed_record_ids==('OUTCOME',)
 if k==12:
  a=m.prepare_state(q,B,E); b=m.prepare_state(replace(q,shadow=replace(q.shadow,risk_score=.39)),B,E); return m.plan_missing_only(a,b).missing_or_changed_record_ids==('SHADOW_DECISION',)
 if k==13:
  r=m.default_evaluation(); return 'SHADOW_EVIDENCE_IS_NOT_TRUTH' in r.reasons and 'SHADOW_PERMIT_CANNOT_BE_ISSUED' in r.reasons and not r.permission_granted and not r.action_executed
 if k==14:
  p=replace(q.policy,prohibit_shadow_permit=False); sh=replace(q.shadow,permit_requested=True,permit_issued=True); r=m.evaluate(replace(q,policy=p,shadow=sh)); return not r.shadow_permit_issued and r.canary_candidate
 if k==15:
  p=replace(q.policy,prohibit_secret_export=False); lr=replace(q.live_request,sensitive=True); r=m.evaluate(replace(q,policy=p,live_request=lr)); return r.canary_candidate and not r.secret_exported
 if k==16:
  o=replace(q.outcome,observed=False); r=m.evaluate(replace(q,outcome=o)); return r.decision==m.Decision.HOLD and r.reviewer_required
 if k==17:
  sh=replace(q.shadow,risk_score=.9); r=m.evaluate(replace(q,shadow=sh)); return r.decision==m.Decision.HOLD and not r.canary_candidate
 if k==18:
  r=m.default_evaluation(); return r.comparison_id=='CMP-160-A' and r.potential_gain>0 and r.decision_diff.stable_decision=='HOLD' and r.decision_diff.shadow_decision=='ALLOW'
 if k==19:
  r=m.default_evaluation(); return r.next_gate_candidate and r.engine_state==m.EngineState.IMPROVEMENT_CANARY_CANDIDATE and not any(neg(r))
 return False
class TestAL160(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL160,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
