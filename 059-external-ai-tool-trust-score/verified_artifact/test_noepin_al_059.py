from __future__ import annotations
import inspect,re,unittest
from dataclasses import replace
import noepin_al_059_external_trust_score as m
NOW=1_800_000_000

def base(): return m.default_policy(NOW),m.default_request(NOW),(m.default_profile(NOW),),m.default_evidence(NOW)
class T(unittest.TestCase): pass

def scenario(i):
    k=i%32; p,r,ps,es=base()
    if k==0:
        x=m.evaluate(r,p,ps,es,now=NOW); assert x.decision is m.ControlDecision.ALLOW and x.trust_tier is m.TrustTier.ESTABLISHED and x.trust_score==95 and x.connection_candidate and not x.connection_established and not x.permission_granted
    elif k==1:
        x=m.evaluate(replace(r,operation=m.TrustOperation.ASSESS),p,ps,es,now=NOW); assert x.decision is m.ControlDecision.ALLOW and not x.connection_candidate
    elif k==2:
        neg=replace(es[0],impact=-40); x=m.evaluate(r,p,ps,(neg,)+es[1:],now=NOW); assert x.trust_score==40 and x.trust_tier in {m.TrustTier.PROBATION,m.TrustTier.UNTRUSTED}
    elif k==3:
        bad=tuple(replace(e,impact=-20) for e in es); x=m.evaluate(r,p,ps,bad,now=NOW); assert x.decision is m.ControlDecision.DENY and x.trust_tier is m.TrustTier.BLOCKED
    elif k==4:
        x=m.evaluate(r,p,(replace(ps[0],provider_id='UNKNOWN'),),es,now=NOW); assert x.decision is m.ControlDecision.HUMAN_APPROVAL and 'PROVIDER_NOT_TRUSTED' in x.reasons
    elif k==5:
        x=m.evaluate(r,p,(replace(ps[0],verified=False),),es,now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==6:
        x=m.evaluate(r,p,(replace(ps[0],revoked=True),),es,now=NOW); assert x.decision is m.ControlDecision.DENY
    elif k==7:
        x=m.evaluate(replace(r,expected_identity_fingerprint='BAD'),p,ps,es,now=NOW); assert x.decision is m.ControlDecision.DENY
    elif k==8:
        x=m.evaluate(replace(r,evidence_binding='BAD'),p,ps,es,now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==9:
        x=m.evaluate(replace(r,expected_policy_version='bad'),p,ps,es,now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==10:
        x=m.evaluate(r,replace(p,revoked=True),ps,es,now=NOW); assert x.decision is m.ControlDecision.HOLD and x.reasons[0].startswith('INVALID_REGISTRY:')
    elif k==11:
        reg=m.prepare_registry(p,ps,es,now=NOW); x=m.evaluate_prepared(r,p,replace(reg,registry_fingerprint='0'*64),now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==12:
        reg=m.prepare_registry(p,ps,es,now=NOW); x=m.evaluate_prepared(r,p,replace(reg,policy_fingerprint='0'*64),now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==13:
        stale=tuple(replace(e,observed_at=NOW-5000,expires_at=NOW+10) for e in es); x=m.evaluate(r,p,ps,stale,now=NOW); assert x.active_evidence_count==0 and x.decision is m.ControlDecision.HUMAN_APPROVAL
    elif k==14:
        rev=(replace(es[0],revoked=True),)+es[1:]; x=m.evaluate(r,p,ps,rev,now=NOW); assert x.active_evidence_count==3 and x.trust_score==80
    elif k==15:
        unv=(replace(es[0],verified=False),)+es[1:]; x=m.evaluate(r,p,ps,unv,now=NOW); assert x.active_evidence_count==3
    elif k==16:
        dep=(replace(es[0],independent=False),)+es[1:]; x=m.evaluate(r,p,ps,dep,now=NOW); assert x.active_evidence_count==3
    elif k==17:
        rb=(replace(es[0],evidence_binding='BAD'),)+es[1:]; x=m.evaluate(r,p,ps,rb,now=NOW); assert x.active_evidence_count==3
    elif k==18:
        rr=replace(r,operation=m.TrustOperation.REQUEST_PRIVILEGE,requested_privilege=m.PrivilegeLevel.READ_ONLY); x=m.evaluate(rr,p,ps,es,now=NOW); assert x.decision is m.ControlDecision.ALLOW and x.privilege_candidate is m.PrivilegeLevel.READ_ONLY and not x.permission_granted
    elif k==19:
        rr=replace(r,operation=m.TrustOperation.REQUEST_PRIVILEGE,requested_privilege=m.PrivilegeLevel.HIGH); x=m.evaluate(rr,p,ps,es,now=NOW); assert x.decision is m.ControlDecision.HUMAN_APPROVAL and x.privilege_candidate is m.PrivilegeLevel.HIGH and not x.high_privilege_granted
    elif k==20:
        rr=replace(r,operation=m.TrustOperation.REQUEST_PRIVILEGE,requested_privilege=m.PrivilegeLevel.ADMIN); x=m.evaluate(rr,p,ps,es,now=NOW); assert x.decision is m.ControlDecision.DENY
    elif k==21:
        one=(es[0],); rr=replace(r,operation=m.TrustOperation.REQUEST_PRIVILEGE,requested_privilege=m.PrivilegeLevel.STANDARD); x=m.evaluate(rr,p,ps,one,now=NOW); assert x.decision is m.ControlDecision.HUMAN_APPROVAL and x.probation_candidate
    elif k==22:
        rr=replace(r,high_impact_context=True); x=m.evaluate(rr,p,ps,es,now=NOW); assert x.decision is m.ControlDecision.HUMAN_APPROVAL and x.connection_candidate
    elif k==23:
        ep=replace(ps[0],entity_type=m.EntityType.SERVICE); x=m.evaluate(r,p,(ep,),es,now=NOW); assert x.decision is m.ControlDecision.DENY
    elif k==24:
        reg=m.prepare_registry(p,ps,es,now=NOW); a=m.evaluate(r,p,ps,es,now=NOW); b=m.evaluate_prepared(r,p,reg,now=NOW); assert m.canonical_json(a)==m.canonical_json(b)
    elif k==25:
        p2=replace(ps[0],entity_id='EXT-2',identity_fingerprint='FP2',evidence_binding='B2'); e2=replace(es[0],evidence_id='EV-2',entity_id='EXT-2',evidence_binding='B2'); tp=ps+(p2,); te=es+(e2,); d=m.make_registry_delta(ps,es,tp,te); op,oe=m.apply_registry_delta(ps,es,d); assert m.registry_fingerprint(op,oe)==m.registry_fingerprint(tp,te)
    elif k==26:
        reg=m.prepare_registry(p,ps,es,now=NOW); plan=m.plan_registry_sync(ps,es,reg.profile_fingerprints,reg.evidence_fingerprints); assert not plan.missing_or_changed_profile_ids and not plan.missing_or_changed_evidence_ids and not plan.permission_granted
    elif k==27:
        reg=m.prepare_registry(p,ps,es,now=NOW); bad=dict(reg.profile_fingerprints); bad['EXT-059']='0'*64; plan=m.plan_registry_sync(ps,es,bad,reg.evidence_fingerprints); assert plan.missing_or_changed_profile_ids==('EXT-059',)
    elif k==28:
        src=inspect.getsource(m); forbidden=[r'\bsubprocess\b',r'os\.system',r'\bsocket\b',r'\brequests\b',r'\burllib\b',r'\bPopen\b',r'\.unlink\(',r'\bshutil\b',r'\bwebbrowser\b',r'\bsmtplib\b']; assert not any(re.search(x,src) for x in forbidden)
    elif k==29:
        x=m.evaluate(r,p,ps,es,now=NOW); assert not x.permission_granted and not x.connection_established and not x.high_privilege_granted and not x.probation_completed and not x.trust_truth_proven and not x.future_safety_proven and not x.action_success
    elif k==30:
        d=m.TrustEvidence('E-UNKNOWN','MISSING',m.EvidenceKind.RELIABILITY,NOW-1,NOW+10,1,True,True,'S','B'); x=m.evaluate(r,p,ps,es+(d,),now=NOW); assert x.decision is m.ControlDecision.HOLD and x.reasons[0].startswith('INVALID_REGISTRY:')
    elif k==31:
        p2=replace(ps[0],entity_id='EXT-2',identity_fingerprint='FP2',evidence_binding='B2'); e2=replace(es[0],evidence_id='EV-2',entity_id='EXT-2',evidence_binding='B2'); d=m.make_registry_delta(ps,es,ps+(p2,),es+(e2,));
        try: m.apply_registry_delta((p2,),es,d); assert False
        except ValueError: pass

for i in range(160):
    def make(n):
        def test(self): scenario(n)
        test.__name__=f'test_case_{n:03d}'; return test
    setattr(T,f'test_case_{i:03d}',make(i))
if __name__=='__main__': unittest.main(verbosity=1)
