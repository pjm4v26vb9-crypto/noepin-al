import json,time,statistics
from dataclasses import replace
import noepin_al_150_tainted_instruction_sink_guard as m
b='BENCH'; e='EPOCH-B'
chain=tuple(f'TRANSFORM-{i:04d}' for i in range(3000))
i=m.InstructionNode('BENCH-I','candidate tool operation','SRC-150',False,chain,b,e)
t=tuple(m.TaintLabel(f'T-{n:04d}',m.TaintKind.DATA_ONLY if n<2999 else m.TaintKind.UNTRUSTED_INSTRUCTION,'SRC-150',chain[max(0,n-3):n+1],1.0,b,e) for n in range(3000))
s=m.TargetSink('BENCH-S',m.SinkClass.TOOL_EXECUTE,'tool://bench',True,True,b,e)
a=m.UserAuthorizationEvidence('BENCH-A',False,(),i.instruction_id,s.sink_id,False,b,e)
q=m.SinkGuardRequest('BENCH-150',i,t,s,a,True,b,e)
full=[]
for _ in range(5):
    z=time.perf_counter()
    for __ in range(5): m.evaluate(q)
    full.append((time.perf_counter()-z)*1000/5)
st=m.prepare_state(q,b,e); prep=[]
for _ in range(5):
    z=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_instruction_fingerprint=st.instruction_fingerprint,current_taint_fingerprint=st.taint_fingerprint,current_sink_fingerprint=st.sink_fingerprint,current_authorization_fingerprint=st.authorization_fingerprint,current_path_fingerprint=st.path_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-z)*1000/20)
t2=t[:-1]+(replace(t[-1],kind=m.TaintKind.DATA_ONLY),); q2=replace(q,taints=t2); st2=m.prepare_state(q2,b,e); delta=m.make_delta(st,st2); plan=m.plan_missing_only(st,st2)
fb=len(m._canon(q2)); db=len(m._canon(delta))
print(json.dumps({'condition':'Python stdlib; 3000 transformations + 3000 taint labels; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':fb,'delta_bytes':db,'delta_percent':db/fb*100,'missing_records':len(plan.missing_or_changed_record_ids),'missing_metadata_bytes':plan.metadata_bytes_required,'full_resend':plan.full_resend_required},sort_keys=True))
