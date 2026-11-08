from __future__ import annotations
import inspect,re,unittest
from dataclasses import replace
import noepin_al_061_logical_execution_interlock as m
NOW=1_800_000_000

def base(): return m.default_policy(NOW),m.default_request(NOW),m.default_approvals(NOW),m.default_receipts(NOW)

def approval(r, *, verified=True, independent=True, approved=True, revoked=False, binding=None, role="OWNER", observed=None, expires=None):
    return m.ApprovalEvidence("APP-1",r.request_id,role,approved,verified,independent,observed or NOW-5,expires or NOW+100,binding or r.evidence_binding,revoked)

def receipt(r,p, *, consumed=True, verified=True, revoked=False, binding=None):
    pid="PC-"+m.sha256((m.request_fingerprint(r)+m.policy_fingerprint(p)).encode("ascii")).hexdigest()[:32]
    return m.PermitReceipt(pid,r.request_id,m.request_fingerprint(r),consumed,verified,NOW-2,binding or r.evidence_binding,revoked)

class T(unittest.TestCase): pass

def scenario(i):
    k=i%32; p,r,a,rc=base()
    if k==0:
        x=m.evaluate(r,p,a,rc,now=NOW); assert x.decision is m.InterlockDecision.ALLOW and x.permit_candidate and not x.permission_granted and not x.permit_issued
    elif k==1:
        x=m.evaluate(replace(r,action="DELETE"),p,a,rc,now=NOW); assert x.decision is m.InterlockDecision.DENY and x.hard_deny_hit
    elif k==2:
        x=m.evaluate(replace(r,target="outside:/x"),p,a,rc,now=NOW); assert x.decision is m.InterlockDecision.DENY
    elif k==3:
        x=m.evaluate(replace(r,scope_fingerprint="BAD"),p,a,rc,now=NOW); assert x.decision is m.InterlockDecision.DENY
    elif k==4:
        x=m.evaluate(replace(r,privilege_elevation=True),p,a,rc,now=NOW); assert x.decision is m.InterlockDecision.DENY and 'PRIVILEGE_ELEVATION_HARD_DENY' in x.reasons
    elif k==5:
        x=m.evaluate(replace(r,sensitive_data=True,external_side_effect=True,explicit_authorization=True),p,(approval(r),),rc,now=NOW); assert x.decision is m.InterlockDecision.DENY
    elif k==6:
        x=m.evaluate(replace(r,counterfactual_available=False),p,a,rc,now=NOW); assert x.decision is m.InterlockDecision.HOLD
    elif k==7:
        x=m.evaluate(replace(r,semantic_confidence=.3),p,a,rc,now=NOW); assert x.decision is m.InterlockDecision.HOLD
    elif k==8:
        x=m.evaluate(replace(r,irreversible=True,safer_alternative_available=True),p,a,rc,now=NOW); assert x.decision is m.InterlockDecision.HOLD and x.safer_alternative_detected
    elif k==9:
        r2=replace(r,irreversible=True); x=m.evaluate(r2,p,a,rc,now=NOW); assert x.decision is m.InterlockDecision.HUMAN_APPROVAL and x.human_approval_required
    elif k==10:
        r2=replace(r,irreversible=True,explicit_authorization=True); x=m.evaluate(r2,p,(approval(r2),),rc,now=NOW); assert x.decision is m.InterlockDecision.ALLOW and x.permit_candidate
    elif k==11:
        r2=replace(r,external_side_effect=True,explicit_authorization=True); x=m.evaluate(r2,p,(approval(r2),),rc,now=NOW); assert x.decision is m.InterlockDecision.ALLOW
    elif k==12:
        x=m.evaluate(replace(r,expected_policy_version="OLD"),p,a,rc,now=NOW); assert x.decision is m.InterlockDecision.HOLD
    elif k==13:
        x=m.evaluate(replace(r,expected_authority_epoch="OLD"),p,a,rc,now=NOW); assert x.decision is m.InterlockDecision.HOLD
    elif k==14:
        x=m.evaluate(replace(r,expected_policy_id="BAD"),p,a,rc,now=NOW); assert x.decision is m.InterlockDecision.HOLD
    elif k==15:
        x=m.evaluate(replace(r,auth_verified=False),p,a,rc,now=NOW); assert x.decision is m.InterlockDecision.HOLD
    elif k==16:
        x=m.evaluate(replace(r,source_trust="UNKNOWN"),p,a,rc,now=NOW); assert x.decision is m.InterlockDecision.HOLD
    elif k==17:
        x=m.evaluate(replace(r,created_at=NOW-700,expires_at=NOW+10),p,a,rc,now=NOW); assert x.decision is m.InterlockDecision.HOLD and 'REQUEST_STALE' in x.reasons
    elif k==18:
        reg=m.prepare_registry(p,a,rc,now=NOW); x=m.evaluate_prepared(r,p,replace(reg,registry_fingerprint='0'*64),now=NOW); assert x.decision is m.InterlockDecision.HOLD
    elif k==19:
        reg=m.prepare_registry(p,a,rc,now=NOW); x=m.evaluate_prepared(r,p,replace(reg,policy_fingerprint='0'*64),now=NOW); assert x.decision is m.InterlockDecision.HOLD
    elif k==20:
        reg=m.prepare_registry(p,a,rc,now=NOW); x=m.evaluate_prepared(r,p,reg,now=NOW); y=m.evaluate(r,p,a,rc,now=NOW); assert m.canonical_json(x)==m.canonical_json(y)
    elif k==21:
        rcp=receipt(r,p); x=m.evaluate(r,p,a,(rcp,),now=NOW); assert x.decision is m.InterlockDecision.DENY and x.replay_detected and not x.action_success
    elif k==22:
        rcp=receipt(r,p,verified=False); x=m.evaluate(r,p,a,(rcp,),now=NOW); assert x.decision is m.InterlockDecision.HOLD
    elif k==23:
        src=inspect.getsource(m); forbidden=[r'\bsubprocess\b',r'os\.system',r'\bsocket\b',r'\brequests\b',r'\burllib\b',r'\bPopen\b',r'\.unlink\(',r'\bshutil\b',r'\bwebbrowser\b',r'\bsmtplib\b',r'\bopen\(']; assert not any(re.search(z,src) for z in forbidden)
    elif k==24:
        x=m.evaluate(r,p,a,rc,now=NOW); assert not x.permission_granted and not x.permit_issued and not x.permit_consumed and not x.action_executed and not x.commit_performed and not x.external_effect_performed and not x.privilege_elevated and not x.data_sent and not x.world_truth_proven and not x.safety_proven and not x.action_success
    elif k==25:
        a2=(approval(r),replace(approval(r),approval_id="APP-2")); delta=m.make_registry_delta(a,rc,a2,rc); aa,rr=m.apply_registry_delta(a,rc,delta); assert m.registry_fingerprint(aa,rr)==m.registry_fingerprint(a2,rc)
    elif k==26:
        a0=(approval(r),); a2=(replace(a0[0],approved=False),); delta=m.make_registry_delta(a0,rc,a2,rc); aa,rr=m.apply_registry_delta(a0,rc,delta); assert aa==a2 and delta.changed_approvals
    elif k==27:
        a0=(approval(r),); a2=(); delta=m.make_registry_delta(a0,rc,a2,rc); aa,rr=m.apply_registry_delta(a0,rc,delta); assert aa==() and delta.removed_approval_ids==(a0[0].approval_id,)
    elif k==28:
        a0=(approval(r),); a2=(replace(a0[0],approved=False),); delta=m.make_registry_delta(a0,rc,a2,rc)
        try: m.apply_registry_delta((),rc,delta); assert False
        except ValueError as e: assert 'DELTA_WRONG_BASE' in str(e)
    elif k==29:
        a0=(approval(r),); reg=m.prepare_registry(p,a0,rc,now=NOW); plan=m.plan_registry_sync(a0,rc,dict(reg.approval_fingerprints),dict(reg.receipt_fingerprints)); assert not plan.missing_or_changed_approval_ids and not plan.full_resend_required and not plan.permission_granted
    elif k==30:
        a0=(approval(r),); reg=m.prepare_registry(p,a0,rc,now=NOW); rem=dict(reg.approval_fingerprints); rem['APP-1']='0'*64; plan=m.plan_registry_sync(a0,rc,rem,dict(reg.receipt_fingerprints)); assert plan.missing_or_changed_approval_ids==('APP-1',) and not plan.action_execution_authorized
    elif k==31:
        r2=replace(r,irreversible=True,explicit_authorization=True); bad=(approval(r2,verified=False),); x=m.evaluate(r2,p,bad,rc,now=NOW); assert x.decision is m.InterlockDecision.HUMAN_APPROVAL and not x.permit_candidate

for i in range(160):
    def make(n):
        def test(self): scenario(n)
        test.__name__=f'test_case_{n:03d}'; return test
    setattr(T,f'test_case_{i:03d}',make(i))
if __name__=='__main__': unittest.main(verbosity=1)
