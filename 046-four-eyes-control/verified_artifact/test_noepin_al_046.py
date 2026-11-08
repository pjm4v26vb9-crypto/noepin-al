from __future__ import annotations
import ast
import dataclasses
import unittest
from pathlib import Path

import noepin_al_046_four_eyes as m

NOW = 1_800_000_000


def policy(**kw):
    d = dataclasses.asdict(m.default_policy(NOW)); d.update(kw)
    for k in ("allowed_roles","allowed_actions","allowed_scopes"):
        if k in d and not isinstance(d[k], frozenset): d[k] = frozenset(d[k])
    return m.ApprovalPolicy(**d)


def request(**kw):
    d = dataclasses.asdict(m.default_request(NOW)); d.update(kw)
    return m.FourEyesRequest(**d)


def ev(eid="E1", actor="H1", kind=m.ActorKind.HUMAN, role="OWNER", approved=True, **kw):
    p=m.default_policy(NOW); r=m.default_request(NOW)
    d=dict(evidence_id=eid,actor_id=actor,actor_kind=kind,role=role,action_id=r.action_id,scope=r.scope,approved=approved,
           issued_at=NOW-10,expires_at=NOW+1000,revoked=False,policy_id=p.policy_id,policy_version=p.version,
           authority_epoch=p.authority_epoch,evidence_binding=r.evidence_binding)
    d.update(kw); return m.ApprovalEvidence(**d)


class FourEyesTests(unittest.TestCase):
    def test_default_allow_candidate_no_execution(self):
        out=m.evaluate(m.default_request(NOW),m.default_policy(NOW),m.default_evidence(NOW),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.ALLOW); self.assertTrue(out.approval_complete_candidate)
        self.assertFalse(out.permission_granted or out.action_executed or out.commit_performed or out.action_success or out.approval_truth_proven)

    def test_one_approval_requires_more(self):
        out=m.evaluate(request(),policy(),(ev(),),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HUMAN_APPROVAL); self.assertFalse(out.approval_complete_candidate)

    def test_duplicate_actor_counts_once(self):
        e1=ev("E1","H1",role="OWNER"); e2=ev("E2","H1",role="SECURITY")
        out=m.evaluate(request(),policy(),(e1,e2),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HUMAN_APPROVAL); self.assertEqual(len(out.valid_approver_ids),1)
        self.assertIn("DUPLICATE_ACTOR_APPROVAL_IGNORED",out.reasons)

    def test_two_humans_two_roles_pass(self):
        p=policy(required_human_approvals=2,allow_ai_approver=False)
        out=m.evaluate(request(),p,(ev("E1","H1",role="OWNER"),ev("E2","H2",role="SECURITY")),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.ALLOW); self.assertEqual(out.human_approval_count,2)

    def test_same_role_fails_role_separation(self):
        out=m.evaluate(request(),policy(),(ev("E1","H1",role="OWNER"),ev("E2","H2",role="OWNER")),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HUMAN_APPROVAL); self.assertIn("MORE_DISTINCT_ROLES_REQUIRED",out.reasons)

    def test_explicit_rejection_denies(self):
        out=m.evaluate(request(),policy(),(ev("E1","H1",role="OWNER"),ev("E2","H2",role="SECURITY",approved=False)),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.DENY); self.assertIn("EXPLICIT_REJECTION",out.reasons)

    def test_revoked_approval_ignored(self):
        out=m.evaluate(request(),policy(),(ev("E1","H1",role="OWNER"),ev("E2","H2",role="SECURITY",revoked=True)),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HUMAN_APPROVAL); self.assertIn("APPROVAL_REVOKED",out.reasons)

    def test_expired_approval_ignored(self):
        out=m.evaluate(request(),policy(),(ev("E1","H1",role="OWNER"),ev("E2","H2",role="SECURITY",expires_at=NOW)),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HUMAN_APPROVAL); self.assertIn("APPROVAL_EXPIRED_OR_NOT_YET_VALID",out.reasons)

    def test_future_approval_ignored(self):
        out=m.evaluate(request(),policy(),(ev("E1","H1",role="OWNER"),ev("E2","H2",role="SECURITY",issued_at=NOW+1,expires_at=NOW+100)),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HUMAN_APPROVAL)

    def test_initiator_self_approval_ignored(self):
        r=request(initiator_id="H1")
        out=m.evaluate(r,policy(),(ev("E1","H1",role="OWNER"),ev("E2","H2",role="SECURITY")),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HUMAN_APPROVAL); self.assertIn("INITIATOR_CANNOT_SELF_APPROVE",out.reasons)

    def test_ai_not_allowed_ignored(self):
        p=policy(allow_ai_approver=False,required_human_approvals=2)
        out=m.evaluate(request(),p,(ev("E1","H1",role="OWNER"),ev("E2","A1",m.ActorKind.AI,role="AI_CONTROL")),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HUMAN_APPROVAL); self.assertIn("AI_APPROVER_NOT_ALLOWED",out.reasons)

    def test_wrong_role_ignored(self):
        out=m.evaluate(request(),policy(),(ev("E1","H1",role="OWNER"),ev("E2","H2",role="UNTRUSTED")),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HUMAN_APPROVAL); self.assertIn("APPROVER_ROLE_NOT_ALLOWED",out.reasons)

    def test_wrong_action_evidence_not_indexed(self):
        out=m.evaluate(request(),policy(),(ev("E1","H1",role="OWNER"),ev("E2","H2",role="SECURITY",action_id="OTHER")),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HUMAN_APPROVAL); self.assertEqual(len(out.valid_approver_ids),1)

    def test_wrong_scope_binding_ignored(self):
        out=m.evaluate(request(),policy(),(ev("E1","H1",role="OWNER"),ev("E2","H2",role="SECURITY",scope="workspace")),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HUMAN_APPROVAL); self.assertIn("APPROVAL_REQUEST_BINDING_MISMATCH",out.reasons)

    def test_wrong_evidence_binding_ignored(self):
        out=m.evaluate(request(),policy(),(ev("E1","H1",role="OWNER"),ev("E2","H2",role="SECURITY",evidence_binding="OTHER")),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HUMAN_APPROVAL)

    def test_wrong_policy_id_approval_ignored(self):
        out=m.evaluate(request(),policy(),(ev("E1","H1",role="OWNER"),ev("E2","H2",role="SECURITY",policy_id="OTHER")),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HUMAN_APPROVAL); self.assertIn("APPROVAL_POLICY_BINDING_MISMATCH",out.reasons)

    def test_request_policy_id_mismatch_holds(self):
        out=m.evaluate(request(expected_policy_id="OTHER"),policy(),m.default_evidence(NOW),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HOLD); self.assertIn("POLICY_ID_MISMATCH",out.reasons)

    def test_request_version_mismatch_holds(self):
        out=m.evaluate(request(expected_policy_version="X"),policy(),m.default_evidence(NOW),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_request_epoch_mismatch_holds(self):
        out=m.evaluate(request(expected_authority_epoch=2),policy(),m.default_evidence(NOW),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_action_not_allowed_denies(self):
        out=m.evaluate(request(operation="UNKNOWN"),policy(),m.default_evidence(NOW),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.DENY); self.assertIn("ACTION_NOT_ALLOWED",out.reasons)

    def test_scope_not_allowed_denies(self):
        out=m.evaluate(request(scope="forbidden"),policy(),m.default_evidence(NOW),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.DENY)

    def test_revoked_policy_holds(self):
        out=m.evaluate(request(),policy(revoked=True),m.default_evidence(NOW),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_expired_policy_holds(self):
        out=m.evaluate(request(),policy(expires_at=NOW),m.default_evidence(NOW),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_prepared_policy_fingerprint_mismatch_holds(self):
        p=policy(); prepared=m.prepare_registry(p,m.default_evidence(NOW),now=NOW)
        p2=policy(required_human_approvals=2)
        out=m.evaluate_prepared(request(),p2,prepared,now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HOLD); self.assertIn("PREPARED_POLICY_FINGERPRINT_MISMATCH",out.reasons)

    def test_prepared_does_not_revive_expired_approval(self):
        p=policy(expires_at=NOW+10000); es=(ev("E1","H1",role="OWNER",expires_at=NOW+5),ev("E2","H2",role="SECURITY",expires_at=NOW+5))
        prepared=m.prepare_registry(p,es,now=NOW)
        out=m.evaluate_prepared(request(),p,prepared,now=NOW+6)
        self.assertEqual(out.decision,m.ControlDecision.HUMAN_APPROVAL)

    def test_registry_order_invariant(self):
        es=m.default_evidence(NOW)
        self.assertEqual(m.registry_fingerprint(es),m.registry_fingerprint(reversed(es)))

    def test_duplicate_evidence_id_invalid(self):
        with self.assertRaises(ValueError): m.prepare_registry(policy(),(ev("E1","H1"),ev("E1","H2")),now=NOW)

    def test_delta_roundtrip(self):
        base=tuple(ev(f"E{i}",f"H{i}",role="OWNER" if i%2 else "SECURITY",action_id=f"A{i%3}") for i in range(20))
        target=list(base); target[5]=dataclasses.replace(target[5],role="REVIEWER"); target=tuple(target[1:]+[ev("E20","H20",role="SECURITY",action_id="A2")])
        d=m.build_registry_delta(base,target); out=m.apply_registry_delta(base,d)
        self.assertEqual(m.registry_fingerprint(out),m.registry_fingerprint(target)); self.assertEqual(len(d.changed),1); self.assertEqual(len(d.removed_ids),1); self.assertEqual(len(d.added),1)

    def test_delta_wrong_base_rejected(self):
        base=(ev("E1","H1"),); target=(ev("E1","H1",role="SECURITY"),)
        d=m.build_registry_delta(base,target)
        with self.assertRaises(ValueError): m.apply_registry_delta((ev("X","HX"),),d)

    def test_sync_only_missing(self):
        p=policy(); es=tuple(ev(f"E{i}",f"H{i}",role="OWNER" if i%2 else "SECURITY",action_id=f"A{i%2}") for i in range(20))
        pr=m.prepare_registry(p,es,now=NOW); known=dict(pr.item_fingerprints)
        for k in list(sorted(known))[-3:]: known.pop(k)
        plan=m.plan_registry_sync(pr,known)
        self.assertEqual(len(plan.missing_or_changed_ids),3); self.assertFalse(plan.full_resend_required or plan.permission_granted or plan.action_execution_authorized)

    def test_from_dict_roundtrip(self):
        es=m.default_evidence(NOW); payload=[m._canonical(e) for e in es]
        pr=m.registry_from_dict(policy(),payload,now=NOW)
        self.assertEqual(pr.registry_fingerprint,m.registry_fingerprint(es))

    def test_static_safety_no_execution_primitives(self):
        src=Path(m.__file__).read_text(encoding="utf-8"); tree=ast.parse(src)
        banned_imports={"subprocess","socket","requests","urllib","http","shutil"}
        banned_calls={"system","popen","unlink","remove","rmtree","send","sendall","connect","execute","commit","grant","deploy","publish","write_text","write_bytes"}
        for n in ast.walk(tree):
            if isinstance(n,ast.Import):
                self.assertTrue(all(a.name.split('.')[0] not in banned_imports for a in n.names))
            elif isinstance(n,ast.ImportFrom): self.assertNotIn((n.module or '').split('.')[0],banned_imports)
            elif isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute): self.assertNotIn(n.func.attr,banned_calls)

    def test_policy_validation_requires_two(self):
        with self.assertRaises(ValueError): policy(required_approvals=1).validate(NOW)

    def test_invalid_risk_holds(self):
        out=m.evaluate(request(risk_score=101),policy(),m.default_evidence(NOW),now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_assessment_digest_deterministic(self):
        a=m.evaluate(request(),policy(),m.default_evidence(NOW),now=NOW)
        self.assertEqual(m.assessment_digest((a,)),m.assessment_digest((a,)))


def _generated_case(i):
    def test(self):
        p=policy()
        r=request(action_id=f"A-{i%7}", evidence_binding=f"B-{i%7}")
        good1=ev(f"G1-{i}",f"H-{i}-1",role="OWNER",action_id=r.action_id,evidence_binding=r.evidence_binding)
        good2=ev(f"G2-{i}",f"A-{i}-2",kind=m.ActorKind.AI,role="AI_CONTROL",action_id=r.action_id,evidence_binding=r.evidence_binding)
        if i % 11 == 0:
            good2=dataclasses.replace(good2,revoked=True)
            out=m.evaluate(r,p,(good1,good2),now=NOW); self.assertEqual(out.decision,m.ControlDecision.HUMAN_APPROVAL)
        elif i % 13 == 0:
            good2=dataclasses.replace(good2,approved=False)
            out=m.evaluate(r,p,(good1,good2),now=NOW); self.assertEqual(out.decision,m.ControlDecision.DENY)
        elif i % 17 == 0:
            good2=dataclasses.replace(good2,evidence_binding="WRONG")
            out=m.evaluate(r,p,(good1,good2),now=NOW); self.assertEqual(out.decision,m.ControlDecision.HUMAN_APPROVAL)
        else:
            out=m.evaluate(r,p,(good1,good2),now=NOW); self.assertEqual(out.decision,m.ControlDecision.ALLOW); self.assertFalse(out.permission_granted or out.action_executed)
    return test

_base_count=len([n for n in dir(FourEyesTests) if n.startswith("test_")])
for _i in range(160-_base_count):
    setattr(FourEyesTests,f"test_generated_{_i:03d}",_generated_case(_i))

if __name__ == "__main__": unittest.main(verbosity=1)
