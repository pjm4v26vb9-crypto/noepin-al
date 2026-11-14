import json,time,statistics
from dataclasses import replace
import noepin_al_177_execution_receipt_artifact as m
q=m.default_request(); b=q.binding; e=q.state_epoch
full=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate(q) for __ in range(1000)]; full.append((time.perf_counter()-z)*1000/1000)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
 z=time.perf_counter(); [m.evaluate_prepared(st,integrity_validated=True,current_receipt_fingerprint=st.receipt_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint) for __ in range(1000)]; prep.append((time.perf_counter()-z)*1000/1000)
r=q.receipt
r2=m.build_receipt(receipt_id=r.receipt_id,request_id=r.request_id,permit_id=r.permit_id,action=r.action,target=r.target,started_at=r.started_at,finished_at=r.finished_at,status=r.status,changes=r.changes+('changed segment evidence',),postconditions=r.postconditions,rollback_reference=r.rollback_reference,intent_fingerprint=r.intent_fingerprint,policy_fingerprint=r.policy_fingerprint,result_digest=r.result_digest,issuer_authority_id=r.issuer_authority_id)
q2=replace(q,receipt=r2); st2=m.prepare_state(q2,b,e); d=m.make_delta(st,st2); plan=m.plan_missing_only(st,st2)
fb=len(m._canon(tuple(q for _ in range(1000)))); db=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 1000 Execution Receipt binding verifications per round; Request/Permit/Action/Target + time/status/changes/postconditions/rollback + Intent/Policy/Result SHA-256; full request batch vs one append-only Receipt change segment; 5 full x 1000 and 5 prepared x 1000','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==m.evaluate_prepared(st,integrity_validated=True,current_receipt_fingerprint=st.receipt_fingerprint,current_query_fingerprint=st.query_fingerprint,current_result_fingerprint=st.result_fingerprint),'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'missing_record_ids':plan.missing_or_changed_record_ids,'full_resend':plan.full_resend_required},sort_keys=True))
