import dataclasses,json,statistics,time
import noepin_al_097_conflict_mass_aggregator as m

def bench(fn,n=10,batches=5):
    vals=[]
    for _ in range(batches):
        t=time.perf_counter_ns()
        for _ in range(n): fn()
        vals.append((time.perf_counter_ns()-t)/1e6/n)
    return statistics.median(vals)
p=m.default_policy(); q=m.default_query()
beliefs=tuple(m.EvidenceBelief(f'E{i:05d}',.78,.08,.14,.55+(i%40)/100,.55+(i%40)/100,f'S{i%200:04d}',f'V{i%7}',f'SF{i}',f'CF{i}',True,p.binding,p.state_epoch) for i in range(5000))
rels=tuple(m.ConflictRelation(f'R{i:05d}',f'E{i:05d}',f'E{(i+1)%5000:05d}',.15+(i%20)/100,.5+(i%40)/100,True,p.binding,p.state_epoch) for i in range(1000))
st=m.prepare_state(q,beliefs,rels,p,binding=p.binding,state_epoch=p.state_epoch); ok=m.validate_prepared_integrity(st)
full=bench(lambda:m.evaluate(q,beliefs,rels,p)); prepared=bench(lambda:m.evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=ok))
tb=list(beliefs)
for i in range(10): tb[i]=dataclasses.replace(tb[i],source_version='V-CHANGED',source_fingerprint=f'SF-CHANGED-{i}')
target=m.prepare_state(q,tuple(tb),rels,p,binding=p.binding,state_epoch=p.state_epoch); d=m.make_delta(st,target); recon=m.apply_delta(st,d)
known=dict(target.record_fingerprints)
for i in range(10): known.pop(f'BELIEF:E{i:05d}',None)
sync=m.missing_only_sync_plan(target,known); fb=m.full_registry_bytes(target); db=m.delta_bytes(d)
print(json.dumps({'condition':'Python stdlib; 5000 Evidence beliefs + 1000 explicit conflict relations; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':full,'prepared_median_ms':prepared,'semantic_match':recon==target and st.precomputed_result==m.evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_calibration_fingerprint=st.calibration_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=ok),'full_bytes':fb,'delta_bytes':db,'delta_percent':(db/fb*100 if fb else 0),'missing_records':len(sync.missing_or_changed_record_ids),'metadata_bytes':sync.metadata_bytes_required,'full_resend':sync.full_resend_required},sort_keys=True))
