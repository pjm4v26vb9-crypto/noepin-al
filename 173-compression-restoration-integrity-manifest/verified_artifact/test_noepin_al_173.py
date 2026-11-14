import unittest
from dataclasses import replace
import noepin_al_173_compression_restoration_integrity_manifest as m
q=m.default_request(); B=q.binding; E=q.state_epoch
NEG=('source_components_mutated','manifest_persisted','reconstruction_executed','decompression_executed','residual_applied','transfer_executed','plan_committed','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted','publish_executed','fallback_executed','original_deleted','tool_invoked','file_write_executed','network_send_executed','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','permission_granted','approval_executed','authority_granted','stop_executed','action_executed','external_write_performed','world_truth_proven','domain_authority_promoted','safety_proven','action_success')
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_components_fingerprint=st.components_fingerprint,current_manifest_fingerprint=st.manifest_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint)
def scenario(k,cycle):
 if k==0:
  r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.target_match and r.version_match and r.manifest_hash_valid and r.metadata_match and r.component_set_match and r.component_hashes_match and r.required_components_available and r.checked_component_count==5 and r.matched_component_count==5 and r.next_gate_candidate
 if k==1:
  cs=list(q.components); cs[0]=replace(cs[0],payload=cs[0].payload+b'X'); r=m.evaluate(replace(q,components=tuple(cs))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.COMPONENT_HASH_MISMATCH
 if k==2:
  r=m.evaluate(replace(q,target_id='OTHER-TARGET')); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.TARGET_MISMATCH
 if k==3:
  r=m.evaluate(replace(q,algorithm_version='ALGO-173-v3')); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.VERSION_INCOMPATIBLE
 if k==4:
  bad=replace(q.expected_manifest,manifest_hash='0'*64); r=m.evaluate(replace(q,expected_manifest=bad)); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.MANIFEST_HASH_MISMATCH
 if k==5:
  r=m.evaluate(replace(q,metadata=q.metadata+(('x','y'),))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.METADATA_MISMATCH
 if k==6:
  r=m.evaluate(replace(q,components=q.components[:-1])); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.COMPONENT_SET_MISMATCH
 if k==7:
  cs=list(q.components); cs[0]=replace(cs[0],available=False); r=m.evaluate(replace(q,components=tuple(cs))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.COMPONENT_UNAVAILABLE
 if k==8:
  cs=list(q.components); cs[-1]=replace(cs[-1],available=False); r=m.evaluate(replace(q,components=tuple(cs))); return r.decision==m.Decision.ALLOW
 if k==9:
  m2=m.build_manifest(q.target_id,q.algorithm_version,q.components,q.metadata); return m2==q.expected_manifest and m._manifest_hash_valid(m2)
 if k==10:
  st=m.prepare_state(q,B,E); return prep(st)==st.result and st.result.decision==m.Decision.ALLOW
 if k==11:
  st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_components_fingerprint=st.components_fingerprint,current_manifest_fingerprint=st.manifest_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint); return r.engine_state==m.EngineState.INVALID
 if k==12:
  st=m.prepare_state(q,B,E); cs=list(q.components); cs[1]=replace(cs[1],payload=cs[1].payload+b'x'); q2=replace(q,components=tuple(cs)); st2=m.prepare_state(q2,B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('COMPONENT_BYTES',)
 if k==13:
  st=m.prepare_state(q,B,E); bad=replace(q.expected_manifest,manifest_hash='f'*64); st2=m.prepare_state(replace(q,expected_manifest=bad),B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('INTEGRITY_MANIFEST',)
 if k==14:
  st=m.prepare_state(q,B,E); st2=m.prepare_state(replace(q,request_id='CRIM-173-B'),B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('INTEGRITY_CONFIG',)
 if k==15:
  r=m.default_evaluation(); return not any(getattr(r,n) for n in NEG)
 if k==16:
  a=m.default_evaluation(); b=m.default_evaluation(); return a==b and m._canon(a)==m._canon(b)
 if k==17:
  e=q.expected_manifest.entries[0]; altered=replace(e,sha256='1'*64); entries=(altered,)+q.expected_manifest.entries[1:]; mh=m._fp(m._manifest_payload(q.expected_manifest.schema,q.expected_manifest.target_id,q.expected_manifest.algorithm_version,entries,q.expected_manifest.metadata_fingerprint)); bad=replace(q.expected_manifest,entries=entries,manifest_hash=mh); r=m.evaluate(replace(q,expected_manifest=bad)); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.COMPONENT_HASH_MISMATCH
 if k==18:
  r=m.evaluate(replace(q,request_id='')); return r.engine_state==m.EngineState.INVALID and not r.next_gate_candidate
 if k==19:
  return len(q.expected_manifest.manifest_hash)==64 and all(len(e.sha256)==64 for e in q.expected_manifest.entries)
 return False
class TestAL173(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL173,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
