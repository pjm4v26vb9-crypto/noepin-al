import argparse,json,time,statistics
from dataclasses import replace
from pathlib import Path
import noepin_al_066_intent_consistency_checker as m

def I(i=''): return m.Intent('user','read','report'+i,'scope'+i,'summarize')
def R(i=''): return m.IntentRequest(I(i),I(i),I(i),I(i),context_fingerprint='CTX'+i)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args(); p=m.IntentPolicy(); reqs=[R(str(i)) for i in range(1500)]; states=[m.prepare(r,p) for r in reqs]; full=[];prep=[]
 for _ in range(5):
  t=time.perf_counter();v=[m.evaluate(r,p) for r in reqs];full.append((time.perf_counter()-t)*1000)
 for _ in range(5):
  t=time.perf_counter();v2=[m.evaluate_prepared(s,r,p,prepared_integrity_validated=True,current_request_fingerprint=s.request_fingerprint) for s,r in zip(states,reqs)];prep.append((time.perf_counter()-t)*1000)
 sem=all(x.decision==y.decision and x.consistency_score==y.consistency_score for x,y in zip(v,v2)); b=states[0];tgt=m.prepare(m.IntentRequest(I(),I(),I(),m.Intent('user','inspect','report','scope','summarize'),context_fingerprint='CTX'),p);d=m.make_delta(b,tgt);sync=m.missing_only_sync(b,tgt);fb=len(json.dumps(b.__dict__,default=str));db=len(json.dumps(d.__dict__,default=str));o={'condition_specific':True,'dataset':{'intent_sets':1500},'batches':5,'full_materialization_median_ms':statistics.median(full),'prepared_median_ms':statistics.median(prep),'semantic_match':sem,'delta':{'full_bytes':fb,'delta_bytes':db,'delta_ratio_percent':db/fb*100,'changed_fields':len(d.changed)},'missing_only_sync':{'missing_fields':len(sync),'metadata_bytes_required':len(json.dumps(sync)),'full_resend_required':False},'authority':{'permission_granted':False,'tool_executed':False,'action_success':False}};a.out.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps(o));return 0 if sem else 2
if __name__=='__main__':raise SystemExit(main())
