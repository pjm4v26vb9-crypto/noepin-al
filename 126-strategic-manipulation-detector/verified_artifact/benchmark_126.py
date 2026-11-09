import json,time,statistics
from dataclasses import replace
import noepin_al_126_strategic_manipulation_detector as m
b='BENCH'; e='EPOCH-B'; records=[]
for i in range(1200):
    obs=((i%100)+1)/100
    claimed=obs + (0.01 if i%17 else 0.18)
    exp=(f'E{i:04d}-A',f'E{i:04d}-B')
    omitted=(exp[1],) if i%53==0 else ()
    records.append(m.ClaimAuditRecord(f'C{i:04d}',f'AGENT-{i%24}',f'M{i%9}',claimed,obs,.03,.75 if i%17==0 else .15,1,exp,exp,omitted,4 if i%101==0 else 0,b,e))
q=m.ManipulationRequest('BENCH-126',tuple(records),m.default_policy(),b,e)
full=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(5): m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
st=m.prepare_state(q,binding=b,state_epoch=e); prep=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_record_fingerprint=st.record_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
rs=list(records); rs[-1]=replace(rs[-1],claimed_value=rs[-1].claimed_value+.01); q2=replace(q,records=tuple(rs)); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon(q2)); delta_bytes=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 1200 claim/outcome audit records across 24 agents; mismatch + omission + incentive alignment + repetition analysis; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required},sort_keys=True))
