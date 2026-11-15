import unittest
from dataclasses import replace
import noepin_al_183_schema_version_negotiation_protocol as m
NEG=('negotiated_version_promoted_to_truth','compatibility_promoted_to_safety_proof','connection_established','connection_executed','protocol_session_committed','permission_granted','permit_issued','approval_executed','human_approval_executed','tool_invoked','action_executed','action_success','stop_executed','file_write_executed','network_send_executed','external_write_performed','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted','dcsr_selected_unadvertised_version','dcsr_bypassed_schema_requirement','dcsr_bypassed_fingerprint_requirement','dcsr_created_compatibility_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','authority_granted','world_truth_proven','domain_authority_promoted','safety_proven')

def prepared(q,integrity=True,**kw):
 st=m.prepare_state(q)
 args=dict(integrity_validated=integrity,current_request_fingerprint=st.request_fingerprint,
           current_result_fingerprint=st.result_fingerprint,current_local_manifest_fingerprint=st.local_manifest_fingerprint,
           current_remote_manifest_fingerprint=st.remote_manifest_fingerprint,current_requirement_fingerprint=st.requirement_fingerprint,
           current_request=q)
 args.update(kw); return m.evaluate_prepared(st,**args)

def scenario(k,v):
 if k==0:
  x=m.default_evaluation(); return x.decision==m.Decision.ALLOW and str(x.negotiated_version)=='2.0' and x.next_gate_candidate and x.engine_state==m.EngineState.NEGOTIATED_VERSION_CANDIDATE and not any(getattr(x,n) for n in NEG)
 if k==1: return m.parse_version('0.0')==m.Version(0,0)
 if k==2:
  try: m.parse_version('1'); return False
  except ValueError: return True
 if k==3:
  try: m.parse_version('-1.0'); return False
  except ValueError: return True
 if k==4:
  try: m.parse_version('1.-1'); return False
  except ValueError: return True
 if k==5:
  try: m.parse_version('1.2.3'); return False
  except ValueError: return True
 if k==6:
  try: m.parse_version('01.2'); return False
  except ValueError: return True
 if k==7: return m.normalize_versions(('2.0','1.0','2.0'))==(m.Version(1,0),m.Version(2,0))
 if k==8:
  try: m.normalize_versions(()); return False
  except ValueError: return True
 if k==9:
  x=m.evaluate(m.make_request(('1.0',),('2.0',))); return x.decision==m.Decision.HOLD and x.escalation==m.Escalation.NO_COMMON_VERSION and not x.next_gate_candidate
 if k==10:
  x=m.evaluate(m.make_request(('1.0','2.0'),('1.0','2.0'),local_schema_id='S1',remote_schema_id='S2')); return x.decision==m.Decision.HOLD and x.full_fallback_candidate and x.escalation==m.Escalation.SCHEMA_MISMATCH
 if k==11:
  x=m.evaluate(m.make_request(('1.0','2.0'),('1.0','2.0'),local_schema_fingerprint='A',remote_schema_fingerprint='B')); return x.decision==m.Decision.HOLD and x.full_fallback_candidate and x.escalation==m.Escalation.FINGERPRINT_MISMATCH
 if k==12:
  x=m.evaluate(m.make_request(('1.0','2.0'),('1.0','2.0'),local_schema_fingerprint='A',remote_schema_fingerprint='B',known_compatible_fingerprint_pairs=(('A','B'),))); return x.decision==m.Decision.ALLOW and str(x.negotiated_version)=='2.0'
 if k==13:
  x=m.evaluate(m.make_request(('1.0','1.5','2.0'),('1.0','1.5','2.0'),minimum_version='1.5')); return tuple(map(str,x.common_versions))==('1.5','2.0') and str(x.negotiated_version)=='2.0'
 if k==14:
  x=m.evaluate(m.make_request(('1.0',),('1.0',),minimum_version='2.0')); return x.decision==m.Decision.HOLD and x.escalation==m.Escalation.NO_COMMON_VERSION
 if k==15:
  q=m.default_request(); return prepared(q)==m.evaluate(q)
 if k==16:
  q=m.default_request(); x=prepared(q,False); return x.decision==m.Decision.HOLD and x.escalation==m.Escalation.PREPARED_STATE_STALE and x.full_fallback_candidate and not x.next_gate_candidate
 if k==17:
  q=m.default_request(); st=m.prepare_state(q); x=m.evaluate_prepared(st,integrity_validated=True,current_request_fingerprint='0'*64,current_result_fingerprint=st.result_fingerprint,current_local_manifest_fingerprint=st.local_manifest_fingerprint,current_remote_manifest_fingerprint=st.remote_manifest_fingerprint,current_requirement_fingerprint=st.requirement_fingerprint,current_request=q); return x.decision==m.Decision.HOLD and x.escalation==m.Escalation.PREPARED_STATE_STALE
 if k==18:
  a=m.build_manifest('C',('1.0','1.1'),'S','F'); b=m.build_manifest('C',('1.1','2.0'),'S','F','EPOCH-2'); d=m.make_delta(a,b); return tuple(map(str,d.added_versions))==('2.0',) and tuple(map(str,d.removed_versions))==('1.0',)
 if k==19:
  a=m.build_manifest('C',('1.0',),'S','F'); b=m.build_manifest('C',('1.0','2.0'),'S','F','EPOCH-2'); p=m.plan_missing_only(a,b); return p.missing_or_changed_record_ids==('SUPPORTED_VERSIONS',) and p.metadata_bytes_required>0 and not p.full_resend_required
 if k==20:
  a=m.build_manifest('C',('1.0',),'S','F'); b=m.build_manifest('C',('1.0',),'S2','F2'); p=m.plan_missing_only(a,b); return p.full_resend_required and p.missing_or_changed_record_ids==('FULL_SCHEMA_MANIFEST',)
 if k==21:
  a=m.build_manifest('A',('1.0',),'S','F'); b=m.build_manifest('B',('1.0',),'S','F'); p=m.plan_missing_only(a,b); return p.full_resend_required and p.missing_or_changed_record_ids==('FULL_VERSION_MANIFEST',)
 if k==22:
  a=m.default_evaluation(); b=m.default_evaluation(); return a==b and m._canon(a)==m._canon(b)
 if k==23:
  x=m.evaluate(m.make_request(('1.0','3.0'),('1.0','2.0'))); return str(x.negotiated_version)=='1.0' and all(str(x.negotiated_version) in {str(v) for v in q} for q in (m.default_request().local.supported_versions,m.default_request().local.supported_versions))
 if k==24:
  try: m.build_manifest('',('1.0',),'S','F'); return False
  except ValueError: return True
 if k==25:
  try: m.build_requirement('S','S','','F'); return False
  except ValueError: return True
 if k==26:
  try: m.build_requirement('S','S','A','B',known_compatible_fingerprint_pairs=(('A',),)); return False
  except ValueError: return True
 if k==27:
  q=m.default_request(); forged=replace(q.local,supported_versions=(m.Version(-1,0),)); x=m.evaluate(replace(q,local=forged)); return x.decision==m.Decision.DENY and x.engine_state==m.EngineState.INVALID_VERSION_MANIFEST
 if k==28:
  x=m.default_evaluation(); return x.compatibility_requirement_satisfied and x.schema_id_match and x.schema_fingerprint_compatible
 if k==29:
  x=m.default_evaluation(); return str(x.negotiated_version) in {str(v) for v in m.default_request().local.supported_versions} and str(x.negotiated_version) in {str(v) for v in m.default_request().remote.supported_versions}
 if k==30:
  q=m.default_request(); st=m.prepare_state(q); changed=m.make_request(remote_supported_versions=('1.1',)); x=m.evaluate_prepared(st,integrity_validated=True,current_request_fingerprint=st.request_fingerprint,current_result_fingerprint=st.result_fingerprint,current_local_manifest_fingerprint=st.local_manifest_fingerprint,current_remote_manifest_fingerprint=st.remote_manifest_fingerprint,current_requirement_fingerprint=st.requirement_fingerprint,current_request=changed); return x.decision==m.Decision.HOLD and x.escalation==m.Escalation.PREPARED_STATE_STALE
 if k==31:
  x=m.default_evaluation(); return x.decision==m.Decision.ALLOW and x.next_action==m.NextAction.CONTINUE_CONNECTION_VALIDATION_CANDIDATE and not x.connection_executed and not x.permission_granted
 return False

class TestAL183(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%32,i//32))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL183,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
