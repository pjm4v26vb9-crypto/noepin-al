import unittest, math
from dataclasses import replace
import noepin_al_170_progressive_restoration_scheduler as m
q=m.default_request(); B=q.binding; E=q.state_epoch
NEG=('source_chunks_mutated','restoration_executed','transfer_executed','stage_committed','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted','publish_executed','fallback_executed','original_deleted','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success')
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_base_fingerprint=st.base_fingerprint,current_detail_fingerprint=st.detail_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint)
def scenario(k,cycle):
 if k==0:
  r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.stage_order[0].stage_kind=='BASE' and r.stage_order[0].priority=='P0' and r.required_details_complete and r.next_gate_candidate
 if k==1:
  r=m.evaluate(replace(q,base_available=False)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.BASE_UNAVAILABLE
 if k==2:
  r=m.evaluate(replace(q,byte_budget=q.base_size_bytes-1)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.BASE_BUDGET_INSUFFICIENT
 if k==3:
  cs=list(q.detail_chunks); cs[0]=replace(cs[0],available=False); r=m.evaluate(replace(q,detail_chunks=tuple(cs))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.REQUIRED_DETAIL_MISSING
 if k==4:
  r=m.evaluate(replace(q,byte_budget=q.base_size_bytes+100)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.MANDATORY_BUDGET_INSUFFICIENT
 if k==5:
  r=m.evaluate(replace(q,latency_budget_ms=q.base_latency_ms+0.1)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.MANDATORY_BUDGET_INSUFFICIENT
 if k==6:
  qq=replace(q,detail_chunks=(),allow_base_only=False); r=m.evaluate(qq); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.BASE_ONLY_NOT_ALLOWED
 if k==7:
  qq=replace(q,detail_chunks=(),allow_base_only=True); r=m.evaluate(qq); return r.decision==m.Decision.ALLOW and r.base_only and r.base_only_policy_explicitly_allowed
 if k==8:
  r=m.default_evaluation(); return len(r.deferred_detail_ids)>=1 and all(x not in r.required_detail_ids for x in r.deferred_detail_ids) and r.bytes_consumed<=r.byte_budget and r.latency_consumed_ms<=r.latency_budget_ms
 if k==9:
  r=m.default_evaluation(); ps=[int(s.priority[1:]) for s in r.stage_order[1:]]; return ps==sorted(ps) and all(x in r.critical_scheduled_ids for x in ('CRIT-A','CRIT-B'))
 if k==10:
  a=m.default_evaluation(); b=m.default_evaluation(); return a==b and m._canon(a)==m._canon(b)
 if k==11:
  st=m.prepare_state(q,B,E); return prep(st)==st.result and st.result.decision==m.Decision.ALLOW
 if k==12:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_base_fingerprint=st.base_fingerprint,current_detail_fingerprint=st.detail_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==13:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=True,current_base_fingerprint='0'*64,current_detail_fingerprint=st.detail_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==14:
  st=m.prepare_state(q,B,E); cs=list(q.detail_chunks); cs[4]=replace(cs[4],importance=0.91); st2=m.prepare_state(replace(q,detail_chunks=tuple(cs)),B,E); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('DETAIL_CHUNKS',) and not p.full_resend_required
 if k==15:
  st=m.prepare_state(q,B,E); st2=m.prepare_state(replace(q,byte_budget=q.byte_budget+1),B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('RESTORATION_SCHEDULER_CONFIG',)
 if k==16:
  cs=list(q.detail_chunks); cs[1]=replace(cs[1],chunk_id=cs[0].chunk_id); r=m.evaluate(replace(q,detail_chunks=tuple(cs))); return r.engine_state==m.EngineState.INVALID and r.decision==m.Decision.HOLD
 if k==17:
  cs=list(q.detail_chunks); cs[0]=replace(cs[0],importance=float('nan')); r=m.evaluate(replace(q,detail_chunks=tuple(cs))); return r.engine_state==m.EngineState.INVALID and r.decision==m.Decision.DENY
 if k==18:
  req=[c for c in q.detail_chunks if c.required]; bb=q.base_size_bytes+sum(c.size_bytes for c in req); ll=q.base_latency_ms+sum(c.latency_ms for c in req); r=m.evaluate(replace(q,byte_budget=bb,latency_budget_ms=ll)); return r.decision==m.Decision.ALLOW and r.required_details_complete and set(r.scheduled_detail_ids)==set(c.chunk_id for c in req)
 if k==19:
  r=m.default_evaluation(); return not any(getattr(r,n) for n in NEG) and r.engine_state==m.EngineState.PROGRESSIVE_RESTORATION_CANDIDATE
 return False
class TestAL170(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL170,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
