import unittest
from dataclasses import replace
import noepin_al_186_distributed_common_state_reconstruction_v1 as m

def safe_false(r): return all(not getattr(r,x) for x in m._FALSE_FIELDS)
def rec(rid,val=1,**kw): return m.make_record(rid,f'al://{rid}',val,kw.pop('payload_bytes',100),**kw)
def mani(node,*rs,schema='1'): return m.make_manifest(node,tuple(rs),schema)
D=m.default_request()

def scenario(k,j):
 r=m.default_evaluation()
 if k==0: return r.decision==m.Decision.ALLOW and r.next_action==m.NextAction.REMOTE_LAZY_MATERIALIZATION_CANDIDATE and r.lazy_record_ids==('D',)
 if k==1: return r.shared_record_ids==('A','B','C') and r.delta_record_ids==()
 if k==2: return r.shared_ratio==0.75 and r.full_payload_bytes==460000
 if k==3: return r.delta_payload_bytes>0 and r.delta_payload_bytes<r.full_payload_bytes
 if k==4: return r.final_validation_required and not r.final_validation_passed and not r.reconstructed_complete
 if k==5: return not r.authoritative and safe_false(r)
 if k==6:
  q=D; final=m.make_manifest('final',q.sender.records); z=m.validate_final(q,final); return z.final_validation_passed and z.reconstructed_complete and not z.authoritative
 if k==7:
  q=D; final=m.make_manifest('final',q.sender.records[:-1]); z=m.validate_final(q,final); return z.decision==m.Decision.HOLD and z.escalation==m.Escalation.PARTIAL_STATE
 if k==8:
  s=mani('s',rec('A')); rr=replace(rec('A'),schema_version='2'); q=m.ReconstructionRequest('x',s,mani('r',rr)); z=m.evaluate(q); return z.escalation==m.Escalation.SCHEMA_MISMATCH and z.full_transfer_candidate
 if k==9:
  a=rec('A',authority='domain://a'); b=rec('A',authority='domain://b'); z=m.evaluate(m.ReconstructionRequest('x',mani('s',a),mani('r',b))); return z.escalation==m.Escalation.AUTHORITY_MISMATCH
 if k==10:
  a=rec('A',dependencies=('x',)); b=rec('A',dependencies=('y',)); z=m.evaluate(m.ReconstructionRequest('x',mani('s',a),mani('r',b))); return z.escalation==m.Escalation.DEPENDENCY_MISMATCH
 if k==11:
  a=rec('A',1); b=rec('A',2); z=m.evaluate(m.ReconstructionRequest('x',mani('s',a),mani('r',b),network=m.NetworkCondition(min_shared_ratio_for_dcsr=0))); return z.delta_record_ids==('A',) and z.next_action==m.NextAction.REQUEST_DELTA_CANDIDATE
 if k==12:
  a=rec('A',1,prepared=True); z=m.evaluate(m.ReconstructionRequest('x',mani('s',a),mani('r'))); return z.lazy_record_ids==('A',)
 if k==13:
  a=rec('A',1,generator=True); z=m.evaluate(m.ReconstructionRequest('x',mani('s',a),mani('r'))); return z.engine_state==m.EngineState.REMOTE_LAZY_CANDIDATE
 if k==14:
  a=rec('A',1,prepared=True); z=m.evaluate(m.ReconstructionRequest('x',mani('s',a),mani('r'),allow_remote_lazy=False)); return z.delta_record_ids==('A',)
 if k==15:
  s=mani('s',rec('A'),rec('B'),rec('C')); rr=mani('r',rec('A',9)); q=m.ReconstructionRequest('x',s,rr,network=m.NetworkCondition(min_shared_ratio_for_dcsr=.5)); z=m.evaluate(q); return z.escalation==m.Escalation.LOW_SHARED_RATIO and z.full_transfer_candidate
 if k==16:
  q=replace(D,network=m.NetworkCondition(bandwidth_bytes_per_sec=0)); return m.evaluate(q).decision==m.Decision.DENY
 if k==17:
  q=replace(D,integrity_validated=False); return m.evaluate(q).decision==m.Decision.DENY and m.evaluate(q).escalation==m.Escalation.INVALID_INPUT
 if k==18:
  q=D; st=m.prepare_state(q); z=m.evaluate_prepared(st,integrity_validated=True,current_request_fingerprint=st.request_fingerprint,current_result_fingerprint=st.result_fingerprint,current_integrity_fingerprint=st.integrity_fingerprint,current_request=q); return z.prepared_state_reused and z.final_candidate_fingerprint==r.final_candidate_fingerprint
 if k==19:
  q=D; st=m.prepare_state(q); z=m.evaluate_prepared(st,integrity_validated=False,current_request_fingerprint=st.request_fingerprint,current_result_fingerprint=st.result_fingerprint,current_integrity_fingerprint=st.integrity_fingerprint,current_request=q); return z.decision==m.Decision.HOLD and z.escalation==m.Escalation.PREPARED_STATE_STALE
 if k==20:
  q=D; st=m.prepare_state(q); q2=replace(q,allow_remote_lazy=False); z=m.evaluate_prepared(st,integrity_validated=True,current_request_fingerprint=st.request_fingerprint,current_result_fingerprint=st.result_fingerprint,current_integrity_fingerprint=st.integrity_fingerprint,current_request=q2); return z.escalation==m.Escalation.PREPARED_STATE_STALE
 if k==21:
  d=m.make_delta(D); return d.requested_record_ids==() and d.lazy_record_ids==('D',) and d.reused_record_ids==('A','B','C') and not d.full_resend_required
 if k==22:
  p=m.plan_missing_only(D); return p.missing_or_changed_record_ids==('LAZY:D',) and not p.full_resend_required
 if k==23:
  s=mani('s',rec('A',1)); rr=mani('r',rec('A',2)); p=m.plan_missing_only(m.ReconstructionRequest('x',s,rr,network=m.NetworkCondition(min_shared_ratio_for_dcsr=0))); return p.missing_or_changed_record_ids==('RECORD:A',)
 if k==24:
  a=rec('A'); s=mani('s',a); rr=mani('r',a); z=m.evaluate(m.ReconstructionRequest('x',s,rr)); return z.next_action==m.NextAction.REUSE_SHARED_STATE_CANDIDATE and z.reconstructed_complete
 if k==25:
  a=rec('A'); s=mani('s',a); rr=mani('r',a); q=m.ReconstructionRequest('x',s,rr); z=m.validate_final(q,rr); return z.final_validation_passed and z.final_candidate_fingerprint==s.manifest_fingerprint
 if k==26:
  a=rec('A'); bad=replace(a,content_fingerprint='0'*64); q=m.ReconstructionRequest('x',mani('s',a),mani('r')); z=m.validate_final(q,mani('f',bad)); return z.escalation==m.Escalation.FINGERPRINT_MISMATCH
 if k==27:
  a=rec('A'); bad=replace(a,authority_reference='domain://bad'); q=m.ReconstructionRequest('x',mani('s',a),mani('r')); return m.validate_final(q,mani('f',bad)).escalation==m.Escalation.AUTHORITY_MISMATCH
 if k==28:
  a=rec('A',dependencies=('x',)); bad=replace(a,dependency_fingerprint=m.dependency_fingerprint(('y',))); q=m.ReconstructionRequest('x',mani('s',a),mani('r')); return m.validate_final(q,mani('f',bad)).escalation==m.Escalation.DEPENDENCY_MISMATCH
 if k==29:
  q=replace(D,receiver=replace(D.receiver,schema_version='2')); return m.evaluate(q).escalation==m.Escalation.SCHEMA_MISMATCH
 if k==30:
  try: m.make_manifest('x',(rec('A'),rec('A'))); return False
  except ValueError: return True
 if k==31:
  try: m.make_record('', 'x', 1, 2); return False
  except ValueError: return True
 if k==32:
  q=D; a=m.evaluate(q); b=m.evaluate(q); return m._canon(a)==m._canon(b)
 if k==33:
  q=D; d1=m.make_delta(q); d2=m.make_delta(q); return d1.fingerprint==d2.fingerprint
 if k==34:
  return m.payload_fingerprint({'b':2,'a':1})==m.payload_fingerprint({'a':1,'b':2})
 if k==35:
  return m.dependency_fingerprint(('b','a'))==m.dependency_fingerprint(('a','b'))
 if k==36:
  z=m.default_evaluation(); return not z.dcsr_invented_state and not z.dcsr_invented_fingerprint and not z.dcsr_reconstructed_unknown_without_data and not z.dcsr_removed_communication_requirement
 if k==37:
  z=m.default_evaluation(); return not z.fingerprint_match_promoted_to_authority and not z.reconstructed_state_promoted_to_authoritative and not z.partial_state_promoted_to_complete
 if k==38:
  q=replace(D,network=m.NetworkCondition(bandwidth_bytes_per_sec=10_000_000,latency_ms=1,max_chunk_bytes=1_000_000,timeout_ms=.1)); z=m.evaluate(q); return z.decision in (m.Decision.ALLOW,m.Decision.HOLD)
 if k==39:
  return m.default_request().sender.manifest_fingerprint!=m.default_request().receiver.manifest_fingerprint
 return False

class TestAL186(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%40,i//40))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL186,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
