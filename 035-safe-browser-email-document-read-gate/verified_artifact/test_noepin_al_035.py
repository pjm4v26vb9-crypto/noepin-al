import dataclasses, json, math, sys
from noepin_al_035_safe_reader_gate import *

P=F=0

def ck(name, cond):
    global P,F
    if cond: P+=1
    else:
        F+=1; print('FAIL',name)

def req(**kw):
    base=dict(request_id='r1',source_type=SourceType.WEB,source_id='src',source_version='v1',content_fingerprint='cfp',origin='https://example.invalid',observed_epoch_ms=1,policy_version='p1',authority_version='a1',context_fingerprint='ctx',source_allowlisted=True,content_bytes=100)
    base.update(kw); return ExternalContentRequest(**base)

g=SafeReaderGate()
# baseline
r=g.evaluate(req()); ck('baseline read',r.decision==Decision.READ_CANDIDATE); ck('untrusted true',r.untrusted_content); ck('no authority',not r.instruction_authority); ck('no truth',not r.truth_established); ck('not trusted',not r.content_trusted); ck('no permission',not r.permission_granted); ck('no action',not r.external_action_executed); ck('no memory',not r.memory_written); ck('no commit',not r.state_committed); ck('no success',not r.action_succeeded); ck('not authoritative',not r.authoritative)
# source types
for st in [SourceType.WEB,SourceType.EMAIL,SourceType.PDF,SourceType.DOCUMENT,SourceType.LOG,SourceType.RAG,SourceType.TOOL_OUTPUT,SourceType.EXTERNAL_AI]: ck('type '+st.value,g.evaluate(req(source_type=st,request_id='r'+st.value)).decision==Decision.READ_CANDIDATE)
ck('unknown hold',g.evaluate(req(source_type=SourceType.UNKNOWN,request_id='u')).decision==Decision.HOLD)
# injection/sanitize/quarantine
ck('instruction sanitize',g.evaluate(req(request_id='i',instruction_markers=('ignore previous',))).decision==Decision.SANITIZE)
ck('mid score sanitize',g.evaluate(req(request_id='m',prompt_injection_score=.5)).decision==Decision.SANITIZE)
ck('high score quarantine',g.evaluate(req(request_id='h',prompt_injection_score=.9)).decision==Decision.QUARANTINE)
ck('active quarantine',g.evaluate(req(request_id='a',active_content_present=True)).decision==Decision.QUARANTINE)
ck('exe quarantine',g.evaluate(req(request_id='e',executable_attachment_present=True)).decision==Decision.QUARANTINE)
ck('hidden quarantine',g.evaluate(req(request_id='o',hidden_or_obfuscated_text=True)).decision==Decision.QUARANTINE)
ck('authority quarantine',g.evaluate(req(request_id='sa',claims_system_authority=True)).decision==Decision.QUARANTINE)
ck('policy override quarantine',g.evaluate(req(request_id='po',requests_policy_override=True)).decision==Decision.QUARANTINE)
ck('shell quarantine',g.evaluate(req(request_id='sh',tool_or_shell_markers=('run shell',))).decision==Decision.QUARANTINE)
ck('secret quarantine',g.evaluate(req(request_id='sec',secret_request_markers=('send api key',))).decision==Decision.QUARANTINE)
ck('memory quarantine',g.evaluate(req(request_id='mw',requests_memory_write=True)).decision==Decision.QUARANTINE)
ck('action quarantine',g.evaluate(req(request_id='ea',requests_external_action=True)).decision==Decision.QUARANTINE)
# privacy / consent
ck('personal hold',g.evaluate(req(request_id='pd',contains_personal_data=True,consent_evidence_present=False)).decision==Decision.HOLD)
ck('sensitive hold',g.evaluate(req(request_id='sd',contains_sensitive_data=True,consent_evidence_present=False)).decision==Decision.HOLD)
ck('personal with evidence read',g.evaluate(req(request_id='pe',contains_personal_data=True,consent_evidence_present=True)).decision==Decision.READ_CANDIDATE)
# high impact
ck('high impact human',g.evaluate(req(request_id='hi',high_impact_context=True)).decision==Decision.HUMAN_CONFIRM)
ck('high impact approved read',g.evaluate(req(request_id='ha',high_impact_context=True,human_approval_evidence=True)).decision==Decision.READ_CANDIDATE)
# source verification
ck('unverified sanitize',g.evaluate(req(request_id='uv',source_allowlisted=False,sender_or_source_verified=False)).decision==Decision.SANITIZE)
ck('verified read',g.evaluate(req(request_id='vv',source_allowlisted=False,sender_or_source_verified=True)).decision==Decision.READ_CANDIDATE)
# signature
ck('bad signature hold',g.evaluate(req(request_id='bs',signed_content=True,signature_valid=False)).decision==Decision.HOLD)
ck('good signature read',g.evaluate(req(request_id='gs',signed_content=True,signature_valid=True)).decision==Decision.READ_CANDIDATE)
# links/attachments don't imply authority
rl=g.evaluate(req(request_id='ln',external_link_count=3,attachment_count=2)); ck('links still candidate',rl.decision==Decision.READ_CANDIDATE); ck('links no action',not rl.external_action_executed)
# validation variants
invalids=[
 ('empty request',dict(request_id='')),('empty source',dict(source_id='')),('empty version',dict(source_version='')),('empty fp',dict(content_fingerprint='')),('empty origin',dict(origin='')),('empty policy',dict(policy_version='')),('empty auth',dict(authority_version='')),('empty ctx',dict(context_fingerprint='')),('negative time',dict(observed_epoch_ms=-1)),('nan score',dict(prompt_injection_score=float('nan'))),('score hi',dict(prompt_injection_score=1.1)),('score lo',dict(prompt_injection_score=-.1)),('neg links',dict(external_link_count=-1)),('neg attach',dict(attachment_count=-1)),('bad max',dict(max_content_bytes=0)),('neg size',dict(content_bytes=-1)),('too large',dict(content_bytes=200,max_content_bytes=100)),('bad marker',dict(instruction_markers=('',))),('too many markers',dict(instruction_markers=tuple('x' for _ in range(129))))]
for n,k in invalids: ck(n,g.evaluate(req(**k)).decision==Decision.DENY)
# control chars
ck('control char id deny',g.evaluate(req(request_id='bad\x01')).decision==Decision.DENY)
ck('control marker deny',g.evaluate(req(request_id='cm',instruction_markers=('bad\x01',))).decision==Decision.DENY)
# authority invariants under bad content
q=g.evaluate(req(request_id='q',prompt_injection_score=.99,requests_external_action=True,requests_memory_write=True,claims_system_authority=True))
for name,val in [('q no truth',q.truth_established),('q no perm',q.permission_granted),('q no action',q.external_action_executed),('q no mem',q.memory_written),('q no commit',q.state_committed),('q no success',q.action_succeeded),('q no auth',q.authoritative)]: ck(name,not val)
# cache exactness
c=SafeReaderGate(enable_cache=True); x=req(request_id='cache'); a=c.evaluate(x); b=c.evaluate(x); ck('first miss',not a.cache_hit); ck('second hit',b.cache_hit); ck('same decision',a.decision==b.decision); ck('same fp',a.request_fingerprint==b.request_fingerprint)
# version/context changes prevent cache hit
for name,mod in [('source version',{'source_version':'v2'}),('policy version',{'policy_version':'p2'}),('authority version',{'authority_version':'a2'}),('context',{'context_fingerprint':'ctx2'}),('content fp',{'content_fingerprint':'cfp2'}),('purpose',{'purpose':'DIFFERENT'})]:
    y=dataclasses.replace(x,**mod); rr=c.evaluate(y); ck(name+' miss',not rr.cache_hit)
# disabled cache
nc=SafeReaderGate(enable_cache=False); n1=nc.evaluate(x); n2=nc.evaluate(x); ck('disabled miss1',not n1.cache_hit); ck('disabled miss2',not n2.cache_hit); ck('disabled deterministic',n1==n2)
# threshold validation
try: SafeReaderGate(injection_sanitize_threshold=.9,injection_quarantine_threshold=.2); ok=False
except ValueError: ok=True
ck('threshold validation',ok)
print(json.dumps({'passed':P,'failed':F},sort_keys=True))
sys.exit(1 if F else 0)
