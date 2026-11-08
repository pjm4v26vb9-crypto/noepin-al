from dataclasses import replace
from pathlib import Path
import inspect
import json
import noepin_al_038_memory_governor as m

COUNT=0

def check(cond, msg="assertion failed"):
    global COUNT
    COUNT += 1
    if not cond:
        raise AssertionError(f"#{COUNT}: {msg}")

def policy(**kw):
    p=m.MemoryPolicy("p1",2,7,frozenset({"assist","care"}),3600,86400,delete_requires_human=True)
    return replace(p, **kw)

def record(**kw):
    r=m.MemoryRecordMeta("mem1",100,1000,frozenset({"assist"}),"INTERNAL","p1",2,7)
    return replace(r, **kw)

def req(op="USE", **kw):
    r=m.MemoryRequest(op,"assist",500,classification="INTERNAL")
    return replace(r, **kw)

# Normal / operation behavior
check(m.evaluate(policy(), req("STORE",requested_retention_seconds=100), None).decision == m.Decision.ALLOW)
check(m.evaluate(policy(), req("USE"), record()).decision == m.Decision.ALLOW)
check(m.evaluate(policy(), req("RETAIN",requested_retention_seconds=1200), record()).decision == m.Decision.ALLOW)
check(m.evaluate(policy(), req("DELETE"), record()).decision == m.Decision.HUMAN_APPROVAL)
check(m.evaluate(policy(), req("DELETE",human_approval_evidence=True), record()).decision == m.Decision.ALLOW)
check(m.evaluate(policy(), req("DELETE",subject_deletion_request=True), record()).decision == m.Decision.ALLOW)
check(m.evaluate(policy(), req("DELETE",now=1000), record()).decision == m.Decision.HUMAN_APPROVAL)
check(m.evaluate(policy(delete_requires_human=False), req("DELETE",now=1000), record()).decision == m.Decision.ALLOW)

# Purpose/classification boundaries
for p in ["other","analytics","ads","training"]:
    check(m.evaluate(policy(), req("USE",purpose=p), record()).decision == m.Decision.DENY)
for c in ["PUBLIC","CONFIDENTIAL","RESTRICTED"]:
    check(m.evaluate(policy(), req("USE",classification=c), record()).decision == m.Decision.DENY)
check(m.evaluate(policy(classifications_allowed=frozenset({"PUBLIC"})), req("STORE",classification="INTERNAL",requested_retention_seconds=100), None).decision == m.Decision.DENY)

# TTL / retention
for t in [1000,1001,9999]:
    check(m.evaluate(policy(), req("USE",now=t), record()).decision == m.Decision.DENY)
check(m.evaluate(policy(), req("USE",now=999), record()).decision == m.Decision.ALLOW)
for secs in [0,1,3600,86400]:
    d=m.evaluate(policy(), req("STORE",requested_retention_seconds=secs), None).decision
    check(d == m.Decision.ALLOW)
for secs in [-1,86401,999999]:
    check(m.evaluate(policy(), req("STORE",requested_retention_seconds=secs), None).decision == m.Decision.DENY)
check(m.evaluate(policy(default_retention_seconds=0), req("STORE"), None).decision == m.Decision.DENY)
check(m.evaluate(policy(), req("RETAIN",requested_retention_seconds=200), record()).decision == m.Decision.DENY)

# Human approval / legal hold
check(m.evaluate(policy(store_requires_human=True), req("STORE",requested_retention_seconds=100), None).decision == m.Decision.HUMAN_APPROVAL)
check(m.evaluate(policy(store_requires_human=True), req("STORE",requested_retention_seconds=100,human_approval_evidence=True), None).decision == m.Decision.ALLOW)
check(m.evaluate(policy(), req("DELETE",human_approval_evidence=True), record(legal_hold=True)).decision == m.Decision.HOLD)
check(m.evaluate(policy(), req("DELETE",subject_deletion_request=True), record(legal_hold=True)).decision == m.Decision.HOLD)

# Deletion pending must block reuse/retention
check(m.evaluate(policy(), req("USE"), record(deletion_requested=True)).decision == m.Decision.DENY)
check(m.evaluate(policy(), req("RETAIN",requested_retention_seconds=1200), record(deletion_requested=True)).decision == m.Decision.DENY)

# Version / authority / revocation
for op in ["USE","RETAIN","DELETE"]:
    rr=req(op, requested_retention_seconds=1200 if op=="RETAIN" else 0)
    check(m.evaluate(policy(), rr, record(policy_version=1)).decision == m.Decision.DENY)
    check(m.evaluate(policy(), rr, record(authority_epoch=6)).decision == m.Decision.DENY)
    check(m.evaluate(policy(), rr, record(policy_id="x")).decision == m.Decision.DENY)
check(m.evaluate(policy(revoked=True), req("USE"), record()).decision == m.Decision.DENY)
check(m.evaluate(policy(), req("USE",expected_policy_id="x"), record()).decision == m.Decision.DENY)
check(m.evaluate(policy(), req("USE",expected_policy_version=1), record()).decision == m.Decision.DENY)
check(m.evaluate(policy(), req("USE",expected_authority_epoch=8), record()).decision == m.Decision.DENY)
check(m.evaluate(policy(), req("USE",expected_policy_id="p1",expected_policy_version=2,expected_authority_epoch=7), record()).decision == m.Decision.ALLOW)

# Invalid / missing input
for op in ["", "SEND", "EXECUTE", "PURGE_ALL", "WRITE"]:
    check(m.evaluate(policy(), req(op), record()).decision == m.Decision.DENY)
check(m.evaluate(policy(), req("USE",purpose=""), record()).decision == m.Decision.DENY)
check(m.evaluate(policy(), req("USE",now=-1), record()).decision == m.Decision.DENY)
check(m.evaluate(policy(), req("USE",classification="SECRET"), record()).decision == m.Decision.DENY)
check(m.evaluate(policy(), req("USE"), None).decision == m.Decision.DENY)
check(m.evaluate(policy(), req("STORE",requested_retention_seconds=100), record()).decision == m.Decision.DENY)
check(m.evaluate(policy(), req("USE"), record(expires_at=50)).decision == m.Decision.DENY)
check(m.evaluate(policy(), req("USE"), record(memory_id="")).decision == m.Decision.DENY)
check(m.evaluate(policy(), req("USE"), record(purposes=frozenset())).decision == m.Decision.DENY)
check(m.evaluate(policy(policy_id=""), req("USE"), record()).decision == m.Decision.DENY)
check(m.evaluate(policy(version=0), req("USE"), record()).decision == m.Decision.DENY)
check(m.evaluate(policy(default_retention_seconds=100,max_retention_seconds=50), req("USE"), record()).decision == m.Decision.DENY)

# Authority invariants: every returned object has zero side-effect claims.
scenarios=[
    (policy(),req("USE"),record()),
    (policy(),req("DELETE",human_approval_evidence=True),record()),
    (policy(),req("DELETE"),record(legal_hold=True)),
    (policy(),req("USE",purpose="ads"),record()),
    (policy(store_requires_human=True),req("STORE",requested_retention_seconds=100),None),
]
for s in scenarios:
    e=m.evaluate(*s)
    check(e.action_executed is False)
    check(e.memory_written is False)
    check(e.memory_deleted is False)
    check(e.truth_established is False)
    check(e.permission_granted is False)

# DCSR exact-state reuse / invalidation
p=policy(); r=record(); q=req("USE")
pe=m.prepare(p,q,r)
check(m.reuse_prepared(pe,p,q,r) == pe.result)
check(m.reuse_prepared(pe,replace(p,authority_epoch=8),q,r) is None)
check(m.reuse_prepared(pe,replace(p,version=3),q,r) is None)
check(m.reuse_prepared(pe,p,replace(q,now=501),r) is None)
check(m.reuse_prepared(pe,p,q,replace(r,expires_at=999)) is None)
check(m.reuse_prepared(pe,p,q,replace(r,deletion_requested=True)) is None)
check(m.reuse_prepared(pe,p,q,replace(r,purposes=frozenset({"care"}))) is None)
check(m.reuse_prepared(pe,p,q,replace(r,legal_hold=True)) is None)


# Pre-materialized canonical fingerprint fast path
qf=m.fingerprint(q); pf=m.fingerprint(p); rf=m.fingerprint(r)
check(m.reuse_prepared_by_fingerprints(pe,request_fingerprint=qf,policy_fingerprint=pf,record_fingerprint=rf,authority_epoch=7)==pe.result)
check(m.reuse_prepared_by_fingerprints(pe,request_fingerprint=qf,policy_fingerprint=pf,record_fingerprint=rf,authority_epoch=8) is None)
check(m.reuse_prepared_by_fingerprints(pe,request_fingerprint='0'*64,policy_fingerprint=pf,record_fingerprint=rf,authority_epoch=7) is None)
check(m.reuse_prepared_by_fingerprints(pe,request_fingerprint=qf,policy_fingerprint='0'*64,record_fingerprint=rf,authority_epoch=7) is None)
check(m.reuse_prepared_by_fingerprints(pe,request_fingerprint=qf,policy_fingerprint=pf,record_fingerprint='0'*64,authority_epoch=7) is None)

# Delta reconstruction and mismatch fail-safe
base={f"m{i}": m.MemoryRecordMeta(f"m{i}",0,1000,frozenset({"assist"}),"INTERNAL","p1",2,7) for i in range(40)}
target=dict(base)
target["m3"]=replace(target["m3"],expires_at=800)
target["m4"]=replace(target["m4"],deletion_requested=True)
del target["m5"]
target["m40"]=m.MemoryRecordMeta("m40",0,1200,frozenset({"assist"}),"INTERNAL","p1",2,7)
delta=m.build_metadata_delta(base,target)
out=m.apply_metadata_delta(base,delta)
check(out==target)
check(m.registry_fingerprint(out)==m.registry_fingerprint(target))
check(len(delta.changed)==2)
check(delta.removed_ids==("m5",))
check(len(delta.added)==1)
try:
    m.apply_metadata_delta({**base,"m0":replace(base["m0"],expires_at=9)},delta)
    raise AssertionError("mismatch accepted")
except ValueError:
    check(True)

# Fingerprint deterministic / order-independent
check(m.fingerprint(frozenset({"b","a"})) == m.fingerprint(frozenset({"a","b"})))
check(m.registry_fingerprint({"b":base["m1"],"a":base["m0"]}) == m.registry_fingerprint({"a":base["m0"],"b":base["m1"]}))
check(m.fingerprint(p)==m.fingerprint(p))

# Static safety: production module contains no execution/network/persistence imports or APIs.
src=Path(m.__file__).read_text(encoding="utf-8")
for token in ["import subprocess","os.system(","socket.","requests.","urllib.request","shutil.","open(","unlink(","remove(","rmtree(","send(","deploy(","publish(","persist("]:
    check(token not in src, f"forbidden primitive {token}")
# Explicitly prove the public surface has no side-effect verbs.
public={n for n,v in inspect.getmembers(m) if inspect.isfunction(v) and not n.startswith("_")}
for forbidden in ["execute","commit","grant","send","persist","delete_memory","write_memory","publish","deploy"]:
    check(forbidden not in public)

print(json.dumps({"passed":COUNT,"total":COUNT,"status":"PASS"},sort_keys=True))
