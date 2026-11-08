import hashlib, json, unittest
from noepin_al_006_ai_arbitrator import *

H0="0"*64

def policy():
    return ArbitrationPolicy(
        min_evidence_score=50,
        max_risk_for_auto_select=40,
        min_margin_for_auto_select=15,
        require_evidence_refs=True,
        require_validated_authority_for_action_candidate=True,
        policy_version="v2"
    )

def prop(pid="p1", **kw):
    d=dict(
        proposal_id=pid, agent_id="a1", recommendation="OPTION_A",
        evidence_score=80, risk_score=20, policy_compatible=True,
        authority_validated=True, action_candidate=False,
        evidence_refs=("e1",), source_fingerprint=H0, rationale="r", metadata={}
    )
    d.update(kw)
    return Proposal(**d)

def req(*ps, **kw):
    d=dict(topic_id="t1", proposals=tuple(ps) if ps else (prop(),), schema_version="1", context={})
    d.update(kw)
    return ArbitrationRequest(**d)

class T(unittest.TestCase):
    def setUp(self): self.a=AIArbitrator(policy())
    def check(self,r,d):
        o=self.a.arbitrate(r); self.assertEqual(o.decision,d)
        self.assertFalse(o.authoritative); self.assertFalse(o.truth_established)
        self.assertFalse(o.action_executed); self.assertFalse(o.action_succeeded)
        return o

    def test_one_select(self): self.check(req(),ArbitrationDecision.SELECT_CANDIDATE)
    def test_missing_topic(self): self.check(req(topic_id=""),ArbitrationDecision.HOLD)
    def test_missing_schema(self): self.check(req(schema_version=""),ArbitrationDecision.HOLD)
    def test_no_proposals(self): self.check(req(proposals=()),ArbitrationDecision.HOLD)
    def test_duplicate_ids(self): self.check(req(prop("x"),prop("x")),ArbitrationDecision.HOLD)
    def test_missing_proposal_id(self): self.check(req(prop("",agent_id="a")),ArbitrationDecision.REJECT_ALL)
    def test_missing_agent(self): self.check(req(prop(agent_id="")),ArbitrationDecision.REJECT_ALL)
    def test_missing_recommendation(self): self.check(req(prop(recommendation="")),ArbitrationDecision.REJECT_ALL)
    def test_bad_evidence_low(self): self.check(req(prop(evidence_score=-1)),ArbitrationDecision.REJECT_ALL)
    def test_bad_evidence_high(self): self.check(req(prop(evidence_score=101)),ArbitrationDecision.REJECT_ALL)
    def test_bool_evidence_invalid(self): self.check(req(prop(evidence_score=True)),ArbitrationDecision.REJECT_ALL)
    def test_bad_risk(self): self.check(req(prop(risk_score=101)),ArbitrationDecision.REJECT_ALL)
    def test_bad_fingerprint(self): self.check(req(prop(source_fingerprint="bad")),ArbitrationDecision.REJECT_ALL)
    def test_policy_incompatible(self): self.check(req(prop(policy_compatible=False)),ArbitrationDecision.REJECT_ALL)
    def test_evidence_below_min(self): self.check(req(prop(evidence_score=49)),ArbitrationDecision.REJECT_ALL)
    def test_evidence_boundary(self): self.check(req(prop(evidence_score=50,risk_score=0)),ArbitrationDecision.SELECT_CANDIDATE)
    def test_evidence_ref_required(self): self.check(req(prop(evidence_refs=())),ArbitrationDecision.REJECT_ALL)
    def test_action_authority_required(self): self.check(req(prop(action_candidate=True,authority_validated=False)),ArbitrationDecision.REJECT_ALL)
    def test_non_action_does_not_require_authority(self): self.check(req(prop(action_candidate=False,authority_validated=False)),ArbitrationDecision.SELECT_CANDIDATE)

    def test_high_risk_human(self): self.check(req(prop(risk_score=41,evidence_score=100)),ArbitrationDecision.HUMAN_REVIEW)
    def test_risk_boundary_auto(self): self.check(req(prop(risk_score=40,evidence_score=100)),ArbitrationDecision.SELECT_CANDIDATE)

    def test_two_clear_margin_select(self):
        o=self.check(req(prop("a",evidence_score=95,risk_score=10),prop("b",evidence_score=60,risk_score=20)),ArbitrationDecision.SELECT_CANDIDATE)
        self.assertEqual(o.selected_proposal_id,"a")
    def test_two_close_human(self):
        self.check(req(prop("a",evidence_score=80,risk_score=20),prop("b",evidence_score=75,risk_score=20)),ArbitrationDecision.HUMAN_REVIEW)
    def test_exact_margin_15_select(self):
        self.check(req(prop("a",evidence_score=90,risk_score=20),prop("b",evidence_score=75,risk_score=20)),ArbitrationDecision.SELECT_CANDIDATE)
    def test_margin_14_human(self):
        self.check(req(prop("a",evidence_score=89,risk_score=20),prop("b",evidence_score=75,risk_score=20)),ArbitrationDecision.HUMAN_REVIEW)
    def test_conflict_near_risk_boundary_human(self):
        self.check(req(prop("a",recommendation="A",evidence_score=100,risk_score=35),prop("b",recommendation="B",evidence_score=80,risk_score=35)),ArbitrationDecision.HUMAN_REVIEW)
    def test_same_recommendation_near_boundary_can_select(self):
        self.check(req(prop("a",recommendation="A",evidence_score=100,risk_score=35),prop("b",recommendation="A",evidence_score=80,risk_score=35)),ArbitrationDecision.SELECT_CANDIDATE)

    def test_majority_does_not_force_truth(self):
        o=self.check(req(
            prop("a",recommendation="A",evidence_score=80,risk_score=20),
            prop("b",recommendation="B",evidence_score=70,risk_score=20),
            prop("c",recommendation="B",evidence_score=70,risk_score=20),
        ),ArbitrationDecision.HUMAN_REVIEW)
        self.assertFalse(o.truth_established)

    def test_ineligible_filtered(self):
        o=self.check(req(prop("a",evidence_score=95,risk_score=10),prop("b",policy_compatible=False)),ArbitrationDecision.SELECT_CANDIDATE)
        self.assertEqual(o.selected_proposal_id,"a"); self.assertIn("b",o.rejected_proposal_ids)
    def test_all_ineligible_reject(self):
        self.check(req(prop("a",policy_compatible=False),prop("b",evidence_score=10)),ArbitrationDecision.REJECT_ALL)

    def test_human_override_select(self):
        o=self.check(req(prop("a"),prop("b",evidence_score=95,risk_score=10),human_override_proposal_id="a",human_approval_ref="H"),ArbitrationDecision.SELECT_CANDIDATE)
        self.assertEqual(o.selected_proposal_id,"a"); self.assertFalse(o.action_executed)
    def test_human_override_missing_ref(self):
        self.check(req(prop("a"),human_override_proposal_id="a"),ArbitrationDecision.HOLD)
    def test_human_override_target_missing(self):
        self.check(req(prop("a"),human_override_proposal_id="z",human_approval_ref="H"),ArbitrationDecision.HOLD)
    def test_human_override_ineligible(self):
        self.check(req(prop("a",policy_compatible=False),human_override_proposal_id="a",human_approval_ref="H"),ArbitrationDecision.HOLD)

    def test_cache_exact(self):
        r=req(); x=self.a.arbitrate(r); y=self.a.arbitrate(r); self.assertFalse(x.cache_reused); self.assertTrue(y.cache_reused)
    def test_cache_not_authority(self):
        r=req(); self.a.arbitrate(r); self.assertFalse(self.a.arbitrate(r).authoritative)
    def test_cache_not_truth(self):
        r=req(); self.a.arbitrate(r); self.assertFalse(self.a.arbitrate(r).truth_established)
    def test_cache_not_action(self):
        r=req(); self.a.arbitrate(r); self.assertFalse(self.a.arbitrate(r).action_executed)
    def test_cache_diff_proposal(self):
        self.assertNotEqual(self.a.fingerprint(req(prop("a"))),self.a.fingerprint(req(prop("b"))))
    def test_cache_diff_human_override(self):
        r1=req(prop("a"),prop("b")); r2=req(prop("a"),prop("b"),human_override_proposal_id="a",human_approval_ref="H")
        self.assertNotEqual(self.a.fingerprint(r1),self.a.fingerprint(r2))
    def test_context_order(self):
        self.assertEqual(self.a.fingerprint(req(context={"b":2,"a":1})),self.a.fingerprint(req(context={"a":1,"b":2})))
    def test_clear_cache(self):
        self.a.arbitrate(req()); self.assertGreater(self.a.cache_size(),0); self.a.clear_cache(); self.assertEqual(self.a.cache_size(),0)
    def test_stable_no_time(self): self.assertNotIn("created_unix_ns",self.a.arbitrate(req()).stable_payload())

    def test_selected_never_success(self):
        o=self.check(req(),ArbitrationDecision.SELECT_CANDIDATE); self.assertFalse(o.action_succeeded)
    def test_selected_never_truth(self):
        o=self.check(req(),ArbitrationDecision.SELECT_CANDIDATE); self.assertFalse(o.truth_established)
    def test_selected_never_authoritative(self):
        o=self.check(req(),ArbitrationDecision.SELECT_CANDIDATE); self.assertFalse(o.authoritative)

    def test_ranking_uses_risk(self):
        o=self.check(req(prop("a",evidence_score=90,risk_score=40),prop("b",evidence_score=85,risk_score=10)),ArbitrationDecision.SELECT_CANDIDATE)
        self.assertEqual(o.selected_proposal_id,"b")
    def test_ranking_tie_deterministic(self):
        o=self.check(req(prop("a",evidence_score=80,risk_score=20),prop("b",evidence_score=80,risk_score=20)),ArbitrationDecision.HUMAN_REVIEW)
        self.assertIsNone(o.selected_proposal_id)

    def test_many_single_valid(self):
        for i in range(10):
            p=prop(f"p{i}",evidence_score=60+i,risk_score=i)
            self.check(req(p),ArbitrationDecision.SELECT_CANDIDATE)

def replay_fingerprint():
    a=AIArbitrator(policy())
    out=[]
    for i in range(1000):
        p1=prop("a",agent_id="x",recommendation="A",evidence_score=60+(i%35),risk_score=i%40,evidence_refs=(f"e{i%7}",),source_fingerprint=f"{i:x}".rjust(64,"0"))
        p2=prop("b",agent_id="y",recommendation="B" if i%3==0 else "A",evidence_score=55+(i%30),risk_score=(i*3)%45,evidence_refs=(f"f{i%5}",),source_fingerprint=f"{i+10000:x}".rjust(64,"0"))
        r=a.arbitrate(req(p1,p2,topic_id=f"t{i%19}"))
        out.append(r.stable_payload())
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    return hashlib.sha256(raw).hexdigest()

if __name__=="__main__":
    unittest.main()
