from dataclasses import replace
import math
from noepin_al_032_vector_guard import *

H=lambda s: __import__('hashlib').sha256(s.encode()).hexdigest()
POL=GuardPolicy("p1","a1","emb","v1",8,"idx","i1")
BASE=VectorObservation(
 AssetKind.RAG_RESULT,"doc1","src1","s1",H("content"),"emb","v1",8,H("vec"),"idx","i1",H("index"),
 True,True,True,"acl1",("user1","user2"),"user1","PUBLIC","research",True,0.1,0,"p1","a1",H("ctx"))

def run():
    passed=0; failed=[]
    def check(name, cond):
        nonlocal passed
        if cond: passed+=1
        else: failed.append(name)

    g=VectorIntegrityGuard(POL)
    r=g.evaluate(BASE); check("baseline allow", r.decision==Decision.ALLOW_CANDIDATE)
    # required strings 13
    fields=["document_id","source_id","source_version","embedding_model_id","embedding_model_version","index_id","index_version","acl_version","requester_principal","purpose","policy_version","authority_version","context_fingerprint"]
    for f in fields:
        rr=g.evaluate(replace(BASE, **{f:""})); check("missing "+f, rr.decision==Decision.DENY)
    # fingerprint invalid 4
    for f in ["content_fingerprint","vector_fingerprint","index_fingerprint","context_fingerprint"]:
        rr=g.evaluate(replace(BASE, **{f:"x"})); check("bad "+f, rr.decision==Decision.DENY)
    # dimension invalid 4
    for v in [0,-1,True,1.5]:
        rr=g.evaluate(replace(BASE, embedding_dimension=v)); check("dim invalid "+repr(v), rr.decision==Decision.DENY)
    # anomaly invalid 3
    for v in [-0.1,float('inf'),float('nan')]:
        rr=g.evaluate(replace(BASE, anomaly_score=v)); check("anomaly invalid "+repr(v), rr.decision==Decision.DENY)
    # marker invalid 3
    for v in [-1,True,1.2]:
        rr=g.evaluate(replace(BASE, suspicious_marker_count=v)); check("marker invalid "+repr(v), rr.decision==Decision.DENY)
    # acl principals invalid 3
    for v in [(), ("",), (1,)]:
        rr=g.evaluate(replace(BASE, allowed_principals=v)); check("acl invalid "+repr(v), rr.decision==Decision.DENY)
    # policy/authority mismatch
    check("policy mismatch", g.evaluate(replace(BASE,policy_version="p2")).decision==Decision.HOLD)
    check("authority mismatch", g.evaluate(replace(BASE,authority_version="a2")).decision==Decision.HOLD)
    # source integrity
    check("signature quarantine", g.evaluate(replace(BASE,signature_verified=False)).decision==Decision.QUARANTINE)
    check("source bind hold", g.evaluate(replace(BASE,source_binding_verified=False)).decision==Decision.HOLD)
    check("provenance hold", g.evaluate(replace(BASE,provenance_verified=False)).decision==Decision.HOLD)
    # model/index mismatch 5
    variants=[("embedding_model_id","other"),("embedding_model_version","v2"),("embedding_dimension",9),("index_id","other"),("index_version","i2")]
    for f,v in variants:
        check("mismatch "+f, g.evaluate(replace(BASE, **{f:v})).decision==Decision.HOLD)
    # ACL/consent
    check("acl deny", g.evaluate(replace(BASE,requester_principal="intruder")).decision==Decision.DENY)
    check("sensitive consent deny", g.evaluate(replace(BASE,classification="SENSITIVE",consent_evidence=False)).decision==Decision.DENY)
    check("sensitive consent allow", g.evaluate(replace(BASE,classification="SENSITIVE",consent_evidence=True)).decision==Decision.ALLOW_CANDIDATE)
    # anomaly thresholds / markers
    check("marker human", g.evaluate(replace(BASE,suspicious_marker_count=1)).decision==Decision.HUMAN_CONFIRM)
    check("anomaly human", g.evaluate(replace(BASE,anomaly_score=0.5)).decision==Decision.HUMAN_CONFIRM)
    check("anomaly quarantine", g.evaluate(replace(BASE,anomaly_score=0.8)).decision==Decision.QUARANTINE)
    check("signature overrides human", g.evaluate(replace(BASE,signature_verified=False,suspicious_marker_count=2)).decision==Decision.QUARANTINE)
    check("acl overrides quarantine", g.evaluate(replace(BASE,requester_principal="x",anomaly_score=0.9)).decision==Decision.DENY)
    # no authority flags 8
    rr=g.evaluate(BASE)
    for name in ["truth_established","source_truth_established","permission_granted","access_executed","data_isolated","index_rebuilt","state_committed","action_succeeded"]:
        check("flag false "+name, getattr(rr,name) is False)
    # cache exact
    g2=VectorIntegrityGuard(POL); a=g2.evaluate(BASE); b=g2.evaluate(BASE); check("cache reused", b.cache_reused is True)
    check("cache same decision", a.decision==b.decision)
    changed=g2.evaluate(replace(BASE,index_version="i2")); check("changed request not cached allow", changed.decision==Decision.HOLD and changed.cache_reused is False)
    # cache key binds policy
    p2=replace(POL, authority_version="a2"); g3=VectorIntegrityGuard(p2); check("policy authority bind", g3.evaluate(BASE).decision==Decision.HOLD)
    # delta tests
    def ent(i, suffix=""):
        return IndexEntry(f"d{i}","s1",H(f"c{i}{suffix}"),H(f"v{i}{suffix}"),"acl1")
    base=IndexBaseline("idx","i1",tuple(ent(i) for i in range(20)))
    target=IndexBaseline("idx","i2",tuple([ent(i,"x") if i in {2,5,9} else ent(i) for i in range(18)] + [ent(20),ent(21)]))
    d=build_index_delta(base,target)
    check("delta changed count", len(d.changed_entries)==5)
    check("delta removed count", len(d.removed_document_ids)==2)
    rebuilt=reconstruct_index(base,d)
    check("delta reconstruct", baseline_fingerprint(rebuilt)==baseline_fingerprint(target))
    try:
        badbase=replace(base,index_version="other")
        reconstruct_index(badbase,d); ok=False
    except ValueError: ok=True
    check("delta base tamper",ok)
    try:
        bad=replace(d,target_fingerprint=H("bad")); reconstruct_index(base,bad); ok=False
    except ValueError: ok=True
    check("delta target tamper",ok)
    try:
        build_index_delta(base, replace(target,index_id="other")); ok=False
    except ValueError: ok=True
    check("delta index mismatch",ok)
    # deterministic fingerprints 6
    check("obs fp deterministic", g.evaluate(BASE,use_cache=False).observation_fingerprint==g.evaluate(BASE,use_cache=False).observation_fingerprint)
    check("obs fp changes content", g.evaluate(BASE,use_cache=False).observation_fingerprint!=g.evaluate(replace(BASE,content_fingerprint=H("other")),use_cache=False).observation_fingerprint)
    check("baseline fp deterministic", baseline_fingerprint(base)==baseline_fingerprint(base))
    check("baseline fp version", baseline_fingerprint(base)!=baseline_fingerprint(replace(base,index_version="i2")))
    check("delta base binding", d.base_fingerprint==baseline_fingerprint(base))
    check("delta target binding", d.target_fingerprint==baseline_fingerprint(target))
    # classification/purpose semantics preserved
    for c in ["PUBLIC","INTERNAL","SENSITIVE","RESTRICTED","PERSONAL","HEALTH","FINANCIAL"]:
        obs=replace(BASE,classification=c,consent_evidence=True)
        res=g.evaluate(obs,use_cache=False)
        check("classification not truth "+c, res.truth_established is False)
    # purpose/context changes invalidate exact cache
    gx=VectorIntegrityGuard(POL); gx.evaluate(BASE)
    check("purpose changed no cache", gx.evaluate(replace(BASE,purpose="ops")).cache_reused is False)
    check("context changed no cache", gx.evaluate(replace(BASE,context_fingerprint=H("ctx2"))).cache_reused is False)
    # asset kinds supported
    for kind in AssetKind:
        check("kind "+kind.value, g.evaluate(replace(BASE,asset_kind=kind),use_cache=False).decision==Decision.ALLOW_CANDIDATE)

    print(f"TOTAL={passed+len(failed)} PASS={passed} FAIL={len(failed)}")
    if failed:
        for x in failed: print("FAIL",x)
        raise SystemExit(1)

if __name__=='__main__': run()
