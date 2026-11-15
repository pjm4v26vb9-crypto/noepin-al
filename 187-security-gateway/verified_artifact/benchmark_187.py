import json,time,statistics
import noepin_al_187_security_gateway as m
req=m.default_request(); pol=m.default_policy(); dyn=m.default_dynamic(); full=[]
for _ in range(5):
    z=time.perf_counter(); [m.evaluate(req,pol,dyn) for __ in range(1000)]; full.append((time.perf_counter()-z)*1000/1000)
st=m.prepare_state(req,pol,dyn); prep=[]
for _ in range(5):
    z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_request=req,current_policy=pol,current_dynamic=dyn,current_result_fingerprint=st.result_fingerprint,current_integrity_fingerprint=st.integrity_fingerprint) for __ in range(1000)]; prep.append((time.perf_counter()-z)*1000/1000)
r=m.evaluate(req,pol,dyn); known={'REQUEST':m.request_fingerprint(req),'POLICY':m.policy_fingerprint(pol)}; plan=m.plan_missing_only(req,pol,dyn,known)
full_bytes=len(m._canon((req,pol,dyn))); delta_bytes=plan.metadata_bytes_required
print(json.dumps({'condition':'Python stdlib Security Gateway; 1000 full evaluations per round vs exact-fingerprint Prepared State reuse; 5 x 1000 each; DCSR comparison reuses request+policy and refreshes dynamic security state','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.fingerprint(r)==st.result_fingerprint,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':(delta_bytes/full_bytes*100 if full_bytes else 0),'missing_fields':plan.missing_or_changed_fields,'missing_metadata_bytes':delta_bytes,'full_reevaluation_required':plan.full_reevaluation_required},sort_keys=True))
