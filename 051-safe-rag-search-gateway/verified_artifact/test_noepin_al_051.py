from __future__ import annotations
import inspect,re,unittest
from dataclasses import replace
import noepin_al_051_safe_rag_gateway as m

NOW=1_800_000_000

def base(): return m.default_policy(NOW),m.default_request(NOW),m.default_documents(NOW)

def doc(oid='X',source='KB-PRIMARY',cls=m.DataClass.INTERNAL,acl=frozenset({'TEAM-AL'}),trust=.95,inj=.05,age=5,prov=True,binding='RAG-EVIDENCE-051',instr=False,revoked=False):
    return m.RetrievedDocument(oid,source,f'kb://{oid}',NOW-age,cls,acl,trust,inj,m.fingerprint(('content',oid)),f'PROV-{oid}',binding,prov,instr,revoked)

class T(unittest.TestCase): pass

def scenario(i):
    kind=i%20
    p,r,items=base()
    if kind==0:
        v=m.evaluate(r,p,items,now=NOW); assert v.decision is m.ControlDecision.ALLOW and len(v.selected_document_ids)==2 and not v.permission_granted and not v.context_committed
    elif kind==1:
        x=doc(f'Q{i}',inj=.9); v=m.evaluate(r,p,(x,),now=NOW); assert v.decision is m.ControlDecision.HOLD and x.document_id in v.quarantined_document_ids
    elif kind==2:
        x=doc(f'HR{i}',inj=.6); v=m.evaluate(r,p,(x,),now=NOW); assert v.decision is m.ControlDecision.HUMAN_APPROVAL and v.human_review_candidate and not v.permission_granted
    elif kind==3:
        x=doc(f'A{i}',acl=frozenset({'OTHER'})); v=m.evaluate(r,p,(x,),now=NOW); assert v.decision is m.ControlDecision.DENY and x.document_id in v.acl_denied_document_ids
    elif kind==4:
        x=doc(f'U{i}',trust=.2); v=m.evaluate(r,p,(x,),now=NOW); assert v.decision is m.ControlDecision.DENY and x.document_id in v.untrusted_document_ids
    elif kind==5:
        x=doc(f'S{i}',age=p.max_document_age_seconds+10); v=m.evaluate(r,p,(x,),now=NOW); assert v.decision is m.ControlDecision.HOLD and x.document_id in v.stale_or_invalid_document_ids
    elif kind==6:
        x=doc(f'P{i}',prov=False); v=m.evaluate(r,p,(x,),now=NOW); assert v.decision is m.ControlDecision.HOLD and x.document_id in v.stale_or_invalid_document_ids
    elif kind==7:
        rr=replace(r,expected_policy_version='bad'); v=m.evaluate(rr,p,items,now=NOW); assert v.decision is m.ControlDecision.HOLD and 'POLICY_VERSION_MISMATCH' in v.reasons
    elif kind==8:
        rr=replace(r,purpose='UNAPPROVED'); v=m.evaluate(rr,p,items,now=NOW); assert v.decision is m.ControlDecision.DENY and 'PURPOSE_NOT_ALLOWED' in v.reasons
    elif kind==9:
        x=doc(f'I{i}',instr=True); v=m.evaluate(r,p,(x,),now=NOW); assert v.decision is m.ControlDecision.HOLD and x.document_id in v.quarantined_document_ids
    elif kind==10:
        prepared=m.prepare_registry(p,items,now=NOW); a=m.evaluate(r,p,items,now=NOW); b=m.evaluate_prepared(r,p,prepared,now=NOW); assert m.canonical_json(a)==m.canonical_json(b)
    elif kind==11:
        prepared=m.prepare_registry(p,items,now=NOW); bad=replace(prepared,registry_fingerprint='0'*64); v=m.evaluate_prepared(r,p,bad,now=NOW); assert v.decision is m.ControlDecision.HOLD and 'PREPARED_REGISTRY_FINGERPRINT_MISMATCH' in v.reasons
    elif kind==12:
        target=items+(doc(f'ADD{i}'),); d=m.make_registry_delta(items,target); rebuilt=m.apply_registry_delta(items,d); assert m.registry_fingerprint(rebuilt)==m.registry_fingerprint(target)
    elif kind==13:
        target=items+(doc(f'ADD{i}'),); d=m.make_registry_delta(items,target); bad=replace(d,base_fingerprint='f'*64)
        try: m.apply_registry_delta(items,bad); raise AssertionError('expected')
        except ValueError: pass
    elif kind==14:
        known={d.document_id:m.fingerprint(d) for d in items}; s=m.plan_registry_sync(items,known); assert s.missing_or_changed_document_ids==() and not s.full_resend_required and not s.permission_granted and not s.context_commit_authorized
    elif kind==15:
        assert m.registry_fingerprint(items)==m.registry_fingerprint(tuple(reversed(items)))
    elif kind==16:
        x=doc(f'R{i}',revoked=True,inj=.99); v=m.evaluate(r,p,(x,items[0]),now=NOW); assert v.decision is m.ControlDecision.ALLOW and x.document_id in v.stale_or_invalid_document_ids
    elif kind==17:
        x=doc(f'B{i}',binding='WRONG'); v=m.evaluate(r,p,(x,items[0]),now=NOW); assert v.decision is m.ControlDecision.ALLOW and x.document_id in v.stale_or_invalid_document_ids
    elif kind==18:
        src=inspect.getsource(m); forbidden=[r'\bsubprocess\b',r'os\.system',r'\bsocket\b',r'\brequests\b',r'\burllib\b',r'\bPopen\b',r'\.unlink\(',r'\bshutil\b',r'\bwebbrowser\b',r'\bsmtplib\b']; assert not any(re.search(x,src) for x in forbidden)
    elif kind==19:
        v=m.evaluate(r,p,items,now=NOW); assert not v.retrieved_content_truth_proven and not v.source_trust_truth_proven and not v.model_invoked and not v.data_transferred and not v.action_success

for i in range(160):
    def make(n):
        def test(self): scenario(n)
        test.__name__=f'test_case_{n:03d}'
        return test
    setattr(T,f'test_case_{i:03d}',make(i))

if __name__=='__main__': unittest.main(verbosity=1)
