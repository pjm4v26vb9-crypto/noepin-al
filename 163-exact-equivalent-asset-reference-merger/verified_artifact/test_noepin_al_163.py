import unittest
from dataclasses import replace
import noepin_al_163_exact_equivalent_asset_reference_merger as m
B='DEFAULT-BINDING'; E='EPOCH-1'
NEG=('canonical_reference_written','reference_rewrite_executed','source_asset_deleted','payload_mutated','import_settings_mutated','behavior_state_mutated','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted','fallback_executed','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','publish_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success')
def neg(r): return [getattr(r,n) for n in NEG]
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_assets_fingerprint=st.assets_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint)
def scenario(k,rep):
 q=m.default_request()
 if k==0:
  r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.merge_group_count==1 and r.merged_duplicate_asset_count==1 and r.retained_original_count==1 and r.canonical_assets[0].canonical_asset_id=='ASSET-163-A1' and not any(neg(r))
 if k==1:
  a=list(q.assets); a[1]=replace(a[1],payload_hash='0'*64); r=m.evaluate(replace(q,assets=tuple(a))); return r.merge_group_count==0 and r.retained_original_count==3
 if k==2:
  a=list(q.assets); a[1]=replace(a[1],import_settings_hash='1'*64); r=m.evaluate(replace(q,assets=tuple(a))); return r.merge_group_count==0 and r.retained_original_count==3
 if k==3:
  a=list(q.assets); a[1]=replace(a[1],state_hash='2'*64); r=m.evaluate(replace(q,assets=tuple(a))); return r.merge_group_count==0 and r.retained_original_count==3
 if k==4:
  a=list(q.assets); a[1]=replace(a[1],payload_known=False); r=m.evaluate(replace(q,assets=tuple(a))); return r.merge_group_count==0 and 'ASSET-163-A2' in r.original_retained_asset_ids and any('UNKNOWN_FINGERPRINT' in x for x in r.reasons)
 if k==5:
  a=list(q.assets); a[1]=replace(a[1],import_known=False); return m.evaluate(replace(q,assets=tuple(a))).engine_state==m.EngineState.ORIGINAL_RETENTION_CANDIDATE
 if k==6:
  a=list(q.assets); a[1]=replace(a[1],state_known=False); return m.evaluate(replace(q,assets=tuple(a))).engine_state==m.EngineState.ORIGINAL_RETENTION_CANDIDATE
 if k==7:
  a=list(q.assets); a[1]=replace(a[1],integrity_verified=False); r=m.evaluate(replace(q,assets=tuple(a))); return r.escalation==m.Escalation.CORRUPT_INPUT and r.decision==m.Decision.HOLD
 if k==8:
  a=list(q.assets); a[1]=replace(a[1],asset_id=a[0].asset_id); return m.evaluate(replace(q,assets=tuple(a))).engine_state==m.EngineState.INVALID
 if k==9:
  a=list(q.assets); a[0]=replace(a[0],payload_hash='bad'); return m.evaluate(replace(q,assets=tuple(a))).engine_state==m.EngineState.INVALID
 if k==10:
  st=m.prepare_state(q,B,E); return prep(st)==st.result
 if k==11:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_assets_fingerprint=st.assets_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==12:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=True,current_assets_fingerprint='0'*64,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==13:
  st=m.prepare_state(q,B,E); a=list(q.assets); a[2]=replace(a[2],state_hash='3'*64); st2=m.prepare_state(replace(q,assets=tuple(a)),B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('ASSETS',)
 if k==14:
  r=m.default_evaluation(); return all(x in r.reasons for x in ('THREE_FINGERPRINT_MATCH_IS_EQUIVALENCE_EVIDENCE_NOT_TRUTH','CANONICAL_ASSET_CANDIDATE_IS_NOT_AUTHORITATIVE_STATE','ORIGINAL_ASSETS_ARE_RETAINED'))
 if k==15:
  a=list(q.assets); a[2]=replace(a[2],payload_hash=a[0].payload_hash,import_settings_hash=a[0].import_settings_hash,state_hash=a[0].state_hash); r=m.evaluate(replace(q,assets=tuple(a))); return r.engine_state==m.EngineState.EXACT_EQUIVALENT_MERGE_CANDIDATE and r.merged_duplicate_asset_count==2 and r.retained_original_count==0
 if k==16:
  a=list(q.assets); a[1]=replace(a[1],payload_hash='4'*64); r=m.evaluate(replace(q,assets=tuple(a))); return r.engine_state==m.EngineState.ORIGINAL_RETENTION_CANDIDATE and r.decision==m.Decision.HOLD
 if k==17:
  a=list(q.assets); a[0]=replace(a[0],binding='BAD'); return m.evaluate(replace(q,assets=tuple(a))).engine_state==m.EngineState.INVALID
 if k==18:
  r=m.default_evaluation(); return r.full_original_fallback_candidate and not r.source_asset_deleted and not r.reference_rewrite_executed and not r.authoritative_state_created and r.next_gate_candidate
 if k==19:
  r=m.default_evaluation(); return r.next_action==m.NextAction.CONTINUE_REFERENCE_MERGE_CANDIDATE and r.engine_state==m.EngineState.MIXED_MERGE_AND_ORIGINAL_CANDIDATE and not any(neg(r))
 return False
class TestAL163(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL163,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
