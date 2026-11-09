import json,time,statistics
from dataclasses import replace
import noepin_al_121_latency_safety_tradeoff_controller as m
b='BENCH-BIND'; e='BENCH-EPOCH'; checks=[]
for i in range(1200):
    mand=(m.RiskClass.LOW if i<3 else None); checks.append(m.SafetyCheck(f'C{i:04d}',.05+(i%11)*.01,.001+(i%7)*.0002,mand,True,False,b,e))
p=m.TradeoffPolicy(.1,0.0,.20); q=m.TradeoffRequest('BENCH-121',45.0,m.RiskClass.MEDIUM,tuple(checks),p,b,e); st=m.prepare_state(q,binding=b,state_epoch=e); integrity=m.validate_prepared_integrity(st)
full=[]; prep=[]; z=z2=None
for _ in range(5):
    t=time.perf_counter();
    for _j in range(5): z=m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
    t=time.perf_counter();
    for _j in range(20): z2=m.evaluate_prepared(st,integrity_validated=integrity,current_context_fingerprint=st.context_fingerprint,current_check_fingerprint=st.check_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_selection_fingerprint=st.selection_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
checks2=[replace(x,latency_ms=x.latency_ms+.001) if i<10 else x for i,x in enumerate(checks)]; q2=replace(q,checks=tuple(checks2)); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2); fb=len(m._canon(q2)); db=len(m._canon(d))
out={'condition':'Python stdlib; 1200 safety checks; mandatory-check policy + latency-aware optional selection; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':z==z2,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required}; print(json.dumps(out,sort_keys=True))
