import json,time,statistics
from dataclasses import replace
import noepin_al_125_debate_convergence_detector as m
b='BENCH'; e='EPOCH-B'; turns=[]
for i in range(1200):
    turns.append(m.DebateTurn(i+1,f'T{i+1:04d}',f'AGENT-{i%8}',f'CLAIM-{(i//20)%6}',(f'E{i//4:04d}',),.1+((i%7)-3)*.005,b,e))
issues=tuple(m.DebateIssue(f'ISSUE-{i:03d}',m.IssueSeverity.LOW,True) for i in range(80))
p=replace(m.default_policy(),window_size=16,max_turns=2000,min_turns=4)
q=m.DebateRequest('BENCH-125',m.RiskClass.MEDIUM,tuple(turns),issues,p,b,e)
full=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(5): m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
st=m.prepare_state(q,binding=b,state_epoch=e); prep=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_turn_fingerprint=st.turn_fingerprint,current_issue_fingerprint=st.issue_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
xs=list(turns); xs[-1]=replace(xs[-1],position=xs[-1].position+.01); q2=replace(q,turns=tuple(xs)); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon(q2)); delta_bytes=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 1200 debate turns / 80 issues; novelty window + position stability + oscillation + unresolved-issue convergence state machine; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_record_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required},sort_keys=True))
