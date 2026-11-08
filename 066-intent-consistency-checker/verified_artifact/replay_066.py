import json,argparse
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import noepin_al_066_intent_consistency_checker as m

def I(**kw):
 d=dict(actor='user',verb='read',target='report',scope='section-a',outcome='summarize'); d.update(kw); return m.Intent(**d)
def R(**kw):
 d=dict(user_goal=I(),claimed_purpose=I(),plan=I(),tool_call=I()); d.update(kw); return m.IntentRequest(**d)
def one(i):
 k=i%8; r=R()
 if k==1:r=R(tool_call=I(target='other'))
 elif k==2:r=R(tool_call=I(scope='all'))
 elif k==3:r=R(tool_call=I(outcome='delete'))
 elif k==4:r=R(plan=I(target='other'))
 elif k==5:r=R(plan=I(target=''))
 elif k==6:r=R(policy_version='bad')
 elif k==7:r=R(tool_call=I(actor='agent'))
 x=m.evaluate(r); return json.dumps(x.__dict__,sort_keys=True,default=str)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);a=ap.parse_args(); runs=[]; digs=[]
 for _ in range(3):
  v=[one(i) for i in range(1000)];runs.append(v);digs.append(sha256('\n'.join(v).encode()).hexdigest())
 div=sum(not(runs[0][i]==runs[1][i]==runs[2][i]) for i in range(1000));o={'runs':3,'evaluations_per_run':1000,'total_evaluations':3000,'digests':digs,'digest_same':len(set(digs))==1,'digest':digs[0],'divergence':div};a.out.write_text(json.dumps(o,indent=2)+'\n');print(json.dumps(o));return 0 if div==0 and len(set(digs))==1 else 2
if __name__=='__main__':raise SystemExit(main())
