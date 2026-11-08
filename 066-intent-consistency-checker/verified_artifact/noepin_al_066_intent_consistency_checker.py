"""NOEPIN AL 066 Intent Consistency Checker — Sequential Successor V2.
Creator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
License / Rights: NOT SPECIFIED
Pure evaluator: no network, shell, external writes, permission grant, or action execution.
"""
from dataclasses import dataclass, asdict
from enum import Enum
from hashlib import sha256
import json
from typing import Tuple, Dict, Iterable

class Decision(str, Enum):
    ALLOW="ALLOW"; DENY="DENY"; HOLD="HOLD"; HUMAN_APPROVAL="HUMAN_APPROVAL"

CRITICAL=("actor","verb","target","scope","outcome")
WEIGHTS={"actor":1.0,"verb":2.0,"target":3.0,"scope":3.0,"outcome":3.0}

def _norm(v:str)->str:
    return " ".join((v or "").strip().lower().split())
def _fp(obj)->str:
    return sha256(json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()

@dataclass(frozen=True)
class Intent:
    actor:str; verb:str; target:str; scope:str; outcome:str
    def normalized(self): return {k:_norm(getattr(self,k)) for k in CRITICAL}

@dataclass(frozen=True)
class IntentRequest:
    user_goal:Intent; claimed_purpose:Intent; plan:Intent; tool_call:Intent
    policy_id:str="AL066-POLICY"; policy_version:str="2"; context_fingerprint:str="CTX"

@dataclass(frozen=True)
class IntentPolicy:
    policy_id:str="AL066-POLICY"; version:str="2"; min_score:float=0.82
    deny_fields:Tuple[str,...]=("target","scope","outcome")

@dataclass(frozen=True)
class PreparedIntentState:
    policy_fingerprint:str; request_fingerprint:str; intents:Tuple[Tuple[str,Tuple[Tuple[str,str],...]],...]

@dataclass(frozen=True)
class IntentDelta:
    base_fingerprint:str; target_fingerprint:str; changed:Tuple[Tuple[str,str,str],...]

@dataclass(frozen=True)
class Result:
    decision:Decision; consistency_score:float; conflict_fields:Tuple[str,...]; missing_fields:Tuple[str,...]; reason_codes:Tuple[str,...]; input_fingerprint:str
    permission_granted:bool=False; tool_executed:bool=False; approval_executed:bool=False; world_truth_proven:bool=False; safety_proven:bool=False; action_success:bool=False


def policy_fingerprint(p:IntentPolicy)->str: return _fp(asdict(p))
def request_fingerprint(r:IntentRequest)->str:
    return _fp({"goal":r.user_goal.normalized(),"purpose":r.claimed_purpose.normalized(),"plan":r.plan.normalized(),"tool":r.tool_call.normalized(),"policy_id":r.policy_id,"policy_version":r.policy_version,"context":r.context_fingerprint})

def _intent_map(r:IntentRequest):
    return {"user_goal":r.user_goal.normalized(),"claimed_purpose":r.claimed_purpose.normalized(),"plan":r.plan.normalized(),"tool_call":r.tool_call.normalized()}

def prepare(r:IntentRequest,p:IntentPolicy)->PreparedIntentState:
    m=_intent_map(r)
    packed=tuple((n,tuple(sorted(v.items()))) for n,v in sorted(m.items()))
    return PreparedIntentState(policy_fingerprint(p),request_fingerprint(r),packed)

def validate_prepared_state(s:PreparedIntentState,r:IntentRequest,p:IntentPolicy)->bool:
    return s.policy_fingerprint==policy_fingerprint(p) and s.request_fingerprint==request_fingerprint(r)

def evaluate(r:IntentRequest,p:IntentPolicy=IntentPolicy())->Result:
    return _evaluate_map(_intent_map(r),r,p)

def evaluate_prepared(s:PreparedIntentState,r:IntentRequest,p:IntentPolicy=IntentPolicy(),*,prepared_integrity_validated:bool=False,current_request_fingerprint:str="")->Result:
    # Expensive structural integrity validation may be performed once at the trust boundary.
    # Repeated prepared evaluation still requires an explicit current request fingerprint.
    if prepared_integrity_validated:
        if s.policy_fingerprint!=policy_fingerprint(p) or not current_request_fingerprint or s.request_fingerprint!=current_request_fingerprint:
            return _hold(r,"PREPARED_STATE_STALE")
    elif not validate_prepared_state(s,r,p):
        return _hold(r,"PREPARED_STATE_STALE")
    m={n:dict(items) for n,items in s.intents}
    return _evaluate_map(m,r,p)

def _hold(r,reason,missing=(),conflicts=()):
    return Result(Decision.HOLD,0.0,tuple(conflicts),tuple(missing),(reason,),request_fingerprint(r))

def _evaluate_map(m:Dict[str,Dict[str,str]],r:IntentRequest,p:IntentPolicy)->Result:
    if r.policy_id!=p.policy_id or r.policy_version!=p.version: return _hold(r,"POLICY_MISMATCH")
    if not r.context_fingerprint: return _hold(r,"CONTEXT_FINGERPRINT_MISSING")
    missing=tuple(f"{n}.{f}" for n,x in m.items() for f in CRITICAL if not x.get(f))
    if missing: return _hold(r,"IMPORTANT_FIELD_MISSING",missing)
    base=m["user_goal"]; conflicts=[]; reasons=[]; total=sum(WEIGHTS.values())*3; matched=0.0
    for n in ("claimed_purpose","plan","tool_call"):
        x=m[n]
        for f in CRITICAL:
            if x[f]==base[f]: matched+=WEIGHTS[f]
            else: conflicts.append(f"{n}.{f}")
    score=matched/total
    conflict_fields=tuple(sorted(set(x.split(".",1)[1] for x in conflicts)))
    # Critical tool-call mismatch is strongest evidence of goal hijack / substitution.
    tool=m["tool_call"]
    for f in p.deny_fields:
        if tool[f]!=base[f]: reasons.append(f"TOOL_{f.upper()}_CONFLICT")
    if reasons: return Result(Decision.DENY,score,conflict_fields,(),tuple(reasons),request_fingerprint(r))
    # Claimed purpose or plan critical divergence is unresolved until actual tool remains bound.
    if any(f in conflict_fields for f in ("target","scope","outcome")):
        return Result(Decision.HOLD,score,conflict_fields,(),("PLAN_OR_PURPOSE_CRITICAL_DIVERGENCE",),request_fingerprint(r))
    if score < p.min_score:
        return Result(Decision.HOLD,score,conflict_fields,(),("CONSISTENCY_BELOW_THRESHOLD",),request_fingerprint(r))
    # actor/verb differences can be representational only, but are reported.
    return Result(Decision.ALLOW,score,conflict_fields,(),("CONSISTENT_INTENT_CANDIDATE",),request_fingerprint(r))

def make_delta(base:PreparedIntentState,target:PreparedIntentState)->IntentDelta:
    b={n:dict(v) for n,v in base.intents}; t={n:dict(v) for n,v in target.intents}; changes=[]
    for n in sorted(set(b)|set(t)):
        for f in CRITICAL:
            bv=b.get(n,{}).get(f,""); tv=t.get(n,{}).get(f,"")
            if bv!=tv: changes.append((n,f,tv))
    return IntentDelta(base.request_fingerprint,target.request_fingerprint,tuple(changes))

def missing_only_sync(local:PreparedIntentState,target:PreparedIntentState)->Tuple[Tuple[str,str,str],...]:
    l={n:dict(v) for n,v in local.intents}; t={n:dict(v) for n,v in target.intents}; out=[]
    for n,x in t.items():
        for f,v in x.items():
            if l.get(n,{}).get(f)!=v: out.append((n,f,v))
    return tuple(out)
