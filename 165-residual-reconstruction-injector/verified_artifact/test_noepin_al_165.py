import unittest
from dataclasses import replace
import noepin_al_165_residual_reconstruction_injector as m
B='DEFAULT-BINDING'; E='EPOCH-1'
NEG=('quantized_base_mutated','residual_sidecar_mutated','reconstructed_values_committed','source_manifest_written','stage_manifest_written','original_deleted','fallback_executed','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','publish_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success')
def neg(r): return [getattr(r,n) for n in NEG]
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_base_fingerprint=st.base_fingerprint,current_sidecar_fingerprint=st.sidecar_fingerprint,current_manifest_fingerprint=st.manifest_fingerprint,current_result_fingerprint=st.result_fingerprint)
def scenario(k,rep):
 q=m.default_request()
 if k==0:
  r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.engine_state==m.EngineState.RECONSTRUCTED_ARRAY_CANDIDATE and r.applied_residual_count==q.manifest.expected_residual_count and r.checksum_verified and r.error_limit_verified and not any(neg(r))
 if k==1:
  r=m.evaluate(q); return r.source_manifest_verified and r.residual_sidecar_verified and all(a.verified for a in r.stage_audit)
 if k==2:
  bad=replace(q,manifest=replace(q.manifest,source_manifest_fingerprint='0'*64)); r=m.evaluate(bad); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.MANIFEST_MISMATCH and not r.reconstructed_values
 if k==3:
  rec=list(q.residual_sidecar); rec[0]=replace(rec[0],index=len(q.quantized_base)); r=m.evaluate(replace(q,residual_sidecar=tuple(rec))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.RESIDUAL_INDEX_OUT_OF_RANGE
 if k==4:
  rec=list(q.residual_sidecar); rec[1]=replace(rec[1],index=rec[0].index); r=m.evaluate(replace(q,residual_sidecar=tuple(rec))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.DUPLICATE_RESIDUAL_INDEX
 if k==5:
  rec=tuple(x for x in q.residual_sidecar if not x.critical); r=m.evaluate(replace(q,residual_sidecar=rec)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.CRITICAL_RESIDUAL_MISSING
 if k==6:
  # No critical residual expected + sidecar absent + explicit policy can produce Base-only candidate.
  vals=(0.0,1.0); base=(0,255); side=(); binding='B'; epoch='E'; source=m._fp((base,1/255,0.0,(),8,1.0,(),binding,epoch)); basevals=(0.0,1.0)
  man=m.ReconstructionManifest(source,1,(1,),(),(),m._fp(basevals),1.0,True)
  qq=m.ReconstructionRequest('BASEONLY',base,1/255,0.0,8,1.0,side,man,basevals,binding,epoch); rr=m.evaluate(qq); return rr.engine_state==m.EngineState.BASE_ONLY_RECONSTRUCTION_CANDIDATE and rr.base_only_candidate and not any(neg(rr))
 if k==7:
  rec=tuple(q.residual_sidecar[:-1]); r=m.evaluate(replace(q,residual_sidecar=rec)); return r.decision==m.Decision.HOLD and r.escalation in {m.Escalation.CRITICAL_RESIDUAL_MISSING,m.Escalation.PARTIAL_RESIDUAL_SIDECAR}
 if k==8:
  stages=list(q.manifest.stage_fingerprints); stages[0]=(stages[0][0],'f'*64); r=m.evaluate(replace(q,manifest=replace(q.manifest,stage_fingerprints=tuple(stages)))); return r.escalation==m.Escalation.STAGE_FINGERPRINT_MISMATCH
 if k==9:
  r=m.evaluate(replace(q,manifest=replace(q.manifest,expected_reconstructed_fingerprint='0'*64))); return r.escalation==m.Escalation.CHECKSUM_MISMATCH
 if k==10:
  r=m.evaluate(replace(q,manifest=replace(q.manifest,max_abs_error=0.0),reference_values=tuple(x+1e-6 for x in q.reference_values))); return r.escalation in {m.Escalation.CHECKSUM_MISMATCH,m.Escalation.ERROR_LIMIT_EXCEEDED}
 if k==11:
  st=m.prepare_state(q,B,E); return prep(st)==st.result and st.result.decision==m.Decision.ALLOW
 if k==12:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_base_fingerprint=st.base_fingerprint,current_sidecar_fingerprint=st.sidecar_fingerprint,current_manifest_fingerprint=st.manifest_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==13:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=True,current_base_fingerprint='0'*64,current_sidecar_fingerprint=st.sidecar_fingerprint,current_manifest_fingerprint=st.manifest_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==14:
  st=m.prepare_state(q,B,E); base=list(q.quantized_base); base[10]+=1; q2=replace(q,quantized_base=tuple(base)); st2=m.prepare_state(q2,B,E); return 'QUANTIZED_BASE' in m.plan_missing_only(st,st2).missing_or_changed_record_ids
 if k==15:
  st=m.prepare_state(q,B,E); rec=list(q.residual_sidecar); rec[-1]=replace(rec[-1],residual=rec[-1].residual+0.00001); q2=replace(q,residual_sidecar=tuple(rec)); st2=m.prepare_state(q2,B,E); p=m.plan_missing_only(st,st2); return 'RESIDUAL_SIDECAR' in p.missing_or_changed_record_ids and not p.full_resend_required
 if k==16:
  rr=m.default_evaluation(); return rr.reconstruction_max_abs_error<=q.manifest.max_abs_error+1e-12 and rr.reconstructed_fingerprint==q.manifest.expected_reconstructed_fingerprint and max(abs(a-b) for a,b in zip(rr.reconstructed_values,q.reference_values))<=q.manifest.max_abs_error+1e-12
 if k==17:
  rr=m.default_evaluation(); return all(x in rr.reasons for x in ('EACH_PROGRESSIVE_STAGE_FINGERPRINT_VERIFIED','RECONSTRUCTED_ARRAY_IS_CANDIDATE_NOT_AUTHORITATIVE_STATE','FULL_ORIGINAL_FALLBACK_RETAINED_AS_CANDIDATE'))
 if k==18:
  qq=replace(q,scale=float('nan')); rr=m.evaluate(qq); return rr.decision==m.Decision.HOLD and rr.escalation==m.Escalation.NONFINITE_INPUT
 if k==19:
  a=m.default_evaluation(); b=m.default_evaluation(); return a==b and m._canon(a)==m._canon(b) and not any(neg(a))
 return False
class TestAL165(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL165,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
