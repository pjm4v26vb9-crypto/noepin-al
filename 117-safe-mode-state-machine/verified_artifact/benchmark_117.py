import json,time,statistics
from dataclasses import replace
import noepin_al_117_safe_mode_state_machine as m
b='BENCH-BIND'; e='BENCH-EPOCH'; ev=[]
for i in range(1200):
    sev=m.RiskSeverity.LOW if i%31 else m.RiskSeverity.MEDIUM
    ev.append(m.RiskEvent(f'E{i:04d}',sev,True,'SYSTEM','V1',f'FP-{i:04d}',b,e))
p=m.SafeModePolicy(.70,.40,.90,3,100,m.SafetyMode.READ_ONLY,m.SafetyMode.READ_ONLY)
q=m.SafeModeRequest('BENCH-117',m.SafetyMode.NORMAL,tuple(ev),.95,m.Connectivity.TRUSTED,p,(m.OperatorSignal.NONE,),5,b,e)
st=m.prepare_state(q,binding=b,state_epoch=e); integrity=m.validate_prepared_integrity(st)
full=[]; prep=[]; z=z2=None
for _ in range(5):
    t0=time.perf_counter()
    for _j in range(5): z=m.evaluate(q)
    full.append((time.perf_counter()-t0)*1000/5)
    t0=time.perf_counter()
    for _j in range(20): z2=m.evaluate_prepared(st,integrity_validated=integrity,current_context_fingerprint=st.context_fingerprint,current_event_fingerprint=st.event_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_registry_fingerprint=st.registry_fingerprint,current_transition_fingerprint=st.transition_fingerprint)
    prep.append((time.perf_counter()-t0)*1000/20)
changed=[replace(x,severity=m.RiskSeverity.HIGH,evidence_fingerprint=x.evidence_fingerprint+'X') for x in ev[:10]]
q2=replace(q,risk_events=tuple(changed)+tuple(ev[10:])); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon(q2)); delta_bytes=len(m._canon(d))
out={'condition':'Python stdlib; 1200 risk events; finite-state safety-mode classification with trust/connectivity/operator signals; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':z==z2,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required}
print(json.dumps(out,sort_keys=True))
