import dataclasses,json,statistics,time
import noepin_al_096_source_freshness_decay as m

def bench(fn,n=10,batches=5):
    vals=[]
    for _ in range(batches):
        t=time.perf_counter_ns()
        for _ in range(n): fn()
        vals.append((time.perf_counter_ns()-t)/1e6/n)
    return statistics.median(vals)
p=m.default_policy(); q=dataclasses.replace(m.default_query(),source_id='SRC-02500')
sources=tuple(m.SourceFreshnessRecord(f'SRC-{i:05d}',1000.0-(i%60),list(m.SourceType)[i%5],list(m.Volatility)[i%4],f'V{i%11}',f'SF{i}',f'CF{i}',False,True,p.binding,p.state_epoch) for i in range(5000))
st=m.prepare_state(q,sources,p,binding=p.binding,state_epoch=p.state_epoch); ok=m.validate_prepared_integrity(st)
full=bench(lambda:m.evaluate(q,sources,p)); prepared=bench(lambda:m.evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=ok))
target_sources=list(sources)
for i in range(10): target_sources[i]=dataclasses.replace(target_sources[i],source_version='V-CHANGED',source_fingerprint=f'SF-CHANGED-{i}')
target=m.prepare_state(q,tuple(target_sources),p,binding=p.binding,state_epoch=p.state_epoch); d=m.make_delta(st,target); recon=m.apply_delta(st,d)
known=dict(target.record_fingerprints)
for i in range(10): known.pop(f'SRC:SRC-{i:05d}',None)
sync=m.missing_only_sync_plan(target,known); fb=m.full_registry_bytes(target); db=m.delta_bytes(d)
print(json.dumps({'condition':'Python stdlib; 5000 Source freshness records; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':full,'prepared_median_ms':prepared,'semantic_match':recon==target and st.precomputed_result==m.evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=ok),'full_bytes':fb,'delta_bytes':db,'delta_percent':(db/fb*100 if fb else 0),'missing_records':len(sync.missing_or_changed_record_ids),'metadata_bytes':sync.metadata_bytes_required,'full_resend':sync.full_resend_required},sort_keys=True))
