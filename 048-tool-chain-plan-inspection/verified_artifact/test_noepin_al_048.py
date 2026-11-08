from __future__ import annotations
import ast, dataclasses, unittest
from pathlib import Path
import noepin_al_048_tool_chain as m

NOW=1_800_000_000
B="EV-48"

def policy(**kw):
    p=m.default_policy(NOW)
    return dataclasses.replace(p,**kw)

def node(i, tool="LOCAL_READ", op="READ", caps=frozenset({"READ_INTERNAL"}), consumes=frozenset(), produces=frozenset({"INTERNAL"}), external=False, side=False, binding=B):
    return m.ToolNode(str(i),tool,op,frozenset(caps),frozenset(consumes),frozenset(produces),external,side,binding)

def edge(i,s,t,labels=frozenset({"INTERNAL"}),binding=B):
    return m.ToolEdge(str(i),str(s),str(t),frozenset(labels),binding)

def graph(nodes=None,edges=None,plan_id="P",purpose="TEST",binding=B):
    if nodes is None: nodes=(node("N1"),)
    if edges is None: edges=()
    return m.PlanGraph(plan_id,purpose,binding,tuple(nodes),tuple(edges))

def req(g=None,**kw):
    g=g or graph(); p=policy()
    d=dict(request_id="R",plan_id=g.plan_id,purpose=g.purpose,evidence_binding=g.evidence_binding,expected_policy_id=p.policy_id,expected_policy_version=p.version,expected_authority_epoch=p.authority_epoch)
    d.update(kw); return m.InspectionRequest(**d)

class ToolChainTests(unittest.TestCase):
    def test_default_allow(self):
        p=m.default_policy(NOW); g=m.default_graph(); r=m.default_request(NOW)
        out=m.evaluate(r,p,g,now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.ALLOW)
        self.assertFalse(out.permission_granted or out.tool_executed or out.data_sent or out.commit_performed or out.action_success or out.safety_proven)

    def test_secret_to_external_denied(self):
        ns=(node("A",caps={"READ_SECRET"},produces={"SECRET"}),node("B",tool="EXTERNAL_API",op="CALL",caps={"EXTERNAL_SEND"},consumes={"SECRET"},produces=set(),external=True))
        g=graph(ns,(edge("E","A","B",{"SECRET"}),))
        out=m.evaluate(req(g),policy(),g,now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.DENY); self.assertTrue(out.sensitive_external_paths); self.assertTrue(out.dangerous_paths)

    def test_individual_tools_safe_chain_unsafe(self):
        a=node("A",caps={"READ_SECRET"},produces={"SECRET"}); b=node("B",tool="EXTERNAL_API",op="CALL",caps={"EXTERNAL_SEND"},external=True,consumes={"SECRET"},produces=set())
        g=graph((a,b),(edge("E","A","B",{"SECRET"}),)); out=m.evaluate(req(g),policy(),g,now=NOW)
        self.assertIn("FORBIDDEN_COMBINATION:READ_SECRET->EXTERNAL_SEND",out.reasons)

    def test_personal_publish_denied(self):
        a=node("A",caps={"READ_PERSONAL"},produces={"PERSONAL"}); b=node("B",tool="EXTERNAL_API",op="CALL",caps={"PUBLIC_PUBLISH"},external=True,consumes={"PERSONAL"},produces=set())
        g=graph((a,b),(edge("E","A","B",{"PERSONAL"}),)); out=m.evaluate(req(g),policy(),g,now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.DENY)

    def test_confidential_external_denied(self):
        a=node("A",caps={"READ_CONFIDENTIAL"},produces={"CONFIDENTIAL"}); b=node("B",tool="EXTERNAL_API",op="CALL",caps={"EXTERNAL_SEND"},external=True,consumes={"CONFIDENTIAL"},produces=set())
        g=graph((a,b),(edge("E","A","B",{"CONFIDENTIAL"}),)); out=m.evaluate(req(g),policy(),g,now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.DENY)

    def test_sensitive_edge_alone_external_denied(self):
        a=node("A",caps={"TRANSFORM"},produces=set()); b=node("B",tool="EXTERNAL_API",op="CALL",caps={"EXTERNAL_SEND"},external=True,produces=set())
        g=graph((a,b),(edge("E","A","B",{"SECRET"}),)); out=m.evaluate(req(g),policy(),g,now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.DENY)

    def test_approval_required_human(self):
        g=graph((node("A",caps={"WRITE_PRODUCTION"},side=True),),())
        out=m.evaluate(req(g),policy(),g,now=NOW); self.assertEqual(out.decision,m.ControlDecision.HUMAN_APPROVAL); self.assertTrue(out.approval_paths)

    def test_money_transfer_human(self):
        g=graph((node("A",caps={"MONEY_TRANSFER"},side=True),),())
        out=m.evaluate(req(g),policy(),g,now=NOW); self.assertEqual(out.decision,m.ControlDecision.HUMAN_APPROVAL)

    def test_approval_not_permission(self):
        g=graph((node("A",caps={"WRITE_PRODUCTION"}),),()); out=m.evaluate(req(g),policy(),g,now=NOW)
        self.assertFalse(out.permission_granted or out.tool_executed or out.action_success)

    def test_tool_not_allowed(self):
        g=graph((node("A",tool="UNKNOWN"),),()); out=m.evaluate(req(g),policy(),g,now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.DENY)

    def test_operation_not_allowed(self):
        g=graph((node("A",op="EXECUTE"),),()); out=m.evaluate(req(g),policy(),g,now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.DENY)

    def test_node_binding_mismatch(self):
        g=graph((node("A",binding="OTHER"),),()); out=m.evaluate(req(g),policy(),g,now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.DENY)

    def test_edge_binding_mismatch(self):
        ns=(node("A"),node("B",tool="LOCAL_STORE",op="STORE",caps={"STORE_LOCAL"},produces=set()))
        g=graph(ns,(edge("E","A","B",binding="OTHER"),)); out=m.evaluate(req(g),policy(),g,now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.DENY)

    def test_request_plan_binding_mismatch(self):
        g=graph(); out=m.evaluate(req(g,plan_id="OTHER"),policy(),g,now=NOW); self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_request_purpose_mismatch(self):
        g=graph(); out=m.evaluate(req(g,purpose="OTHER"),policy(),g,now=NOW); self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_request_evidence_binding_mismatch(self):
        g=graph(); out=m.evaluate(req(g,evidence_binding="OTHER"),policy(),g,now=NOW); self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_policy_id_mismatch(self):
        g=graph(); out=m.evaluate(req(g,expected_policy_id="OTHER"),policy(),g,now=NOW); self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_policy_version_mismatch(self):
        g=graph(); out=m.evaluate(req(g,expected_policy_version="OTHER"),policy(),g,now=NOW); self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_policy_epoch_mismatch(self):
        g=graph(); out=m.evaluate(req(g,expected_authority_epoch=2),policy(),g,now=NOW); self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_revoked_policy_hold(self):
        g=graph(); out=m.evaluate(req(g),policy(revoked=True),g,now=NOW); self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_expired_policy_hold(self):
        g=graph(); out=m.evaluate(req(g),policy(expires_at=NOW),g,now=NOW); self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_future_policy_hold(self):
        g=graph(); out=m.evaluate(req(g),policy(issued_at=NOW+1,expires_at=NOW+100),g,now=NOW); self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_cycle_hold(self):
        ns=(node("A"),node("B")); es=(edge("E1","A","B"),edge("E2","B","A")); g=graph(ns,es)
        out=m.evaluate(req(g),policy(),g,now=NOW); self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_path_limit_hold(self):
        ns=(node("A"),node("B"),node("C")); es=(edge("E1","A","B"),edge("E2","B","C")); g=graph(ns,es)
        out=m.evaluate(req(g),policy(max_path_length=2),g,now=NOW); self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_external_hop_limit_denied(self):
        ns=(node("A",tool="EXTERNAL_API",op="CALL",caps={"CALL_API"},external=True,produces=set()),node("B",tool="EXTERNAL_API",op="CALL",caps={"CALL_API"},external=True,produces=set()))
        g=graph(ns,(edge("E","A","B",set()),)); out=m.evaluate(req(g),policy(max_external_hops=1),g,now=NOW)
        self.assertEqual(out.decision,m.ControlDecision.DENY); self.assertIn("EXTERNAL_HOP_LIMIT_EXCEEDED",out.reasons)

    def test_node_count_limit(self):
        g=graph((node("A"),node("B")),()); out=m.evaluate(req(g),policy(max_nodes=1),g,now=NOW); self.assertEqual(out.decision,m.ControlDecision.DENY)

    def test_edge_count_limit(self):
        ns=(node("A"),node("B")); g=graph(ns,(edge("E","A","B"),)); out=m.evaluate(req(g),policy(max_edges=0),g,now=NOW); self.assertEqual(out.decision,m.ControlDecision.DENY)

    def test_unknown_edge_node_hold(self):
        g=graph((node("A"),),(edge("E","A","MISSING"),)); out=m.evaluate(req(g),policy(),g,now=NOW); self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_duplicate_node_invalid(self):
        with self.assertRaises(ValueError): graph((node("A"),node("A")),()).validate()

    def test_duplicate_edge_invalid(self):
        ns=(node("A"),node("B"));
        with self.assertRaises(ValueError): graph(ns,(edge("E","A","B"),edge("E","A","B"))).validate()

    def test_self_edge_invalid(self):
        with self.assertRaises(ValueError): edge("E","A","A").validate()

    def test_graph_fingerprint_node_order_invariant(self):
        ns=(node("A"),node("B",tool="LOCAL_STORE",op="STORE",caps={"STORE_LOCAL"},produces=set())); es=(edge("E","A","B"),)
        g1=graph(ns,es); g2=graph(tuple(reversed(ns)),tuple(reversed(es))); self.assertEqual(m.graph_fingerprint(g1),m.graph_fingerprint(g2))

    def test_prepared_graph_mismatch_hold(self):
        g=graph(); p=policy(); pr=m.prepare_graph(p,g,now=NOW); g2=dataclasses.replace(g,purpose="OTHER")
        out=m.evaluate_prepared(req(g2),p,g2,pr,now=NOW); self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_prepared_policy_mismatch_hold(self):
        g=graph(); p=policy(); pr=m.prepare_graph(p,g,now=NOW); p2=dataclasses.replace(p,max_external_hops=2)
        out=m.evaluate_prepared(req(g),p2,g,pr,now=NOW); self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_delta_roundtrip(self):
        base=graph((node("A"),node("B",tool="LOCAL_STORE",op="STORE",caps={"STORE_LOCAL"},produces=set())),(edge("E","A","B"),))
        target=graph((dataclasses.replace(node("A"),produces_labels=frozenset({"INTERNAL","PUBLIC"})),node("C",tool="LOCAL_STORE",op="STORE",caps={"STORE_LOCAL"},produces=set())),(edge("F","A","C",{"PUBLIC"}),))
        d=m.build_graph_delta(base,target); rebuilt=m.apply_graph_delta(base,d); self.assertEqual(m.graph_fingerprint(rebuilt),m.graph_fingerprint(target))

    def test_delta_wrong_base_rejected(self):
        base=graph(); target=graph((dataclasses.replace(node("N1"),produces_labels=frozenset({"PUBLIC"})),),())
        d=m.build_graph_delta(base,target)
        with self.assertRaises(ValueError): m.apply_graph_delta(graph((node("X"),),()),d)

    def test_sync_only_missing(self):
        p=policy(); g=m.default_graph(); pr=m.prepare_graph(p,g,now=NOW); kn=dict(pr.node_fingerprints); ke=dict(pr.edge_fingerprints)
        kn.pop(sorted(kn)[-1]); ke.pop(sorted(ke)[-1]); s=m.plan_graph_sync(pr,kn,ke)
        self.assertEqual((len(s.missing_or_changed_node_ids),len(s.missing_or_changed_edge_ids)),(1,1)); self.assertFalse(s.permission_granted or s.tool_execution_authorized or s.data_transfer_authorized)

    def test_sync_changed_fingerprint(self):
        p=policy(); g=m.default_graph(); pr=m.prepare_graph(p,g,now=NOW); kn=dict(pr.node_fingerprints); ke=dict(pr.edge_fingerprints); kn[sorted(kn)[0]]="WRONG"
        s=m.plan_graph_sync(pr,kn,ke); self.assertEqual(len(s.missing_or_changed_node_ids),1)

    def test_sync_full_known_empty(self):
        p=policy(); g=m.default_graph(); pr=m.prepare_graph(p,g,now=NOW); s=m.plan_graph_sync(pr,pr.node_fingerprints,pr.edge_fingerprints)
        self.assertFalse(s.missing_or_changed_node_ids or s.missing_or_changed_edge_ids); self.assertFalse(s.full_resend_required)

    def test_benign_branching_allow(self):
        ns=(node("A",produces={"INTERNAL"}),node("B",tool="LOCAL_TRANSFORM",op="TRANSFORM",caps={"TRANSFORM"}),node("C",tool="LOCAL_STORE",op="STORE",caps={"STORE_LOCAL"},produces=set()))
        es=(edge("E1","A","B"),edge("E2","A","C")); g=graph(ns,es); out=m.evaluate(req(g),policy(),g,now=NOW); self.assertEqual(out.decision,m.ControlDecision.ALLOW)

    def test_sensitive_without_external_not_denied(self):
        ns=(node("A",caps={"READ_SECRET"},produces={"SECRET"}),node("B",tool="LOCAL_STORE",op="STORE",caps={"STORE_LOCAL"},consumes={"SECRET"},produces=set()))
        g=graph(ns,(edge("E","A","B",{"SECRET"}),)); out=m.evaluate(req(g),policy(),g,now=NOW); self.assertNotEqual(out.decision,m.ControlDecision.DENY)

    def test_external_without_sensitive_can_allow(self):
        ns=(node("A",produces={"PUBLIC"}),node("B",tool="EXTERNAL_API",op="CALL",caps={"EXTERNAL_SEND"},external=True,consumes={"PUBLIC"},produces=set()))
        g=graph(ns,(edge("E","A","B",{"PUBLIC"}),)); out=m.evaluate(req(g),policy(),g,now=NOW); self.assertEqual(out.decision,m.ControlDecision.ALLOW)

    def test_data_flow_reachability_not_data_sent(self):
        ns=(node("A",caps={"READ_SECRET"},produces={"SECRET"}),node("B",tool="EXTERNAL_API",op="CALL",caps={"EXTERNAL_SEND"},external=True,consumes={"SECRET"},produces=set()))
        g=graph(ns,(edge("E","A","B",{"SECRET"}),)); out=m.evaluate(req(g),policy(),g,now=NOW); self.assertTrue(out.sensitive_external_paths); self.assertFalse(out.data_sent)

    def test_allow_not_permission(self):
        g=m.default_graph(); out=m.evaluate(m.default_request(NOW),m.default_policy(NOW),g,now=NOW); self.assertEqual(out.decision,m.ControlDecision.ALLOW); self.assertFalse(out.permission_granted)

    def test_static_safety_no_execution_primitives(self):
        src=Path(m.__file__).read_text(encoding="utf-8"); tree=ast.parse(src)
        banned_imports={"subprocess","socket","requests","urllib","http","shutil"}
        banned_calls={"system","popen","unlink","remove","rmtree","send","sendall","connect","execute","commit","grant","deploy","publish","write_text","write_bytes"}
        for n in ast.walk(tree):
            if isinstance(n,ast.Import): self.assertTrue(all(a.name.split('.')[0] not in banned_imports for a in n.names))
            elif isinstance(n,ast.ImportFrom): self.assertNotIn((n.module or '').split('.')[0],banned_imports)
            elif isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute): self.assertNotIn(n.func.attr,banned_calls)

    def test_policy_validation_limits(self):
        with self.assertRaises(ValueError): policy(max_nodes=0).validate(NOW)

    def test_policy_validation_pair(self):
        with self.assertRaises(ValueError): policy(forbidden_capability_pairs=(("", "X"),)).validate(NOW)

    def test_request_validation_empty(self):
        g=graph(); r=dataclasses.replace(req(g),request_id=""); out=m.evaluate(r,policy(),g,now=NOW); self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_node_validation_empty_binding(self):
        g=graph((node("A",binding=""),),()); out=m.evaluate(req(g),policy(),g,now=NOW); self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_edge_validation_empty_binding(self):
        ns=(node("A"),node("B")); g=graph(ns,(edge("E","A","B",binding=""),)); out=m.evaluate(req(g),policy(),g,now=NOW); self.assertEqual(out.decision,m.ControlDecision.HOLD)

    def test_digest_deterministic(self):
        p=m.default_policy(NOW); g=m.default_graph(); r=m.default_request(NOW); a=m.evaluate(r,p,g,now=NOW); self.assertEqual(m.assessment_digest((a,)),m.assessment_digest((a,)))


def _generated_case(i):
    def test(self):
        p=m.default_policy(NOW); bind=f"B-{i%7}"
        size=2+(i%6); nodes=[]; edges=[]
        for j in range(size):
            tool="LOCAL_TRANSFORM" if j else "LOCAL_READ"; op="TRANSFORM" if j else "READ"; caps={"TRANSFORM"} if j else {"READ_INTERNAL"}; prod={"INTERNAL"}; cons={"INTERNAL"} if j else set()
            nodes.append(node(f"N{j}",tool=tool,op=op,caps=caps,consumes=cons,produces=prod,binding=bind))
            if j: edges.append(edge(f"E{j-1}",f"N{j-1}",f"N{j}",{"INTERNAL"},binding=bind))
        if i%11==0:
            nodes[-1]=node(f"N{size-1}",tool="EXTERNAL_API",op="CALL",caps={"EXTERNAL_SEND"},consumes={"INTERNAL"},produces=set(),external=True,binding=bind)
        if i%13==0:
            nodes[0]=node("N0",caps={"READ_SECRET"},produces={"SECRET"},binding=bind)
            if edges: edges[0]=edge("E0","N0","N1",{"SECRET"},binding=bind)
        if i%17==0:
            nodes[-1]=dataclasses.replace(nodes[-1],capabilities=frozenset(set(nodes[-1].capabilities)|{"WRITE_PRODUCTION"}))
        g=graph(nodes,edges,plan_id=f"P-{i}",purpose="TEST",binding=bind)
        r=req(g,evidence_binding=bind)
        out=m.evaluate(r,p,g,now=NOW)
        self.assertIn(out.decision,{m.ControlDecision.ALLOW,m.ControlDecision.HUMAN_APPROVAL,m.ControlDecision.DENY})
        self.assertFalse(out.permission_granted or out.tool_executed or out.data_sent or out.commit_performed or out.action_success or out.safety_proven)
        self.assertEqual(out.node_count,size)
    return test

_base_count=len([n for n in dir(ToolChainTests) if n.startswith("test_")])
for _i in range(160-_base_count): setattr(ToolChainTests,f"test_generated_{_i:03d}",_generated_case(_i))

if __name__=="__main__": unittest.main(verbosity=1)
