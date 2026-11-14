import unittest
from dataclasses import replace
import noepin_al_172_lightweighting_strategy_orchestrator as m
q=m.default_request(); B=q.binding; E=q.state_epoch
NEG=('source_records_mutated','compression_executed','quantization_executed','residual_applied','transfer_executed','plan_committed','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted','publish_executed','fallback_executed','original_deleted','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success')
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_records_fingerprint=st.records_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint)
def dct(r): return {x.record_id:x for x in r.selections}
def scenario(k,cycle):
 if k==0:
  r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.budget_feasible and r.all_reconstruction_guaranteed and r.critical_high_sensitivity_lossy_count==0 and r.next_gate_candidate
 if k==1: return dct(m.default_evaluation())['EXACT-A'].strategy==m.Strategy.EXACT_REUSE
 if k==2: return dct(m.default_evaluation())['SHARED-A'].strategy==m.Strategy.SHARED_PROFILE
 if k==3: return dct(m.default_evaluation())['DELTA-A'].strategy==m.Strategy.DELTA
 if k==4: return dct(m.default_evaluation())['NUM-A'].strategy==m.Strategy.QUANTIZATION_RESIDUAL
 if k==5: return dct(m.default_evaluation())['CRIT-HIGH'].strategy==m.Strategy.LOSSLESS
 if k==6: return dct(m.default_evaluation())['ORIGINAL-A'].strategy==m.Strategy.ORIGINAL
 if k==7: return dct(m.default_evaluation())['EXACT-CRIT'].strategy==m.Strategy.EXACT_REUSE
 if k==8:
  r=m.evaluate(replace(q,size_budget_bytes=m.default_evaluation().planned_total_bytes-1)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.SAFE_PLAN_EXCEEDS_BUDGET
 if k==9:
  rs=list(q.records); rs[0]=replace(rs[0],available=False); r=m.evaluate(replace(q,records=tuple(rs))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.SOURCE_UNAVAILABLE
 if k==10:
  rs=list(q.records); rs[3]=replace(rs[3],quantization_error=0.5,lossless_bytes=1900); r=m.evaluate(replace(q,records=tuple(rs))); return dct(r)['NUM-A'].strategy==m.Strategy.LOSSLESS
 if k==11:
  rs=list(q.records); rs[1]=replace(rs[1],shared_profile_fingerprint_match=False,lossless_bytes=2000); r=m.evaluate(replace(q,records=tuple(rs))); return dct(r)['SHARED-A'].strategy==m.Strategy.LOSSLESS
 if k==12:
  rs=list(q.records); rs[2]=replace(rs[2],delta_reversible=False,lossless_bytes=1800); r=m.evaluate(replace(q,records=tuple(rs))); return dct(r)['DELTA-A'].strategy==m.Strategy.LOSSLESS
 if k==13:
  rs=list(q.records); rs[4]=replace(rs[4],lossless_available=False); r=m.evaluate(replace(q,records=tuple(rs))); return dct(r)['CRIT-HIGH'].strategy==m.Strategy.ORIGINAL
 if k==14:
  st=m.prepare_state(q,B,E); return prep(st)==st.result and st.result.decision==m.Decision.ALLOW
 if k==15:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_records_fingerprint=st.records_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==16:
  st=m.prepare_state(q,B,E); rs=list(q.records); rs[5]=replace(rs[5],importance=.61); st2=m.prepare_state(replace(q,records=tuple(rs)),B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('ASSET_DATA_RECORDS',)
 if k==17:
  st=m.prepare_state(q,B,E); st2=m.prepare_state(replace(q,size_budget_bytes=q.size_budget_bytes+10),B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('LIGHTWEIGHTING_CONFIG',)
 if k==18:
  a=m.default_evaluation(); b=m.default_evaluation(); return a==b and m._canon(a)==m._canon(b)
 if k==19:
  r=m.default_evaluation(); return not any(getattr(r,n) for n in NEG) and r.expected_savings_bytes==r.original_total_bytes-r.planned_total_bytes
 return False
class TestAL172(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL172,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
