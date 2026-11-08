from __future__ import annotations

from dataclasses import dataclass, field, asdict, replace
from enum import Enum
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple
import hashlib
import json
import time


class EventType(str, Enum):
    INPUT = "INPUT"
    DECISION = "DECISION"
    TOOL_REQUEST = "TOOL_REQUEST"
    TOOL_RESULT = "TOOL_RESULT"
    APPROVAL = "APPROVAL"
    ACTION_REQUEST = "ACTION_REQUEST"
    ACTION_RESULT = "ACTION_RESULT"
    POLICY = "POLICY"
    SECURITY = "SECURITY"
    STATE = "STATE"


@dataclass(frozen=True)
class AuditEvent:
    event_id: str
    run_id: str
    actor_ref: str
    event_type: EventType
    observed_epoch_ns: int
    payload_fingerprint: str
    source_ref: str
    decision: Optional[str] = None
    claimed_outcome: Optional[str] = None
    approval_ref: Optional[str] = None
    evidence_refs: Tuple[str, ...] = ()
    authority_version: Optional[int] = None
    target_version: Optional[str] = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LedgerRecord:
    sequence: int
    event: AuditEvent
    previous_hash: str
    record_hash: str
    appended_epoch_ns: int


@dataclass(frozen=True)
class VerificationResult:
    valid: bool
    reason_codes: Tuple[str, ...]
    record_count: int
    head_hash: str
    ledger_fingerprint: str
    cache_reused: bool = False
    authoritative: bool = False
    truth_established: bool = False
    action_success_established: bool = False

    def stable_payload(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "reason_codes": list(self.reason_codes),
            "record_count": self.record_count,
            "head_hash": self.head_hash,
            "ledger_fingerprint": self.ledger_fingerprint,
            "cache_reused": self.cache_reused,
            "authoritative": self.authoritative,
            "truth_established": self.truth_established,
            "action_success_established": self.action_success_established,
        }


class AuditForensicLedger:
    """
    NOEPIN AL 018 — Audit / Forensic Ledger.

    Local append-only evidence structure. No external database, network, process,
    tool, or action execution is performed by this class.

    Invariants:
      Recorded claim != Truth
      Recorded action result != Action Success
      Hash-chain integrity != Semantic truth
      Approval reference != Approval authority
      Evidence reference != Evidence validity
      Cache hit != Verification authority
    """

    GENESIS = "0" * 64

    def __init__(self, *, policy_version: str = "1", enable_verify_cache: bool = True) -> None:
        if not policy_version:
            raise ValueError("policy_version required")
        self.policy_version = str(policy_version)
        self.enable_verify_cache = bool(enable_verify_cache)
        self._records: list[LedgerRecord] = []
        self._verify_cache: Dict[Tuple[str, str], VerificationResult] = {}
        self._seen_event_ids: set[str] = set()

    @staticmethod
    def _norm(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {str(k): AuditForensicLedger._norm(value[k]) for k in sorted(value, key=lambda x: str(x))}
        if isinstance(value, (list, tuple)):
            return [AuditForensicLedger._norm(v) for v in value]
        if isinstance(value, set):
            return sorted(AuditForensicLedger._norm(v) for v in value)
        if isinstance(value, Enum):
            return value.value
        if value is None or isinstance(value, (str, int, float, bool)):
            return value
        return str(value)

    @staticmethod
    def _valid_hash(value: str) -> bool:
        if not isinstance(value, str) or len(value) != 64:
            return False
        try:
            int(value, 16)
            return True
        except ValueError:
            return False

    @staticmethod
    def _valid_int(value: Any) -> bool:
        return isinstance(value, int) and not isinstance(value, bool)

    @classmethod
    def _event_bytes(cls, sequence: int, event: AuditEvent, previous_hash: str, appended_epoch_ns: int) -> bytes:
        payload = {
            "sequence": sequence,
            "event": cls._norm(asdict(event)),
            "previous_hash": previous_hash,
            "appended_epoch_ns": appended_epoch_ns,
        }
        return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")

    @classmethod
    def compute_record_hash(cls, sequence: int, event: AuditEvent, previous_hash: str, appended_epoch_ns: int) -> str:
        return hashlib.sha256(cls._event_bytes(sequence, event, previous_hash, appended_epoch_ns)).hexdigest()

    @classmethod
    def _records_fingerprint(cls, records: Iterable[LedgerRecord]) -> str:
        payload = [cls._norm(asdict(r)) for r in records]
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    @staticmethod
    def _validate_event(event: AuditEvent) -> None:
        if not event.event_id or not event.run_id or not event.actor_ref or not event.source_ref:
            raise ValueError("required audit event field missing")
        if not AuditForensicLedger._valid_int(event.observed_epoch_ns) or event.observed_epoch_ns < 0:
            raise ValueError("invalid observed_epoch_ns")
        if not AuditForensicLedger._valid_hash(event.payload_fingerprint):
            raise ValueError("invalid payload_fingerprint")
        if event.authority_version is not None:
            if not AuditForensicLedger._valid_int(event.authority_version) or event.authority_version < 1:
                raise ValueError("invalid authority_version")

    def append(self, event: AuditEvent, *, appended_epoch_ns: Optional[int] = None) -> LedgerRecord:
        self._validate_event(event)
        if event.event_id in self._seen_event_ids:
            raise ValueError("duplicate event_id")
        ts = time.time_ns() if appended_epoch_ns is None else appended_epoch_ns
        if not self._valid_int(ts) or ts < 0:
            raise ValueError("invalid appended_epoch_ns")
        if self._records and ts < self._records[-1].appended_epoch_ns:
            raise ValueError("appended_epoch_ns must be monotonic")
        sequence = len(self._records) + 1
        previous_hash = self._records[-1].record_hash if self._records else self.GENESIS
        record_hash = self.compute_record_hash(sequence, event, previous_hash, ts)
        record = LedgerRecord(sequence, event, previous_hash, record_hash, ts)
        self._records.append(record)
        self._seen_event_ids.add(event.event_id)
        self._verify_cache.clear()
        return record

    def records(self) -> Tuple[LedgerRecord, ...]:
        return tuple(self._records)

    def head_hash(self) -> str:
        return self._records[-1].record_hash if self._records else self.GENESIS

    def search(
        self,
        *,
        run_id: Optional[str] = None,
        actor_ref: Optional[str] = None,
        event_type: Optional[EventType] = None,
        approval_ref: Optional[str] = None,
    ) -> Tuple[LedgerRecord, ...]:
        out = []
        for r in self._records:
            e = r.event
            if run_id is not None and e.run_id != run_id:
                continue
            if actor_ref is not None and e.actor_ref != actor_ref:
                continue
            if event_type is not None and e.event_type != event_type:
                continue
            if approval_ref is not None and e.approval_ref != approval_ref:
                continue
            out.append(r)
        return tuple(out)

    def reconstruct_run(self, run_id: str) -> Tuple[LedgerRecord, ...]:
        if not run_id:
            raise ValueError("run_id required")
        return self.search(run_id=run_id)

    def verify_records(self, records: Optional[Tuple[LedgerRecord, ...]] = None) -> VerificationResult:
        recs = tuple(self._records) if records is None else tuple(records)
        fingerprint = self._records_fingerprint(recs)
        key = (fingerprint, self.policy_version)
        if self.enable_verify_cache and key in self._verify_cache:
            cached = self._verify_cache[key]
            return VerificationResult(
                cached.valid, cached.reason_codes, cached.record_count, cached.head_hash,
                cached.ledger_fingerprint, True, False, False, False
            )

        reasons = []
        prev = self.GENESIS
        last_ts = -1
        seen_ids = set()
        for idx, record in enumerate(recs, start=1):
            if record.sequence != idx:
                reasons.append(f"SEQUENCE_MISMATCH:{idx}")
            if record.previous_hash != prev:
                reasons.append(f"PREVIOUS_HASH_MISMATCH:{idx}")
            if not self._valid_hash(record.record_hash):
                reasons.append(f"RECORD_HASH_INVALID:{idx}")
            try:
                self._validate_event(record.event)
            except ValueError:
                reasons.append(f"EVENT_INVALID:{idx}")
            if record.event.event_id in seen_ids:
                reasons.append(f"DUPLICATE_EVENT_ID:{idx}")
            seen_ids.add(record.event.event_id)
            if record.appended_epoch_ns < last_ts:
                reasons.append(f"APPEND_TIME_REGRESSION:{idx}")
            expected = self.compute_record_hash(
                record.sequence, record.event, record.previous_hash, record.appended_epoch_ns
            )
            if record.record_hash != expected:
                reasons.append(f"RECORD_HASH_MISMATCH:{idx}")
            prev = record.record_hash
            last_ts = record.appended_epoch_ns

        result = VerificationResult(
            valid=not reasons,
            reason_codes=tuple(reasons) if reasons else ("CHAIN_VALID",),
            record_count=len(recs),
            head_hash=recs[-1].record_hash if recs else self.GENESIS,
            ledger_fingerprint=fingerprint,
            cache_reused=False,
            authoritative=False,
            truth_established=False,
            action_success_established=False,
        )
        if self.enable_verify_cache:
            self._verify_cache[key] = result
        return result

    def verify(self) -> VerificationResult:
        return self.verify_records()

    def export_snapshot(self) -> Mapping[str, Any]:
        # Pure data snapshot. Does not write to filesystem or external storage.
        verification = self.verify()
        return {
            "policy_version": self.policy_version,
            "record_count": len(self._records),
            "head_hash": self.head_hash(),
            "ledger_fingerprint": verification.ledger_fingerprint,
            "records": tuple(self._records),
            "authoritative": False,
            "truth_established": False,
            "action_success_established": False,
        }

    def cache_size(self) -> int:
        return len(self._verify_cache)

    def clear_cache(self) -> None:
        self._verify_cache.clear()
