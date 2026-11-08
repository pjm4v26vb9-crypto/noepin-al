from __future__ import annotations
import inspect,re,unittest
from dataclasses import replace
import noepin_al_055_social_engineering as m
NOW=1_800_000_000

def base(): return m.default_policy(NOW),m.default_context(NOW),m.default_evidence(NOW)
class T(unittest.TestCase): pass

def scenario(i):
    k=i%32; p,c,e=base()
    if k==0:
        x=m.evaluate(c,p,e,now=NOW); assert x.decision is m.ControlDecision.ALLOW and not x.permission_granted and not x.human_approval_completed and not x.intent_truth_proven
    elif k==1:
        ee=(replace(e[0],bypass_request=m.SignalLevel.HIGH),); x=m.evaluate(c,p,ee,now=NOW); assert x.decision is m.ControlDecision.DENY and 'CRITICAL_MANIPULATION_SIGNAL_CANDIDATE' in x.reasons
    elif k==2:
        ee=(replace(e[0],credential_request=m.SignalLevel.HIGH),); x=m.evaluate(c,p,ee,now=NOW); assert x.decision is m.ControlDecision.DENY
    elif k==3:
        ee=(replace(e[0],impersonation=m.SignalLevel.CRITICAL),); x=m.evaluate(c,p,ee,now=NOW); assert x.decision is m.ControlDecision.DENY
    elif k==4:
        ee=(replace(e[0],urgency=m.SignalLevel.HIGH,authority_pressure=m.SignalLevel.MEDIUM),); x=m.evaluate(c,p,ee,now=NOW); assert x.decision in (m.ControlDecision.HUMAN_APPROVAL,m.ControlDecision.DENY) and x.human_reconfirmation_candidate
    elif k==5:
        cc=replace(c,action_type='GRANT_PERMISSION',risk_label='HIGH'); x=m.evaluate(cc,p,e,now=NOW); assert x.decision is m.ControlDecision.HUMAN_APPROVAL
    elif k==6:
        ee=(replace(e[0],explanation_clear=False),); x=m.evaluate(c,p,ee,now=NOW); assert x.decision is m.ControlDecision.HUMAN_APPROVAL and 'CLEAR_APPROVAL_EXPLANATION_REQUIRED' in x.reasons
    elif k==7:
        cc=replace(c,action_type='GRANT_PERMISSION',risk_label='HIGH'); ee=(replace(e[0],alternatives_offered=False),); x=m.evaluate(cc,p,ee,now=NOW); assert x.decision is m.ControlDecision.HUMAN_APPROVAL and 'HIGH_RISK_ALTERNATIVES_REQUIRED' in x.reasons
    elif k==8:
        cc=replace(c,current_user_decision='DECLINED'); ee=(replace(e[0],continued_after_decline=True),); x=m.evaluate(cc,p,ee,now=NOW); assert x.decision is m.ControlDecision.DENY
    elif k==9:
        ee=(replace(e[0],repeated_asks=5),); x=m.evaluate(c,p,ee,now=NOW); assert x.decision is m.ControlDecision.DENY and 'REPEATED_ASK_LIMIT_EXCEEDED' in x.reasons
    elif k==10:
        cc=replace(c,expected_policy_version='bad'); x=m.evaluate(cc,p,e,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'POLICY_VERSION_MISMATCH' in x.reasons
    elif k==11:
        x=m.evaluate(c,replace(p,revoked=True),e,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'POLICY_REVOKED' in x.reasons
    elif k==12:
        x=m.evaluate(c,p,(replace(e[0],verified=False),),now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==13:
        x=m.evaluate(c,p,(replace(e[0],independent_observer=False),),now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==14:
        x=m.evaluate(c,p,(replace(e[0],evidence_binding='WRONG'),),now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==15:
        x=m.evaluate(c,p,(replace(e[0],observed_at=NOW-5000),),now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==16:
        reg=m.prepare_registry(p,e,now=NOW); x=m.evaluate(c,p,e,now=NOW); y=m.evaluate_prepared(c,p,reg,now=NOW); assert m.canonical_json(x)==m.canonical_json(y)
    elif k==17:
        reg=m.prepare_registry(p,e,now=NOW); x=m.evaluate_prepared(c,p,replace(reg,registry_fingerprint='0'*64),now=NOW); assert x.decision is m.ControlDecision.HOLD and 'PREPARED_REGISTRY_FINGERPRINT_MISMATCH' in x.reasons
    elif k==18:
        ne=(replace(e[0],urgency=m.SignalLevel.MEDIUM),m.InteractionEvidence('E2','I2','O2',True,True,NOW-10,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,1,False,True,True,True,'B2',False)); d=m.make_registry_delta(e,ne); out=m.apply_registry_delta(e,d); assert m.registry_fingerprint(out)==m.registry_fingerprint(ne)
    elif k==19:
        known={x.evidence_id:m.fingerprint(x) for x in e}; plan=m.plan_registry_sync(e,known); assert plan.missing_or_changed_evidence_ids==() and not plan.permission_granted and not plan.approval_execution_authorized
    elif k==20:
        src=inspect.getsource(m); forbidden=[r'\bsubprocess\b',r'os\.system',r'\bsocket\b',r'\brequests\b',r'\burllib\b',r'\bPopen\b',r'\.unlink\(',r'\bshutil\b',r'\bwebbrowser\b',r'\bsmtplib\b']; assert not any(re.search(x,src) for x in forbidden)
    elif k==21:
        x=m.evaluate(c,p,e,now=NOW); assert not x.permission_granted and not x.human_approval_completed and not x.approval_executed and not x.user_decision_overridden and not x.message_sent and not x.intent_truth_proven and not x.persuasion_safe_proven and not x.action_success
    elif k==22:
        ee=(replace(e[0],urgency=m.SignalLevel.MEDIUM,secrecy=m.SignalLevel.MEDIUM,fear_pressure=m.SignalLevel.MEDIUM),); x=m.evaluate(c,p,ee,now=NOW); assert x.score>0 and x.manipulation_risk_candidate
    elif k==23:
        ee=(replace(e[0],reciprocity_pressure=m.SignalLevel.LOW),); x=m.evaluate(c,p,ee,now=NOW); assert x.decision is m.ControlDecision.ALLOW and x.score>0 and not x.persuasion_safe_proven
    elif k==24:
        x=m.evaluate(replace(c,explanation_present=False),p,e,now=NOW); assert x.decision is m.ControlDecision.HUMAN_APPROVAL
    elif k==25:
        x=m.evaluate(c,p,(replace(e[0],revoked=True),),now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==26:
        bad=replace(p,expires_at=NOW-1); x=m.evaluate(c,bad,e,now=NOW); assert x.decision is m.ControlDecision.HOLD and x.reasons[0].startswith('INVALID_REGISTRY:')
    elif k==27:
        x=m.evaluate(replace(c,expected_authority_epoch=2),p,e,now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==28:
        reg=m.prepare_registry(p,e,now=NOW); tam=replace(reg,policy_fingerprint='0'*64); x=m.evaluate_prepared(c,p,tam,now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==29:
        es=(m.InteractionEvidence('B','I','O',True,True,NOW,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,0,False,True,True,True,'X'),m.InteractionEvidence('A','I','O',True,True,NOW,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,m.SignalLevel.NONE,0,False,True,True,True,'X')); assert m.registry_fingerprint(es)==m.registry_fingerprint(tuple(reversed(es)))
    elif k==30:
        try: m.prepare_registry(p,(e[0],e[0]),now=NOW); assert False
        except ValueError: pass
    elif k==31:
        ee=(replace(e[0],urgency=m.SignalLevel.CRITICAL,secrecy=m.SignalLevel.HIGH,authority_pressure=m.SignalLevel.HIGH),); x=m.evaluate(c,p,ee,now=NOW); assert x.decision is m.ControlDecision.DENY and x.score>=p.deny_score

for i in range(160):
    def make(n):
        def test(self): scenario(n)
        test.__name__=f'test_case_{n:03d}'; return test
    setattr(T,f'test_case_{i:03d}',make(i))
if __name__=='__main__': unittest.main(verbosity=1)
