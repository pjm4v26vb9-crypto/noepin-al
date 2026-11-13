import json,time,statistics
from dataclasses import replace
import noepin_al_151_capability_escrow as m
b='BENCH'; e='EPOCH-B'
ids=tuple(f'CAP-{i:04d}' for i in range(3000)); capid=ids[-1]
c=m.RequestedCapability(capid,m.CapabilityClass.PROD_ADMIN_API,'vault-ref://bench',True,b,e)
co=m.EscrowConditions('COND-B',True,True,'deploy','service://bench',tuple(f'CLAIM-{i:04d}' for i in range(3000)),b,e)
a=m.AgentIdentity('AGENT-B',True,'TRUST-B',b,e)
p=m.PermitEvidence('PERMIT-B',True,True,capid,a.agent_id,co.purpose,co.target_ref,100,180,'NONCE-B',b,e)
pol=m.EscrowPolicy('POL-B',True,True,True,120,(m.CapabilityClass.PROD_ADMIN_API,),ids,b,e)
q=m.CapabilityEscrowRequest('REQ-B',c,co,a,p,pol,False,False,True,150,b,e)
full=[]
for _ in range(5):
    z=time.perf_counter()
    for __ in range(5): m.evaluate(q)
    full.append((time.perf_counter()-z)*1000/5)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
    z=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_capability_fingerprint=st.capability_fingerprint,current_conditions_fingerprint=st.conditions_fingerprint,current_agent_fingerprint=st.agent_fingerprint,current_permit_fingerprint=st.permit_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_request_context_fingerprint=st.request_context_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-z)*1000/20)
p2=replace(p,nonce='NONCE-B-2'); q2=replace(q,permit=p2); st2=m.prepare_state(q2,b,e); delta=m.make_delta(st,st2); plan=m.plan_missing_only(st,st2)
fb=len(m._canon(q2)); db=len(m._canon(delta))
print(json.dumps({'condition':'Python stdlib; 3000 allowed capability IDs + 3000 required claims; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend':plan.full_resend_required},sort_keys=True))
