\
import json,time,statistics
from dataclasses import replace
import noepin_al_160_shadow_mode_comparison_engine as m
b='BENCH'; e='EPOCH-B'
live=m.LiveRequest('LIVE','GENERAL',False,'a'*64,b,e); stable=m.DecisionRecord('S',m.Decision.HOLD,'MORE',.42,False,False,b,e); shadow=m.DecisionRecord('SH',m.Decision.ALLOW,'ENOUGH',.38,False,False,b,e); outcome=m.Outcome('O',True,True,.91,b,e); policy=m.ShadowPolicy(True,True,.05,.25,b,e); q=m.ShadowComparisonRequest('CMP',live,stable,shadow,outcome,policy,b,e)
full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate(q) for __ in range(3000)]; full.append((time.perf_counter()-z)*1000/3000)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_live_request_fingerprint=st.live_request_fingerprint,current_stable_fingerprint=st.stable_fingerprint,current_shadow_fingerprint=st.shadow_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_result_fingerprint=st.result_fingerprint) for __ in range(3000)]; prep.append((time.perf_counter()-z)*1000/3000)
q2=replace(q,outcome=replace(outcome,utility_score=.92)); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); plan=m.plan_missing_only(st,st2); fb=len(m._canon(tuple(q2 for _ in range(3000)))); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 3000 shadow comparisons sharing canonical input state; full-state batch vs one changed Outcome delta; 5 full x 3000 and 5 prepared x 3000','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend':plan.full_resend_required},sort_keys=True))
