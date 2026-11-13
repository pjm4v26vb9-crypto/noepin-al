import json,time,statistics
from dataclasses import replace
import noepin_al_168_shared_base_delta_compressor as m
q=m.default_request(); b=q.binding; e=q.state_epoch
full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate(q) for __ in range(100)]; full.append((time.perf_counter()-z)*1000/100)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_variants_fingerprint=st.variants_fingerprint,current_config_fingerprint=st.config_fingerprint,current_result_fingerprint=st.result_fingerprint) for __ in range(100)]; prep.append((time.perf_counter()-z)*1000/100)
vs=list(q.variants); vv=list(vs[3].values); vv[9]+=1; vs[3]=replace(vs[3],values=tuple(vv)); q2=replace(q,variants=tuple(vs)); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); plan=m.plan_missing_only(st,st2)
fb=len(m._canon(tuple(q for _ in range(100)))); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 100 shared-base delta compression evaluations per round; 21 variants x 256 integer values; exact reversible reconstruction + delta/full comparison; full request batch vs one changed Variant record; 5 full x 100 and 5 prepared x 100','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend':plan.full_resend_required},sort_keys=True))
