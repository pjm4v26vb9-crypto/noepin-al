from __future__ import annotations
import inspect,re,unittest
from dataclasses import replace
import noepin_al_058_ephemeral_credential as m
NOW=1_800_000_000

def base_issue(): return m.default_policy(NOW),m.default_request(NOW),m.default_records(NOW)
def base_use():
    p=m.default_policy(NOW); rec=m.default_active_record(NOW)
    r=replace(m.default_request(NOW),operation=m.CredentialOperation.USE,credential_id=rec.credential_id,requested_ttl_seconds=0)
    return p,r,(rec,)
class T(unittest.TestCase): pass

def scenario(i):
    k=i%32
    if k in {0,1,2,3,4,5,6,7,8,9,10,11,12}: p,r,rs=base_issue()
    else: p,r,rs=base_use()
    if k==0:
        x=m.evaluate(r,p,rs,now=NOW); assert x.decision is m.ControlDecision.ALLOW and x.expires_at_candidate==NOW+300 and x.automatic_revoke_candidate and not x.credential_issued and not x.permission_granted
    elif k==1:
        x=m.evaluate(replace(r,requested_ttl_seconds=901),p,rs,now=NOW); assert x.decision is m.ControlDecision.DENY and 'TTL_EXCEEDS_POLICY' in x.reasons
    elif k==2:
        x=m.evaluate(replace(r,requested_ttl_seconds=0),p,rs,now=NOW); assert x.decision is m.ControlDecision.DENY and 'TTL_REQUIRED' in x.reasons
    elif k==3:
        x=m.evaluate(replace(r,role='ADMIN'),p,rs,now=NOW); assert x.decision is m.ControlDecision.DENY and 'ROLE_NOT_ALLOWED' in x.reasons
    elif k==4:
        x=m.evaluate(replace(r,scopes=frozenset({'WRITE_RESOURCE'})),p,rs,now=NOW); assert x.decision is m.ControlDecision.DENY and 'SCOPE_NOT_ALLOWED' in x.reasons
    elif k==5:
        x=m.evaluate(replace(r,audience='API-X'),p,rs,now=NOW); assert x.decision is m.ControlDecision.DENY and 'AUDIENCE_NOT_ALLOWED' in x.reasons
    elif k==6:
        x=m.evaluate(replace(r,run_id=''),p,rs,now=NOW); assert x.decision is m.ControlDecision.DENY and 'RUN_BINDING_REQUIRED' in x.reasons
    elif k==7:
        x=m.evaluate(replace(r,task_completed=True),p,rs,now=NOW); assert x.decision is m.ControlDecision.DENY and x.automatic_revoke_candidate and x.revocation_candidate
    elif k==8:
        rec=m.default_active_record(NOW); x=m.evaluate(r,p,(rec,),now=NOW); assert x.decision is m.ControlDecision.HOLD and 'ACTIVE_MATCHING_CREDENTIAL_EXISTS' in x.reasons
    elif k==9:
        x=m.evaluate(replace(r,expected_policy_version='bad'),p,rs,now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==10:
        x=m.evaluate(r,replace(p,revoked=True),rs,now=NOW); assert x.decision is m.ControlDecision.HOLD and x.reasons[0].startswith('INVALID_REGISTRY:')
    elif k==11:
        reg=m.prepare_registry(p,rs,now=NOW); x=m.evaluate_prepared(r,p,replace(reg,registry_fingerprint='0'*64),now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==12:
        reg=m.prepare_registry(p,rs,now=NOW); x=m.evaluate_prepared(r,p,replace(reg,policy_fingerprint='0'*64),now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==13:
        x=m.evaluate(r,p,rs,now=NOW); assert x.decision is m.ControlDecision.ALLOW and 'CREDENTIAL_USE_CANDIDATE' in x.reasons and x.revocation_candidate and not x.credential_used
    elif k==14:
        x=m.evaluate(r,p,(replace(rs[0],verified=False),),now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==15:
        x=m.evaluate(r,p,(replace(rs[0],issuer_id='BAD'),),now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==16:
        x=m.evaluate(r,p,(replace(rs[0],revoked=True),),now=NOW); assert x.decision is m.ControlDecision.DENY and 'CREDENTIAL_REVOKED' in x.reasons
    elif k==17:
        x=m.evaluate(r,p,(replace(rs[0],expires_at=NOW),),now=NOW); assert x.decision is m.ControlDecision.DENY and 'CREDENTIAL_EXPIRED' in x.reasons
    elif k==18:
        x=m.evaluate(r,p,(replace(rs[0],expires_at=rs[0].issued_at+p.max_ttl_seconds+1),),now=NOW); assert x.decision is m.ControlDecision.DENY and 'CREDENTIAL_TTL_POLICY_VIOLATION' in x.reasons
    elif k==19:
        x=m.evaluate(r,p,(replace(rs[0],evidence_binding='BAD'),),now=NOW); assert x.decision is m.ControlDecision.DENY and 'EVIDENCE_BINDING_MISMATCH' in x.reasons
    elif k==20:
        x=m.evaluate(r,p,(replace(rs[0],task_id='OTHER'),),now=NOW); assert x.decision is m.ControlDecision.DENY and 'TASK_BINDING_MISMATCH' in x.reasons
    elif k==21:
        x=m.evaluate(r,p,(replace(rs[0],run_id='OTHER'),),now=NOW); assert x.decision is m.ControlDecision.DENY and 'RUN_BINDING_MISMATCH' in x.reasons
    elif k==22:
        x=m.evaluate(r,p,(replace(rs[0],subject_id='OTHER'),),now=NOW); assert x.decision is m.ControlDecision.DENY and 'SUBJECT_BINDING_MISMATCH' in x.reasons
    elif k==23:
        x=m.evaluate(r,p,(replace(rs[0],use_count=1),),now=NOW); assert x.decision is m.ControlDecision.DENY and 'USE_LIMIT_EXHAUSTED' in x.reasons
    elif k==24:
        x=m.evaluate(replace(r,task_completed=True),p,rs,now=NOW); assert x.decision is m.ControlDecision.DENY and x.automatic_revoke_candidate and not x.revocation_executed
    elif k==25:
        rr=replace(r,operation=m.CredentialOperation.REVOKE); x=m.evaluate(rr,p,rs,now=NOW); assert x.decision is m.ControlDecision.ALLOW and x.revocation_candidate and not x.revocation_executed
    elif k==26:
        rr=replace(r,operation=m.CredentialOperation.STATUS); x=m.evaluate(rr,p,rs,now=NOW); assert x.decision is m.ControlDecision.ALLOW and not x.permission_granted
    elif k==27:
        reg=m.prepare_registry(p,rs,now=NOW); x=m.evaluate(r,p,rs,now=NOW); y=m.evaluate_prepared(r,p,reg,now=NOW); assert m.canonical_json(x)==m.canonical_json(y)
    elif k==28:
        tr=rs+(replace(rs[0],credential_id='CRED-2',task_id='T2',run_id='R2',subject_id='S2',evidence_binding='B2'),); dl=m.make_registry_delta(rs,tr); out=m.apply_registry_delta(rs,dl); assert m.registry_fingerprint(out)==m.registry_fingerprint(tr)
    elif k==29:
        reg=m.prepare_registry(p,rs,now=NOW); plan=m.plan_registry_sync(rs,reg.record_fingerprints); assert not plan.missing_or_changed_credential_ids and not plan.permission_granted and not plan.credential_issue_authorized
    elif k==30:
        src=inspect.getsource(m); forbidden=[r'\bsubprocess\b',r'os\.system',r'\bsocket\b',r'\brequests\b',r'\burllib\b',r'\bPopen\b',r'\.unlink\(',r'\bshutil\b',r'\bwebbrowser\b',r'\bsmtplib\b']; assert not any(re.search(x,src) for x in forbidden)
    elif k==31:
        x=m.evaluate(r,p,rs,now=NOW); assert not x.permission_granted and not x.credential_issued and not x.credential_used and not x.revocation_executed and not x.credential_persisted and not x.authoritative_credential_state_changed and not x.task_success_proven and not x.action_success

for i in range(160):
    def make(n):
        def test(self): scenario(n)
        test.__name__=f'test_case_{n:03d}'; return test
    setattr(T,f'test_case_{i:03d}',make(i))
if __name__=='__main__': unittest.main(verbosity=1)
