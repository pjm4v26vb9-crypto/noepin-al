import unittest
from dataclasses import replace
import noepin_al_151_capability_escrow as m
B='TEST-BINDING'; E='EPOCH-T'
def cap(cid='CAP-X',cls=m.CapabilityClass.PROD_ADMIN_API,proxy=True): return m.RequestedCapability(cid,cls,'vault-ref://x',proxy,B,E)
def cond(known=True,single=True,purpose='deploy',target='service://prod',claims=('A',)): return m.EscrowConditions('COND-X',known,single,purpose,target,claims,B,E)
def agent(verified=True,aid='AGENT-X'): return m.AgentIdentity(aid,verified,'TRUST-X',B,E)
def permit(valid=True,approved=True,cid='CAP-X',aid='AGENT-X',purpose='deploy',target='service://prod',issued=100,expires=180,nonce='N-X'):
    return m.PermitEvidence('PERMIT-X',valid,approved,cid,aid,purpose,target,issued,expires,nonce,B,E)
def policy(verified=True,allow_proxy=True,require_single=True,max_ttl=120,classes=(m.CapabilityClass.PROD_ADMIN_API,),ids=('CAP-X',)):
    return m.EscrowPolicy('POL-X',verified,allow_proxy,require_single,max_ttl,classes,ids,B,E)
def req(c=None,co=None,a=None,p=None,pol=None,direct=False,replay=False,escrow=True,now=150):
    return m.CapabilityEscrowRequest('REQ-X',c or cap(),co or cond(),a or agent(),p or permit(),pol or policy(),direct,replay,escrow,now,B,E)
def neg(r):
    return (r.secret_material_returned,r.capability_handoff_executed,r.proxy_execution_executed,r.permit_consumed,r.receipt_issued,
    r.permit_promoted_to_permission,r.escrow_grant_promoted_to_authority,r.receipt_promoted_to_action_success,r.vault_accessed,
    r.delegated_credential_issued,r.tool_invoked,r.file_write_executed,r.network_send_executed,r.policy_modified,r.permit_modified,
    r.dlp_replaced,r.authentication_replaced,r.encryption_replaced,r.dcsr_reconstruction_created_fact,r.sender_authority_inherited,
    r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,
    r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,
    r.safety_proven,r.action_success)
def prepared(st): return m.evaluate_prepared(st,integrity_validated=True,current_capability_fingerprint=st.capability_fingerprint,
    current_conditions_fingerprint=st.conditions_fingerprint,current_agent_fingerprint=st.agent_fingerprint,current_permit_fingerprint=st.permit_fingerprint,
    current_policy_fingerprint=st.policy_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
def scenario(k,j):
    if k==0:
        r=m.evaluate(req()); return r.decision==m.Decision.ALLOW and r.engine_state==m.EngineState.PROXY_EXECUTION_CANDIDATE and r.proxy_execution_candidate and r.grant_candidate_id and r.receipt_candidate_id and not any(neg(r))
    if k==1:
        r=m.evaluate(req(direct=True)); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.DIRECT_CAPABILITY_REQUEST and not r.secret_material_returned
    if k==2:
        r=m.evaluate(req(now=181)); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.PERMIT_EXPIRED and r.engine_state==m.EngineState.EXPIRED_CANDIDATE
    if k==3:
        r=m.evaluate(req(replay=True)); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.REPLAY_DETECTED and not r.permit_consumed
    if k==4:
        r=m.evaluate(req(escrow=False)); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.ESCROW_UNAVAILABLE
    if k==5:
        r=m.evaluate(req(co=cond(known=False))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.CONDITIONS_UNKNOWN
    if k==6:
        r=m.evaluate(req(co=cond(single=False))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.NOT_SINGLE_USE
    if k==7:
        r=m.evaluate(req(p=permit(valid=False))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.PERMIT_INVALID
    if k==8:
        r=m.evaluate(req(a=agent(False))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.AGENT_IDENTITY_UNVERIFIED
    if k==9:
        r=m.evaluate(req(c=cap(proxy=False))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.PROXY_UNAVAILABLE
    if k==10:
        r=m.evaluate(req(pol=policy(verified=False))); return r.decision==m.Decision.HOLD and r.escalation==m.Escalation.POLICY_UNVERIFIED
    if k==11:
        r=m.evaluate(req(pol=policy(classes=(m.CapabilityClass.SECRET_KEY_USE,)))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.CAPABILITY_NOT_ALLOWED
    if k==12:
        r=m.evaluate(req(p=permit(target='service://other'))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.PERMIT_BINDING_MISMATCH
    if k==13:
        r=m.evaluate(req(p=permit(issued=0,expires=180),pol=policy(max_ttl=120))); return r.decision==m.Decision.DENY and r.escalation==m.Escalation.TTL_POLICY_VIOLATION
    if k==14:
        q=req(); st=m.prepare_state(q,B,E); return prepared(st)==st.result
    if k==15:
        q=req(); st=m.prepare_state(q,B,E); r=m.evaluate_prepared(st,integrity_validated=False,current_capability_fingerprint=st.capability_fingerprint,current_conditions_fingerprint=st.conditions_fingerprint,current_agent_fingerprint=st.agent_fingerprint,current_permit_fingerprint=st.permit_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint); return r.engine_state==m.EngineState.INVALID
    if k==16:
        q=req(); st=m.prepare_state(q,B,E); q2=req(p=permit(nonce='N-Y')); st2=m.prepare_state(q2,B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('PERMIT',)
    if k==17:
        q=req(); st=m.prepare_state(q,B,E); q2=req(pol=policy(ids=('CAP-X','CAP-Y'))); st2=m.prepare_state(q2,B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('ESCROW_POLICY',)
    if k==18:
        q=req(); st=m.prepare_state(q,B,E); q2=req(replay=True); st2=m.prepare_state(q2,B,E); return m.plan_missing_only(st,st2).missing_or_changed_record_ids==('REQUEST_CONTEXT',)
    if k==19:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.next_action==m.NextAction.CONTINUE_PROXY_CANDIDATE and r.escalation==m.Escalation.NONE and r.engine_state==m.EngineState.PROXY_EXECUTION_CANDIDATE and r.proxy_execution_candidate and r.next_gate_candidate and not any(neg(r))
    return False
class TestAL151(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%20,i//20))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL151,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
