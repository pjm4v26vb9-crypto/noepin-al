import unittest
from dataclasses import replace
import noepin_al_146_cross_context_leakage_detector as m
B='B'; E='E'
def ctx(cid='C1',ctype='PROJECT',ns='N1',owner='O1',**kw):
    d=dict(context_id=cid,context_type=ctype,namespace=ns,owner_ref=owner,binding=B,state_epoch=E); d.update(kw); return m.ContextRef(**d)
def bridge(**kw):
    d=dict(bridge_id='BR1',source_context_id='C1',destination_context_id='C2',allowed_labels=(m.DataLabel.SENSITIVE,),scope_verified=True,approval_evidence_valid=True,binding=B,state_epoch=E); d.update(kw); return m.BridgeEvidence(**d)
def pol(**kw):
    d=dict(policy_id='P1',verified=True,allow_public_crossing=True,allow_shared_crossing=True,shared_context_pairs=(('C1','C2'),),bridge_evidence=(),binding=B,state_epoch=E); d.update(kw); return m.AccessPolicy(**d)
def req(**kw):
    d=dict(request_id='Q',source_context=ctx('C1'),destination_context=ctx('C1'),data_labels=(m.DataLabel.INTERNAL,),access_policy=pol(),provenance_ids=('S1',),binding=B,state_epoch=E); d.update(kw); return m.CrossingRequest(**d)
def neg(r):
    return (r.crossing_decision_promoted_to_transfer,r.leak_trace_promoted_to_leak_proof,r.bridge_evidence_promoted_to_permission,r.bridge_evidence_promoted_to_approval,r.context_id_promoted_to_identity_authority,r.data_transfer_executed,r.external_send_executed,r.memory_transfer_executed,r.tool_invoked,r.policy_modified,r.dlp_replaced,r.authentication_replaced,r.encryption_replaced,r.dcsr_reconstruction_created_fact,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success)
def prep(st):
    return m.evaluate_prepared(st,integrity_validated=True,current_source_fingerprint=st.source_fingerprint,current_destination_fingerprint=st.destination_fingerprint,current_labels_fingerprint=st.labels_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_provenance_fingerprint=st.provenance_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
def scenario(k,j):
    if k==0:
        r=m.evaluate(req()); return r.decision==m.Decision.ALLOW and not r.crossing and r.engine_state==m.EngineState.SAME_CONTEXT_CANDIDATE
    if k==1:
        r=m.evaluate(req(destination_context=ctx('C2'),data_labels=(m.DataLabel.SENSITIVE,))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.UNAUTHORIZED_CROSSING
    if k==2:
        r=m.evaluate(req(destination_context=ctx('C2'),data_labels=(m.DataLabel.PUBLIC,))); return r.decision==m.Decision.ALLOW and r.crossing and not r.data_transfer_executed
    if k==3:
        r=m.evaluate(req(destination_context=ctx('C2'),data_labels=(m.DataLabel.SHARED,))); return r.decision==m.Decision.ALLOW and r.engine_state==m.EngineState.CROSS_CONTEXT_ALLOWED_CANDIDATE
    if k==4:
        r=m.evaluate(req(destination_context=ctx('C2'),data_labels=(m.DataLabel.SENSITIVE,),access_policy=pol(bridge_evidence=(bridge(),)))); return r.decision==m.Decision.ALLOW and r.bridge_candidate_id=='BR1' and not r.permission_granted
    if k==5:
        r=m.evaluate(req(destination_context=ctx('C2'),data_labels=(m.DataLabel.SENSITIVE,),access_policy=pol(bridge_evidence=(bridge(scope_verified=False),)))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.BRIDGE_REQUIRED
    if k==6:
        r=m.evaluate(req(destination_context=ctx('C2'),access_policy=pol(verified=False))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.POLICY_UNVERIFIED
    if k==7:
        r=m.evaluate(req(destination_context=ctx('UNKNOWN'),data_labels=(m.DataLabel.SENSITIVE,))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.UNKNOWN_CONTEXT
    if k==8:
        r=m.evaluate(req(destination_context=ctx('UNKNOWN'),data_labels=(m.DataLabel.PUBLIC,))); return r.decision==m.Decision.ALLOW
    if k==9:
        r=m.evaluate(req(destination_context=ctx('C2'),data_labels=(m.DataLabel.SHARED,),access_policy=pol(shared_context_pairs=()))); return r.decision==m.Decision.DENY
    if k==10:
        r=m.evaluate(req(destination_context=ctx('C2'),data_labels=(m.DataLabel.PUBLIC,),access_policy=pol(allow_public_crossing=False))); return r.decision==m.Decision.DENY
    if k==11:
        r=m.evaluate(req(destination_context=ctx('C2'),data_labels=(m.DataLabel.SECRET,),access_policy=pol(bridge_evidence=(bridge(allowed_labels=(m.DataLabel.SECRET,)),)))); return r.decision==m.Decision.ALLOW and r.required_bridge
    if k==12:
        q=req(data_labels=()); return m.evaluate(q).engine_state==m.EngineState.INVALID
    if k==13:
        q=req(source_context=ctx(binding='X')); return m.evaluate(q).engine_state==m.EngineState.INVALID
    if k==14:
        q=req(access_policy=pol(state_epoch='X')); return m.evaluate(q).engine_state==m.EngineState.INVALID
    if k==15:
        st=m.prepare_state(req(),B,E); return prep(st)==st.result
    if k==16:
        st=m.prepare_state(req(),B,E); rr=m.evaluate_prepared(st,integrity_validated=False,current_source_fingerprint=st.source_fingerprint,current_destination_fingerprint=st.destination_fingerprint,current_labels_fingerprint=st.labels_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_provenance_fingerprint=st.provenance_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return rr.engine_state==m.EngineState.INVALID
    if k==17:
        q=req(); st=m.prepare_state(q,B,E); q2=replace(q,destination_context=ctx('C2')); st2=m.prepare_state(q2,B,E); d=m.make_delta(st,st2); p=m.plan_missing_only(st,st2); return d.destination_changed and p.missing_or_changed_record_ids==('DESTINATION_CONTEXT',) and not p.full_resend_required
    if k==18:
        q=req(); st=m.prepare_state(q,B,E); q2=replace(q,access_policy=pol(allow_public_crossing=False)); st2=m.prepare_state(q2,B,E); p=m.plan_missing_only(st,st2); return p.missing_or_changed_record_ids==('ACCESS_POLICY',)
    if k==19:
        return not any(neg(m.default_evaluation()))
    return False
class TestAL146(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL146,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
