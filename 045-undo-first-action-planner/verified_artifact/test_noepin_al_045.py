from __future__ import annotations

import ast
import dataclasses
import unittest
from pathlib import Path

import noepin_al_045_undo_planner as m

NOW = 1_800_000_000


class TestUndoFirstPlanner(unittest.TestCase):
    def setUp(self):
        self.policy = m.default_policy(NOW)
        self.candidates = m.default_candidates()
        self.prepared = m.prepare_catalog(self.policy, self.candidates, now=NOW)


def req(objective, operation, **kwargs):
    p = m.default_policy(NOW)
    base = dict(
        request_id=f"REQ-{objective}-{operation}", objective=objective, requested_operation=operation,
        evidence_binding="E-REQ", expected_policy_id=p.policy_id, expected_policy_version=p.version,
        expected_authority_epoch=p.authority_epoch,
    )
    base.update(kwargs)
    return m.PlanRequest(**base)


def make_catalog(n=80, prefix="X"):
    out=[]
    for i in range(n):
        out.append(m.ActionCandidate(
            f"{prefix}-{i:04d}", f"objective-{i%10}", "draft" if i%2==0 else "trash",
            100-(i%20), 5+(i%30), "UNDO", "local", False, False, f"E-{prefix}-{i}"
        ))
    return tuple(out)


def register(name, fn):
    setattr(TestUndoFirstPlanner, name, fn)


# Group A: reversible substitution behavior (20)
scenarios = [
    ("remove_file","delete","trash"),
    ("communicate","send","draft"),
    ("release","publish","preview"),
    ("update_file","overwrite","versioned_write"),
    ("deploy_change","deploy","dry_run"),
]
for i in range(20):
    objective, op, expected = scenarios[i % len(scenarios)]
    def t(self, objective=objective, op=op, expected=expected, i=i):
        r = req(objective, op, request_id=f"A-{i}")
        d = m.evaluate_prepared(r, self.policy, self.prepared, now=NOW)
        self.assertEqual(d.decision, m.ControlDecision.ALLOW)
        self.assertEqual(d.recommended_operation, expected)
        self.assertIn("REVERSIBLE_ALTERNATIVE_SELECTED", d.reasons)
        self.assertFalse(d.action_executed); self.assertFalse(d.permission_granted); self.assertFalse(d.action_success)
    register(f"test_{i+1:03d}_substitution", t)

# Group B: exact reversible operations (20)
reversible = [
    ("remove_file","trash"), ("communicate","draft"), ("release","preview"),
    ("update_file","versioned_write"), ("deploy_change","dry_run")
]
for j in range(20):
    objective, op = reversible[j % len(reversible)]
    idx=20+j
    def t(self, objective=objective, op=op, idx=idx):
        r=req(objective,op,request_id=f"B-{idx}",require_exact_operation=True)
        d=m.evaluate_prepared(r,self.policy,self.prepared,now=NOW)
        self.assertEqual(d.decision,m.ControlDecision.ALLOW)
        self.assertEqual(d.recommended_operation,op)
        self.assertIn("REQUESTED_OPERATION_SELECTED",d.reasons)
        self.assertGreaterEqual(d.reversibility_score,self.policy.min_reversibility_for_direct_allow)
    register(f"test_{idx+1:03d}_exact_reversible",t)

# Group C: irreversible / approval / risk behavior (20)
irrev=[("remove_file","delete",m.ControlDecision.HUMAN_APPROVAL),
       ("communicate","send",m.ControlDecision.HUMAN_APPROVAL),
       ("release","publish",m.ControlDecision.HOLD),
       ("update_file","overwrite",m.ControlDecision.HUMAN_APPROVAL),
       ("deploy_change","deploy",m.ControlDecision.HOLD)]
for j in range(20):
    objective,op,expected=irrev[j%len(irrev)]; approved=bool(j%2); idx=40+j
    def t(self,objective=objective,op=op,expected=expected,approved=approved,idx=idx):
        r=req(objective,op,request_id=f"C-{idx}",require_exact_operation=True,human_approval_evidence=approved)
        d=m.evaluate_prepared(r,self.policy,self.prepared,now=NOW)
        if expected==m.ControlDecision.HOLD:
            self.assertEqual(d.decision,m.ControlDecision.HOLD)
            self.assertIn("RISK_ABOVE_POLICY_LIMIT",d.reasons)
        elif approved:
            self.assertEqual(d.decision,m.ControlDecision.ALLOW)
            self.assertIn("HUMAN_APPROVAL_EVIDENCE_PRESENT",d.reasons)
        else:
            self.assertEqual(d.decision,m.ControlDecision.HUMAN_APPROVAL)
            self.assertIn("IRREVERSIBLE_REQUIRES_HUMAN_APPROVAL",d.reasons)
        self.assertFalse(d.action_executed); self.assertFalse(d.commit_performed); self.assertFalse(d.permission_granted)
    register(f"test_{idx+1:03d}_irreversible",t)

# Group D: policy identity/version/epoch/revocation/expiry fail closed (20)
for j in range(20):
    mode=j%5; idx=60+j
    def t(self,mode=mode,idx=idx):
        r=req("communicate","send",request_id=f"D-{idx}")
        p=self.policy
        prepared=self.prepared
        if mode==0: r=dataclasses.replace(r,expected_policy_id="WRONG")
        elif mode==1: r=dataclasses.replace(r,expected_policy_version="WRONG")
        elif mode==2: r=dataclasses.replace(r,expected_authority_epoch=99)
        elif mode==3:
            p=dataclasses.replace(p,revoked=True)
        elif mode==4:
            p=dataclasses.replace(p,expires_at=NOW)
        d=m.evaluate_prepared(r,p,prepared,now=NOW)
        self.assertIn(d.decision,(m.ControlDecision.HOLD,m.ControlDecision.DENY))
        self.assertFalse(d.action_executed); self.assertFalse(d.permission_granted)
    register(f"test_{idx+1:03d}_policy_fail_closed",t)

# Group E: invalid input and boundaries (20)
for j in range(20):
    mode=j%5; idx=80+j
    def t(self,mode=mode,idx=idx):
        if mode==0:
            bad=dataclasses.replace(self.candidates[0],reversibility_score=101)
            d=m.evaluate(req("remove_file","delete",request_id=f"E-{idx}"),self.policy,(bad,),now=NOW)
            self.assertEqual(d.decision,m.ControlDecision.HOLD)
        elif mode==1:
            bad=dataclasses.replace(self.candidates[0],risk_score=-1)
            d=m.evaluate(req("remove_file","delete",request_id=f"E-{idx}"),self.policy,(bad,),now=NOW)
            self.assertEqual(d.decision,m.ControlDecision.HOLD)
        elif mode==2:
            d=m.evaluate_prepared(dataclasses.replace(req("communicate","send"),objective=""),self.policy,self.prepared,now=NOW)
            self.assertEqual(d.decision,m.ControlDecision.HOLD)
        elif mode==3:
            dup=(self.candidates[0],self.candidates[0])
            with self.assertRaises(ValueError): m.prepare_catalog(self.policy,dup,now=NOW)
        else:
            r=req("no-such-objective","send",request_id=f"E-{idx}")
            d=m.evaluate_prepared(r,self.policy,self.prepared,now=NOW)
            self.assertEqual(d.decision,m.ControlDecision.HOLD)
            self.assertIn("NO_OBJECTIVE_CANDIDATE",d.reasons)
    register(f"test_{idx+1:03d}_invalid_boundary",t)

# Group F: prepared/full equivalence and determinism (20)
for j in range(20):
    objective,op,_=scenarios[j%len(scenarios)]; idx=100+j
    def t(self,objective=objective,op=op,idx=idx):
        r=req(objective,op,request_id=f"F-{idx}")
        full=m.evaluate(r,self.policy,tuple(reversed(self.candidates)),now=NOW)
        prep=m.evaluate_prepared(r,self.policy,self.prepared,now=NOW)
        self.assertEqual(full,prep)
        self.assertEqual(m.catalog_fingerprint(self.candidates),m.catalog_fingerprint(tuple(reversed(self.candidates))))
        self.assertEqual(m.fingerprint(full),m.fingerprint(prep))
    register(f"test_{idx+1:03d}_prepared_equivalence",t)

# Group G: delta / sync reconstruction (20)
for j in range(20):
    idx=120+j
    def t(self,j=j,idx=idx):
        base=list(make_catalog(60,"G"))
        target=list(base)
        pos=j%20
        target[pos]=dataclasses.replace(target[pos],risk_score=(target[pos].risk_score+7)%100,evidence_binding=f"E-G-CHANGED-{idx}")
        if j%2==0:
            target=target[1:]
            target.append(m.ActionCandidate(f"G-NEW-{idx}","objective-1","draft",99,4,"UNDO","local",False,False,f"E-NEW-{idx}"))
        delta=m.build_catalog_delta(base,target)
        rebuilt=m.apply_catalog_delta(base,delta)
        self.assertEqual(m.catalog_fingerprint(rebuilt),m.catalog_fingerprint(target))
        p=m.prepare_catalog(self.policy,target,now=NOW)
        known=dict(p.item_fingerprints)
        missing_id=sorted(known)[j%len(known)]
        del known[missing_id]
        plan=m.plan_catalog_sync(p,known)
        self.assertEqual(plan.missing_or_changed_ids,(missing_id,))
        self.assertFalse(plan.action_execution_authorized); self.assertFalse(plan.permission_granted)
    register(f"test_{idx+1:03d}_delta_sync",t)

# Group H: authority invariants + static safety (20)
for j in range(20):
    idx=140+j
    def t(self,j=j,idx=idx):
        r=req("communicate","send",request_id=f"H-{idx}")
        d=m.evaluate_prepared(r,self.policy,self.prepared,now=NOW)
        self.assertFalse(d.permission_granted)
        self.assertFalse(d.action_executed)
        self.assertFalse(d.commit_performed)
        self.assertFalse(d.state_mutated)
        self.assertFalse(d.action_success)
        self.assertFalse(d.undo_success)
        self.assertFalse(d.safety_proven)
        if j%4==0:
            src=Path(m.__file__).read_text(encoding="utf-8")
            tree=ast.parse(src)
            forbidden_imports={"subprocess","socket","requests","urllib.request","shutil"}
            imports=set()
            for node in ast.walk(tree):
                if isinstance(node,ast.Import): imports.update(a.name for a in node.names)
                elif isinstance(node,ast.ImportFrom) and node.module: imports.add(node.module)
            self.assertTrue(forbidden_imports.isdisjoint(imports))
        elif j%4==1:
            self.assertEqual(m.fingerprint(self.candidates),m.fingerprint(tuple(self.candidates)))
        elif j%4==2:
            self.assertNotEqual(m.fingerprint(r),"")
        else:
            self.assertEqual(len(d.request_fingerprint),64)
    register(f"test_{idx+1:03d}_authority_static",t)


if __name__ == "__main__":
    unittest.main(verbosity=1)
