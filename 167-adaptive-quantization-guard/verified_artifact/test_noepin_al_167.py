import unittest, math
from dataclasses import replace
import noepin_al_167_adaptive_quantization_guard as m
B='DEFAULT-BINDING'; E='EPOCH-1'
NEG=('source_values_mutated','quantization_committed','reconstructed_values_committed','lossless_fallback_executed','original_deleted','candidate_state_written','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','publish_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success')
def neg(r): return [getattr(r,n) for n in NEG]
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_values_fingerprint=st.values_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint)
def scenario(k,rep):
 q=m.default_request()
 if k==0:
  r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.engine_state==m.EngineState.QUANTIZATION_CANDIDATE and r.next_gate_candidate and r.selected_bit_width is not None and not any(neg(r))
 if k==1:
  r=m.evaluate(q); acc=[x.bit_width for x in r.candidate_evaluations if x.accepted]; return r.selected_bit_width==min(acc) and r.lightest_acceptable_selected
 if k==2:
  r=m.evaluate(q); sel=next(x for x in r.candidate_evaluations if x.bit_width==r.selected_bit_width); return sel.weighted_error_pass and sel.critical_error_pass and r.critical_error_guard_preserved
 if k==3:
  qq=replace(q,weighted_error_threshold=0.0,critical_max_error_threshold=0.0,candidate_bits=(2,3,4)); r=m.evaluate(qq); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.ALL_CANDIDATES_REJECTED and r.lossless_original_retention_candidate and not r.next_gate_candidate
 if k==4:
  r=m.evaluate(replace(q,candidate_bits=(4,4,8))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.DUPLICATE_BIT_WIDTH
 if k==5:
  r=m.evaluate(replace(q,candidate_bits=(1,8))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.INVALID_BIT_WIDTH
 if k==6:
  vals=list(q.values); vals[3]=float('nan'); r=m.evaluate(replace(q,values=tuple(vals))); return r.escalation==m.Escalation.NONFINITE_INPUT
 if k==7:
  im=list(q.importance); im[4]=1.2; r=m.evaluate(replace(q,importance=tuple(im))); return r.escalation==m.Escalation.INVALID_IMPORTANCE
 if k==8:
  r=m.evaluate(replace(q,importance=q.importance[:-1])); return r.escalation==m.Escalation.LENGTH_MISMATCH
 if k==9:
  r=m.evaluate(replace(q,values=())); return r.escalation==m.Escalation.EMPTY_DATA
 if k==10:
  qq=replace(q,candidate_bits=tuple(reversed(q.candidate_bits))); r=m.evaluate(qq); return tuple(x.bit_width for x in r.candidate_evaluations)==tuple(sorted(q.candidate_bits))
 if k==11:
  st=m.prepare_state(q,B,E); return prep(st)==st.result and st.result.decision==m.Decision.ALLOW
 if k==12:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_values_fingerprint=st.values_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==13:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=True,current_values_fingerprint='0'*64,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==14:
  st=m.prepare_state(q,B,E); vals=list(q.values); vals[5]+=0.0001; st2=m.prepare_state(replace(q,values=tuple(vals)),B,E); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('VALUE-0005',) and not p.full_resend_required
 if k==15:
  st=m.prepare_state(q,B,E); st2=m.prepare_state(replace(q,weighted_error_threshold=q.weighted_error_threshold*0.9),B,E); return 'QUANTIZATION_GUARD_CONFIG' in m.plan_missing_only(st,st2).missing_or_changed_record_ids
 if k==16:
  a=m.default_evaluation(); b=m.default_evaluation(); return a==b and m._canon(a)==m._canon(b)
 if k==17:
  r=m.default_evaluation(); return not any(neg(r)) and all(x in r.reasons for x in ('LIGHTEST_ACCEPTABLE_BIT_SELECTED','QUANTIZATION_RESULT_IS_CANDIDATE_NOT_COMMIT','NO_PERMISSION_WRITE_DEPLOYMENT_OR_ACTION_EXECUTION'))
 if k==18:
  qq=replace(q,critical=tuple(False for _ in q.critical)); r=m.evaluate(qq); return r.decision==m.Decision.ALLOW and all(x.critical_max_error==0.0 for x in r.candidate_evaluations)
 if k==19:
  # Unknown importance on a Critical item is conservatively weighted as 1.0 rather than ignored.
  w=m._importance_weights(q); return w[255]==1.0 and q.critical[255] and q.importance[255] is None
 return False
class TestAL167(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL167,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
