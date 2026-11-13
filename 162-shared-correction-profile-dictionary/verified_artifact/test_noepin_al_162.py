import unittest
from dataclasses import replace
import noepin_al_162_shared_correction_profile_dictionary as m
B='DEFAULT-BINDING'; E='EPOCH-1'
NEG=('profile_registry_written','target_reference_written','original_profile_deleted','source_profile_mutated','profile_content_mutated','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted','fallback_executed','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','plan_committed','publish_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success')
def neg(r): return [getattr(r,n) for n in NEG]
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_targets_fingerprint=st.targets_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint)
def scenario(k,rep):
 q=m.default_request()
 if k==0:
  r=m.evaluate(q); return r.decision==m.Decision.ALLOW and r.shared_profile_count==1 and r.shared_target_count==2 and r.individual_target_count==1 and r.duplicate_profiles_removed_candidate==1 and not any(neg(r))
 if k==1:
  t=list(q.targets); t[1]=replace(t[1],compatibility_fingerprint='0'*64); r=m.evaluate(replace(q,targets=tuple(t))); return r.shared_profile_count==0 and r.individual_target_count==3
 if k==2:
  t=list(q.targets); t[1]=replace(t[1],critical_attributes=('SKELETON-V2','UNIT-METER')); r=m.evaluate(replace(q,targets=tuple(t))); return r.shared_profile_count==0 and any(x.reason=='CRITICAL_ATTRIBUTE_MISMATCH' for x in r.target_references)
 if k==3:
  t=list(q.targets); t[1]=replace(t[1],profile=(m.ProfileField('gain','0.5'),m.ProfileField('offset','0.125'),m.ProfileField('mode','SAFE'))); r=m.evaluate(replace(q,targets=tuple(t))); return r.shared_profile_count==0 and any('PROFILE_CONTENT_MISMATCH_SPLIT' in x for x in r.reasons)
 if k==4:
  t=list(q.targets); t[1]=replace(t[1],compatibility_known=False); r=m.evaluate(replace(q,targets=tuple(t))); return r.individual_target_count==3 and any(x.reason=='UNKNOWN_COMPATIBILITY_INDIVIDUAL' for x in r.target_references)
 if k==5:
  t=list(q.targets); t[1]=replace(t[1],integrity_verified=False); r=m.evaluate(replace(q,targets=tuple(t))); return r.individual_target_count==3 and any(x.reason=='INTEGRITY_UNVERIFIED_INDIVIDUAL' for x in r.target_references)
 if k==6:
  t=list(q.targets); t[1]=replace(t[1],usage_tag='OTHER_USE'); r=m.evaluate(replace(q,targets=tuple(t))); return r.shared_profile_count==0 and any('USAGE_TAG_MISMATCH_SPLIT' in x for x in r.reasons)
 if k==7:
  t=list(q.targets); t[1]=replace(t[1],target_id=t[0].target_id); return m.evaluate(replace(q,targets=tuple(t))).engine_state==m.EngineState.INVALID
 if k==8:
  t=list(q.targets); t[0]=replace(t[0],compatibility_fingerprint='bad'); return m.evaluate(replace(q,targets=tuple(t))).engine_state==m.EngineState.INVALID
 if k==9:
  t=list(q.targets); t[0]=replace(t[0],binding='BAD'); return m.evaluate(replace(q,targets=tuple(t))).engine_state==m.EngineState.INVALID
 if k==10:
  st=m.prepare_state(q,B,E); return prep(st)==st.result
 if k==11:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_targets_fingerprint=st.targets_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==12:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=True,current_targets_fingerprint='0'*64,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==13:
  a=m.prepare_state(q,B,E); t=list(q.targets); t[2]=replace(t[2],usage_tag='ASSET_CORRECTION_V2'); b=m.prepare_state(replace(q,targets=tuple(t)),B,E); return m.plan_missing_only(a,b).missing_or_changed_record_ids==('TARGETS',)
 if k==14:
  r=m.default_evaluation(); return all(x in r.reasons for x in ('FINGERPRINT_MATCH_IS_COMPATIBILITY_EVIDENCE_NOT_TRUTH','RECONSTRUCTED_PARTIAL_CACHED_STATE_IS_NOT_AUTHORITATIVE_STATE','ORIGINAL_PROFILE_IS_RETAINED'))
 if k==15:
  # all exact same => single shared profile for all 3
  t=list(q.targets); t[2]=replace(t[2],compatibility_fingerprint=t[0].compatibility_fingerprint,profile=t[0].profile,usage_tag=t[0].usage_tag,critical_attributes=t[0].critical_attributes); r=m.evaluate(replace(q,targets=tuple(t))); return r.engine_state==m.EngineState.SHARED_PROFILE_CANDIDATE and r.shared_target_count==3 and r.individual_target_count==0
 if k==16:
  # all unique => individual fallback
  t=list(q.targets); t[1]=replace(t[1],compatibility_fingerprint='1'*64); r=m.evaluate(replace(q,targets=tuple(t))); return r.engine_state==m.EngineState.INDIVIDUAL_FALLBACK_CANDIDATE and r.decision==m.Decision.HOLD
 if k==17:
  t=list(q.targets); t[0]=replace(t[0],profile=()); return m.evaluate(replace(q,targets=tuple(t))).engine_state==m.EngineState.INVALID
 if k==18:
  r=m.default_evaluation(); return r.reconstruction_fallback_original_candidate and not r.original_profile_deleted and not r.authoritative_state_created and r.next_gate_candidate
 if k==19:
  r=m.default_evaluation(); return r.next_action==m.NextAction.CONTINUE_SHARED_PROFILE_CANDIDATE and r.engine_state==m.EngineState.MIXED_SHARED_AND_INDIVIDUAL_CANDIDATE and not any(neg(r))
 return False
class TestAL162(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL162,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
