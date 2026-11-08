from __future__ import annotations
import json
from hashlib import sha256
import noepin_al_041_behavior_anomaly as m

NOW=1_800_000_000

def dataset():
    b=m.default_baseline(NOW)
    events=[]
    for i in range(100):
        mode=i%5
        kw={}
        if mode==1: kw["operation"]=f"UNSEEN_{i%7}"
        elif mode==2: kw["events_per_minute"]=180.0+i
        elif mode==3: kw["tool_name"]=f"REMOTE_{i%4}"; kw["operation"]="DEPLOY"
        elif mode==4: kw["capabilities"]=frozenset({"READ_METADATA","LOCAL_EVAL","ROOT"})
        e=m.BehaviorEvent(
            event_id=f"R{i}",actor_id="A",observed_at=NOW,tool_name=kw.get("tool_name","LOCAL_ANALYZER"),
            operation=kw.get("operation","ANALYZE"),resource_class="INTERNAL_METADATA",
            events_per_minute=kw.get("events_per_minute",30.0),tool_calls_per_minute=10.0,
            capabilities=kw.get("capabilities",frozenset({"READ_METADATA","LOCAL_EVAL"})),
            expected_baseline_id=b.baseline_id,expected_baseline_version=b.version,
            expected_authority_epoch=b.authority_epoch,evidence_id=f"EV{i}",evidence_verified=True)
        events.append(e)
    return b,events

def run_once():
    b,events=dataset(); p=m.prepare_baseline(b,now=NOW)
    vals=[]
    for _ in range(10):
        vals.extend(m.evaluate_prepared(e,p,now=NOW) for e in events)
    body=m.canonical_json(vals)
    return sha256(body.encode()).hexdigest(),len(vals)

if __name__=="__main__":
    runs=[run_once() for _ in range(3)]
    out={"runs":len(runs),"evaluations_per_run":runs[0][1],"total_evaluations":sum(x[1] for x in runs),"digests":[x[0] for x in runs],"divergence":len({x[0] for x in runs})-1}
    print(json.dumps(out,sort_keys=True))
