from __future__ import annotations
import inspect,re,unittest
from dataclasses import replace
import noepin_al_056_explanation_layer as m
NOW=1_800_000_000

def base(): return m.default_policy(NOW),m.default_record(NOW),m.default_reasons(),m.default_evidence(NOW),m.default_traces(NOW)
class T(unittest.TestCase): pass

def scenario(i):
    k=i%32; p,d,rs,es,ts=base()
    if k==0:
        x=m.evaluate(d,p,rs,es,ts,now=NOW); assert x.decision is m.ControlDecision.ALLOW and x.explanation_complete_candidate and not x.permission_granted and not x.decision_truth_proven
    elif k==1:
        x=m.evaluate(replace(d,reason_codes=('UNKNOWN',)),p,rs,es,ts,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'UNKNOWN_REASON_CODE' in x.reasons
    elif k==2:
        x=m.evaluate(replace(d,evidence_ref_ids=('MISSING',)),p,rs,es,ts,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'EVIDENCE_REFERENCE_MISSING' in x.reasons
    elif k==3:
        x=m.evaluate(replace(d,policy_trace_ids=('MISSING',)),p,rs,es,ts,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'POLICY_TRACE_MISSING' in x.reasons
    elif k==4:
        x=m.evaluate(d,p,rs,(replace(es[0],verified=False),),ts,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'EVIDENCE_UNVERIFIED' in x.reasons
    elif k==5:
        x=m.evaluate(d,p,rs,(replace(es[0],revoked=True),),ts,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'EVIDENCE_REVOKED' in x.reasons
    elif k==6:
        x=m.evaluate(d,p,rs,(replace(es[0],evidence_binding='WRONG'),),ts,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'EVIDENCE_BINDING_MISMATCH' in x.reasons
    elif k==7:
        x=m.evaluate(d,p,rs,(replace(es[0],observed_at=NOW-5000),),ts,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'EVIDENCE_STALE' in x.reasons
    elif k==8:
        x=m.evaluate(d,p,rs,es,(replace(ts[0],verified=False),),now=NOW); assert x.decision is m.ControlDecision.HOLD and 'POLICY_TRACE_UNVERIFIED' in x.reasons
    elif k==9:
        x=m.evaluate(d,p,rs,es,(replace(ts[0],revoked=True),),now=NOW); assert x.decision is m.ControlDecision.HOLD and 'POLICY_TRACE_REVOKED' in x.reasons
    elif k==10:
        x=m.evaluate(d,p,rs,es,(replace(ts[0],evidence_binding='WRONG'),),now=NOW); assert x.decision is m.ControlDecision.HOLD and 'POLICY_TRACE_BINDING_MISMATCH' in x.reasons
    elif k==11:
        x=m.evaluate(d,p,rs,es,(replace(ts[0],policy_version='2'),),now=NOW); assert x.decision is m.ControlDecision.HOLD and 'POLICY_TRACE_POLICY_MISMATCH' in x.reasons
    elif k==12:
        x=m.evaluate(replace(d,expected_policy_version='bad'),p,rs,es,ts,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'POLICY_VERSION_MISMATCH' in x.reasons
    elif k==13:
        x=m.evaluate(d,replace(p,revoked=True),rs,es,ts,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'POLICY_REVOKED' in x.reasons
    elif k==14:
        r=(replace(rs[0],applicable_decisions=frozenset({'DENY'})),); x=m.evaluate(d,p,r,es,ts,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'REASON_DECISION_MISMATCH' in x.reasons
    elif k==15:
        r=(replace(rs[0],required_evidence_types=frozenset({'OTHER'})),); x=m.evaluate(d,p,r,es,ts,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'REQUIRED_EVIDENCE_TYPE_MISSING' in x.reasons
    elif k==16:
        r=(replace(rs[0],required_policy_rules=frozenset({'OTHER_RULE'})),); x=m.evaluate(d,p,r,es,ts,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'REQUIRED_POLICY_TRACE_MISSING' in x.reasons
    elif k==17:
        ee=(replace(es[0],sensitivity='SECRET',display_label='SECRET-VALUE-MUST-NOT-LEAK'),); x=m.evaluate(d,p,rs,ee,ts,now=NOW); assert x.decision is m.ControlDecision.ALLOW and x.redacted_evidence_ids==('EVID-056',) and all('SECRET-VALUE-MUST-NOT-LEAK' not in s for s in x.human_summary)
    elif k==18:
        try: m.prepare_registry(p,rs,(es[0],es[0]),ts,now=NOW); assert False
        except ValueError: pass
    elif k==19:
        try: m.prepare_registry(p,rs,es,(ts[0],ts[0]),now=NOW); assert False
        except ValueError: pass
    elif k==20:
        try: m.prepare_registry(p,(rs[0],rs[0]),es,ts,now=NOW); assert False
        except ValueError: pass
    elif k==21:
        reg=m.prepare_registry(p,rs,es,ts,now=NOW); x=m.evaluate(d,p,rs,es,ts,now=NOW); y=m.evaluate_prepared(d,p,reg,now=NOW); assert m.canonical_json(x)==m.canonical_json(y)
    elif k==22:
        reg=m.prepare_registry(p,rs,es,ts,now=NOW); x=m.evaluate_prepared(d,p,replace(reg,registry_fingerprint='0'*64),now=NOW); assert x.decision is m.ControlDecision.HOLD and 'PREPARED_REGISTRY_FINGERPRINT_MISMATCH' in x.reasons
    elif k==23:
        reg=m.prepare_registry(p,rs,es,ts,now=NOW); x=m.evaluate_prepared(d,p,replace(reg,policy_fingerprint='0'*64),now=NOW); assert x.decision is m.ControlDecision.HOLD and 'PREPARED_POLICY_FINGERPRINT_MISMATCH' in x.reasons
    elif k==24:
        trs=rs+(m.ReasonCodeDefinition('SECOND','AUDIT','Second reason.',frozenset({'ALLOW'}),frozenset(),frozenset(),True),); tes=es+(m.EvidenceReference('E2','D2','OTHER','S2',NOW-1,True,True,'PUBLIC','Other','B2'),); tts=ts+(m.PolicyTraceStep('T2','D2','R2','EXPLAIN-056','1',1,'ALLOW',NOW-1,True,'B2'),); dl=m.make_registry_delta(rs,es,ts,trs,tes,tts); out=m.apply_registry_delta(rs,es,ts,dl); assert m.registry_fingerprint(*out)==m.registry_fingerprint(trs,tes,tts)
    elif k==25:
        reg=m.prepare_registry(p,rs,es,ts,now=NOW); plan=m.plan_registry_sync(rs,es,ts,reg.reason_fingerprints,reg.evidence_fingerprints,reg.trace_fingerprints); assert not plan.missing_or_changed_reason_codes and not plan.missing_or_changed_evidence_ids and not plan.missing_or_changed_trace_ids and not plan.permission_granted
    elif k==26:
        reg=m.prepare_registry(p,rs,es,ts,now=NOW); ef=dict(reg.evidence_fingerprints); ef['EVID-056']='0'*64; plan=m.plan_registry_sync(rs,es,ts,reg.reason_fingerprints,ef,reg.trace_fingerprints); assert plan.missing_or_changed_evidence_ids==('EVID-056',) and not plan.decision_override_authorized
    elif k==27:
        src=inspect.getsource(m); forbidden=[r'\bsubprocess\b',r'os\.system',r'\bsocket\b',r'\brequests\b',r'\burllib\b',r'\bPopen\b',r'\.unlink\(',r'\bshutil\b',r'\bwebbrowser\b',r'\bsmtplib\b']; assert not any(re.search(x,src) for x in forbidden)
    elif k==28:
        x=m.evaluate(d,p,rs,es,ts,now=NOW); assert not x.permission_granted and not x.upstream_decision_changed and not x.action_executed and not x.evidence_truth_proven and not x.decision_truth_proven and not x.policy_compliance_proven and not x.safety_proven and not x.action_success
    elif k==29:
        r2=rs+(m.ReasonCodeDefinition('ZZ','AUDIT','z',frozenset({'ALLOW'}),frozenset(),frozenset()),); e2=es+(m.EvidenceReference('ZZ','D2','OTHER','S2',NOW,True,True,'PUBLIC','z','B2'),); t2=ts+(m.PolicyTraceStep('ZZ','D2','R2','EXPLAIN-056','1',1,'ALLOW',NOW,True,'B2'),); assert m.registry_fingerprint(r2,e2,t2)==m.registry_fingerprint(tuple(reversed(r2)),tuple(reversed(e2)),tuple(reversed(t2)))
    elif k==30:
        bad=replace(p,expires_at=NOW-1); x=m.evaluate(d,bad,rs,es,ts,now=NOW); assert x.decision is m.ControlDecision.HOLD and x.reasons[0].startswith('INVALID_REGISTRY:')
    elif k==31:
        rr=(m.ReasonCodeDefinition('BLOCKED','SECURITY','Request was blocked by the referenced control rule.',frozenset({'DENY'}),frozenset({'REQUEST_METADATA'}),frozenset({'DENY_RULE'}),True),)
        ee=(replace(es[0],decision_id='DEC-DENY',evidence_binding='B-DENY'),); tt=(replace(ts[0],decision_id='DEC-DENY',rule_id='DENY_RULE',outcome='DENY',evidence_binding='B-DENY'),); dd=replace(d,decision_id='DEC-DENY',upstream_decision=m.ControlDecision.DENY,reason_codes=('BLOCKED',),evidence_ref_ids=('EVID-056',),policy_trace_ids=('TRACE-056',),explanation_binding='B-DENY'); x=m.evaluate(dd,p,rr,ee,tt,now=NOW); assert x.decision is m.ControlDecision.ALLOW and x.upstream_decision is m.ControlDecision.DENY and not x.upstream_decision_changed and not x.permission_granted

for i in range(160):
    def make(n):
        def test(self): scenario(n)
        test.__name__=f'test_case_{n:03d}'; return test
    setattr(T,f'test_case_{i:03d}',make(i))
if __name__=='__main__': unittest.main(verbosity=1)
