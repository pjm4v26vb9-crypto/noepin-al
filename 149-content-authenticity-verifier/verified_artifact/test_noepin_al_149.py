import unittest
from dataclasses import replace
import noepin_al_149_content_authenticity_verifier as m
B='B'; E='E'
def content(text='hello', cls=m.ContentClass.POLICY, critical=True, binding=B, epoch=E): return m.ContentArtifact('C',text,cls,critical,binding,epoch)
def sig(text='hello', present=True, verified=True, signer='PUB', stale=False, binding=B, epoch=E): return m.SignatureEvidence('S',present,verified,signer,m._content_sha(text),stale,'OFFLINE',binding,epoch)
def prov(publisher='PUB', verified=True, path='registry://ok', paths=('registry://ok',), chain=('A','B'), binding=B, epoch=E): return m.ProvenanceMetadata(publisher,chain,verified,path,paths,binding,epoch)
def exp(text='hello', publisher='PUB', digest=None, binding=B, epoch=E): return m.PublisherExpectation(publisher,m._content_sha(text) if digest is None else digest,binding,epoch)
def req(c=None,s=None,p=None,x=None): return m.AuthenticityRequest('R',c or content(),s or sig(),p or prov(),x or exp(),B,E)
def neg(r):
    return (r.authenticity_promoted_to_truth,r.signature_evidence_promoted_to_publisher_authority,r.trust_adjustment_applied,
    r.quarantine_executed,r.content_used,r.policy_applied,r.tool_definition_activated,r.content_published,r.external_send_executed,
    r.external_verification_service_called,r.tool_invoked,r.policy_modified,r.trust_store_modified,r.dlp_replaced,r.authentication_replaced,
    r.encryption_replaced,r.dcsr_reconstruction_created_fact,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,
    r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.external_write_performed,
    r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success)
def prep(st): return m.evaluate_prepared(st,integrity_validated=True,current_content_fingerprint=st.content_fingerprint,current_signature_fingerprint=st.signature_fingerprint,current_provenance_fingerprint=st.provenance_fingerprint,current_expectation_fingerprint=st.expectation_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
def scenario(k,j):
    if k==0:
        r=m.evaluate(req()); return r.decision==m.Decision.ALLOW and r.authenticity_state==m.AuthenticityState.AUTHENTIC_CANDIDATE and r.trust_adjustment_candidate==2 and not any(neg(r))
    if k==1:
        r=m.evaluate(req(c=content('tampered'),s=sig('hello'),x=exp('hello'))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.HASH_MISMATCH
    if k==2:
        r=m.evaluate(req(s=sig(verified=False))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.SIGNATURE_INVALID
    if k==3:
        r=m.evaluate(req(p=prov(publisher='OTHER'))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.PUBLISHER_MISMATCH
    if k==4:
        r=m.evaluate(req(s=sig(present=False,verified=False,signer=''))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.SIGNATURE_MISSING
    if k==5:
        c=content(cls=m.ContentClass.RESEARCH,critical=False); r=m.evaluate(req(c=c,s=sig(present=False,verified=False,signer=''))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.SIGNATURE_MISSING
    if k==6:
        r=m.evaluate(req(s=sig(stale=True))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.SIGNATURE_STALE
    if k==7:
        r=m.evaluate(req(p=prov(verified=False))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.PROVENANCE_INVALID
    if k==8:
        c=content(cls=m.ContentClass.RESEARCH,critical=False); r=m.evaluate(req(c=c,p=prov(verified=False))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.PROVENANCE_INVALID
    if k==9:
        r=m.evaluate(req(p=prov(path='download://mirror'))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.ACQUISITION_PATH_MISMATCH
    if k==10:
        c=content(cls=m.ContentClass.RESEARCH,critical=False); r=m.evaluate(req(c=c,p=prov(path='download://mirror'))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.ACQUISITION_PATH_MISMATCH
    if k==11:
        r=m.evaluate(req(x=exp(digest=''))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.HASH_MISSING
    if k==12: return m.evaluate(req(c=content(binding='X'))).authenticity_state==m.AuthenticityState.INVALID
    if k==13: return m.evaluate(req(p=prov(chain=('A','A')))).authenticity_state==m.AuthenticityState.INVALID
    if k==14:
        q=req(); st=m.prepare_state(q,B,E); return prep(st)==st.result
    if k==15:
        q=req(); st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_content_fingerprint=st.content_fingerprint,current_signature_fingerprint=st.signature_fingerprint,current_provenance_fingerprint=st.provenance_fingerprint,current_expectation_fingerprint=st.expectation_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return r.authenticity_state==m.AuthenticityState.INVALID
    if k==16:
        q=req(); st=m.prepare_state(q,B,E); q2=req(c=content('changed'),s=sig('changed'),x=exp('changed')); st2=m.prepare_state(q2,B,E); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('CONTENT','SIGNATURE_EVIDENCE','PUBLISHER_EXPECTATION') and not p.full_resend_required
    if k==17:
        q=req(); st=m.prepare_state(q,B,E); q2=req(s=sig(stale=True)); st2=m.prepare_state(q2,B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('SIGNATURE_EVIDENCE',)
    if k==18:
        q=req(); st=m.prepare_state(q,B,E); q2=req(p=prov(path='registry://other',paths=('registry://ok','registry://other'))); st2=m.prepare_state(q2,B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('PROVENANCE_METADATA',)
    if k==19:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.next_action==m.NextAction.CONTINUE_USE_CANDIDATE and r.next_gate_candidate and not any(neg(r))
    return False
class TestAL149(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL149,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
