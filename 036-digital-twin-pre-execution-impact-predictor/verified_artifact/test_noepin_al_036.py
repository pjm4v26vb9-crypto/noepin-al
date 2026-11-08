import sys, math, hashlib
from dataclasses import replace
from noepin_al_036_digital_twin import *

passed=failed=0
failures=[]
def check(name, cond):
    global passed, failed
    if cond: passed += 1
    else: failed += 1; failures.append(name)

def mk_items(n=8):
    crit=[Criticality.LOW,Criticality.MEDIUM,Criticality.HIGH,Criticality.CRITICAL]
    return tuple(StateItem(f"asset-{i}", hashlib.sha256(f"v{i}".encode()).hexdigest(), crit[i%4], i==7) for i in range(n))

def snap(items=None, sid="prod", version="v1", t=1000, base=""):
    items=items or mk_items()
    fp=DigitalTwinImpactPredictor.snapshot_fingerprint(items)
    return Snapshot(sid,version,t,items,fp,base)

def req(actions=None, now=1100, **kw):
    if actions is None:
        before=mk_items()[0].value_fingerprint
        actions=(PlannedChange("asset-0",before,hashlib.sha256(b"new").hexdigest()),)
    d=dict(request_id="r1",policy_version="p1",authority_version="a1",target_production_version="v1",observed_epoch_ms=now,max_snapshot_age_ms=1000,context_fingerprint="c1",actions=actions,impact_human_threshold=5,require_human_for_high_criticality=True,human_approval_evidence=False)
    d.update(kw); return SimulationRequest(**d)

E=DigitalTwinImpactPredictor(); P=snap(); PP=E.prepare_snapshot(P); T=snap(sid="twin",base=PP.fingerprint); TP=E.prepare_snapshot(T)
# 1-10 baseline/authority
r=E.evaluate_prepared(PP,TP,req()); check("allow-basic",r.decision==Decision.ALLOW_CANDIDATE); check("no-production-exec",not r.production_executed); check("no-success",not r.production_succeeded); check("no-permission",not r.permission_granted); check("no-commit",not r.state_committed); check("non-authoritative",not r.authoritative); check("changed-one",r.impact.changed_targets==("asset-0",)); check("no-side",r.impact.side_effect_targets==()); check("result-diff",r.impact.resulting_twin_fingerprint!=TP.fingerprint); check("simulation-flag",r.simulation_performed)
# 11-20 stale/version/binding
check("prod-version-hold",E.evaluate_prepared(PP,TP,req(target_production_version="v2")).decision==Decision.HOLD)
Tbad=E.prepare_snapshot(snap(sid="twin2",base="x"*64)); check("base-hold",E.evaluate_prepared(PP,Tbad,req()).decision==Decision.HOLD)
Tver=E.prepare_snapshot(snap(sid="twin3",version="v2",base=PP.fingerprint)); check("twin-version-hold",E.evaluate_prepared(PP,Tver,req()).decision==Decision.HOLD)
check("prod-stale",E.evaluate_prepared(PP,TP,req(now=5000,max_snapshot_age_ms=100)).decision==Decision.HOLD)
Pfuture=E.prepare_snapshot(snap(sid="pf",t=2000)); Tfuture=E.prepare_snapshot(snap(sid="tf",t=2000,base=Pfuture.fingerprint)); check("future-hold",E.evaluate_prepared(Pfuture,Tfuture,req(now=1000)).decision==Decision.HOLD)
# expected before
bad_a=replace(req().actions[0], expected_before_fingerprint="bad"); check("before-hold",E.evaluate_prepared(PP,TP,req(actions=(bad_a,))).decision==Decision.HOLD)
missing=PlannedChange("missing","x","y"); check("missing-hold",E.evaluate_prepared(PP,TP,req(actions=(missing,))).decision==Decision.HOLD)
# drift
it=list(mk_items()); it[0]=replace(it[0],value_fingerprint="z"*64); Td=E.prepare_snapshot(snap(tuple(it),sid="td",base=PP.fingerprint)); check("drift-hold",E.evaluate_prepared(PP,Td,req()).decision==Decision.HOLD)
# protected
prot=PlannedChange("asset-7",mk_items()[7].value_fingerprint,"n"*64); check("protected-deny",E.evaluate_prepared(PP,TP,req(actions=(prot,))).decision==Decision.DENY)
# no-op
noop=PlannedChange("asset-0",mk_items()[0].value_fingerprint,mk_items()[0].value_fingerprint); rr=E.evaluate_prepared(PP,TP,req(actions=(noop,))); check("noop-reason","NOOP_CHANGE" in rr.reasons)
# 21-30 impact
high=PlannedChange("asset-2",mk_items()[2].value_fingerprint,"h"*64); check("high-human",E.evaluate_prepared(PP,TP,req(actions=(high,))).decision==Decision.HUMAN_CONFIRM)
crit=PlannedChange("asset-3",mk_items()[3].value_fingerprint,"c"*64); check("critical-human",E.evaluate_prepared(PP,TP,req(actions=(crit,))).decision==Decision.HUMAN_CONFIRM)
irr=replace(req().actions[0],reversible=False); check("irreversible-human",E.evaluate_prepared(PP,TP,req(actions=(irr,))).decision==Decision.HUMAN_CONFIRM)
side=replace(req().actions[0],side_effect_targets=("s1","s2","s3","s4")); check("impact-threshold-human",E.evaluate_prepared(PP,TP,req(actions=(side,),impact_human_threshold=5)).decision==Decision.HUMAN_CONFIRM)
unk=replace(req().actions[0],unknown_side_effects=True); check("unknown-hold",E.evaluate_prepared(PP,TP,req(actions=(unk,))).decision==Decision.HOLD)
check("approval-high-allow",E.evaluate_prepared(PP,TP,req(actions=(high,),human_approval_evidence=True)).decision==Decision.ALLOW_CANDIDATE)
check("approval-irreversible-allow",E.evaluate_prepared(PP,TP,req(actions=(irr,),human_approval_evidence=True)).decision==Decision.ALLOW_CANDIDATE)
check("approval-doesnt-fix-unknown",E.evaluate_prepared(PP,TP,req(actions=(unk,),human_approval_evidence=True)).decision==Decision.HOLD)
check("approval-doesnt-fix-protected",E.evaluate_prepared(PP,TP,req(actions=(prot,),human_approval_evidence=True)).decision==Decision.DENY)
check("high-disabled-allow",E.evaluate_prepared(PP,TP,req(actions=(high,),require_human_for_high_criticality=False)).decision==Decision.ALLOW_CANDIDATE)
# 31-50 request validation
badfields=[("request_id",""),("policy_version",""),("authority_version",""),("target_production_version",""),("context_fingerprint","")]
for f,v in badfields:
    check("bad-"+f,E.evaluate_prepared(PP,TP,replace(req(),**{f:v})).decision==Decision.DENY)
check("bad-now",E.evaluate_prepared(PP,TP,replace(req(),observed_epoch_ms=-1)).decision==Decision.DENY)
check("bad-age",E.evaluate_prepared(PP,TP,replace(req(),max_snapshot_age_ms=-1)).decision==Decision.DENY)
check("bad-threshold",E.evaluate_prepared(PP,TP,replace(req(),impact_human_threshold=0)).decision==Decision.DENY)
check("no-actions",E.evaluate_prepared(PP,TP,replace(req(),actions=())).decision==Decision.DENY)
a=req().actions[0]
for f,v in [("target_id",""),("expected_before_fingerprint",""),("after_fingerprint",""),("change_kind","")]:
    check("bad-action-"+f,E.evaluate_prepared(PP,TP,req(actions=(replace(a,**{f:v}),))).decision==Decision.DENY)
check("duplicate-action",E.evaluate_prepared(PP,TP,req(actions=(a,a))).decision==Decision.DENY)
check("bad-side",E.evaluate_prepared(PP,TP,req(actions=(replace(a,side_effect_targets=("",)),))).decision==Decision.DENY)
check("control-request",E.evaluate_prepared(PP,TP,replace(req(),request_id="x\n")).decision==Decision.DENY)
check("control-target",E.evaluate_prepared(PP,TP,req(actions=(replace(a,target_id="asset-0\n"),))).decision==Decision.DENY)
# 51-61 snapshot validation
for badsnap in [
    replace(P,snapshot_id=""), replace(P,snapshot_version=""), replace(P,declared_fingerprint=""), replace(P,observed_epoch_ms=-1), replace(P,items=()),
    replace(P,items=(StateItem("","x"),)), replace(P,items=(StateItem("x",""),)),
    replace(P,items=(StateItem("x","a"),StateItem("x","b"))),
    replace(P,base_production_fingerprint="bad\n"), replace(P,declared_fingerprint="0"*64)
]:
    check("snapshot-deny-"+str(passed+failed), E.evaluate(badsnap,T,req()).decision==Decision.DENY)
# order-independent fingerprint
rev=tuple(reversed(mk_items())); check("order-independent",DigitalTwinImpactPredictor.snapshot_fingerprint(rev)==P.declared_fingerprint)
# 62-71 delta
it2=list(mk_items()); it2[0]=replace(it2[0],value_fingerprint="q"*64); it2=tuple(it2[:-1])+(StateItem("asset-new","n"*64,Criticality.LOW,False),)
T2raw=snap(it2,sid="target",version="v2",t=1200,base=PP.fingerprint); T2=E.prepare_snapshot(T2raw); d=E.make_delta(TP,T2); rec=E.reconstruct_candidate(TP,d)
check("delta-fp",rec.fingerprint==T2.fingerprint); check("delta-version",rec.snapshot_version=="v2"); check("delta-change",any(x.item_id=="asset-0" for x in d.changed_items)); check("delta-add",any(x.item_id=="asset-new" for x in d.changed_items)); check("delta-remove","asset-7" in d.removed_item_ids)
alt_items=list(mk_items()); alt_items[1]=replace(alt_items[1],value_fingerprint="alt"*16); ALT=E.prepare_snapshot(snap(tuple(alt_items),sid="alt"))
try: E.reconstruct_candidate(ALT,d); ok=False
except ValueError: ok=True
check("delta-base-mismatch",ok)
bad_delta=replace(d,target_fingerprint="0"*64)
try: E.reconstruct_candidate(TP,bad_delta); ok=False
except ValueError: ok=True
check("delta-target-mismatch",ok)
check("delta-no-commit",not hasattr(rec,"state_committed"))
check("delta-base-bind",d.base_fingerprint==TP.fingerprint); check("delta-target-bind",d.target_fingerprint==T2.fingerprint)
# 72-81 cache/materialization semantics and authority invariants
pp2=E.prepare_snapshot(P); check("prepare-cache-object",pp2 is PP)
check("prepared-readonly",type(PP.index).__name__=="mappingproxy")
rr=E.evaluate_prepared(PP,TP,req()); check("result-not-authoritative",rr.authoritative is False)
check("result-no-permission",rr.permission_granted is False)
check("result-no-production",rr.production_executed is False)
check("result-no-success",rr.production_succeeded is False)
check("result-no-commit",rr.state_committed is False)
check("dryrun-not-prod",rr.simulation_performed and not rr.production_executed)
check("fp-binds-twin",E.request_fingerprint(req(),PP.fingerprint,TP.fingerprint)!=E.request_fingerprint(req(),PP.fingerprint,"0"*64))
check("fp-binds-request",E.request_fingerprint(req(),PP.fingerprint,TP.fingerprint)!=E.request_fingerprint(replace(req(),context_fingerprint="c2"),PP.fingerprint,TP.fingerprint))
check("twin-bound-to-production", TP.base_production_fingerprint==PP.fingerprint)
check("dryrun-output-not-prod-fp", r.impact.resulting_twin_fingerprint!=PP.fingerprint)
check("human-evidence-not-production-success", E.evaluate_prepared(PP,TP,req(actions=(high,),human_approval_evidence=True)).production_succeeded is False)
check("human-evidence-not-permission", E.evaluate_prepared(PP,TP,req(actions=(high,),human_approval_evidence=True)).permission_granted is False)

print(f"PASS={passed} FAIL={failed} TOTAL={passed+failed}")
if failures:
    print("FAILURES="+",".join(failures))
    sys.exit(1)
