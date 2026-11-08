from __future__ import annotations
import inspect,re,unittest
from dataclasses import replace
import noepin_al_053_change_version_control as m
NOW=1_800_000_000

def base():
    p=m.default_policy(NOW); r=m.default_request(NOW); v,a,b=m.default_registry(NOW); return p,r,v,a,b

class T(unittest.TestCase): pass

def scenario(i):
    k=i%20; p,r,v,a,b=base()
    if k==0:
        x=m.evaluate(r,p,v,a,b,now=NOW); assert x.decision is m.ControlDecision.ALLOW and x.rollback_ready_candidate and not x.permission_granted and not x.change_committed and not x.deployment_executed
    elif k==1:
        rr=replace(r,parent_fingerprint=m.fingerprint(('wrong-parent',i))); x=m.evaluate(rr,p,v,a,b,now=NOW); assert x.decision is m.ControlDecision.DENY and 'PARENT_FINGERPRINT_MISMATCH' in x.reasons
    elif k==2:
        rr=replace(r,current_version='0.9.0'); x=m.evaluate(rr,p,v,a,b,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'CURRENT_VERSION_MISMATCH' in x.reasons
    elif k==3:
        rr=replace(r,current_fingerprint=m.fingerprint(('bad-current',i))); x=m.evaluate(rr,p,v,a,b,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'CURRENT_FINGERPRINT_MISMATCH' in x.reasons
    elif k==4:
        rr=replace(r,proposed_fingerprint=r.current_fingerprint); x=m.evaluate(rr,p,v,a,b,now=NOW); assert x.decision is m.ControlDecision.DENY and 'NO_EFFECTIVE_VERSION_CHANGE' in x.reasons
    elif k==5:
        x=m.evaluate(r,p,v,(),b,now=NOW); assert x.decision is m.ControlDecision.HUMAN_APPROVAL and x.human_review_candidate and 'REQUIRED_APPROVAL_ROLE_MISSING' in x.reasons
    elif k==6:
        bad=(replace(a[0],approved=False),); x=m.evaluate(r,p,v,bad,b,now=NOW); assert x.decision is m.ControlDecision.DENY and 'EXPLICIT_APPROVAL_REJECTION' in x.reasons
    elif k==7:
        x=m.evaluate(r,p,v,a,(),now=NOW); assert x.decision is m.ControlDecision.HOLD and 'VALID_ROLLBACK_POINT_REQUIRED' in x.reasons
    elif k==8:
        bad=(replace(b[0],revoked=True),); x=m.evaluate(r,p,v,a,bad,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'VALID_ROLLBACK_POINT_REQUIRED' in x.reasons
    elif k==9:
        rr=replace(r,expected_policy_version='bad'); x=m.evaluate(rr,p,v,a,b,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'POLICY_VERSION_MISMATCH' in x.reasons
    elif k==10:
        rr=replace(r,component_type='UNSUPPORTED'); x=m.evaluate(rr,p,v,a,b,now=NOW); assert x.decision is m.ControlDecision.DENY and 'COMPONENT_TYPE_NOT_ALLOWED' in x.reasons
    elif k==11:
        reg=m.prepare_registry(p,v,a,b,now=NOW); x=m.evaluate(r,p,v,a,b,now=NOW); y=m.evaluate_prepared(r,p,reg,now=NOW); assert m.canonical_json(x)==m.canonical_json(y)
    elif k==12:
        reg=m.prepare_registry(p,v,a,b,now=NOW); bad=replace(reg,registry_fingerprint='0'*64); x=m.evaluate_prepared(r,p,bad,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'PREPARED_REGISTRY_FINGERPRINT_MISMATCH' in x.reasons
    elif k==13:
        nv=(replace(v[0],active=False),m.VersionRecord('VER-053-B',r.component_id,r.component_type,r.proposed_version,r.proposed_fingerprint,r.parent_fingerprint,NOW,r.evidence_binding,True,False))
        d=m.make_registry_delta(v,a,b,nv,a,b); rv,ra,rb=m.apply_registry_delta(v,a,b,d); assert m.registry_fingerprint(rv,ra,rb)==m.registry_fingerprint(nv,a,b)
    elif k==14:
        d=m.make_registry_delta(v,a,b,v,a,b); bad=replace(d,base_fingerprint='f'*64)
        try: m.apply_registry_delta(v,a,b,bad); raise AssertionError('expected')
        except ValueError: pass
    elif k==15:
        known={**{'version:'+x.record_id:m.fingerprint(x) for x in v},**{'approval:'+x.approval_id:m.fingerprint(x) for x in a},**{'rollback:'+x.rollback_id:m.fingerprint(x) for x in b}}
        s=m.plan_registry_sync(v,a,b,known); assert s.missing_or_changed_version_ids==() and s.missing_or_changed_approval_ids==() and s.missing_or_changed_rollback_ids==() and not s.permission_granted and not s.deployment_authorized
    elif k==16:
        assert m.registry_fingerprint(v,a,b)==m.registry_fingerprint(tuple(reversed(v)),tuple(reversed(a)),tuple(reversed(b)))
    elif k==17:
        coll=v+(m.VersionRecord('COLLIDE',r.component_id,r.component_type,r.proposed_version,m.fingerprint(('other',i)),r.current_fingerprint,NOW,r.evidence_binding,False,False),)
        x=m.evaluate(r,p,coll,a,b,now=NOW); assert x.decision is m.ControlDecision.DENY and 'VERSION_COLLISION' in x.reasons
    elif k==18:
        src=inspect.getsource(m); forbidden=[r'\bsubprocess\b',r'os\.system',r'\bsocket\b',r'\brequests\b',r'\burllib\b',r'\bPopen\b',r'\.unlink\(',r'\bshutil\b',r'\bwebbrowser\b',r'\bsmtplib\b']; assert not any(re.search(x,src) for x in forbidden)
    elif k==19:
        x=m.evaluate(r,p,v,a,b,now=NOW); assert not x.permission_granted and not x.change_committed and not x.deployment_executed and not x.rollback_executed and not x.active_version_changed and not x.version_truth_proven and not x.action_success

for i in range(160):
    def make(n):
        def test(self): scenario(n)
        test.__name__=f'test_case_{n:03d}'; return test
    setattr(T,f'test_case_{i:03d}',make(i))
if __name__=='__main__': unittest.main(verbosity=1)
