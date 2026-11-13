import unittest
from dataclasses import replace
import noepin_al_169_reconstruction_confidence_gate as m
B='DEFAULT-BINDING'; E='EPOCH-1'
NEG=('reconstructed_values_mutated','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted','publish_executed','final_validation_committed','fallback_executed','original_deleted','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success')
def neg(r): return [getattr(r,n) for n in NEG]
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_reconstruction_fingerprint=st.reconstruction_fingerprint,current_evidence_fingerprint=st.evidence_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint)
def scenario(k,rep):
 q=m.default_request()
 if k==0:
  r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.next_gate_candidate and r.engine_state==m.EngineState.RECONSTRUCTION_CONFIDENCE_CANDIDATE and not any(neg(r))
 if k==1:
  r=m.evaluate(q); return r.fingerprint_match and r.residual_coverage==0.96 and r.residual_coverage_sufficient
 if k==2:
  r=m.evaluate(q); return r.maximum_error==0 and r.critical_maximum_error==0 and r.maximum_error_within_threshold and r.critical_error_within_threshold
 if k==3:
  vals=list(q.reconstructed_values); vals[3]+=0.01; qq=replace(q,reconstructed_values=tuple(vals)); r=m.evaluate(qq); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.HASH_MISMATCH
 if k==4:
  qq=replace(q,residual_applied=90); r=m.evaluate(qq); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.COVERAGE_INSUFFICIENT
 if k==5:
  exp=list(q.expected_values); exp[7]+=0.002; qq=replace(q,expected_values=tuple(exp),expected_fingerprint=m.fingerprint_values(q.reconstructed_values)); r=m.evaluate(qq); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.CRITICAL_ERROR_EXCEEDED
 if k==6:
  exp=list(q.expected_values); exp[10]+=0.003; qq=replace(q,expected_values=tuple(exp),expected_fingerprint=m.fingerprint_values(q.reconstructed_values)); r=m.evaluate(qq); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.MAX_ERROR_EXCEEDED
 if k==7:
  qq=replace(q,expected_fingerprint='f'*64); r=m.evaluate(qq); return r.decision==m.Decision.DENY and not r.next_gate_candidate
 if k==8:
  qq=replace(q,reconstructed_values=q.reconstructed_values[:-1]); r=m.evaluate(qq); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.LENGTH_MISMATCH
 if k==9:
  vals=list(q.reconstructed_values); vals[0]=float('nan'); r=m.evaluate(replace(q,reconstructed_values=tuple(vals))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.INVALID_VALUE
 if k==10:
  r=m.evaluate(replace(q,expected_critical_indices=q.expected_critical_indices[:-1])); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.EXPECTED_CRITICAL_EVIDENCE_MISSING and not r.next_gate_candidate
 if k==11:
  st=m.prepare_state(q,B,E); return prep(st)==st.result and st.result.decision==m.Decision.ALLOW
 if k==12:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_reconstruction_fingerprint=st.reconstruction_fingerprint,current_evidence_fingerprint=st.evidence_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==13:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=True,current_reconstruction_fingerprint='0'*64,current_evidence_fingerprint=st.evidence_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==14:
  st=m.prepare_state(q,B,E); vals=list(q.reconstructed_values); vals[9]=round(vals[9]+0.0001,6); q2=replace(q,reconstructed_values=tuple(vals),expected_values=tuple(vals),expected_fingerprint=m.fingerprint_values(tuple(vals))); st2=m.prepare_state(q2,B,E); p=m.plan_missing_only(st,st2); return 'RECONSTRUCTION_RESULT' in p.missing_or_changed_record_ids and 'EXPECTED_EVIDENCE' in p.missing_or_changed_record_ids and not p.full_resend_required
 if k==15:
  st=m.prepare_state(q,B,E); st2=m.prepare_state(replace(q,minimum_residual_coverage=0.9),B,E); return 'CONFIDENCE_GATE_CONFIG' in m.plan_missing_only(st,st2).missing_or_changed_record_ids
 if k==16:
  a=m.default_evaluation(); b=m.default_evaluation(); return a==b and m._canon(a)==m._canon(b)
 if k==17:
  r=m.default_evaluation(); return 0<=r.confidence<=1 and dict(r.confidence_components)['hash']==1.0
 if k==18:
  r=m.default_evaluation(); return all(x in r.reasons for x in ('EXPECTED_FINGERPRINT_MATCHED','RESIDUAL_COVERAGE_SUFFICIENT','CONFIDENCE_IS_AUDIT_SCORE_NOT_AUTHORITY'))
 if k==19:
  a=m.evaluate(replace(q,residual_applied=101)); b=m.evaluate(replace(q,minimum_residual_coverage=1.1)); return a.engine_state==m.EngineState.INVALID and b.engine_state==m.EngineState.INVALID
 return False
class TestAL169(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL169,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
