import json,time,statistics
import noepin_al_178_risk_envelope_artifact as m
q=m.default_request(); b=q.binding; e=q.state_epoch
full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate(q) for __ in range(1000)]; full.append((time.perf_counter()-z)*1000/1000)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_envelope_fingerprint=st.envelope_fingerprint,current_context_fingerprint=st.context_fingerprint,current_result_fingerprint=st.result_fingerprint) for __ in range(1000)]; prep.append((time.perf_counter()-z)*1000/1000)
x=dict(observed=dict(q.envelope.observed),limits=dict(q.envelope.limits),critical_dimensions=q.envelope.critical_dimensions,rationale=q.envelope.rationale,envelope_id=q.envelope.envelope_id); x['observed']['uncertainty']=0.25
e2=m.build_envelope(**x); q2=m.RiskEvaluationRequest(q.evaluation_id,e2,e2.observed,e2.limits,e2.critical_dimensions,q.context_id,q.binding,q.state_epoch); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); plan=m.plan_missing_only(st,st2)
fb=len(m._canon(tuple(q for _ in range(1000)))); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 1000 Risk Envelope validations per round; seven observed dimensions + seven limits + critical set + rationale; full request batch vs one changed observed risk dimension; 5 full x 1000 and 5 prepared x 1000','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==m.evaluate_prepared(st,integrity_validated=True,current_envelope_fingerprint=st.envelope_fingerprint,current_context_fingerprint=st.context_fingerprint,current_result_fingerprint=st.result_fingerprint),'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'missing_record_ids':plan.missing_or_changed_record_ids,'full_resend':plan.full_resend_required},sort_keys=True))
