import unittest
from dataclasses import replace
import noepin_al_156_feedback_reliability_filter as m
B='DEFAULT-BINDING';E='EPOCH-1'
NEG={'learning_update_committed','feedback_written_to_training','online_learning_committed','model_updated','risk_model_mutated','policy_modified','hard_constraint_modified','guardrail_modified','source_authority_granted','source_reliability_promoted_to_truth','outcome_evidence_promoted_to_action_success','canary_deployed','shadow_promoted_to_production','fallback_executed','rollback_executed','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','publish_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success'}
def neg(r): return [getattr(r,f.name) for f in m.fields(r) if f.name in NEG]
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_feedback_fingerprint=st.feedback_fingerprint,current_source_fingerprint=st.source_fingerprint,current_evidence_fingerprint=st.evidence_fingerprint,current_context_fingerprint=st.context_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint)
def scenario(k,cycle):
 q=m.default_request()
 if k==0:
  r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.accepted_weight>.8 and r.evidence_match
 if k==1:
  bad=replace(q.source,source_valid=False); r=m.evaluate(replace(q,source=bad)); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.UNTRUSTED_SOURCE and r.rejected_feedback
 if k==2:
  f=replace(q.feedback,self_feedback=True); ev=replace(q.evidence,independent_observed=False,supports_feedback=False,evidence_strength=.2); r=m.evaluate(replace(q,feedback=f,evidence=ev)); return r.decision==m.Decision.HOLD and r.accepted_weight<=.25 and r.escalation==m.Escalation.SELF_FEEDBACK_ONLY
 if k==3:
  ev=replace(q.evidence,supports_feedback=False,evidence_strength=.9); r=m.evaluate(replace(q,evidence=ev)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.CONFLICT_HIGH and r.accepted_weight<.4
 if k==4:
  cx=replace(q.context,delay_seconds=7200); r=m.evaluate(replace(q,context=cx)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.DELAY_HIGH
 if k==5:
  f=replace(q.feedback,proposes_policy_weakening=True); ev=replace(q.evidence,evidence_strength=.5); r=m.evaluate(replace(q,feedback=f,evidence=ev)); return r.decision==m.Decision.HOLD and r.accepted_weight==0 and r.escalation==m.Escalation.INSUFFICIENT_POLICY_EVIDENCE
 if k==6:
  f=replace(q.feedback,proposes_policy_weakening=True); ev=replace(q.evidence,evidence_strength=.95); r=m.evaluate(replace(q,feedback=f,evidence=ev)); return r.decision==m.Decision.ALLOW and r.next_gate_candidate and not r.policy_modified
 if k==7:
  sh=replace(q.shadow,safety_regression=True); r=m.evaluate(replace(q,shadow=sh)); return r.decision==m.Decision.DENY and r.fallback_known_safe_candidate and not r.fallback_executed
 if k==8:
  bad=replace(q.source,binding='BAD'); return m.evaluate(replace(q,source=bad)).engine_state==m.EngineState.INVALID
 if k==9:
  bad=replace(q.context,minimum_accept_weight=1.2); return m.evaluate(replace(q,context=bad)).engine_state==m.EngineState.INVALID
 if k==10:
  st=m.prepare_state(q,B,E); return prep(st)==st.result
 if k==11:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_feedback_fingerprint=st.feedback_fingerprint,current_source_fingerprint=st.source_fingerprint,current_evidence_fingerprint=st.evidence_fingerprint,current_context_fingerprint=st.context_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==12:
  a=m.prepare_state(q,B,E); b=m.prepare_state(replace(q,shadow=replace(q.shadow,shadow_version='shadow-v3')),B,E); return m.plan_missing_only(a,b).missing_or_changed_record_ids==('SHADOW_CANARY_STATE',)
 if k==13:
  a=m.prepare_state(q,B,E); b=m.prepare_state(replace(q,evidence=replace(q.evidence,corroboration_ids=('OBS-C',))),B,E); return m.plan_missing_only(a,b).missing_or_changed_record_ids==('OUTCOME_EVIDENCE',)
 if k==14:
  r=m.default_evaluation(); return 'FEEDBACK_EVIDENCE_IS_NOT_TRUTH' in r.reasons and 'ACCEPTED_WEIGHT_IS_NOT_LEARNING_UPDATE' in r.reasons and not r.world_truth_proven and not r.learning_update_committed
 if k==15:
  s=replace(q.source,historical_reliability=.1); r=m.evaluate(replace(q,source=s)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.LOW_RELIABILITY
 if k==16:
  cx=replace(q.context,conflict_score=.9); r=m.evaluate(replace(q,context=cx)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.CONFLICT_HIGH
 if k==17:
  s=replace(q.source,identity_verified=False); return m.evaluate(replace(q,source=s)).decision==m.Decision.DENY
 if k==18:
  r=m.default_evaluation(); return r.feedback_id=='FB-156-A' and r.engine_state==m.EngineState.ACCEPTED_FEEDBACK_CANDIDATE and r.next_action==m.NextAction.CONTINUE_LEARNING_CANDIDATE
 if k==19:
  r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.escalation==m.Escalation.NONE and r.next_gate_candidate and not any(neg(r))
 return False
class TestAL156(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL156,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
