import unittest
from dataclasses import replace
import noepin_al_180_evidence_deficiency_request_protocol as m
NEG=('evidence_promoted_to_truth','accepted_response_promoted_to_truth','allowed_source_promoted_to_trust','allowed_source_promoted_to_authority','evidence_id_promoted_to_provenance_validity','closed_request_promoted_to_parent_decision_allow','closed_request_promoted_to_hold_release','dcsr_invented_evidence','dcsr_widened_allowed_sources','dcsr_closed_unresolved_claim','permission_granted','policy_decision_executed','approval_executed','human_approval_executed','permit_issued','tool_invoked','action_executed','action_success','stop_executed','file_write_executed','network_send_executed','external_write_performed','authoritative_state_created','cached_state_promoted','reconstructed_state_promoted','partial_state_promoted','dcsr_reconstruction_created_fact','sender_authority_inherited','sender_intent_inherited','sender_agreement_inherited','authority_granted','world_truth_proven','domain_authority_promoted','safety_proven')
def scenario(k,round_no):
 if k==0:
  r=m.build_request(' R ',' D ',(' claim one ','claim two'),(' system record ','signed_record')); return r.status==m.RequestStatus.OPEN and r.missing_claims==('claim one','claim two') and r.allowed_source_types==('SYSTEM_RECORD','SIGNED_RECORD')
 if k==1:
  r=m.build_request('R','D',('a','b'),('S',)); nr,x=m.apply_response(m.make_response_request(r,m.EvidenceResponse('a','s','E1'))); return x.response_accepted and m.pending_claims(nr)==('b',) and not x.closed
 if k==2:
  r=m.build_request('R','D',('a','b'),('S',)); nr,x=m.apply_response(m.make_response_request(r,m.EvidenceResponse('a','S','E1'),True)); return x.decision==m.Decision.DENY and x.escalation==m.Escalation.CLOSE_WITH_PENDING_CLAIMS and nr==r
 if k==3:
  r=m.build_request('R','D',('a',),('S',)); nr,x=m.apply_response(m.make_response_request(r,m.EvidenceResponse('a','S','E1'),True)); return x.closed and nr.status==m.RequestStatus.CLOSED and not m.pending_claims(nr)
 if k==4:
  r=m.default_closed_request(); x=m.evaluate_response(m.make_response_request(r,m.EvidenceResponse('authorization scope current','HUMAN_PROVIDED_RECORD','E4'))); return x.decision==m.Decision.DENY and x.escalation==m.Escalation.REQUEST_ALREADY_CLOSED
 if k==5:
  r=m.build_request('R','D',('a',),('S',)); x=m.evaluate_response(m.make_response_request(r,m.EvidenceResponse('b','S','E1'))); return x.escalation==m.Escalation.UNREQUESTED_CLAIM and not x.response_accepted
 if k==6:
  r=m.build_request('R','D',('a',),('S',)); x=m.evaluate_response(m.make_response_request(r,m.EvidenceResponse('a','T','E1'))); return x.escalation==m.Escalation.SOURCE_TYPE_NOT_ALLOWED and not x.source_allowed
 if k==7:
  r=m.build_request('R','D',('a',),('S',)); x=m.evaluate_response(m.make_response_request(r,m.EvidenceResponse('a','S','   '))); return x.escalation==m.Escalation.EVIDENCE_ID_MISSING and not x.evidence_id_present
 if k==8:
  try: m.build_request('R','D',(),('S',)); return False
  except ValueError: return True
 if k==9:
  try: m.build_request('R','D',('a',),()); return False
  except ValueError: return True
 if k==10:
  try: m.build_request('R','D',('a',' a '),('S',)); return False
  except ValueError: return True
 if k==11:
  r=m.build_request('R','D',('a',),('S',)); r,_=m.apply_response(m.make_response_request(r,m.EvidenceResponse('a','S','E1'))); x=m.evaluate_response(m.make_response_request(r,m.EvidenceResponse('a','S','E2'))); return x.escalation==m.Escalation.CLAIM_ALREADY_RESOLVED
 if k==12:
  r=m.default_open_request(); bad=replace(r,request_fingerprint='0'*64); x=m.evaluate_response(m.make_response_request(bad,m.EvidenceResponse('authorization scope current','HUMAN_PROVIDED_RECORD','E3'),True)); return x.decision==m.Decision.DENY and x.escalation==m.Escalation.REQUEST_FINGERPRINT_MISMATCH
 if k==13:
  q=m.default_response_request(); st=m.prepare_state(q,q.binding,q.state_epoch); x=m.evaluate_prepared(st,integrity_validated=True,current_deficiency_fingerprint=st.deficiency_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint); return x==st.result and x.closed
 if k==14:
  q=m.default_response_request(); st=m.prepare_state(q,q.binding,q.state_epoch); x=m.evaluate_prepared(st,integrity_validated=False,current_deficiency_fingerprint=st.deficiency_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint); return x.engine_state==m.EngineState.INVALID and not x.response_accepted
 if k==15:
  old=m.default_open_request(); new=m.default_closed_request(); p=m.plan_missing_only(old,new); return p.missing_or_changed_record_ids==('CLAIM:authorization scope current','REQUEST_STATUS') and not p.full_resend_required
 if k==16:
  old=m.default_open_request(); new=m.default_closed_request(); d=m.make_delta(old,new); return d.accepted_response_records_added==('CLAIM:authorization scope current',) and d.close_state_changed
 if k==17:
  r=m.default_open_request(); r,_=m.apply_response(m.default_response_request()); return r.status==m.RequestStatus.CLOSED and m.close_request(r)==r
 if k==18:
  r=m.default_open_request();
  try: m.close_request(r); return False
  except ValueError: return True
 if k==19:
  a=m.default_evaluation(); b=m.default_evaluation(); return a==b and m._canon(a)==m._canon(b) and a.next_gate_candidate and not any(getattr(a,n) for n in NEG)
 return False
class TestAL180(unittest.TestCase): pass
def mk(i):
 def t(self): self.assertTrue(scenario(i%20,i//20))
 t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL180,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
