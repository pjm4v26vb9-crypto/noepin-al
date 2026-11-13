import json,time,statistics
from dataclasses import replace
import noepin_al_142_semantic_taint_propagation_engine as m
b='BENCH'; e='EPOCH-B'; ds=[]; ts=[]
for i in range(2500):
    labels=()
    if i%7==0: labels+=(m.TaintLabel.UNTRUSTED,)
    if i%29==0: labels+=(m.TaintLabel.SENSITIVE,)
    if i%97==0: labels+=(m.TaintLabel.EXTERNAL_INSTRUCTION,)
    ds.append(m.DataItem(f'D-{i:04d}',labels,(f'SRC-{i:04d}',),b,e))
for i in range(0,2500,5):
    inputs=tuple(f'D-{j:04d}' for j in range(i,min(i+5,2500)))
    ts.append(m.Transformation(f'T-{i:04d}',m.TransformKind.MERGE,inputs,f'O-{i:04d}'))
sinks=(m.Sink('INTERNAL',m.SinkKind.INTERNAL),)
edges=tuple(m.FlowEdge(t.output_id,'INTERNAL') for t in ts)
q=m.TaintRequest('BENCH-142',tuple(ds),tuple(ts),edges,sinks,b,e)
full=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(3): m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/3)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_data_fingerprint=st.data_fingerprint,current_transform_fingerprint=st.transform_fingerprint,current_flow_fingerprint=st.flow_fingerprint,current_sink_fingerprint=st.sink_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
ys=list(ds); ys[-1]=replace(ys[-1],provenance_ids=(ys[-1].provenance_ids[0],'SRC-CHANGED')); q2=replace(q,data_items=tuple(ys)); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
fb=len(m._canon(q2)); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 2500 Data items; 500 merge transformations; semantic taint propagation with provenance/flow/sink candidates; 3 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required},sort_keys=True))
