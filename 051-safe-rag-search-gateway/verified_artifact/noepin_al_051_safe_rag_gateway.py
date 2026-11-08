"""NOEPIN AL 051 — Safe RAG / Retrieval Gateway.

Pure control-plane evaluator implementing ACL-aware Retrieval, Source Trust,
Provenance/Evidence binding, Injection Risk, and Content Quarantine.
It returns retrieval/context candidates only and never grants permission,
commits model context, invokes a model, sends data, or promotes retrieved
content/source trust/fingerprint matches to authoritative truth.

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


class DataClass(str, Enum):
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


@dataclass(frozen=True)
class RAGPolicy:
    policy_id: str
    version: str
    authority_epoch: int
    issued_at: int
    expires_at: int
    allowed_purposes: FrozenSet[str]
    allowed_classifications: FrozenSet[DataClass]
    trusted_source_ids: FrozenSet[str]
    min_source_trust: float
    quarantine_injection_threshold: float
    human_review_injection_threshold: float
    max_document_age_seconds: int
    max_documents: int
    require_verified_provenance: bool = True
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
        if not self.allowed_purposes or not self.allowed_classifications or not self.trusted_source_ids:
            raise ValueError("policy sets must not be empty")
        if not 0 <= self.min_source_trust <= 1:
            raise ValueError("min_source_trust out of range")
        if not 0 <= self.human_review_injection_threshold < self.quarantine_injection_threshold <= 1:
            raise ValueError("invalid injection thresholds")
        if self.max_document_age_seconds < 1 or self.max_documents < 1:
            raise ValueError("invalid limits")


@dataclass(frozen=True)
class RAGRequest:
    request_id: str
    requester_id: str
    principals: FrozenSet[str]
    purpose: str
    query_fingerprint: str
    expected_policy_id: str
    expected_policy_version: str
    expected_authority_epoch: int
    evidence_binding: str
    allowed_classifications: FrozenSet[DataClass]
    requested_source_ids: FrozenSet[str]

    def validate(self) -> None:
        if not self.request_id or not self.requester_id or not self.principals:
            raise ValueError("requester identity/principals required")
        if not self.purpose or not self.query_fingerprint or not self.evidence_binding:
            raise ValueError("purpose/query/evidence binding required")
        if not self.expected_policy_id or not self.expected_policy_version or self.expected_authority_epoch < 1:
            raise ValueError("policy binding required")
        if not self.allowed_classifications:
            raise ValueError("allowed classifications required")


@dataclass(frozen=True)
class RetrievedDocument:
    document_id: str
    source_id: str
    source_uri: str
    captured_at: int
    classification: DataClass
    acl_principals: FrozenSet[str]
    source_trust: float
    injection_risk: float
    content_sha256: str
    provenance_binding: str
    evidence_binding: str
    provenance_verified: bool
    instruction_like_content: bool = False
    revoked: bool = False

    def validate(self) -> None:
        if not self.document_id or not self.source_id or not self.source_uri:
            raise ValueError("document/source required")
        if self.captured_at < 0:
            raise ValueError("captured_at invalid")
        if not self.acl_principals:
            raise ValueError("acl required")
        if not 0 <= self.source_trust <= 1 or not 0 <= self.injection_risk <= 1:
            raise ValueError("score out of range")
        if len(self.content_sha256) != 64 or any(c not in "0123456789abcdef" for c in self.content_sha256.lower()):
            raise ValueError("content sha256 invalid")
        if not self.provenance_binding or not self.evidence_binding:
            raise ValueError("provenance/evidence binding required")


@dataclass(frozen=True)
class PreparedDocumentRegistry:
    registry_fingerprint: str
    policy_fingerprint: str
    documents: Tuple[RetrievedDocument, ...]
    document_fingerprints: Mapping[str, str]
    source_index: Mapping[str, Tuple[str, ...]]
    class_index: Mapping[str, Tuple[str, ...]]


@dataclass(frozen=True)
class DocumentDelta:
    base_fingerprint: str
    target_fingerprint: str
    changed_documents: Tuple[RetrievedDocument, ...]
    removed_document_ids: Tuple[str, ...]
    added_documents: Tuple[RetrievedDocument, ...]


@dataclass(frozen=True)
class RegistrySyncPlan:
    missing_or_changed_document_ids: Tuple[str, ...]
    metadata_bytes_required: int
    full_metadata_bytes: int
    full_resend_required: bool
    permission_granted: bool = False
    context_commit_authorized: bool = False
    model_invocation_authorized: bool = False
    data_transfer_authorized: bool = False


@dataclass(frozen=True)
class RAGVerdict:
    decision: ControlDecision
    reasons: Tuple[str, ...]
    request_id: str
    selected_document_ids: Tuple[str, ...]
    quarantined_document_ids: Tuple[str, ...]
    acl_denied_document_ids: Tuple[str, ...]
    untrusted_document_ids: Tuple[str, ...]
    stale_or_invalid_document_ids: Tuple[str, ...]
    human_review_candidate: bool
    registry_fingerprint: str
    policy_fingerprint: str
    request_fingerprint: str
    permission_granted: bool = False
    context_committed: bool = False
    model_invoked: bool = False
    data_transferred: bool = False
    retrieved_content_truth_proven: bool = False
    source_trust_truth_proven: bool = False
    action_success: bool = False


def _canonical(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {f.name: _canonical(getattr(value, f.name)) for f in fields(value)}
    if isinstance(value, Mapping):
        return {str(k): _canonical(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    if isinstance(value, (set, frozenset)):
        vals=[_canonical(v) for v in value]
        return sorted(vals,key=lambda x: json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(",",":")))
    if isinstance(value, tuple):
        return [_canonical(v) for v in value]
    if isinstance(value, list):
        return [_canonical(v) for v in value]
    return value


def canonical_json(value: Any) -> str:
    return json.dumps(_canonical(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: Any) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _normalize_documents(documents: Iterable[RetrievedDocument]) -> Tuple[RetrievedDocument, ...]:
    items=tuple(documents)
    ids=[d.document_id for d in items]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate document id")
    return tuple(sorted(items,key=lambda d:d.document_id))


def registry_fingerprint(documents: Iterable[RetrievedDocument]) -> str:
    return fingerprint(_normalize_documents(documents))


def prepare_registry(policy: RAGPolicy, documents: Iterable[RetrievedDocument], *, now: int) -> PreparedDocumentRegistry:
    policy.validate(now)
    docs=_normalize_documents(documents)
    if len(docs) > policy.max_documents:
        raise ValueError("too many documents")
    fps={d.document_id:fingerprint(d) for d in docs}
    by_source={}
    by_class={}
    for d in docs:
        by_source.setdefault(d.source_id,[]).append(d.document_id)
        by_class.setdefault(d.classification.value,[]).append(d.document_id)
    return PreparedDocumentRegistry(
        registry_fingerprint=fingerprint(docs),
        policy_fingerprint=fingerprint(policy),
        documents=docs,
        document_fingerprints=fps,
        source_index={k:tuple(sorted(v)) for k,v in sorted(by_source.items())},
        class_index={k:tuple(sorted(v)) for k,v in sorted(by_class.items())},
    )


def _acl_allows(req: RAGRequest, d: RetrievedDocument) -> bool:
    return "*" in d.acl_principals or bool(req.principals & d.acl_principals)


def _hold(req: RAGRequest, policy: RAGPolicy, prepared: PreparedDocumentRegistry|None, reason: str) -> RAGVerdict:
    return RAGVerdict(
        ControlDecision.HOLD,(reason,),req.request_id,(),(),(),(),(),False,
        prepared.registry_fingerprint if prepared else "",
        fingerprint(policy),fingerprint(req)
    )


def evaluate_prepared(request: RAGRequest, policy: RAGPolicy, prepared: PreparedDocumentRegistry, *, now: int) -> RAGVerdict:
    try:
        request.validate()
    except ValueError:
        return _hold(request,policy,prepared,"REQUEST_INVALID")
    try:
        policy.validate(now)
    except ValueError:
        return _hold(request,policy,prepared,"POLICY_INVALID_OR_NOT_CURRENT")
    if policy.revoked:
        return _hold(request,policy,prepared,"POLICY_REVOKED")
    if request.expected_policy_id != policy.policy_id:
        return _hold(request,policy,prepared,"POLICY_ID_MISMATCH")
    if request.expected_policy_version != policy.version:
        return _hold(request,policy,prepared,"POLICY_VERSION_MISMATCH")
    if request.expected_authority_epoch != policy.authority_epoch:
        return _hold(request,policy,prepared,"AUTHORITY_EPOCH_MISMATCH")
    if prepared.policy_fingerprint != fingerprint(policy):
        return _hold(request,policy,prepared,"PREPARED_POLICY_FINGERPRINT_MISMATCH")
    if prepared.registry_fingerprint != registry_fingerprint(prepared.documents):
        return _hold(request,policy,prepared,"PREPARED_REGISTRY_FINGERPRINT_MISMATCH")
    if request.purpose not in policy.allowed_purposes:
        return RAGVerdict(ControlDecision.DENY,("PURPOSE_NOT_ALLOWED",),request.request_id,(),(),(),(),(),False,prepared.registry_fingerprint,fingerprint(policy),fingerprint(request))

    selected=[]; quarantined=[]; acl_denied=[]; untrusted=[]; stale_invalid=[]; review=False
    for d in prepared.documents:
        try:
            d.validate()
        except ValueError:
            stale_invalid.append(d.document_id); continue
        if request.requested_source_ids and d.source_id not in request.requested_source_ids:
            continue
        if d.revoked or now-d.captured_at > policy.max_document_age_seconds or d.captured_at > now:
            stale_invalid.append(d.document_id); continue
        if d.evidence_binding != request.evidence_binding:
            stale_invalid.append(d.document_id); continue
        if policy.require_verified_provenance and not d.provenance_verified:
            stale_invalid.append(d.document_id); continue
        if d.source_id not in policy.trusted_source_ids or d.source_trust < policy.min_source_trust:
            untrusted.append(d.document_id); continue
        if d.classification not in policy.allowed_classifications or d.classification not in request.allowed_classifications:
            acl_denied.append(d.document_id); continue
        if not _acl_allows(request,d):
            acl_denied.append(d.document_id); continue
        if d.instruction_like_content or d.injection_risk >= policy.quarantine_injection_threshold:
            quarantined.append(d.document_id); continue
        if d.injection_risk >= policy.human_review_injection_threshold:
            quarantined.append(d.document_id); review=True; continue
        selected.append(d.document_id)

    selected=tuple(sorted(selected)); quarantined=tuple(sorted(quarantined)); acl_denied=tuple(sorted(acl_denied)); untrusted=tuple(sorted(untrusted)); stale_invalid=tuple(sorted(stale_invalid))
    reasons=[]
    if selected: reasons.append("SAFE_RETRIEVAL_CANDIDATES_AVAILABLE")
    if quarantined: reasons.append("CONTENT_QUARANTINED")
    if acl_denied: reasons.append("ACL_OR_CLASSIFICATION_DENIED")
    if untrusted: reasons.append("SOURCE_TRUST_INSUFFICIENT")
    if stale_invalid: reasons.append("STALE_OR_INVALID_EVIDENCE")
    if selected:
        decision=ControlDecision.HUMAN_APPROVAL if review else ControlDecision.ALLOW
    elif quarantined:
        decision=ControlDecision.HUMAN_APPROVAL if review else ControlDecision.HOLD
    elif acl_denied or untrusted:
        decision=ControlDecision.DENY
    else:
        decision=ControlDecision.HOLD
    return RAGVerdict(decision,tuple(reasons) or ("NO_ELIGIBLE_DOCUMENT",),request.request_id,selected,quarantined,acl_denied,untrusted,stale_invalid,decision is ControlDecision.HUMAN_APPROVAL,prepared.registry_fingerprint,fingerprint(policy),fingerprint(request))


def evaluate(request: RAGRequest, policy: RAGPolicy, documents: Iterable[RetrievedDocument], *, now: int) -> RAGVerdict:
    try:
        prepared=prepare_registry(policy,documents,now=now)
    except ValueError:
        return _hold(request,policy,None,"REGISTRY_INVALID")
    return evaluate_prepared(request,policy,prepared,now=now)


def make_registry_delta(base: Iterable[RetrievedDocument], target: Iterable[RetrievedDocument]) -> DocumentDelta:
    b=_normalize_documents(base); t=_normalize_documents(target)
    bm={d.document_id:d for d in b}; tm={d.document_id:d for d in t}
    changed=tuple(tm[k] for k in sorted(set(bm)&set(tm)) if fingerprint(bm[k])!=fingerprint(tm[k]))
    removed=tuple(sorted(set(bm)-set(tm)))
    added=tuple(tm[k] for k in sorted(set(tm)-set(bm)))
    return DocumentDelta(registry_fingerprint(b),registry_fingerprint(t),changed,removed,added)


def apply_registry_delta(base: Iterable[RetrievedDocument], delta: DocumentDelta) -> Tuple[RetrievedDocument, ...]:
    b=_normalize_documents(base)
    if registry_fingerprint(b)!=delta.base_fingerprint:
        raise ValueError("base fingerprint mismatch")
    m={d.document_id:d for d in b}
    for k in delta.removed_document_ids:
        if k not in m: raise ValueError("remove missing document")
        del m[k]
    for d in delta.changed_documents:
        if d.document_id not in m: raise ValueError("change missing document")
        m[d.document_id]=d
    for d in delta.added_documents:
        if d.document_id in m: raise ValueError("duplicate add")
        m[d.document_id]=d
    out=_normalize_documents(m.values())
    if registry_fingerprint(out)!=delta.target_fingerprint:
        raise ValueError("target fingerprint mismatch")
    return out


def plan_registry_sync(target: Iterable[RetrievedDocument], remote_known_fingerprints: Mapping[str,str]) -> RegistrySyncPlan:
    docs=_normalize_documents(target)
    missing=[d for d in docs if remote_known_fingerprints.get(d.document_id)!=fingerprint(d)]
    metadata_bytes=len(canonical_json(tuple(missing)).encode("utf-8"))
    full_bytes=len(canonical_json(docs).encode("utf-8"))
    return RegistrySyncPlan(tuple(d.document_id for d in missing),metadata_bytes,full_bytes,metadata_bytes>=int(full_bytes*0.8))


def verdicts_digest(items: Iterable[RAGVerdict]) -> str:
    return fingerprint(tuple(items))


def default_policy(now: int) -> RAGPolicy:
    return RAGPolicy(
        "NOEPIN-AL-051-RAG-POLICY","1",1,now-1000,now+100000,
        frozenset({"ANSWER_USER_QUERY","INTERNAL_SEARCH"}),
        frozenset({DataClass.PUBLIC,DataClass.INTERNAL,DataClass.CONFIDENTIAL}),
        frozenset({"KB-PRIMARY","DOCS-TRUSTED"}),0.70,0.80,0.45,3600,10000,True,False
    )


def default_request(now: int) -> RAGRequest:
    p=default_policy(now)
    return RAGRequest("REQ-051","USER-A",frozenset({"USER-A","TEAM-AL"}),"ANSWER_USER_QUERY","QUERY-FP-051",p.policy_id,p.version,p.authority_epoch,"RAG-EVIDENCE-051",frozenset({DataClass.PUBLIC,DataClass.INTERNAL}),frozenset({"KB-PRIMARY"}))


def _sha(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def default_documents(now: int) -> Tuple[RetrievedDocument, ...]:
    return (
        RetrievedDocument("DOC-051-1","KB-PRIMARY","kb://primary/1",now-20,DataClass.INTERNAL,frozenset({"TEAM-AL"}),0.95,0.05,_sha("doc1"),"PROV-051-1","RAG-EVIDENCE-051",True,False,False),
        RetrievedDocument("DOC-051-2","KB-PRIMARY","kb://primary/2",now-15,DataClass.PUBLIC,frozenset({"*"}),0.90,0.10,_sha("doc2"),"PROV-051-2","RAG-EVIDENCE-051",True,False,False),
    )


ORIGIN_GUID_POLICY = "PRESERVE_EXISTING_SYSTEM_ORIGIN_GUID_BY_PROVENANCE_REFERENCE"
LICENSE_RIGHTS = "NOT SPECIFIED"
CREATOR = "NOEPIN / のえぴん"
