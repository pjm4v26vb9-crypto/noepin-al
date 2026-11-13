import unittest
from dataclasses import replace
import noepin_al_168_shared_base_delta_compressor as m
B='DEFAULT-BINDING'; E='EPOCH-1'
NEG=('source_variants_mutated','shared_base_committed','delta_storage_committed','individual_full_storage_committed','source_deleted','fallback_executed','reconstruction_map_written','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','publish_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success')
def neg(r): return [getattr(r,n) for n in NEG]
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_variants_fingerprint=st.variants_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint)
def scenario(k,rep):
 q=m.default_request()
 if k==0:
  r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.next_gate_candidate and r.engine_state==m.EngineState.SHARED_BASE_DELTA_CANDIDATE and not any(neg(r))
 if k==1:
  r=m.evaluate(q); return r.base_variant_id=='BASE-A' and r.delta_variant_count==18 and r.individual_full_variant_count==2 and r.incompatible_variant_count==1
 if k==2:
  r=m.evaluate(q); p=next(x for x in r.variant_plans if x.variant_id=='VAR-05'); return p.mode=='DELTA' and p.reversible and p.reconstruction_match and p.delta_bytes<p.full_bytes
 if k==3:
  r=m.evaluate(q); p=next(x for x in r.variant_plans if x.variant_id=='VAR-DENSE'); return p.mode=='INDIVIDUAL_FULL' and p.reason in {'DELTA_NOT_SMALLER_THAN_FULL_RETAIN_FULL','DELTA_RATIO_THRESHOLD_EXCEEDED_RETAIN_FULL'}
 if k==4:
  r=m.evaluate(q); p=next(x for x in r.variant_plans if x.variant_id=='VAR-OTHER'); return p.mode=='INDIVIDUAL_FULL' and p.reason=='INCOMPATIBLE_WITH_BASE'
 if k==5:
  r=m.evaluate(q); return r.critical_reversibility_preserved and r.all_reconstructions_exact
 if k==6:
  r=m.evaluate(replace(q,delta_ratio_threshold=0.000001)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.NO_BENEFICIAL_DELTA and not r.next_gate_candidate
 if k==7:
  vs=list(q.variants); vs[1]=replace(vs[1],variant_id='BASE-A'); r=m.evaluate(replace(q,variants=tuple(vs))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.DUPLICATE_VARIANT_ID
 if k==8:
  r=m.evaluate(replace(q,base_variant_id='MISSING')); return r.escalation==m.Escalation.BASE_VARIANT_MISSING
 if k==9:
  r=m.evaluate(replace(q,variants=())); return r.escalation==m.Escalation.EMPTY_VARIANTS
 if k==10:
  vs=list(q.variants); vs[2]=replace(vs[2],values=vs[2].values+(1,)); r=m.evaluate(replace(q,variants=tuple(vs))); p=next(x for x in r.variant_plans if x.variant_id==vs[2].variant_id); return p.mode=='INDIVIDUAL_FULL' and p.reason=='INCOMPATIBLE_WITH_BASE'
 if k==11:
  st=m.prepare_state(q,B,E); return prep(st)==st.result and st.result.decision==m.Decision.ALLOW
 if k==12:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_variants_fingerprint=st.variants_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==13:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=True,current_variants_fingerprint='0'*64,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==14:
  st=m.prepare_state(q,B,E); vs=list(q.variants); vv=list(vs[3].values); vv[9]+=1; vs[3]=replace(vs[3],values=tuple(vv)); st2=m.prepare_state(replace(q,variants=tuple(vs)),B,E); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==(f'VARIANT-{vs[3].variant_id}',) and not p.full_resend_required
 if k==15:
  st=m.prepare_state(q,B,E); st2=m.prepare_state(replace(q,delta_ratio_threshold=0.4),B,E); return 'SHARED_BASE_DELTA_CONFIG' in m.plan_missing_only(st,st2).missing_or_changed_record_ids
 if k==16:
  a=m.default_evaluation(); b=m.default_evaluation(); return a==b and m._canon(a)==m._canon(b)
 if k==17:
  r=m.default_evaluation(); return r.estimated_candidate_bytes<r.estimated_original_bytes and r.estimated_savings_bytes>0 and 0<r.compression_ratio<1
 if k==18:
  r=m.default_evaluation(); return all(x in r.reasons for x in ('RECONSTRUCTION_FINGERPRINT_VERIFIED','NON_BENEFICIAL_OR_INCOMPATIBLE_VARIANTS_RETAIN_FULL','NO_PERMISSION_WRITE_DEPLOYMENT_OR_ACTION_EXECUTION'))
 if k==19:
  vs=list(q.variants); bad=list(vs[4].values); bad[0]=True; vs[4]=replace(vs[4],values=tuple(bad)); r=m.evaluate(replace(q,variants=tuple(vs))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.INVALID_VALUE
 return False
class TestAL168(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL168,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
