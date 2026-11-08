from __future__ import annotations
import inspect,re,unittest
from dataclasses import replace
import noepin_al_057_emergency_safe_mode as m
NOW=1_800_000_000

def base(): return m.default_policy(NOW),m.default_request(NOW),m.default_signals(NOW),m.default_receipts(NOW)
class T(unittest.TestCase): pass

def scenario(i):
    k=i%32; p,r,ss,rs=base()
    if k==0:
        x=m.evaluate(r,p,ss,rs,now=NOW); assert x.decision is m.ControlDecision.ALLOW and x.mode_candidate is m.SafeMode.LOCAL_ONLY and x.network_disabled_candidate and x.local_only_candidate and not x.mode_transition_executed
    elif k==1:
        s=(replace(ss[0],severity='CRITICAL'),); x=m.evaluate(r,p,s,rs,now=NOW); assert x.decision is m.ControlDecision.ALLOW and x.mode_candidate is m.SafeMode.OFFLINE_SAFE and x.read_only_candidate and x.local_only_candidate
    elif k==2:
        s=(replace(ss[0],severity='MEDIUM',categories=frozenset({'AUTOMATION_ANOMALY'})),); x=m.evaluate(r,p,s,rs,now=NOW); assert x.decision is m.ControlDecision.HUMAN_APPROVAL and x.mode_candidate is m.SafeMode.DEGRADED
    elif k==3:
        s=(replace(ss[0],severity='LOW'),); x=m.evaluate(r,p,s,rs,now=NOW); assert x.decision is m.ControlDecision.HOLD and x.mode_candidate is m.SafeMode.NORMAL
    elif k==4:
        x=m.evaluate(replace(r,network_required=True,operation_kind='NETWORK'),p,ss,rs,now=NOW); assert x.decision is m.ControlDecision.DENY and 'NETWORK_REQUIRED_BUT_DISABLED_CANDIDATE' in x.reasons
    elif k==5:
        s=(replace(ss[0],severity='CRITICAL'),); x=m.evaluate(replace(r,write_required=True,operation_kind='WRITE'),p,s,rs,now=NOW); assert x.decision is m.ControlDecision.DENY and 'WRITE_REQUIRED_BUT_READ_ONLY_CANDIDATE' in x.reasons
    elif k==6:
        x=m.evaluate(replace(r,external_tool_required=True,operation_kind='EXTERNAL_TOOL'),p,ss,rs,now=NOW); assert x.decision is m.ControlDecision.DENY and 'EXTERNAL_TOOL_REQUIRED_BUT_DISABLED_CANDIDATE' in x.reasons
    elif k==7:
        x=m.evaluate(replace(r,automation_required=True,operation_kind='AUTOMATION'),p,ss,rs,now=NOW); assert x.decision is m.ControlDecision.DENY and 'AUTOMATION_REQUIRED_BUT_DISABLED_CANDIDATE' in x.reasons
    elif k==8:
        rec=(m.ReplayReceipt('RCPT-1',r.request_id,r.nonce,m.SafeMode.LOCAL_ONLY,NOW-5,True,r.evidence_binding,False),); x=m.evaluate(r,p,ss,rec,now=NOW); assert x.decision is m.ControlDecision.DENY and x.replay_detected and 'REPLAY_NONCE_ALREADY_USED' in x.reasons
    elif k==9:
        rec=(m.ReplayReceipt('RCPT-1',r.request_id,r.nonce,m.SafeMode.LOCAL_ONLY,NOW-5,False,r.evidence_binding,False),); x=m.evaluate(r,p,ss,rec,now=NOW); assert x.decision is m.ControlDecision.ALLOW and not x.replay_detected
    elif k==10:
        rec=(m.ReplayReceipt('RCPT-1',r.request_id,r.nonce,m.SafeMode.LOCAL_ONLY,NOW-5,True,r.evidence_binding,True),); x=m.evaluate(r,p,ss,rec,now=NOW); assert x.decision is m.ControlDecision.ALLOW and not x.replay_detected
    elif k==11:
        rec=(m.ReplayReceipt('RCPT-1',r.request_id,r.nonce,m.SafeMode.LOCAL_ONLY,NOW-p.max_receipt_age_seconds-1,True,r.evidence_binding,False),); x=m.evaluate(r,p,ss,rec,now=NOW); assert x.decision is m.ControlDecision.ALLOW and not x.replay_detected
    elif k==12:
        rec=(m.ReplayReceipt('RCPT-1',r.request_id,r.nonce,m.SafeMode.LOCAL_ONLY,NOW-5,True,'WRONG',False),); x=m.evaluate(r,p,ss,rec,now=NOW); assert x.decision is m.ControlDecision.ALLOW and not x.replay_detected
    elif k==13:
        x=m.evaluate(r,p,(),rs,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'NO_ACTIVE_INDEPENDENT_SIGNAL' in x.reasons
    elif k==14:
        x=m.evaluate(r,p,(replace(ss[0],verified=False),),rs,now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==15:
        x=m.evaluate(r,p,(replace(ss[0],independent=False),),rs,now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==16:
        x=m.evaluate(r,p,(replace(ss[0],observed_at=NOW-p.max_signal_age_seconds-1),),rs,now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==17:
        x=m.evaluate(r,p,(replace(ss[0],evidence_binding='WRONG'),),rs,now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==18:
        x=m.evaluate(r,p,(replace(ss[0],revoked=True),),rs,now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==19:
        x=m.evaluate(replace(r,expected_policy_version='bad'),p,ss,rs,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'POLICY_VERSION_MISMATCH' in x.reasons
    elif k==20:
        x=m.evaluate(r,replace(p,revoked=True),ss,rs,now=NOW); assert x.decision is m.ControlDecision.HOLD and x.reasons[0].startswith('INVALID_REGISTRY:')
    elif k==21:
        reg=m.prepare_registry(p,ss,rs,now=NOW); x=m.evaluate_prepared(r,p,replace(reg,registry_fingerprint='0'*64),now=NOW); assert x.decision is m.ControlDecision.HOLD and 'PREPARED_REGISTRY_FINGERPRINT_MISMATCH' in x.reasons
    elif k==22:
        reg=m.prepare_registry(p,ss,rs,now=NOW); x=m.evaluate_prepared(r,p,replace(reg,policy_fingerprint='0'*64),now=NOW); assert x.decision is m.ControlDecision.HOLD and 'PREPARED_POLICY_FINGERPRINT_MISMATCH' in x.reasons
    elif k==23:
        reg=m.prepare_registry(p,ss,rs,now=NOW); x=m.evaluate(r,p,ss,rs,now=NOW); y=m.evaluate_prepared(r,p,reg,now=NOW); assert m.canonical_json(x)==m.canonical_json(y)
    elif k==24:
        ts=ss+(m.IncidentSignal('SIG-2','INC-2','MEDIUM',frozenset({'DEPENDENCY_OUTAGE'}),NOW-1,True,True,'B2',False),); tr=rs+(m.ReplayReceipt('R2','REQ-2','N2',m.SafeMode.DEGRADED,NOW-1,True,'B2',False),); dl=m.make_registry_delta(ss,rs,ts,tr); out=m.apply_registry_delta(ss,rs,dl); assert m.registry_fingerprint(*out)==m.registry_fingerprint(ts,tr)
    elif k==25:
        ts=ss+(m.IncidentSignal('SIG-2','INC-2','MEDIUM',frozenset({'DEPENDENCY_OUTAGE'}),NOW-1,True,True,'B2',False),); dl=m.make_registry_delta(ss,rs,ts,rs)
        try: m.apply_registry_delta((),rs,dl); assert False
        except ValueError: pass
    elif k==26:
        reg=m.prepare_registry(p,ss,rs,now=NOW); plan=m.plan_registry_sync(ss,rs,reg.signal_fingerprints,reg.receipt_fingerprints); assert not plan.missing_or_changed_signal_ids and not plan.missing_or_changed_receipt_ids and not plan.permission_granted
    elif k==27:
        reg=m.prepare_registry(p,ss,rs,now=NOW); sf=dict(reg.signal_fingerprints); sf['SIG-057']='0'*64; plan=m.plan_registry_sync(ss,rs,sf,reg.receipt_fingerprints); assert plan.missing_or_changed_signal_ids==('SIG-057',) and not plan.mode_transition_authorized and not plan.receipt_persist_authorized
    elif k==28:
        s2=ss+(m.IncidentSignal('ZZ','OTHER','LOW',frozenset({'DEPENDENCY_OUTAGE'}),NOW,True,True,'OTHER',False),); r2=(m.ReplayReceipt('ZZ','REQ-X','N-X',m.SafeMode.NORMAL,NOW,True,'OTHER',False),); assert m.registry_fingerprint(s2,r2)==m.registry_fingerprint(tuple(reversed(s2)),tuple(reversed(r2)))
    elif k==29:
        src=inspect.getsource(m); forbidden=[r'\bsubprocess\b',r'os\.system',r'\bsocket\b',r'\brequests\b',r'\burllib\b',r'\bPopen\b',r'\.unlink\(',r'\bshutil\b',r'\bwebbrowser\b',r'\bsmtplib\b']; assert not any(re.search(x,src) for x in forbidden)
    elif k==30:
        x=m.evaluate(r,p,ss,rs,now=NOW); assert not x.permission_granted and not x.mode_transition_executed and not x.network_disconnect_executed and not x.external_tool_shutdown_executed and not x.automation_stop_executed and not x.writes_disabled_executed and not x.receipt_persisted and not x.partial_state_authoritative and not x.safety_truth_proven and not x.action_success
    elif k==31:
        other=(m.IncidentSignal('OTHER','OTHER','CRITICAL',frozenset({'INTEGRITY_RISK'}),NOW,True,True,r.evidence_binding,False),); x=m.evaluate(r,p,other,rs,now=NOW); assert x.decision is m.ControlDecision.HOLD and x.mode_candidate is m.SafeMode.NORMAL

for i in range(160):
    def make(n):
        def test(self): scenario(n)
        test.__name__=f'test_case_{n:03d}'; return test
    setattr(T,f'test_case_{i:03d}',make(i))
if __name__=='__main__': unittest.main(verbosity=1)
