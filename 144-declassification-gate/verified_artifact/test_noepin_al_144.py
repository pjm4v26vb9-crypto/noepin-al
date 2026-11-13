import unittest
from dataclasses import replace
import noepin_al_144_declassification_gate as m

B='B'; E='E'
def proof(**kw):
    d=dict(proof_id='P',verified=True,sanitizer_id='S',max_residual_sensitivity=0.1,target_classification=m.Classification.INTERNAL,provenance_ids=('SRC',),binding=B,state_epoch=E); d.update(kw); return m.SanitizationProof(**d)
def appr(**kw):
    d=dict(approver_id='A',authority_verified=True,permitted_from=(m.Classification.CONFIDENTIAL,m.Classification.RESTRICTED,m.Classification.SECRET),permitted_to=(m.Classification.PUBLIC,m.Classification.INTERNAL,m.Classification.CONFIDENTIAL),approval_binding='AB',binding=B,state_epoch=E); d.update(kw); return m.ApproverEvidence(**d)
def req(**kw):
    d=dict(request_id='R',data_id='D',current_classification=m.Classification.CONFIDENTIAL,requested_classification=m.Classification.INTERNAL,residual_sensitivity=0.05,sanitization_proof=proof(),approver=appr(),binding=B,state_epoch=E,provenance_ids=('SRC',)); d.update(kw); return m.DeclassificationRequest(**d)

def scenario(k,j):
    if k==0:
        r=m.evaluate(req()); return r.decision==m.Decision.ALLOW and r.engine_state==m.EngineState.DECLASSIFICATION_ALLOWED_CANDIDATE and not r.classification_mutated
    if k==1:
        r=m.evaluate(req(sanitization_proof=None)); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.PROOF_MISSING
    if k==2:
        r=m.evaluate(req(sanitization_proof=proof(verified=False))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.PROOF_INVALID
    if k==3:
        r=m.evaluate(req(residual_sensitivity=0.3)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.RESIDUAL_SENSITIVITY
    if k==4:
        r=m.evaluate(req(approver=None)); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.AUTHORITY_INVALID
    if k==5:
        r=m.evaluate(req(approver=appr(authority_verified=False))); return r.decision==m.Decision.DENY
    if k==6:
        r=m.evaluate(req(requested_classification=m.Classification.CONFIDENTIAL)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.CLASSIFICATION_INVALID
    if k==7:
        r=m.evaluate(req(current_classification=m.Classification.SECRET,requested_classification=m.Classification.PUBLIC,residual_sensitivity=0.04,sanitization_proof=proof(max_residual_sensitivity=0.05,target_classification=m.Classification.PUBLIC),approver=appr())); return r.decision==m.Decision.ALLOW
    if k==8:
        r=m.evaluate(req(current_classification=m.Classification.SECRET,requested_classification=m.Classification.PUBLIC,residual_sensitivity=0.06,sanitization_proof=proof(max_residual_sensitivity=0.05,target_classification=m.Classification.PUBLIC),approver=appr())); return r.decision==m.Decision.HOLD
    if k==9:
        r=m.evaluate(req(sanitization_proof=proof(target_classification=m.Classification.CONFIDENTIAL))); return r.escalation==m.Escalation.PROOF_INVALID
    if k==10:
        r=m.evaluate(req(approver=appr(permitted_to=(m.Classification.PUBLIC,)))); return r.escalation==m.Escalation.AUTHORITY_INVALID
    if k==11:
        r=m.evaluate(req(approver=appr(permitted_from=(m.Classification.RESTRICTED,)))); return r.escalation==m.Escalation.AUTHORITY_INVALID
    if k==12:
        r=m.evaluate(req(residual_sensitivity=1.2)); return r.engine_state==m.EngineState.INVALID
    if k==13:
        r=m.evaluate(req(sanitization_proof=proof(binding='X'))); return r.engine_state==m.EngineState.INVALID
    if k==14:
        r=m.evaluate(req(approver=appr(state_epoch='X'))); return r.engine_state==m.EngineState.INVALID
    if k==15:
        q=req(); st=m.prepare_state(q,B,E); rr=m.evaluate_prepared(st,integrity_validated=True,current_request_fingerprint=st.request_fingerprint,current_proof_fingerprint=st.proof_fingerprint,current_approver_fingerprint=st.approver_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return rr==st.result
    if k==16:
        q=req(); st=m.prepare_state(q,B,E); rr=m.evaluate_prepared(st,integrity_validated=False,current_request_fingerprint=st.request_fingerprint,current_proof_fingerprint=st.proof_fingerprint,current_approver_fingerprint=st.approver_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return rr.engine_state==m.EngineState.INVALID
    if k==17:
        q=req(); st=m.prepare_state(q,B,E); q2=replace(q,residual_sensitivity=0.04); st2=m.prepare_state(q2,B,E); d=m.make_delta(st,st2); p=m.plan_missing_only(st,st2); return d.request_changed and p.missing_or_changed_record_ids==('REQUEST_CONTEXT',) and not p.full_resend_required
    if k==18:
        q=req(); st=m.prepare_state(q,B,E); q2=replace(q,sanitization_proof=replace(q.sanitization_proof,provenance_ids=('SRC','SRC2'))); st2=m.prepare_state(q2,B,E); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('SANITIZATION_PROOF',)
    if k==19:
        r=m.default_evaluation(); neg=(r.classification_mutated,r.data_released,r.external_send_executed,r.approval_executed,r.approver_evidence_promoted_to_authority,r.sanitization_proof_promoted_to_universal_safety,r.residual_score_promoted_to_truth,r.declassification_decision_promoted_to_permission,r.tool_invoked,r.policy_modified,r.dlp_replaced,r.authentication_replaced,r.encryption_replaced,r.dcsr_reconstruction_created_fact,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success); return not any(neg)
    return False

class TestAL144(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL144,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
