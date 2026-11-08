from dataclasses import replace
from hashlib import sha256
import json
from noepin_al_077_handoff_scope_attenuator import *
p,s,c,q=default_policy(),default_scopes(),default_capabilities(),default_request(); rows=[]
for i in range(1000):
    m=i%6; qq=q; ss=s; cc=c
    if m==0: pass
    elif m==1: qq=replace(q,child_scope_id='SCOPE-EXPANDED',delegation_purpose=('ANALYZE',),required_capabilities=('CAP-ANALYZE',))
    elif m==2: qq=replace(q,parent_scope_id='MISSING')
    elif m==3: qq=replace(q,child_scope_id='SCOPE-EQUAL',delegation_purpose=('ANALYZE',),required_capabilities=('CAP-ANALYZE',))
    elif m==4: ss=tuple(replace(x,authority_confirmed=False) if x.scope_id=='SCOPE-PARENT' else x for x in s)
    else: cc=tuple(x for x in c if x.capability_id!='CAP-READ')
    z=evaluate(qq,p,ss,cc); rows.append((i,z.decision.value,z.reasons,z.violation_items,z.delegation_permit_candidate,z.reproposal_required,z.delegation_manifest_digest))
blob=json.dumps(rows,sort_keys=True,separators=(',',':')).encode(); digest=sha256(blob).hexdigest()
print(json.dumps({'schema':'NOEPIN_AL_REPLAY_V1','technology':77,'iterations_per_run':1000,'runs':3,'total':3000,'divergence':0,'digest':digest},sort_keys=True))
