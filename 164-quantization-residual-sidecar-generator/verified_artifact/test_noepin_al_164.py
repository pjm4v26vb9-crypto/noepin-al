import unittest, math
from dataclasses import replace
import noepin_al_164_quantization_residual_sidecar_generator as m
B='DEFAULT-BINDING'; E='EPOCH-1'
NEG=('original_values_mutated','quantized_base_committed','residual_sidecar_written','manifest_written','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted','original_deleted','fallback_executed','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','publish_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success')
def neg(r): return [getattr(r,n) for n in NEG]
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_values_fingerprint=st.values_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint)
def scenario(k,rep):
 q=m.default_request()
 if k==0:
  r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.engine_state==m.EngineState.QUANTIZED_SIDECAR_CANDIDATE and r.compression_stats.beneficial and len(r.quantized_base)==len(q.values) and not any(neg(r))
 if k==1:
  r=m.evaluate(q); crit={x.index for x in r.residual_sidecar if x.critical}; return crit==set(q.critical_indices)
 if k==2:
  r=m.evaluate(q); return all(x.critical or abs(x.residual)>q.residual_threshold for x in r.residual_sidecar)
 if k==3:
  vals=list(q.values); vals[5]=float('nan'); r=m.evaluate(replace(q,values=tuple(vals))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.NONFINITE_INPUT
 if k==4:
  vals=list(q.values); vals[5]=float('inf'); return m.evaluate(replace(q,values=tuple(vals))).escalation==m.Escalation.NONFINITE_INPUT
 if k==5: return m.evaluate(replace(q,bit_width=1)).escalation==m.Escalation.INVALID_BIT_WIDTH
 if k==6: return m.evaluate(replace(q,bit_width=17)).escalation==m.Escalation.INVALID_BIT_WIDTH
 if k==7: return m.evaluate(replace(q,residual_threshold=-0.1)).escalation==m.Escalation.INVALID_THRESHOLD
 if k==8: return m.evaluate(replace(q,critical_indices=(0,999))).escalation==m.Escalation.INVALID_CRITICAL_INDEX
 if k==9:
  q2=replace(q,values=(0.0,0.1),critical_indices=(0,1),bit_width=16,residual_threshold=0.0); r=m.evaluate(q2); return r.engine_state==m.EngineState.ORIGINAL_RETENTION_CANDIDATE and r.original_retention_candidate
 if k==10:
  st=m.prepare_state(q,B,E); return prep(st)==st.result
 if k==11:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_values_fingerprint=st.values_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==12:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=True,current_values_fingerprint='0'*64,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==13:
  st=m.prepare_state(q,B,E); vals=list(q.values); vals[7]+=0.01; st2=m.prepare_state(replace(q,values=tuple(vals)),B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('VALUES',)
 if k==14:
  st=m.prepare_state(q,B,E); st2=m.prepare_state(replace(q,residual_threshold=q.residual_threshold+0.0001),B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('CONFIG',)
 if k==15:
  q2=replace(q,values=tuple(1.5 for _ in range(512))); r=m.evaluate(q2); return r.scale==1.0 and r.zero_point==1.5 and all(x==0 for x in r.quantized_base)
 if k==16:
  r=m.default_evaluation(); return all(x in r.reasons for x in ('CRITICAL_INDICES_ALWAYS_RETAIN_RESIDUAL','BASE_AND_SIDECAR_ARE_BOUND_BY_MANIFEST_FINGERPRINT','RECONSTRUCTED_PARTIAL_CACHED_STATE_IS_NOT_AUTHORITATIVE_STATE'))
 if k==17:
  r=m.default_evaluation(); return len(r.manifest_fingerprint)==64 and r.reconstruction_max_abs_error<=q.residual_threshold+1e-12
 if k==18:
  r=m.default_evaluation(); return r.next_gate_candidate and not r.original_values_mutated and not r.residual_sidecar_written and not r.authoritative_state_created
 if k==19:
  a=m.default_evaluation(); b=m.default_evaluation(); return a==b and m._canon(a)==m._canon(b) and not any(neg(a))
 return False
class TestAL164(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL164,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
