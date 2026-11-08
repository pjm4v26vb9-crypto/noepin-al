from __future__ import annotations
import inspect, re, unittest
from dataclasses import replace
import noepin_al_050_independent_safety_monitor as m

NOW=1_800_000_000

def base():
    return m.default_policy(NOW),m.default_context(),m.default_request(NOW),m.default_observations(NOW)

def obs(oid='X',severity=m.SignalSeverity.LOW,risk=.1,ind=True,selfr=False,op='READ_LOCAL',tool='FILE_READ',age=5,verified=True,revoked=False,worker='WORKER-A',task='TASK-A',plan='PLAN-A',channel='TOOL',binding='MONITOR-EVIDENCE-050'):
    return m.SafetyObservation(oid,worker,task,NOW-age,channel,'SIG-'+oid,severity,risk,tool,op,plan,binding,verified,ind,selfr,revoked)

class T(unittest.TestCase): pass

def scenario(i):
    kind=i%20; variant=i//20
    p,c,r,items=base()
    if kind==0:
        v=m.evaluate(r,p,c,items,now=NOW); assert v.decision is m.ControlDecision.ALLOW and not v.permission_granted and not v.block_executed
    elif kind==1:
        x=obs(f'H{i}',m.SignalSeverity.HIGH,.6); v=m.evaluate(r,p,c,(x,),now=NOW); assert v.decision is m.ControlDecision.HUMAN_APPROVAL and v.human_review_candidate and not v.block_candidate
    elif kind==2:
        x=obs(f'C{i}',m.SignalSeverity.CRITICAL,.9); v=m.evaluate(r,p,c,(x,),now=NOW); assert v.decision is m.ControlDecision.DENY and v.block_candidate and not v.block_executed
    elif kind==3:
        rr=replace(r,requested_tool='EXTERNAL_SEND',requested_operation='SEND_SECRET'); v=m.evaluate(rr,p,c,items,now=NOW); assert v.decision is m.ControlDecision.DENY and v.prohibited_operation_observed
    elif kind==4:
        only=(obs(f'S{i}',ind=False,selfr=True),); v=m.evaluate(r,p,c,only,now=NOW); assert v.decision is m.ControlDecision.HOLD and 'INDEPENDENT_EVIDENCE_REQUIRED' in v.reasons
    elif kind==5:
        pp=replace(p,revoked=True); v=m.evaluate(r,pp,c,items,now=NOW); assert v.decision is m.ControlDecision.HOLD and 'POLICY_REVOKED' in v.reasons
    elif kind==6:
        rr=replace(r,expected_policy_version='bad'); v=m.evaluate(rr,p,c,items,now=NOW); assert v.decision is m.ControlDecision.HOLD and 'POLICY_VERSION_MISMATCH' in v.reasons
    elif kind==7:
        cc=replace(c,evidence_verified=False); v=m.evaluate(r,p,cc,items,now=NOW); assert v.decision is m.ControlDecision.HOLD and 'CONTEXT_EVIDENCE_UNVERIFIED' in v.reasons
    elif kind==8:
        stale=(obs(f'OLD{i}',age=p.max_observation_age_seconds+10),); v=m.evaluate(r,p,c,stale,now=NOW); assert v.decision is m.ControlDecision.HOLD and 'INDEPENDENT_EVIDENCE_REQUIRED' in v.reasons
    elif kind==9:
        wrong=(obs(f'W{i}',worker='OTHER'),); v=m.evaluate(r,p,c,wrong,now=NOW); assert v.decision is m.ControlDecision.HOLD
    elif kind==10:
        prepared=m.prepare_registry(p,c,items,now=NOW); a=m.evaluate(r,p,c,items,now=NOW); b=m.evaluate_prepared(r,p,c,prepared,now=NOW); assert m.canonical_json(a)==m.canonical_json(b)
    elif kind==11:
        prepared=m.prepare_registry(p,c,items,now=NOW); bad=replace(prepared,registry_fingerprint='0'*64); v=m.evaluate_prepared(r,p,c,bad,now=NOW); assert v.decision is m.ControlDecision.HOLD and 'PREPARED_REGISTRY_FINGERPRINT_MISMATCH' in v.reasons
    elif kind==12:
        target=items+(obs(f'ADD{i}'),); d=m.make_registry_delta(items,target); rebuilt=m.apply_registry_delta(items,d); assert m.registry_fingerprint(rebuilt)==m.registry_fingerprint(target)
    elif kind==13:
        target=items+(obs(f'ADD{i}'),); d=m.make_registry_delta(items,target); bad=replace(d,base_fingerprint='f'*64)
        try: m.apply_registry_delta(items,bad); raise AssertionError('expected')
        except ValueError: pass
    elif kind==14:
        known={o.observation_id:m.fingerprint(o) for o in items}; s=m.plan_registry_sync(items,known); assert s.missing_or_changed_observation_ids==() and not s.full_resend_required and not s.permission_granted
    elif kind==15:
        assert m.registry_fingerprint(items)==m.registry_fingerprint(tuple(reversed(items)))
    elif kind==16:
        x=obs(f'R{i}',revoked=True,severity=m.SignalSeverity.CRITICAL,risk=1); v=m.evaluate(r,p,c,(x,items[0]),now=NOW); assert v.decision is m.ControlDecision.ALLOW
    elif kind==17:
        x=obs(f'U{i}',verified=False,severity=m.SignalSeverity.CRITICAL,risk=1); v=m.evaluate(r,p,c,(x,items[0]),now=NOW); assert v.decision is m.ControlDecision.ALLOW
    elif kind==18:
        src=inspect.getsource(m); forbidden=[r'\bsubprocess\b',r'os\.system',r'\bsocket\b',r'\brequests\b',r'\burllib\b',r'\bPopen\b',r'\.unlink\(',r'\bshutil\b']; assert not any(re.search(x,src) for x in forbidden)
    elif kind==19:
        v=m.evaluate(r,p,c,items,now=NOW); assert not v.observed_signal_truth_proven and not v.system_safe_proven and not v.tool_executed and not v.action_success

for i in range(160):
    def make(n):
        def test(self): scenario(n)
        test.__name__=f'test_case_{n:03d}'
        return test
    setattr(T,f'test_case_{i:03d}',make(i))

if __name__=='__main__': unittest.main(verbosity=1)
