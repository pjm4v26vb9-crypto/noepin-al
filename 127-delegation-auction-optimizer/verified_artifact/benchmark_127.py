import json,time,statistics
from dataclasses import replace
import noepin_al_127_delegation_auction_optimizer as m
b='BENCH'; e='EPOCH-B'; task=m.DelegationTask('BENCH-TASK',('reasoning','code'),('sandbox',),.45,.60,b,e); bids=[]
for i in range(1200):
    caps=('reasoning','code','review') if i%11 else ('reasoning',)
    auth=('sandbox',) if i%17 else ()
    bids.append(m.AgentBid(f'AGENT-{i:04d}',caps,auth,.05+(i%70)/100,.05+(i%40)/100,.50+(i%50)/100,.60+(i%40)/100,b,e))
q=m.AuctionRequest('BENCH-127',task,tuple(bids),m.default_policy(),b,e)
full=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(5): m.evaluate(q)
    full.append((time.perf_counter()-t)*1000/5)
st=m.prepare_state(q,binding=b,state_epoch=e); prep=[]
for _ in range(5):
    t=time.perf_counter()
    for __ in range(20): m.evaluate_prepared(st,integrity_validated=True,current_context_fingerprint=st.context_fingerprint,current_bid_fingerprint=st.bid_fingerprint,current_policy_fingerprint=st.policy_fingerprint,current_outcome_fingerprint=st.outcome_fingerprint)
    prep.append((time.perf_counter()-t)*1000/20)
bs=list(bids); bs[-1]=replace(bs[-1],cost=bs[-1].cost+.01); q2=replace(q,bids=tuple(bs)); st2=m.prepare_state(q2,binding=b,state_epoch=e); d=m.make_delta(st,st2); sp=m.plan_missing_only(st,st2)
full_bytes=len(m._canon(q2)); delta_bytes=len(m._canon(d))
print(json.dumps({'condition':'Python stdlib; 1200 delegation bids; hard capability/authority/risk/availability/trust filters + constrained utility ranking; 5 full evaluations x 5 batches and 20 prepared reuses x 5 batches','full_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':m.evaluate(q)==st.result,'full_bytes':full_bytes,'delta_bytes':delta_bytes,'delta_percent':delta_bytes/full_bytes*100,'missing_records':len(sp.missing_or_changed_bid_ids),'missing_metadata_bytes':sp.metadata_bytes_required,'full_resend':sp.full_resend_required},sort_keys=True))
