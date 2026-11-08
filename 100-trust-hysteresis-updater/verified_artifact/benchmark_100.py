import dataclasses,json,statistics,time
import noepin_al_100_trust_hysteresis_updater as m

def bench(fn,n=10,batches=5):
    vals=[]
    for _ in range(batches):
        t=time.perf_counter_ns()
        for _ in range(n): fn()
        vals.append((time.perf_counter_ns()-t)/1e6/n)
    return statistics.median(vals)
p=m.default_policy(); q=dataclasses.replace(m.default_query(),current_trust=.76,current_tier=m.TrustTier.STANDARD,current_success_streak=0,last_event_time=0.0,reference_time=10000.0)
events=[]
for i in range(5000):
    outcome=m.EventOutcome.SUCCESS if i%17 else m.EventOutcome.FAILURE
    sev=m.Severity.LOW if outcome==m.EventOutcome.SUCCESS else (m.Severity.MEDIUM if i%51 else m.Severity.HIGH)
    events.append(m.TrustEvent(f'E{i:05d}',outcome,sev,float(i+1),.95,i,f'M{i%5}',f'P{i%3}',f'K{i%7}',f'SF{i}',True,p.binding,p.state_epoch))
events=tuple(events)
st=m.prepare_state(q,events,p,binding=p.binding,state_epoch=p.state_epoch); ok=m.validate_prepared_integrity(st)
full=bench(lambda:m.evaluate(q,events,p)); prepared=bench(lambda:m.evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=ok))
tr=list(events)
for i in range(10): tr[i]=dataclasses.replace(tr[i],metric_version='K-CHANGED',source_fingerprint=f'SF-CHANGED-{i}')
target=m.prepare_state(q,tuple(tr),p,binding=p.binding,state_epoch=p.state_epoch); d=m.make_delta(st,target); recon=m.apply_delta(st,d)
known=dict(target.event_fingerprints)
for i in range(10): known.pop(f'EV:E{i:05d}',None)
sync=m.missing_only_sync_plan(target,known); fb=m.full_registry_bytes(target); db=m.delta_bytes(d)
print(json.dumps({'condition':'Python stdlib; 5000 Trust events across model/policy/metric versions; asymmetric hysteresis update; 10 evaluations x 5 batches; prepared verified-result reuse','full_median_ms':full,'prepared_median_ms':prepared,'semantic_match':recon==target and st.precomputed_result==m.evaluate_prepared(st,current_context_fingerprint=st.context_fingerprint,current_dependency_fingerprint=st.dependency_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,prepared_integrity_validated=ok),'full_bytes':fb,'delta_bytes':db,'delta_percent':(db/fb*100 if fb else 0),'missing_records':len(sync.missing_or_changed_event_ids),'metadata_bytes':sync.metadata_bytes_required,'full_resend':sync.full_resend_required},sort_keys=True))
