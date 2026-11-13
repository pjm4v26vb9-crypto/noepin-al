"""NOEPIN AL 147 — Semantic Secret Detector — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-147
DCSR: AUXILIARY INTEGRATION / 補助統合.

Detects explicit and semantic secret candidates including split credential material. Outputs are
classification/redaction candidates only. Secret Label Candidate != Secret Truth. Confidence !=
Safety Proof. Redaction Plan != Redaction Execution. HOLD/DENY Candidate != Stop Execution.
This core does not send data, mutate content, invoke tools, replace authentication/encryption/Policy/DLP,
or grant permission. DCSR reconstruction cannot create Truth, Authority, Permission, Approval, Action,
or Action Success.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from hashlib import sha256
import json, math, re

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    CLEAR_CANDIDATE='CLEAR_CANDIDATE'; SECRET_DETECTED_CANDIDATE='SECRET_DETECTED_CANDIDATE'
    REVIEW_CANDIDATE='REVIEW_CANDIDATE'; INVALID='INVALID'
class NextAction(str, Enum):
    CONTINUE_CANDIDATE='CONTINUE_CANDIDATE'; REDACT_CANDIDATE='REDACT_CANDIDATE'
    RESTRICT_EXTERNAL_CANDIDATE='RESTRICT_EXTERNAL_CANDIDATE'; POLICY_REVIEW_CANDIDATE='POLICY_REVIEW_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'; KNOWN_SECRET='KNOWN_SECRET'; SEMANTIC_SECRET='SEMANTIC_SECRET'; SPLIT_SECRET='SPLIT_SECRET'
    LOW_CONFIDENCE='LOW_CONFIDENCE'; PUBLIC_CREDENTIAL_POLICY='PUBLIC_CREDENTIAL_POLICY'; INVALID_CONFIGURATION='INVALID_CONFIGURATION'
class SecretClass(str, Enum):
    API_KEY='API_KEY'; RECOVERY_CODE='RECOVERY_CODE'; TOKEN='TOKEN'; CREDENTIAL_COMBINATION='CREDENTIAL_COMBINATION'
    AUTH_MATERIAL='AUTH_MATERIAL'; UNKNOWN='UNKNOWN'

@dataclass(frozen=True)
class ContentFragment:
    fragment_id:str; content:str; role:str; provenance_ids:tuple[str,...]; binding:str; state_epoch:str
@dataclass(frozen=True)
class KnownSecretPattern:
    pattern_id:str; regex:str; secret_class:SecretClass; enabled:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class UsageSemantics:
    external_target:bool; auth_usage_expected:bool; public_credential_declared:bool; policy_verified:bool
    context_tags:tuple[str,...]; binding:str; state_epoch:str
@dataclass(frozen=True)
class SecretRequest:
    request_id:str; fragments:tuple[ContentFragment,...]; context:str; known_patterns:tuple[KnownSecretPattern,...]
    usage:UsageSemantics; semantic_coverage_known:bool; binding:str; state_epoch:str
@dataclass(frozen=True)
class SecretLabelCandidate:
    secret_class:SecretClass; confidence:float; source_fragment_ids:tuple[str,...]; evidence:tuple[str,...]
@dataclass(frozen=True)
class RedactionPlanCandidate:
    fragment_ids:tuple[str,...]; strategy:str; preserve_structure:bool
@dataclass(frozen=True)
class SecretResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState
    secret_labels:tuple[SecretLabelCandidate,...]; confidence:float; redaction_plan:RedactionPlanCandidate|None
    reasons:tuple[str,...]; trace:tuple[str,...]; next_gate_candidate:bool
    secret_label_promoted_to_truth:bool=False; confidence_promoted_to_safety_proof:bool=False
    redaction_plan_executed:bool=False; content_mutated:bool=False; external_send_executed:bool=False
    disclosure_executed:bool=False; credential_used:bool=False; tool_invoked:bool=False; policy_modified:bool=False
    dlp_replaced:bool=False; authentication_replaced:bool=False; encryption_replaced:bool=False
    dcsr_reconstruction_created_fact:bool=False; sender_authority_inherited:bool=False; sender_intent_inherited:bool=False
    sender_agreement_inherited:bool=False; permission_granted:bool=False; approval_executed:bool=False
    authority_granted:bool=False; stop_executed:bool=False; action_executed:bool=False; plan_committed:bool=False
    publish_executed:bool=False; external_write_performed:bool=False; world_truth_proven:bool=False
    domain_authority_promoted:bool=False; safety_proven:bool=False; action_success:bool=False
@dataclass(frozen=True)
class PreparedSecretState:
    request:SecretRequest; result:SecretResult; fragments_fingerprint:str; context_fingerprint:str
    patterns_fingerprint:str; usage_fingerprint:str; outcome_fingerprint:str; integrity_fingerprint:str
    binding:str; state_epoch:str
@dataclass(frozen=True)
class SecretDelta:
    fragments_changed:bool; context_changed:bool; patterns_changed:bool; usage_changed:bool
    from_manifest_fingerprint:str; to_manifest_fingerprint:str
@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

def _obj(v):
    if isinstance(v,Enum): return v.value
    if is_dataclass(v): return {f.name:_obj(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v,dict): return {str(k):_obj(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list)): return [_obj(x) for x in v]
    return v

def _canon(v): return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def _fp(v): return sha256(_canon(v)).hexdigest()

def default_request():
    b='DEFAULT-BINDING'; e='EPOCH-1'
    f=ContentFragment('FRAG-147-A','api_key = "sk_live_ABCDEF1234567890ABCDEF"','CONFIG',('SRC-147-A',),b,e)
    p=KnownSecretPattern('PAT-147-API',r'\bsk_live_[A-Za-z0-9]{20,}\b',SecretClass.API_KEY,True,b,e)
    u=UsageSemantics(True,True,False,True,('code-review','external'),b,e)
    return SecretRequest('REQ-147',(f,),'code review before external publication',(p,),u,True,b,e)

def _invalid(req,reason):
    return SecretResult(Decision.HOLD,NextAction.POLICY_REVIEW_CANDIDATE,Escalation.INVALID_CONFIGURATION,EngineState.INVALID,
        (),1.0,None,(reason,'NO_EXTERNAL_SEND_EXECUTION','NO_CONTENT_MUTATION'),(),False)

def _validate(req):
    if not req.request_id or not req.binding or not req.state_epoch: return 'EMPTY_REQUEST_CONTEXT'
    if not req.fragments: return 'NO_CONTENT_FRAGMENTS'
    ids=[f.fragment_id for f in req.fragments]
    if len(set(ids))!=len(ids) or any(not x for x in ids): return 'INVALID_FRAGMENT_IDS'
    for f in req.fragments:
        if f.binding!=req.binding or f.state_epoch!=req.state_epoch or not f.role: return 'FRAGMENT_BINDING_MISMATCH'
        if len(set(f.provenance_ids))!=len(f.provenance_ids) or any(not x for x in f.provenance_ids): return 'INVALID_PROVENANCE'
    pids=[p.pattern_id for p in req.known_patterns]
    if len(set(pids))!=len(pids) or any(not x for x in pids): return 'INVALID_PATTERN_IDS'
    for p in req.known_patterns:
        if p.binding!=req.binding or p.state_epoch!=req.state_epoch: return 'PATTERN_BINDING_MISMATCH'
        try: re.compile(p.regex)
        except re.error: return 'INVALID_PATTERN_REGEX'
    u=req.usage
    if u.binding!=req.binding or u.state_epoch!=req.state_epoch: return 'USAGE_BINDING_MISMATCH'
    if len(set(u.context_tags))!=len(u.context_tags): return 'DUPLICATE_CONTEXT_TAGS'
    return None

def _entropy(s):
    if not s: return 0.0
    counts={c:s.count(c) for c in set(s)}; n=len(s)
    return -sum((v/n)*math.log2(v/n) for v in counts.values())

def _known(req):
    out=[]
    for p in req.known_patterns:
        if not p.enabled: continue
        rx=re.compile(p.regex)
        for f in req.fragments:
            if rx.search(f.content):
                out.append(SecretLabelCandidate(p.secret_class,1.0,(f.fragment_id,),('KNOWN_PATTERN:'+p.pattern_id,)))
    return out

def _semantic(req):
    out=[]; lower_ctx=(req.context+' '+' '.join(req.usage.context_tags)).lower()
    for f in req.fragments:
        t=f.content.lower()
        pairs=[
            (SecretClass.RECOVERY_CODE,('recovery code','backup code','復旧コード')),
            (SecretClass.API_KEY,('api key','api_key','apikey')),
            (SecretClass.TOKEN,('bearer token','access token','refresh token','token=')),
            (SecretClass.AUTH_MATERIAL,('password','passphrase','client secret','private key','credential')),
        ]
        for cls,words in pairs:
            if any(w in t for w in words):
                conf=0.90 if req.usage.auth_usage_expected or any(x in lower_ctx for x in ('auth','login','credential','code review')) else 0.74
                out.append(SecretLabelCandidate(cls,conf,(f.fragment_id,),('SEMANTIC_AUTH_USAGE',)))
        # High entropy only becomes a review candidate, never truth.
        toks=re.findall(r'[A-Za-z0-9_\-]{24,}',f.content)
        if any(_entropy(x)>=3.6 for x in toks):
            out.append(SecretLabelCandidate(SecretClass.UNKNOWN,0.62,(f.fragment_id,),('HIGH_ENTROPY_TOKEN_CANDIDATE',)))
    return out

def _split(req):
    # Detect useful credential combinations spread across fragments, without reconstructing or using them.
    url_ids=[]; token_ids=[]; user_ids=[]; pass_ids=[]
    for f in req.fragments:
        t=f.content.lower()
        if ('internal' in t and ('http://' in t or 'https://' in t)) or 'login_url' in t: url_ids.append(f.fragment_id)
        if any(x in t for x in ('token=', 'access token', 'bearer ', 'secret=')): token_ids.append(f.fragment_id)
        if any(x in t for x in ('username=', 'user=')): user_ids.append(f.fragment_id)
        if any(x in t for x in ('password=', 'passphrase=')): pass_ids.append(f.fragment_id)
    out=[]
    if url_ids and token_ids:
        ids=tuple(sorted(set(url_ids+token_ids)))
        if len(ids)>=2: out.append(SecretLabelCandidate(SecretClass.CREDENTIAL_COMBINATION,0.96,ids,('INTERNAL_URL_PLUS_TOKEN_COMBINATION',)))
    if user_ids and pass_ids:
        ids=tuple(sorted(set(user_ids+pass_ids)))
        if len(ids)>=2: out.append(SecretLabelCandidate(SecretClass.CREDENTIAL_COMBINATION,0.98,ids,('USERNAME_PASSWORD_COMBINATION',)))
    return out

def _dedupe(labels):
    best={}
    for x in labels:
        k=(x.secret_class,x.source_fragment_ids,x.evidence)
        if k not in best or x.confidence>best[k].confidence: best[k]=x
    return tuple(sorted(best.values(),key=lambda x:(-x.confidence,x.secret_class.value,x.source_fragment_ids,x.evidence)))

def evaluate(req):
    err=_validate(req)
    if err: return _invalid(req,err)
    labels=_dedupe(_known(req)+_semantic(req)+_split(req))
    conf=max((x.confidence for x in labels),default=0.0)
    trace=tuple(f'{x.secret_class.value}:{x.confidence:.2f}:{",".join(x.source_fragment_ids)}' for x in labels)
    plan=None
    if labels:
        ids=tuple(sorted({fid for x in labels for fid in x.source_fragment_ids}))
        plan=RedactionPlanCandidate(ids,'MASK_OR_TOKENIZE_CANDIDATE',True)
    if req.usage.external_target and not req.semantic_coverage_known:
        return SecretResult(Decision.HOLD,NextAction.REDACT_CANDIDATE,Escalation.LOW_CONFIDENCE,EngineState.REVIEW_CANDIDATE,
            labels,max(conf,0.5),plan,('SEMANTIC_COVERAGE_UNKNOWN_FOR_EXTERNAL_TARGET','HOLD_OR_REDACT_CANDIDATE','NO_EXTERNAL_SEND_EXECUTION'),trace,True)
    known=any('KNOWN_PATTERN:' in ev for x in labels for ev in x.evidence)
    split=any(x.secret_class==SecretClass.CREDENTIAL_COMBINATION for x in labels)
    high=any(x.confidence>=0.85 and x.secret_class!=SecretClass.UNKNOWN for x in labels)
    low=bool(labels) and not high and not known and not split
    if req.usage.public_credential_declared and labels:
        return SecretResult(Decision.HOLD,NextAction.POLICY_REVIEW_CANDIDATE,Escalation.PUBLIC_CREDENTIAL_POLICY,EngineState.REVIEW_CANDIDATE,
            labels,conf,plan,('PUBLIC_CREDENTIAL_DECLARATION_REQUIRES_POLICY_EVALUATION','NO_PERMISSION_GRANT','NO_EXTERNAL_SEND_EXECUTION'),trace,True)
    if req.usage.external_target and known:
        return SecretResult(Decision.DENY,NextAction.RESTRICT_EXTERNAL_CANDIDATE,Escalation.KNOWN_SECRET,EngineState.SECRET_DETECTED_CANDIDATE,
            labels,conf,plan,('KNOWN_SECRET_CANDIDATE_EXTERNAL_TARGET','DENY_IS_CANDIDATE_NOT_STOP_EXECUTION','NO_EXTERNAL_SEND_EXECUTION'),trace,True)
    if req.usage.external_target and split:
        return SecretResult(Decision.DENY,NextAction.RESTRICT_EXTERNAL_CANDIDATE,Escalation.SPLIT_SECRET,EngineState.SECRET_DETECTED_CANDIDATE,
            labels,conf,plan,('SPLIT_SECRET_COMBINATION_CANDIDATE','NO_EXTERNAL_SEND_EXECUTION'),trace,True)
    if req.usage.external_target and high:
        return SecretResult(Decision.HOLD,NextAction.REDACT_CANDIDATE,Escalation.SEMANTIC_SECRET,EngineState.SECRET_DETECTED_CANDIDATE,
            labels,conf,plan,('HIGH_CONFIDENCE_SEMANTIC_SECRET_CANDIDATE','NO_REDACTION_EXECUTION','NO_EXTERNAL_SEND_EXECUTION'),trace,True)
    if low:
        return SecretResult(Decision.HOLD,NextAction.POLICY_REVIEW_CANDIDATE,Escalation.LOW_CONFIDENCE,EngineState.REVIEW_CANDIDATE,
            labels,conf,plan,('LOW_CONFIDENCE_SECRET_CANDIDATE','REVIEW_REQUIRED','NO_EXTERNAL_SEND_EXECUTION'),trace,True)
    if labels:
        return SecretResult(Decision.ALLOW,NextAction.CONTINUE_CANDIDATE,Escalation.NONE,EngineState.SECRET_DETECTED_CANDIDATE,
            labels,conf,plan,('SECRET_CANDIDATE_INTERNAL_ONLY','ALLOW_IS_CANDIDATE_NOT_PERMISSION','NO_CREDENTIAL_USE'),trace,True)
    return SecretResult(Decision.ALLOW,NextAction.CONTINUE_CANDIDATE,Escalation.NONE,EngineState.CLEAR_CANDIDATE,
        (),0.0,None,('NO_SECRET_CANDIDATE_DETECTED','ALLOW_IS_CANDIDATE_NOT_PERMISSION'),(),True)

def prepare_state(req,binding,state_epoch):
    if req.binding!=binding or req.state_epoch!=state_epoch: return PreparedSecretState(req,_invalid(req,'PREPARE_BINDING_MISMATCH'),'','','','','','','',binding,state_epoch)
    result=evaluate(req); ff=_fp(req.fragments); cf=_fp(req.context); pf=_fp(req.known_patterns); uf=_fp(req.usage); of=_fp(result)
    integ=_fp((ff,cf,pf,uf,of,binding,state_epoch))
    return PreparedSecretState(req,result,ff,cf,pf,uf,of,integ,binding,state_epoch)

def evaluate_prepared(st,*,integrity_validated,current_fragments_fingerprint,current_context_fingerprint,current_patterns_fingerprint,current_usage_fingerprint,current_outcome_fingerprint):
    exp=_fp((st.fragments_fingerprint,st.context_fingerprint,st.patterns_fingerprint,st.usage_fingerprint,st.outcome_fingerprint,st.binding,st.state_epoch))
    if not integrity_validated or exp!=st.integrity_fingerprint: return _invalid(st.request,'PREPARED_INTEGRITY_INVALID')
    if (current_fragments_fingerprint,current_context_fingerprint,current_patterns_fingerprint,current_usage_fingerprint,current_outcome_fingerprint)!=(st.fragments_fingerprint,st.context_fingerprint,st.patterns_fingerprint,st.usage_fingerprint,st.outcome_fingerprint):
        return _invalid(st.request,'PREPARED_FINGERPRINT_MISMATCH')
    return st.result

def make_delta(old,new):
    of=_fp((old.fragments_fingerprint,old.context_fingerprint,old.patterns_fingerprint,old.usage_fingerprint,old.outcome_fingerprint))
    nf=_fp((new.fragments_fingerprint,new.context_fingerprint,new.patterns_fingerprint,new.usage_fingerprint,new.outcome_fingerprint))
    return SecretDelta(old.fragments_fingerprint!=new.fragments_fingerprint,old.context_fingerprint!=new.context_fingerprint,
        old.patterns_fingerprint!=new.patterns_fingerprint,old.usage_fingerprint!=new.usage_fingerprint,of,nf)

def plan_missing_only(old,new):
    ids=[]
    if old.fragments_fingerprint!=new.fragments_fingerprint: ids.append('CONTENT_FRAGMENTS')
    if old.context_fingerprint!=new.context_fingerprint: ids.append('CONTEXT')
    if old.patterns_fingerprint!=new.patterns_fingerprint: ids.append('KNOWN_SECRET_PATTERNS')
    if old.usage_fingerprint!=new.usage_fingerprint: ids.append('USAGE_SEMANTICS')
    return MissingOnlyPlan(tuple(ids),len(_canon(tuple(ids)))+104,False)

def default_evaluation(): return evaluate(default_request())

if __name__=='__main__': print(json.dumps(_obj(default_evaluation()),ensure_ascii=False,sort_keys=True))
