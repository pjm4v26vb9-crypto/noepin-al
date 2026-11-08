import ast
import json
import unittest
from dataclasses import replace
from pathlib import Path

from noepin_al_039_rules_engine import (
    Decision, Evidence, EvidenceStatus, EvaluationRequest, Operator, Rule, RuleProfile,
    Severity, apply_profile_delta, canonical_json, evaluate, evaluate_prepared, fingerprint,
    gap_report, make_profile_delta, prepare_context, profile_from_dict,
)

NOW=1_800_000_000


def rule(i=1, **kw):
    base=dict(rule_id=f"R{i}", source="INTERNAL", source_version="2026.1", control_id=f"C{i}",
              field=f"controls.c{i}", operator=Operator.TRUE, expected=None, severity=Severity.MEDIUM,
              required_evidence_type=None, requires_human_review=False, enabled=True)
    base.update(kw); return Rule(**base)

def profile(rules=None, **kw):
    base=dict(profile_id="P", profile_version="1", authority_epoch=3, issued_at=NOW-100,
              expires_at=NOW+1000, revoked=False, rules=tuple([rule()] if rules is None else rules))
    base.update(kw); return RuleProfile(**base)

def req(attrs=None, **kw):
    base=dict(request_id="Q", subject_id="S", operation="AUDIT", attributes=attrs or {"controls":{"c1":True}}, requested_sources=())
    base.update(kw); return EvaluationRequest(**base)

def ev(**kw):
    base=dict(evidence_id="E", evidence_type="scan", status=EvidenceStatus.VALID, observed_at=NOW-10,
              expires_at=NOW+100, subject_id="S", profile_id="P", profile_version="1", authority_epoch=3, attributes={})
    base.update(kw); return Evidence(**base)

class CoreTests(unittest.TestCase):
    def test_allow(self): self.assertEqual(evaluate(req(), profile(), [], now=NOW).decision, Decision.ALLOW)
    def test_hold_no_findings(self): self.assertEqual(evaluate(req(), profile([replace(rule(), enabled=False)]), [], now=NOW).decision, Decision.HOLD)
    def test_critical_gap_denies(self): self.assertEqual(evaluate(req({"controls":{"c1":False}}), profile([replace(rule(), severity=Severity.CRITICAL)]), [], now=NOW).decision, Decision.DENY)
    def test_medium_gap_holds(self): self.assertEqual(evaluate(req({"controls":{"c1":False}}), profile(), [], now=NOW).decision, Decision.HOLD)
    def test_human_review(self): self.assertEqual(evaluate(req(), profile([replace(rule(), requires_human_review=True)]), [], now=NOW).decision, Decision.HUMAN_APPROVAL)
    def test_evidence_required_valid(self):
        r=replace(rule(), required_evidence_type="scan"); self.assertEqual(evaluate(req(), profile([r]), [ev()], now=NOW).decision, Decision.ALLOW)
    def test_evidence_missing(self):
        r=replace(rule(), required_evidence_type="scan"); self.assertEqual(evaluate(req(), profile([r]), [], now=NOW).decision, Decision.HOLD)
    def test_evidence_present_invalid(self):
        r=replace(rule(), required_evidence_type="scan"); self.assertEqual(evaluate(req(), profile([r]), [ev(status=EvidenceStatus.INVALID)], now=NOW).decision, Decision.HOLD)
    def test_evidence_expired(self):
        r=replace(rule(), required_evidence_type="scan"); self.assertEqual(evaluate(req(), profile([r]), [ev(expires_at=NOW)], now=NOW).decision, Decision.HOLD)
    def test_evidence_wrong_subject(self):
        r=replace(rule(), required_evidence_type="scan"); self.assertEqual(evaluate(req(), profile([r]), [ev(subject_id="X")], now=NOW).decision, Decision.HOLD)
    def test_evidence_wrong_profile_version(self):
        r=replace(rule(), required_evidence_type="scan"); self.assertEqual(evaluate(req(), profile([r]), [ev(profile_version="0")], now=NOW).decision, Decision.HOLD)
    def test_evidence_wrong_epoch(self):
        r=replace(rule(), required_evidence_type="scan"); self.assertEqual(evaluate(req(), profile([r]), [ev(authority_epoch=2)], now=NOW).decision, Decision.HOLD)
    def test_profile_expired(self):
        with self.assertRaises(ValueError): evaluate(req(), profile(expires_at=NOW), [], now=NOW)
    def test_profile_future(self):
        with self.assertRaises(ValueError): evaluate(req(), profile(issued_at=NOW+1, expires_at=NOW+100), [], now=NOW)
    def test_profile_revoked(self):
        with self.assertRaises(ValueError): evaluate(req(), profile(revoked=True), [], now=NOW)
    def test_duplicate_rule_id(self):
        with self.assertRaises(ValueError): evaluate(req(), profile([rule(), rule()]), [], now=NOW)
    def test_invalid_request(self):
        with self.assertRaises(ValueError): evaluate(req(request_id=""), profile(), [], now=NOW)
    def test_requested_source_filter(self):
        p=profile([rule(1, source="NIST"), rule(2, source="OWASP", field="controls.c2")])
        q=req({"controls":{"c1":True}}, requested_sources=("NIST",))
        self.assertEqual(evaluate(q,p,[],now=NOW).decision, Decision.ALLOW)
    def test_gap_report_never_claims_compliance(self):
        g=gap_report(evaluate(req(),profile(),[],now=NOW)); self.assertFalse(g["compliance_proven"]); self.assertFalse(g["action_executed"])
    def test_result_never_claims_authoritative_compliance(self):
        r=evaluate(req(),profile(),[],now=NOW); self.assertFalse(r.authoritative_compliance_proven); self.assertFalse(r.action_executed)
    def test_prepared_same_semantics(self):
        p=profile(); q=req(); c=prepare_context(q,p,[],now=NOW); self.assertEqual(evaluate(q,p,[],now=NOW), evaluate_prepared(c))
    def test_prepared_state_fingerprint_deterministic(self):
        c1=prepare_context(req(),profile(),[],now=NOW); c2=prepare_context(req(),profile(),[],now=NOW); self.assertEqual(c1.state_fingerprint,c2.state_fingerprint)
    def test_canonical_json_order(self): self.assertEqual(fingerprint({"b":2,"a":1}),fingerprint({"a":1,"b":2}))
    def test_delta_round_trip(self):
        b=profile([rule(1),rule(2)]); t=profile([rule(1),replace(rule(2),severity=Severity.HIGH),rule(3)],profile_version="2",authority_epoch=4)
        d=make_profile_delta(b,t); self.assertEqual(apply_profile_delta(b,d),t)
    def test_delta_base_mismatch(self):
        b=profile([rule(1)]); t=profile([rule(1),rule(2)],profile_version="2"); d=make_profile_delta(b,t)
        with self.assertRaises(ValueError): apply_profile_delta(profile([replace(rule(1), severity=Severity.HIGH)]), d)
    def test_profile_from_dict(self):
        d={"profile_id":"P","profile_version":"1","authority_epoch":3,"issued_at":NOW-1,"expires_at":NOW+1,"rules":[{"rule_id":"R","source":"NIST","source_version":"1","control_id":"C","field":"x","operator":"TRUE"}]}
        self.assertEqual(profile_from_dict(d).rules[0].source,"NIST")
    def test_version_mismatch_changes_fp(self): self.assertNotEqual(fingerprint(profile()),fingerprint(profile(profile_version="2")))
    def test_epoch_changes_fp(self): self.assertNotEqual(fingerprint(profile()),fingerprint(profile(authority_epoch=4)))
    def test_evidence_status_changes_fp(self): self.assertNotEqual(fingerprint([ev()]),fingerprint([ev(status=EvidenceStatus.REVOKED)]))
    def test_empty_rule_profile_holds(self): self.assertEqual(evaluate(req(), profile([]), [], now=NOW).decision, Decision.HOLD)

    def test_profile_rule_order_does_not_change_fingerprint(self):
        a=profile([rule(1),rule(2)])
        b=profile([rule(2),rule(1)])
        self.assertEqual(fingerprint(a), fingerprint(b))
    def test_profile_rule_order_does_not_change_result(self):
        a=profile([rule(1),rule(2,field="controls.c2")])
        b=profile([rule(2,field="controls.c2"),rule(1)])
        q=req({"controls":{"c1":True,"c2":True}})
        self.assertEqual(evaluate(q,a,[],now=NOW), evaluate(q,b,[],now=NOW))
    def test_static_no_execution_or_mutation_primitives(self):
        src=Path(__file__).with_name("noepin_al_039_rules_engine.py").read_text(encoding="utf-8")
        tree=ast.parse(src)
        banned_imports={"subprocess","socket","requests","urllib","http.client","shutil"}
        imports=set()
        for n in ast.walk(tree):
            if isinstance(n,ast.Import): imports.update(a.name for a in n.names)
            elif isinstance(n,ast.ImportFrom) and n.module: imports.add(n.module)
        self.assertTrue(banned_imports.isdisjoint(imports), imports)
        banned_calls={"system","popen","unlink","remove","rmtree","send","sendall","connect","execute","commit","grant","deploy","publish","persist","write_text","write_bytes"}
        calls={n.func.attr for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)}
        calls|={n.func.id for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name)}
        self.assertTrue(banned_calls.isdisjoint(calls), banned_calls & calls)

class OperatorTests(unittest.TestCase):
    pass

cases=[]
for op,actual,expected,ok in [
    (Operator.EQUALS,"x","x",True),(Operator.EQUALS,"x","y",False),
    (Operator.NOT_EQUALS,"x","y",True),(Operator.NOT_EQUALS,"x","x",False),
    (Operator.IN,"x",["x","y"],True),(Operator.IN,"z",["x","y"],False),
    (Operator.CONTAINS,["x","y"],"x",True),(Operator.CONTAINS,["x","y"],"z",False),
    (Operator.PRESENT,1,None,True),(Operator.TRUE,True,None,True),(Operator.TRUE,False,None,False),
    (Operator.FALSE,False,None,True),(Operator.FALSE,True,None,False),
]: cases.append((op,actual,expected,ok))
for idx,(op,actual,expected,ok) in enumerate(cases):
    def make_test(op=op,actual=actual,expected=expected,ok=ok,idx=idx):
        def test(self):
            rr=rule(idx+1,field="x",operator=op,expected=expected)
            res=evaluate(req({"x":actual}),profile([rr]),[],now=NOW)
            self.assertEqual(res.decision is Decision.ALLOW, ok)
        return test
    setattr(OperatorTests,f"test_operator_{idx:02d}",make_test())

class GeneratedBoundaryTests(unittest.TestCase):
    pass

# 72 deterministic generated cases across severities and evidence states.
for i in range(72):
    def make_case(i=i):
        def test(self):
            sev=[Severity.LOW,Severity.MEDIUM,Severity.HIGH,Severity.CRITICAL][i%4]
            needs_ev=(i%3==0)
            good=(i%5!=0)
            rr=rule(i+100,field="x",severity=sev,required_evidence_type="scan" if needs_ev else None)
            evid=[ev(evidence_id=f"E{i}")] if needs_ev and good else ([] if needs_ev else [])
            res=evaluate(req({"x":good}),profile([rr]),evid,now=NOW)
            if good:
                self.assertEqual(res.decision,Decision.ALLOW)
            elif sev is Severity.CRITICAL:
                self.assertEqual(res.decision,Decision.DENY)
            else:
                self.assertEqual(res.decision,Decision.HOLD)
            self.assertFalse(res.authoritative_compliance_proven)
            self.assertFalse(res.action_executed)
        return test
    setattr(GeneratedBoundaryTests,f"test_generated_{i:03d}",make_case())

if __name__ == "__main__": unittest.main(verbosity=2)
