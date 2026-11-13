import unittest
from dataclasses import replace
import noepin_al_158_policy_regression_detector as m
B='DEFAULT-BINDING'; E='EPOCH-1'
NEG={'release_executed','release_block_executed','reviewer_invoked','regression_corpus_mutated','expected_decisions_mutated','policy_modified','hard_constraint_modified','guardrail_modified','model_updated','canary_deployed','shadow_promoted_to_production','fallback_executed','rollback_executed','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','publish_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success'}
def neg(r): return [getattr(r,f.name) for f in m.fields(r) if f.name in NEG]
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_corpus_fingerprint=st.corpus_fingerprint,current_versions_fingerprint=st.versions_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint)
def ch(q,idx,**kw):
 xs=list(q.corpus); xs[idx]=replace(xs[idx],**kw); return replace(q,corpus=tuple(xs))
def scenario(k,cycle):
 q=m.default_request()
 if k==0:
  r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.release_gate==m.ReleaseGate.PASS_CANDIDATE and not r.decision_diff and r.next_gate_candidate
 if k==1:
  r=m.evaluate(ch(q,0,new_decision=m.Decision.ALLOW,new_reason='RELAXED')); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.CRITICAL_SAFETY_REGRESSION and r.release_gate==m.ReleaseGate.BLOCK_CANDIDATE and r.fallback_known_safe_candidate and not r.release_block_executed
 if k==2:
  r=m.evaluate(ch(q,2,new_decision=m.Decision.ALLOW,new_reason='NEW_ALLOW')); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.HOLD_TO_ALLOW_REVIEW and r.release_gate==m.ReleaseGate.REVIEW_REQUIRED_CANDIDATE
 if k==3:
  r=m.evaluate(ch(q,3,new_decision=m.Decision.DENY,new_reason='OVERBLOCK')); return r.decision==m.Decision.ALLOW and r.escalation==m.Escalation.USABILITY_REGRESSION and r.usability_regression_count==1 and r.next_gate_candidate
 if k==4:
  r=m.evaluate(ch(q,4,new_reason='SAME_DECISION_DIFFERENT_REASON')); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.REASON_CHANGE_REVIEW and r.reason_change_count==1
 if k==5:
  r=m.evaluate(replace(q,corpus_complete=False)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.CORPUS_INCOMPLETE and not r.next_gate_candidate
 if k==6:
  sh=replace(q.shadow,safety_regression=True); r=m.evaluate(replace(q,shadow=sh)); return r.decision==m.Decision.DENY and r.engine_state==m.EngineState.SAFETY_REGRESSION_FALLBACK_CANDIDATE and r.fallback_version_candidate=='policy-v1' and not r.fallback_executed
 if k==7:
  bad=replace(q.versions,binding='BAD'); return m.evaluate(replace(q,versions=bad)).engine_state==m.EngineState.INVALID
 if k==8:
  bad=replace(q.corpus[0],case_id=q.corpus[1].case_id); return m.evaluate(replace(q,corpus=(bad,)+q.corpus[1:])).engine_state==m.EngineState.INVALID
 if k==9:
  st=m.prepare_state(q,B,E); return prep(st)==st.result
 if k==10:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_corpus_fingerprint=st.corpus_fingerprint,current_versions_fingerprint=st.versions_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==11:
  a=m.prepare_state(q,B,E); b=m.prepare_state(replace(q,versions=replace(q.versions,new_version='policy-v3')),B,E); return m.plan_missing_only(a,b).missing_or_changed_record_ids==('VERSION_PAIR',)
 if k==12:
  a=m.prepare_state(q,B,E); b=m.prepare_state(ch(q,5,new_reason='NEW_REASON'),B,E); return m.plan_missing_only(a,b).missing_or_changed_record_ids==('REGRESSION_CORPUS',)
 if k==13:
  r=m.default_evaluation(); return 'REGRESSION_EVIDENCE_IS_NOT_TRUTH' in r.reasons and 'RELEASE_GATE_IS_CANDIDATE_NOT_RELEASE_OR_BLOCK_EXECUTION' in r.reasons and not r.world_truth_proven and not r.release_executed
 if k==14:
  r=m.evaluate(ch(q,3,expected_decision=m.Decision.HOLD)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.EXPECTED_DECISION_MISMATCH and r.expected_mismatch_count==1
 if k==15:
  p=replace(q.policy,reason_change_requires_review=False); r=m.evaluate(replace(ch(q,4,new_reason='CHANGED'),policy=p)); return r.decision==m.Decision.ALLOW and not r.decision_diff and r.reason_change_count==1
 if k==16:
  r=m.evaluate(replace(q,corpus=())); return r.escalation==m.Escalation.CORPUS_INCOMPLETE
 if k==17:
  v=replace(q.versions,new_version=q.versions.old_version); return m.evaluate(replace(q,versions=v)).engine_state==m.EngineState.INVALID
 if k==18:
  r=m.default_evaluation(); return r.old_version=='policy-v1' and r.new_version=='policy-v2' and r.case_count==6 and r.engine_state==m.EngineState.REGRESSION_FREE_CANDIDATE
 if k==19:
  r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.escalation==m.Escalation.NONE and not any(neg(r))
 return False
class TestAL158(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL158,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
