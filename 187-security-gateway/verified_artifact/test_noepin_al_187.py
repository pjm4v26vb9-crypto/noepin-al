from dataclasses import replace
import unittest
import noepin_al_187_security_gateway as m

DREQ=m.default_request(); DPOL=m.default_policy(); DDYN=m.default_dynamic()

def ok_false(r): return all(not getattr(r,n) for n in m.FALSE_FIELDS) and not r.authoritative

def scenario(k,round_no):
    req=replace(DREQ,request_id=f'REQ-{round_no}-{k}',nonce=f'n-{round_no}-{k}',now_ms=1_000_000+round_no)
    pol=DPOL; dyn=DDYN
    if k==0:
        r=m.evaluate(req,pol,dyn); return r.decision==m.Decision.ALLOW and r.next_gate_candidate and r.permit_candidate_bound and ok_false(r)
    if k==1: return m.evaluate(replace(req,request_id=''),pol,dyn).escalation==m.Escalation.MISSING_FIELD
    if k==2: return m.evaluate(replace(req,api_key='bad'),pol,dyn).decision==m.Decision.DENY
    if k==3: return m.evaluate(replace(req,principal_id='other'),pol,dyn).escalation==m.Escalation.AUTHENTICATION_FAILED
    if k==4: return m.evaluate(req,replace(pol,allowed_actions=()),dyn).escalation==m.Escalation.ROLE_POLICY_MISSING
    if k==5: return m.evaluate(req,pol,replace(dyn,seen_nonces=(req.nonce,))).escalation==m.Escalation.REPLAY_DETECTED
    if k==6: return m.evaluate(req,pol,replace(dyn,requests_in_window=10)).escalation==m.Escalation.RATE_LIMIT
    if k==7: return m.evaluate(replace(req,action='tool.delete'),pol,dyn).escalation==m.Escalation.ACTION_SCOPE
    if k==8: return m.evaluate(replace(req,target='workspace://other/item'),pol,dyn).escalation==m.Escalation.TARGET_SCOPE
    if k==9: return m.evaluate(replace(req,parameters=(('secret','x'),)),pol,dyn).escalation==m.Escalation.PARAMETER_SCOPE
    if k==10: return m.evaluate(req,pol,replace(dyn,semantic_decision='DENY')).escalation==m.Escalation.SEMANTIC_DENY
    if k==11: return m.evaluate(req,pol,replace(dyn,semantic_decision='HOLD')).escalation==m.Escalation.SEMANTIC_HOLD
    if k==12: return m.evaluate(req,pol,replace(dyn,semantic_decision='MAYBE')).escalation==m.Escalation.SEMANTIC_UNKNOWN
    if k==13:
        wr=replace(req,action='tool.write'); r=m.evaluate(wr,pol,dyn); return r.decision==m.Decision.HUMAN_APPROVAL and r.human_approval_required and not r.human_approval_evidence_match and ok_false(r)
    if k==14:
        wr=replace(req,action='tool.write'); bd=m.approval_binding_fingerprint(wr); dy=replace(dyn,human_approval_id='APR-1',approval_request_fingerprint=bd,approval_valid=True); r=m.evaluate(wr,pol,dy); return r.decision==m.Decision.ALLOW and r.human_approval_evidence_match and not r.human_approval_executed and not r.permission_granted
    if k==15:
        wr=replace(req,action='tool.write'); dy=replace(dyn,human_approval_id='APR-1',approval_request_fingerprint='bad',approval_valid=True); return m.evaluate(wr,pol,dy).escalation==m.Escalation.APPROVAL_BINDING_MISMATCH
    if k==16:
        r=m.evaluate(req,pol,dyn); return m.validate_permit_candidate(r,req,pol,dyn)
    if k==17:
        r=m.evaluate(req,pol,dyn); return not m.validate_permit_candidate(r,replace(req,target=req.target+'x'),pol,dyn)
    if k==18:
        r=m.evaluate(req,pol,dyn); return not m.validate_permit_candidate(r,replace(req,now_ms=r.permit_candidate_expiry_ms+1),pol,dyn)
    if k==19:
        r=m.evaluate(req,pol,dyn); dy=replace(dyn,used_permit_candidate_ids=(r.permit_candidate_id,)); return m.evaluate(req,pol,dy).escalation==m.Escalation.PERMIT_CANDIDATE_INVALID
    if k==20:
        a=m.evaluate(req,pol,dyn); b=m.evaluate(req,pol,dyn); return m.fingerprint(a)==m.fingerprint(b)
    if k==21:
        s=m.prepare_state(req,pol,dyn); r=m.evaluate_prepared(s,integrity_validated=True,current_request=req,current_policy=pol,current_dynamic=dyn,current_result_fingerprint=s.result_fingerprint,current_integrity_fingerprint=s.integrity_fingerprint); return r.prepared_state_reused and m.fingerprint(replace(r,prepared_state_reused=False))==s.result_fingerprint
    if k==22:
        s=m.prepare_state(req,pol,dyn); r=m.evaluate_prepared(s,integrity_validated=False,current_request=req,current_policy=pol,current_dynamic=dyn,current_result_fingerprint=s.result_fingerprint,current_integrity_fingerprint=s.integrity_fingerprint); return r.escalation==m.Escalation.PREPARED_STATE_STALE
    if k==23:
        s=m.prepare_state(req,pol,dyn); nd=replace(dyn,requests_in_window=dyn.requests_in_window+1); r=m.evaluate_prepared(s,integrity_validated=True,current_request=req,current_policy=pol,current_dynamic=nd,current_result_fingerprint=s.result_fingerprint,current_integrity_fingerprint=s.integrity_fingerprint); return r.escalation==m.Escalation.PREPARED_STATE_STALE
    if k==24:
        known={'REQUEST':m.request_fingerprint(req),'POLICY':m.policy_fingerprint(pol)}; d=m.make_delta(req,pol,dyn,known); return d.reused_fields==('POLICY','REQUEST') and d.missing_or_changed_fields==('DYNAMIC_SECURITY_STATE',) and not d.full_reevaluation_required
    if k==25:
        d=m.make_delta(req,pol,dyn,{}); return len(d.missing_or_changed_fields)==3 and d.full_reevaluation_required
    if k==26:
        known={'REQUEST':m.request_fingerprint(req),'POLICY':m.policy_fingerprint(pol),'DYNAMIC_SECURITY_STATE':m.dynamic_fingerprint(dyn)}; d=m.make_delta(req,pol,dyn,known); return len(d.missing_or_changed_fields)==0 and not d.full_reevaluation_required
    if k==27: return m.request_fingerprint(req)!=m.request_fingerprint(replace(req,nonce=req.nonce+'x'))
    if k==28: return m.policy_fingerprint(pol)!=m.policy_fingerprint(replace(pol,policy_version='2'))
    if k==29: return m.dynamic_fingerprint(dyn)!=m.dynamic_fingerprint(replace(dyn,semantic_decision='HOLD'))
    if k==30: return m.approval_binding_fingerprint(req)!=m.approval_binding_fingerprint(replace(req,target=req.target+'x'))
    if k==31:
        r=m.evaluate(req,pol,replace(dyn,semantic_decision='HUMAN_APPROVAL')); return r.decision==m.Decision.HUMAN_APPROVAL
    if k==32:
        rr=replace(req,parameters=(('value','x'),('mode','metadata'))); r=m.evaluate(rr,pol,dyn); return r.decision==m.Decision.ALLOW
    if k==33:
        p=replace(pol,allowed_target_patterns=('workspace://safe/*','workspace://public/*')); return m.evaluate(replace(req,target='workspace://public/x'),p,dyn).decision==m.Decision.ALLOW
    if k==34:
        p=replace(pol,max_requests_per_window=0); return m.evaluate(req,p,dyn).escalation==m.Escalation.RATE_LIMIT
    if k==35:
        r=m.evaluate(req,pol,dyn); return r.audit_candidate_fingerprint and len(r.audit_candidate_fingerprint)==64
    if k==36:
        r=m.evaluate(req,pol,dyn); return not r.permit_issued and not r.credential_minted and not r.permission_granted
    if k==37:
        r=m.evaluate(req,pol,dyn); return not r.policy_allow_promoted_to_permission and not r.permit_candidate_promoted_to_issued
    if k==38:
        r=m.evaluate(req,pol,dyn); return not r.dcsr_bypassed_authentication and not r.dcsr_bypassed_replay and not r.dcsr_reused_human_approval
    if k==39:
        r=m.default_evaluation(); return r.decision==m.Decision.ALLOW and r.request_id=='REQ-00-A' and ok_false(r)
    return False

class TestAL187(unittest.TestCase): pass
def mk(i):
    def t(self): self.assertTrue(scenario(i%40,i//40))
    t.__name__=f'test_case_{i:03d}'; return t
for i in range(160): setattr(TestAL187,f'test_case_{i:03d}',mk(i))
if __name__=='__main__': unittest.main(verbosity=2)
