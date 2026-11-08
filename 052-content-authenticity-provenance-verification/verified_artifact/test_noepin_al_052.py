from __future__ import annotations
import inspect,re,unittest
from dataclasses import replace
import noepin_al_052_content_authenticity as m

NOW=1_800_000_000

def base():
    p=m.default_policy(NOW); r=m.default_request(NOW); steps,sigs=m.default_evidence(NOW); return p,r,steps,sigs

class T(unittest.TestCase): pass

def scenario(i):
    kind=i%20
    p,r,steps,sigs=base()
    if kind==0:
        v=m.evaluate(r,p,steps,sigs,now=NOW); assert v.decision is m.ControlDecision.ALLOW and v.trust_label is m.TrustLabel.VERIFIED and v.chain_valid and v.signature_verification_evidence_valid and not v.permission_granted and not v.content_accepted
    elif kind==1:
        bad=(steps[0],replace(steps[1],input_sha256=m.fingerprint(('broken',i))))
        v=m.evaluate(r,p,bad,sigs,now=NOW); assert v.decision is m.ControlDecision.DENY and v.trust_label is m.TrustLabel.TAMPERED and 'PROVENANCE_CHAIN_BREAK' in v.reasons
    elif kind==2:
        bad=(steps[0],replace(steps[1],output_sha256=m.fingerprint(('wrong-tip',i))))
        v=m.evaluate(r,p,bad,sigs,now=NOW); assert v.decision is m.ControlDecision.DENY and 'CONTENT_HASH_NOT_IN_PROVENANCE_TIP' in v.reasons
    elif kind==3:
        rr=replace(r,expected_origin_id='OTHER-ORIGIN'); v=m.evaluate(rr,p,steps,sigs,now=NOW); assert v.decision is m.ControlDecision.DENY and 'ORIGIN_MISMATCH' in v.reasons
    elif kind==4:
        v=m.evaluate(r,p,steps,(),now=NOW); assert v.decision is m.ControlDecision.HOLD and 'VERIFIED_SIGNATURE_MISSING' in v.reasons
    elif kind==5:
        bad=(replace(sigs[0],signature_verified=False),); v=m.evaluate(r,p,steps,bad,now=NOW); assert v.decision is m.ControlDecision.DENY and v.trust_label is m.TrustLabel.TAMPERED and 'SIGNATURE_VERIFICATION_FAILED' in v.reasons
    elif kind==6:
        bad=(replace(sigs[0],verifier_id='UNTRUSTED'),); v=m.evaluate(r,p,steps,bad,now=NOW); assert v.decision is m.ControlDecision.HOLD and bad[0].signature_id in v.invalid_or_stale_signature_ids
    elif kind==7:
        mid=tuple(replace(x,origin_trust=.65) for x in steps); v=m.evaluate(r,p,mid,sigs,now=NOW); assert v.decision is m.ControlDecision.HUMAN_APPROVAL and v.trust_label is m.TrustLabel.REVIEW and v.human_review_candidate
    elif kind==8:
        low=tuple(replace(x,origin_trust=.30) for x in steps); v=m.evaluate(r,p,low,sigs,now=NOW); assert v.decision is m.ControlDecision.DENY and 'ORIGIN_TRUST_TOO_LOW' in v.reasons
    elif kind==9:
        rr=replace(r,expected_policy_version='bad'); v=m.evaluate(rr,p,steps,sigs,now=NOW); assert v.decision is m.ControlDecision.HOLD and 'POLICY_VERSION_MISMATCH' in v.reasons
    elif kind==10:
        rr=replace(r,purpose='UNAPPROVED'); v=m.evaluate(rr,p,steps,sigs,now=NOW); assert v.decision is m.ControlDecision.DENY and 'PURPOSE_NOT_ALLOWED' in v.reasons
    elif kind==11:
        prepared=m.prepare_registry(p,steps,sigs,now=NOW); a=m.evaluate(r,p,steps,sigs,now=NOW); b=m.evaluate_prepared(r,p,prepared,now=NOW); assert m.canonical_json(a)==m.canonical_json(b)
    elif kind==12:
        prepared=m.prepare_registry(p,steps,sigs,now=NOW); bad=replace(prepared,registry_fingerprint='0'*64); v=m.evaluate_prepared(r,p,bad,now=NOW); assert v.decision is m.ControlDecision.HOLD and 'PREPARED_REGISTRY_FINGERPRINT_MISMATCH' in v.reasons
    elif kind==13:
        newstep=replace(steps[1],operation='TRANSFORM-V2')
        target=(steps[0],newstep); d=m.make_registry_delta(steps,sigs,target,sigs); rs,rg=m.apply_registry_delta(steps,sigs,d); assert m.registry_fingerprint(rs,rg)==m.registry_fingerprint(target,sigs)
    elif kind==14:
        d=m.make_registry_delta(steps,sigs,steps,sigs); bad=replace(d,base_fingerprint='f'*64)
        try: m.apply_registry_delta(steps,sigs,bad); raise AssertionError('expected')
        except ValueError: pass
    elif kind==15:
        known={**{'step:'+x.step_id:m.fingerprint(x) for x in steps},**{'sig:'+x.signature_id:m.fingerprint(x) for x in sigs}}; s=m.plan_registry_sync(steps,sigs,known); assert s.missing_or_changed_step_ids==() and s.missing_or_changed_signature_ids==() and not s.permission_granted and not s.content_use_authorized
    elif kind==16:
        assert m.registry_fingerprint(steps,sigs)==m.registry_fingerprint(tuple(reversed(steps)),tuple(reversed(sigs)))
    elif kind==17:
        bad=(steps[0],replace(steps[1],revoked=True)); v=m.evaluate(r,p,bad,sigs,now=NOW); assert v.decision is m.ControlDecision.DENY and 'CONTENT_HASH_NOT_IN_PROVENANCE_TIP' in v.reasons
    elif kind==18:
        src=inspect.getsource(m); forbidden=[r'\bsubprocess\b',r'os\.system',r'\bsocket\b',r'\brequests\b',r'\burllib\b',r'\bPopen\b',r'\.unlink\(',r'\bshutil\b',r'\bwebbrowser\b',r'\bsmtplib\b']; assert not any(re.search(x,src) for x in forbidden)
    elif kind==19:
        v=m.evaluate(r,p,steps,sigs,now=NOW); assert not v.permission_granted and not v.content_accepted and not v.content_executed and not v.data_transferred and not v.content_truth_proven and not v.authenticity_truth_proven and not v.action_success

for i in range(160):
    def make(n):
        def test(self): scenario(n)
        test.__name__=f'test_case_{n:03d}'
        return test
    setattr(T,f'test_case_{i:03d}',make(i))

if __name__=='__main__': unittest.main(verbosity=1)
