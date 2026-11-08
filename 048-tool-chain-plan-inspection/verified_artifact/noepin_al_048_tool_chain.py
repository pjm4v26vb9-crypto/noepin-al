"""NOEPIN AL 048 — Tool-Chain Plan Inspection.

Pure control-plane evaluator for Plan Graph / Combination Rule / Data-flow Analysis.
It detects dangerous multi-tool paths even when individual tools are locally allowed.
It never grants permission, invokes tools, sends data, commits state, or treats graph
reachability / fingerprints as truth, authority, safety proof, or execution success.

Creator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support using ChatGPT
License / Rights: NOT SPECIFIED
"""
from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json
from typing import Any, FrozenSet, Iterable, Mapping, Tuple


class ControlDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    HOLD = "HOLD"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"


@dataclass(frozen=True)
class ChainPolicy:
    policy_id: str
    version: str
    authority_epoch: int
    issued_at: int
    expires_at: int
    allowed_tools: FrozenSet[str]
    allowed_operations: FrozenSet[str]
    sensitive_labels: FrozenSet[str]
    external_sink_capabilities: FrozenSet[str]
    approval_required_capabilities: FrozenSet[str]
    forbidden_capability_pairs: Tuple[Tuple[str, str], ...]
    max_nodes: int
    max_edges: int
    max_path_length: int
    max_external_hops: int
    require_edge_binding: bool = True
    revoked: bool = False

    def validate(self, now: int) -> None:
        if not self.policy_id or not self.version:
            raise ValueError("policy id/version required")
        if self.authority_epoch < 1:
            raise ValueError("authority_epoch must be >=1")
        if self.issued_at < 0 or self.expires_at <= self.issued_at:
            raise ValueError("invalid policy lifetime")
        if not self.issued_at <= now < self.expires_at:
            raise ValueError("policy not current")
        if not self.allowed_tools or not self.allowed_operations:
            raise ValueError("allowed tools/operations required")
        if self.max_nodes < 1 or self.max_edges < 0 or self.max_path_length < 1 or self.max_external_hops < 0:
            raise ValueError("invalid plan limits")
        for pair in self.forbidden_capability_pairs:
            if len(pair) != 2 or not pair[0] or not pair[1]:
                raise ValueError("invalid forbidden capability pair")


@dataclass(frozen=True)
class ToolNode:
    node_id: str
    tool_id: str
    operation: str
    capabilities: FrozenSet[str]
    consumes_labels: FrozenSet[str]
    produces_labels: FrozenSet[str]
    external_boundary: bool
    side_effect: bool
    evidence_binding: str

    def validate(self) -> None:
        if not self.node_id or not self.tool_id or not self.operation:
            raise ValueError("node/tool/operation required")
        if not self.evidence_binding:
            raise ValueError("node evidence binding required")
        if any(not x for x in self.capabilities | self.consumes_labels | self.produces_labels):
            raise ValueError("empty node metadata")


@dataclass(frozen=True)
class ToolEdge:
    edge_id: str
    source_id: str
    target_id: str
    data_labels: FrozenSet[str]
    evidence_binding: str

    def validate(self) -> None:
        if not self.edge_id or not self.source_id or not self.target_id:
            raise ValueError("edge/source/target required")
        if self.source_id == self.target_id:
            raise ValueError("self edge not allowed")
        if not self.evidence_binding:
            raise ValueError("edge evidence binding required")
        if any(not x for x in self.data_labels):
            raise ValueError("empty edge label")


@dataclass(frozen=True)
class PlanGraph:
    plan_id: str
    purpose: str
    evidence_binding: str
    nodes: Tuple[ToolNode, ...]
    edges: Tuple[ToolEdge, ...]

    def validate(self) -> None:
        if not self.plan_id or not self.purpose or not self.evidence_binding:
            raise ValueError("plan identity/purpose/binding required")
        _normalize_nodes(self.nodes)
        _normalize_edges(self.edges, self.nodes)


@dataclass(frozen=True)
class InspectionRequest:
    request_id: str
    plan_id: str
    purpose: str
    evidence_binding: str
    expected_policy_id: str
    expected_policy_version: str
    expected_authority_epoch: int

    def validate(self) -> None:
        if not self.request_id or not self.plan_id or not self.purpose or not self.evidence_binding:
            raise ValueError("request identity/purpose/binding required")
        if not self.expected_policy_id or not self.expected_policy_version or self.expected_authority_epoch < 1:
            raise ValueError("expected policy binding required")


@dataclass(frozen=True)
class PreparedPlanGraph:
    graph_fingerprint: str
    policy_fingerprint: str
    nodes: Tuple[ToolNode, ...]
    edges: Tuple[ToolEdge, ...]
    node_fingerprints: Mapping[str, str]
    edge_fingerprints: Mapping[str, str]
    adjacency: Mapping[str, Tuple[str, ...]]
    reverse_adjacency: Mapping[str, Tuple[str, ...]]


@dataclass(frozen=True)
class GraphDelta:
    base_fingerprint: str
    target_fingerprint: str
    changed_nodes: Tuple[ToolNode, ...]
    removed_node_ids: Tuple[str, ...]
    added_nodes: Tuple[ToolNode, ...]
    changed_edges: Tuple[ToolEdge, ...]
    removed_edge_ids: Tuple[str, ...]
    added_edges: Tuple[ToolEdge, ...]


@dataclass(frozen=True)
class GraphSyncPlan:
    missing_or_changed_node_ids: Tuple[str, ...]
    missing_or_changed_edge_ids: Tuple[str, ...]
    metadata_bytes_required: int
    full_metadata_bytes: int
    full_resend_required: bool
    permission_granted: bool = False
    tool_execution_authorized: bool = False
    data_transfer_authorized: bool = False


@dataclass(frozen=True)
class PlanAssessment:
    decision: ControlDecision
    reasons: Tuple[str, ...]
    request_id: str
    plan_id: str
    dangerous_paths: Tuple[Tuple[str, ...], ...]
    sensitive_external_paths: Tuple[Tuple[str, ...], ...]
    approval_paths: Tuple[Tuple[str, ...], ...]
    graph_fingerprint: str
    policy_fingerprint: str
    request_fingerprint: str
    node_count: int
    edge_count: int
    max_observed_path_length: int
    external_hop_count: int
    permission_granted: bool = False
    tool_executed: bool = False
    data_sent: bool = False
    commit_performed: bool = False
    action_success: bool = False
    safety_proven: bool = False


def _canonical(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {f.name: _canonical(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (set, frozenset)):
        vals = [_canonical(v) for v in value]
        return sorted(vals, key=lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    if isinstance(value, (tuple, list)):
        return [_canonical(v) for v in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_canonical(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _normalize_nodes(nodes: Iterable[ToolNode]) -> Tuple[ToolNode, ...]:
    out = tuple(sorted(nodes, key=lambda n: n.node_id))
    ids = [n.node_id for n in out]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate node_id")
    for n in out:
        n.validate()
    return out


def _normalize_edges(edges: Iterable[ToolEdge], nodes: Iterable[ToolNode]) -> Tuple[ToolEdge, ...]:
    node_ids = {n.node_id for n in nodes}
    out = tuple(sorted(edges, key=lambda e: e.edge_id))
    ids = [e.edge_id for e in out]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate edge_id")
    for e in out:
        e.validate()
        if e.source_id not in node_ids or e.target_id not in node_ids:
            raise ValueError("edge references unknown node")
    return out


def graph_fingerprint(graph: PlanGraph) -> str:
    graph.validate()
    return fingerprint({
        "plan_id": graph.plan_id,
        "purpose": graph.purpose,
        "evidence_binding": graph.evidence_binding,
        "nodes": _normalize_nodes(graph.nodes),
        "edges": _normalize_edges(graph.edges, graph.nodes),
    })


def prepare_graph(policy: ChainPolicy, graph: PlanGraph, *, now: int) -> PreparedPlanGraph:
    policy.validate(now)
    if policy.revoked:
        raise ValueError("policy revoked")
    graph.validate()
    nodes = _normalize_nodes(graph.nodes)
    edges = _normalize_edges(graph.edges, nodes)
    node_fps = {n.node_id: fingerprint(n) for n in nodes}
    edge_fps = {e.edge_id: fingerprint(e) for e in edges}
    adj: dict[str, list[str]] = {n.node_id: [] for n in nodes}
    rev: dict[str, list[str]] = {n.node_id: [] for n in nodes}
    for e in edges:
        adj[e.source_id].append(e.target_id)
        rev[e.target_id].append(e.source_id)
    return PreparedPlanGraph(
        graph_fingerprint=graph_fingerprint(graph),
        policy_fingerprint=fingerprint(policy),
        nodes=nodes,
        edges=edges,
        node_fingerprints=node_fps,
        edge_fingerprints=edge_fps,
        adjacency={k: tuple(sorted(v)) for k, v in sorted(adj.items())},
        reverse_adjacency={k: tuple(sorted(v)) for k, v in sorted(rev.items())},
    )


def _all_paths(prepared: PreparedPlanGraph, max_len: int) -> Tuple[Tuple[str, ...], ...]:
    indeg = {n.node_id: 0 for n in prepared.nodes}
    for e in prepared.edges:
        indeg[e.target_id] += 1
    roots = tuple(sorted(k for k, v in indeg.items() if v == 0))
    if not roots and prepared.nodes:
        raise ValueError("plan cycle or no root")
    result: list[Tuple[str, ...]] = []
    stack: list[Tuple[str, Tuple[str, ...]]] = [(r, (r,)) for r in reversed(roots)]
    while stack:
        cur, path = stack.pop()
        nxt = prepared.adjacency.get(cur, ())
        if not nxt:
            result.append(path)
            continue
        for target in reversed(nxt):
            if target in path:
                raise ValueError("plan cycle detected")
            new_path = path + (target,)
            if len(new_path) > max_len:
                raise ValueError("path length limit exceeded")
            stack.append((target, new_path))
    return tuple(sorted(set(result)))


def _edge_map(prepared: PreparedPlanGraph) -> Mapping[Tuple[str, str], Tuple[ToolEdge, ...]]:
    out: dict[Tuple[str, str], list[ToolEdge]] = {}
    for e in prepared.edges:
        out.setdefault((e.source_id, e.target_id), []).append(e)
    return {k: tuple(sorted(v, key=lambda x: x.edge_id)) for k, v in out.items()}


def _empty_assessment(request: InspectionRequest, graph: PlanGraph, policy: ChainPolicy, decision: ControlDecision,
                      reasons: Iterable[str]) -> PlanAssessment:
    return PlanAssessment(
        decision=decision,
        reasons=tuple(sorted(set(reasons))),
        request_id=request.request_id,
        plan_id=request.plan_id,
        dangerous_paths=(),
        sensitive_external_paths=(),
        approval_paths=(),
        graph_fingerprint=fingerprint(graph),
        policy_fingerprint=fingerprint(policy),
        request_fingerprint=fingerprint(request),
        node_count=len(graph.nodes), edge_count=len(graph.edges), max_observed_path_length=0, external_hop_count=0,
    )


def evaluate_prepared(request: InspectionRequest, policy: ChainPolicy, graph: PlanGraph,
                      prepared: PreparedPlanGraph, *, now: int) -> PlanAssessment:
    try:
        request.validate(); policy.validate(now); graph.validate()
    except ValueError as exc:
        return _empty_assessment(request, graph, policy, ControlDecision.HOLD, (f"INVALID_INPUT:{exc}",))
    if policy.revoked:
        return _empty_assessment(request, graph, policy, ControlDecision.HOLD, ("POLICY_REVOKED",))
    if request.expected_policy_id != policy.policy_id or request.expected_policy_version != policy.version or request.expected_authority_epoch != policy.authority_epoch:
        return _empty_assessment(request, graph, policy, ControlDecision.HOLD, ("POLICY_BINDING_MISMATCH",))
    if request.plan_id != graph.plan_id or request.purpose != graph.purpose or request.evidence_binding != graph.evidence_binding:
        return _empty_assessment(request, graph, policy, ControlDecision.HOLD, ("PLAN_REQUEST_BINDING_MISMATCH",))
    if prepared.policy_fingerprint != fingerprint(policy):
        return _empty_assessment(request, graph, policy, ControlDecision.HOLD, ("PREPARED_POLICY_FINGERPRINT_MISMATCH",))
    if prepared.graph_fingerprint != graph_fingerprint(graph):
        return _empty_assessment(request, graph, policy, ControlDecision.HOLD, ("PREPARED_GRAPH_FINGERPRINT_MISMATCH",))
    if len(prepared.nodes) > policy.max_nodes or len(prepared.edges) > policy.max_edges:
        return _empty_assessment(request, graph, policy, ControlDecision.DENY, ("PLAN_SIZE_LIMIT_EXCEEDED",))

    reasons: set[str] = set()
    for n in prepared.nodes:
        if n.tool_id not in policy.allowed_tools:
            reasons.add(f"TOOL_NOT_ALLOWED:{n.tool_id}")
        if n.operation not in policy.allowed_operations:
            reasons.add(f"OPERATION_NOT_ALLOWED:{n.operation}")
        if n.evidence_binding != graph.evidence_binding:
            reasons.add(f"NODE_BINDING_MISMATCH:{n.node_id}")
    if policy.require_edge_binding:
        for e in prepared.edges:
            if e.evidence_binding != graph.evidence_binding:
                reasons.add(f"EDGE_BINDING_MISMATCH:{e.edge_id}")
    if reasons:
        return replace(_empty_assessment(request, graph, policy, ControlDecision.DENY, reasons),
                       graph_fingerprint=prepared.graph_fingerprint, policy_fingerprint=prepared.policy_fingerprint)

    try:
        paths = _all_paths(prepared, policy.max_path_length)
    except ValueError as exc:
        return replace(_empty_assessment(request, graph, policy, ControlDecision.HOLD, (f"INVALID_PLAN_GRAPH:{exc}",)),
                       graph_fingerprint=prepared.graph_fingerprint, policy_fingerprint=prepared.policy_fingerprint)

    nodes = {n.node_id: n for n in prepared.nodes}
    edge_map = _edge_map(prepared)
    dangerous: list[Tuple[str, ...]] = []
    sensitive_external: list[Tuple[str, ...]] = []
    approval: list[Tuple[str, ...]] = []
    max_path = 0
    external_hops = 0

    for path in paths:
        max_path = max(max_path, len(path))
        caps: set[str] = set()
        carried_labels: set[str] = set()
        path_external_hops = 0
        for idx, nid in enumerate(path):
            node = nodes[nid]
            caps.update(node.capabilities)
            carried_labels.update(node.consumes_labels)
            carried_labels.update(node.produces_labels)
            if node.external_boundary:
                path_external_hops += 1
            if idx:
                for e in edge_map.get((path[idx-1], nid), ()):
                    carried_labels.update(e.data_labels)
        external_hops = max(external_hops, path_external_hops)
        for src_cap, sink_cap in policy.forbidden_capability_pairs:
            if src_cap in caps and sink_cap in caps:
                dangerous.append(path); reasons.add(f"FORBIDDEN_COMBINATION:{src_cap}->{sink_cap}")
        has_external_sink = bool(caps & policy.external_sink_capabilities) or any(nodes[n].external_boundary for n in path)
        if has_external_sink and carried_labels & policy.sensitive_labels:
            sensitive_external.append(path); reasons.add("SENSITIVE_DATA_EXTERNAL_PATH")
        if caps & policy.approval_required_capabilities:
            approval.append(path)
        if path_external_hops > policy.max_external_hops:
            dangerous.append(path); reasons.add("EXTERNAL_HOP_LIMIT_EXCEEDED")

    dangerous_t = tuple(sorted(set(dangerous)))
    sensitive_t = tuple(sorted(set(sensitive_external)))
    approval_t = tuple(sorted(set(approval)))
    if dangerous_t or sensitive_t:
        decision = ControlDecision.DENY
    elif approval_t:
        decision = ControlDecision.HUMAN_APPROVAL
        reasons.add("APPROVAL_REQUIRED_CAPABILITY_PRESENT")
    else:
        decision = ControlDecision.ALLOW
        reasons.add("PLAN_GRAPH_POLICY_MATCH")

    return PlanAssessment(
        decision=decision,
        reasons=tuple(sorted(reasons)),
        request_id=request.request_id,
        plan_id=request.plan_id,
        dangerous_paths=dangerous_t,
        sensitive_external_paths=sensitive_t,
        approval_paths=approval_t,
        graph_fingerprint=prepared.graph_fingerprint,
        policy_fingerprint=prepared.policy_fingerprint,
        request_fingerprint=fingerprint(request),
        node_count=len(prepared.nodes),
        edge_count=len(prepared.edges),
        max_observed_path_length=max_path,
        external_hop_count=external_hops,
    )


def evaluate(request: InspectionRequest, policy: ChainPolicy, graph: PlanGraph, *, now: int) -> PlanAssessment:
    try:
        prepared = prepare_graph(policy, graph, now=now)
    except ValueError as exc:
        return _empty_assessment(request, graph, policy, ControlDecision.HOLD, (f"PREPARE_FAILED:{exc}",))
    return evaluate_prepared(request, policy, graph, prepared, now=now)


def build_graph_delta(base: PlanGraph, target: PlanGraph) -> GraphDelta:
    base.validate(); target.validate()
    if (base.plan_id, base.purpose, base.evidence_binding) != (target.plan_id, target.purpose, target.evidence_binding):
        raise ValueError("graph scalar identity mismatch")
    bn = {n.node_id:n for n in _normalize_nodes(base.nodes)}; tn = {n.node_id:n for n in _normalize_nodes(target.nodes)}
    be = {e.edge_id:e for e in _normalize_edges(base.edges, base.nodes)}; te = {e.edge_id:e for e in _normalize_edges(target.edges, target.nodes)}
    changed_nodes = tuple(tn[k] for k in sorted(bn.keys() & tn.keys()) if fingerprint(bn[k]) != fingerprint(tn[k]))
    removed_nodes = tuple(sorted(bn.keys() - tn.keys())); added_nodes = tuple(tn[k] for k in sorted(tn.keys()-bn.keys()))
    changed_edges = tuple(te[k] for k in sorted(be.keys() & te.keys()) if fingerprint(be[k]) != fingerprint(te[k]))
    removed_edges = tuple(sorted(be.keys()-te.keys())); added_edges = tuple(te[k] for k in sorted(te.keys()-be.keys()))
    return GraphDelta(graph_fingerprint(base), graph_fingerprint(target), changed_nodes, removed_nodes, added_nodes, changed_edges, removed_edges, added_edges)


def apply_graph_delta(base: PlanGraph, delta: GraphDelta) -> PlanGraph:
    if graph_fingerprint(base) != delta.base_fingerprint:
        raise ValueError("base fingerprint mismatch")
    nodes = {n.node_id:n for n in _normalize_nodes(base.nodes)}
    edges = {e.edge_id:e for e in _normalize_edges(base.edges, base.nodes)}
    for k in delta.removed_node_ids: nodes.pop(k, None)
    for n in delta.changed_nodes + delta.added_nodes: nodes[n.node_id]=n
    for k in list(edges):
        e=edges[k]
        if e.source_id not in nodes or e.target_id not in nodes: edges.pop(k)
    for k in delta.removed_edge_ids: edges.pop(k, None)
    for e in delta.changed_edges + delta.added_edges: edges[e.edge_id]=e
    target = PlanGraph(base.plan_id, base.purpose, base.evidence_binding, tuple(nodes.values()), tuple(edges.values()))
    if graph_fingerprint(target) != delta.target_fingerprint:
        raise ValueError("target fingerprint mismatch")
    return target


def plan_graph_sync(prepared: PreparedPlanGraph, known_node_fingerprints: Mapping[str,str], known_edge_fingerprints: Mapping[str,str]) -> GraphSyncPlan:
    missing_nodes=tuple(sorted(k for k,v in prepared.node_fingerprints.items() if known_node_fingerprints.get(k)!=v))
    missing_edges=tuple(sorted(k for k,v in prepared.edge_fingerprints.items() if known_edge_fingerprints.get(k)!=v))
    node_map={n.node_id:n for n in prepared.nodes}; edge_map={e.edge_id:e for e in prepared.edges}
    payload={"nodes":[node_map[k] for k in missing_nodes],"edges":[edge_map[k] for k in missing_edges]}
    full={"nodes":prepared.nodes,"edges":prepared.edges}
    needed=len(canonical_json(payload).encode("utf-8")); full_bytes=len(canonical_json(full).encode("utf-8"))
    return GraphSyncPlan(missing_nodes,missing_edges,needed,full_bytes,needed >= full_bytes)


def assessment_digest(items: Iterable[PlanAssessment]) -> str:
    return fingerprint(tuple(items))


def default_policy(now: int) -> ChainPolicy:
    return ChainPolicy(
        policy_id="CHAIN-POLICY-1", version="1", authority_epoch=1,
        issued_at=now-100, expires_at=now+10000,
        allowed_tools=frozenset({"LOCAL_READ","LOCAL_TRANSFORM","LOCAL_STORE","APPROVAL_GATE","EXTERNAL_API"}),
        allowed_operations=frozenset({"READ","TRANSFORM","STORE","CHECK","CALL"}),
        sensitive_labels=frozenset({"SECRET","PERSONAL","CONFIDENTIAL"}),
        external_sink_capabilities=frozenset({"EXTERNAL_SEND","PUBLIC_PUBLISH"}),
        approval_required_capabilities=frozenset({"WRITE_PRODUCTION","MONEY_TRANSFER"}),
        forbidden_capability_pairs=(("READ_SECRET","EXTERNAL_SEND"),("READ_PERSONAL","PUBLIC_PUBLISH"),("READ_CONFIDENTIAL","EXTERNAL_SEND")),
        max_nodes=10000, max_edges=20000, max_path_length=10000, max_external_hops=1,
    )


def default_graph() -> PlanGraph:
    bind="BUILD48-EVIDENCE"
    nodes=(
        ToolNode("N1","LOCAL_READ","READ",frozenset({"READ_INTERNAL"}),frozenset(),frozenset({"INTERNAL"}),False,False,bind),
        ToolNode("N2","LOCAL_TRANSFORM","TRANSFORM",frozenset({"TRANSFORM"}),frozenset({"INTERNAL"}),frozenset({"INTERNAL"}),False,False,bind),
        ToolNode("N3","LOCAL_STORE","STORE",frozenset({"STORE_LOCAL"}),frozenset({"INTERNAL"}),frozenset(),False,True,bind),
    )
    edges=(
        ToolEdge("E1","N1","N2",frozenset({"INTERNAL"}),bind),
        ToolEdge("E2","N2","N3",frozenset({"INTERNAL"}),bind),
    )
    return PlanGraph("PLAN-48","BUILD_SUCCESSOR",bind,nodes,edges)


def default_request(now: int) -> InspectionRequest:
    p=default_policy(now); g=default_graph()
    return InspectionRequest("REQ-48",g.plan_id,g.purpose,g.evidence_binding,p.policy_id,p.version,p.authority_epoch)


__all__=[
    "ControlDecision","ChainPolicy","ToolNode","ToolEdge","PlanGraph","InspectionRequest","PreparedPlanGraph","GraphDelta","GraphSyncPlan","PlanAssessment",
    "canonical_json","fingerprint","graph_fingerprint","prepare_graph","evaluate","evaluate_prepared","build_graph_delta","apply_graph_delta","plan_graph_sync","assessment_digest",
    "default_policy","default_graph","default_request"
]
