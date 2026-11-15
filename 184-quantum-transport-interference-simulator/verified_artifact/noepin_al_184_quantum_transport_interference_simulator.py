"""NOEPIN AL 184 — AL Quantum Transport and Interference Simulator — Sequential Successor V2.
Creator / Originator / Project Owner / Original Concept / Architecture Direction: NOEPIN / のえぴん
AI-assisted implementation / analysis / documentation support: ChatGPT
License / Rights: NOT SPECIFIED
Canonical ID: NOEPIN-AL-184
DCSR: LIMITED APPLICATION / 限定適用.

CPU-only mathematical simulator. This module does not connect to a QPU, network,
device, browser, shell, external filesystem, or credential/permission system. It
models remote-CZ transport fidelity, dynamical-decoupling tradeoffs, and a toy
entanglement-routing model under hard quality/resource constraints. ALLOW means
only that a simulation candidate satisfies this model's local constraints. It is
not Truth, Permission Grant, Human Approval, QPU execution, physical performance,
quantum advantage, unknown-state reconstruction, Action Execution, Action Success,
or a universal Safety Proof.

DCSR may reuse integrity-verified parameters/results/log metadata when current
fingerprints match. It may not reconstruct an unknown quantum state, invent a
physical measurement, improve real hardware fidelity, or authorize execution.
"""
from __future__ import annotations
from dataclasses import dataclass, fields, is_dataclass, replace
from enum import Enum
from hashlib import sha256
import json, math, random

class Decision(str, Enum):
    ALLOW='ALLOW'; HOLD='HOLD'; DENY='DENY'
class EngineState(str, Enum):
    SIMULATION_CANDIDATE='SIMULATION_CANDIDATE'
    QUALITY_HOLD_CANDIDATE='QUALITY_HOLD_CANDIDATE'
    PERMISSION_EVIDENCE_DENIED='PERMISSION_EVIDENCE_DENIED'
    INVALID_REQUEST='INVALID_REQUEST'
    PREPARED_STATE_STALE='PREPARED_STATE_STALE'
class NextAction(str, Enum):
    CONTINUE_MODEL_REVIEW_CANDIDATE='CONTINUE_MODEL_REVIEW_CANDIDATE'
    ADJUST_CONSTRAINTS_CANDIDATE='ADJUST_CONSTRAINTS_CANDIDATE'
    REQUEST_PERMISSION_EVIDENCE_CANDIDATE='REQUEST_PERMISSION_EVIDENCE_CANDIDATE'
    RETAIN_NO_EXECUTION_CANDIDATE='RETAIN_NO_EXECUTION_CANDIDATE'
    FULL_RECOMPUTE_CANDIDATE='FULL_RECOMPUTE_CANDIDATE'
class Escalation(str, Enum):
    NONE='NONE'
    INVALID_INPUT='INVALID_INPUT'
    MISSING_PURPOSE='MISSING_PURPOSE'
    PERMISSION_EVIDENCE_MISSING='PERMISSION_EVIDENCE_MISSING'
    RESOURCE_BUDGET_UNSATISFIED='RESOURCE_BUDGET_UNSATISFIED'
    QUALITY_CONSTRAINT_UNSATISFIED='QUALITY_CONSTRAINT_UNSATISFIED'
    ROUTE_CONSTRAINT_UNSATISFIED='ROUTE_CONSTRAINT_UNSATISFIED'
    PREPARED_STATE_STALE='PREPARED_STATE_STALE'


def _obj(v):
    if isinstance(v, Enum): return v.value
    if is_dataclass(v): return {f.name:_obj(getattr(v,f.name)) for f in fields(v)}
    if isinstance(v, dict): return {str(k):_obj(v[k]) for k in sorted(v,key=str)}
    if isinstance(v,(tuple,list,set,frozenset)):
        seq=[_obj(x) for x in v]
        if isinstance(v,(set,frozenset)):
            seq=sorted(seq,key=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')))
        return seq
    if isinstance(v,float):
        if math.isnan(v) or math.isinf(v): return str(v)
        return round(v,15)
    return v

def _canon(v): return json.dumps(_obj(v),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
def _fp(v): return sha256(_canon(v)).hexdigest()

def _finite(name,v,lo=None,hi=None):
    if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(float(v)): raise ValueError(f'{name}: finite number required')
    x=float(v)
    if lo is not None and x<lo: raise ValueError(f'{name}: below minimum')
    if hi is not None and x>hi: raise ValueError(f'{name}: above maximum')
    return x

@dataclass(frozen=True)
class Link:
    a:str; b:str; fidelity:float; success:float; latency:float; energy:float

@dataclass(frozen=True)
class SimulationRequest:
    experiment_id:str
    seed:int
    bell_fidelity:float
    gate_trials:int
    noise_trials:int
    noise_sigma:float
    slow_fraction:float
    pulse_error:float
    t1:float
    tphi:float
    min_gate_fidelity:float
    min_dd_quality:float
    max_pulses:int
    graph:tuple[Link,...]
    start:str
    goal:str
    min_route_fidelity:float
    min_route_success:float
    max_expected_latency:float
    max_expected_energy:float
    purpose:str
    permission_evidence_present:bool
    resource_budget:float
    estimated_classical_cost:float
    estimated_qpu_cost:float
    qpu_available:bool=False

@dataclass(frozen=True)
class GateMetrics:
    trials:int; seed:int; resource_fidelity:float; mean_state_fidelity:float; min_state_fidelity:float
    pauli_counts:tuple[tuple[str,int],...]

@dataclass(frozen=True)
class DDMetric:
    name:str; probability_plus_x:float; standard_error:float; pulse_count:int; lower_bound:float; score:float; feasible:bool

@dataclass(frozen=True)
class RouteMetric:
    path:tuple[str,...]; hops:int; swaps:int; pair_fidelity:float; success_probability:float
    one_attempt_latency:float; expected_latency:float; energy_per_attempt:float; expected_energy:float; score:float

@dataclass(frozen=True)
class SimulationResult:
    decision:Decision; next_action:NextAction; escalation:Escalation; engine_state:EngineState
    experiment_id:str; backend_candidate:str|None; gate:GateMetrics|None; dd_candidates:tuple[DDMetric,...]
    selected_dd_strategy:str|None; selected_route:RouteMetric|None; route_candidate_count:int
    request_fingerprint:str; simulation_fingerprint:str; next_gate_candidate:bool; full_recompute_candidate:bool
    reasons:tuple[str,...]; prepared_state_reused:bool=False
    permission_granted:bool=False; permit_issued:bool=False; approval_executed:bool=False; human_approval_executed:bool=False
    qpu_invoked:bool=False; qpu_execution_authorized:bool=False; network_send_executed:bool=False; tool_invoked:bool=False
    action_executed:bool=False; action_success:bool=False; stop_executed:bool=False; file_write_executed:bool=False
    external_write_performed:bool=False; authoritative_state_created:bool=False; cached_state_promoted:bool=False
    reconstructed_state_promoted:bool=False; partial_state_promoted:bool=False; dcsr_reconstructed_unknown_quantum_state:bool=False
    dcsr_invented_measurement:bool=False; dcsr_improved_hardware_fidelity:bool=False; unknown_quantum_state_reconstructed:bool=False
    quantum_state_cloned:bool=False; physical_fidelity_proven:bool=False; quantum_advantage_proven:bool=False
    hardware_energy_proven:bool=False; world_truth_proven:bool=False; domain_authority_promoted:bool=False; safety_proven:bool=False
    classical_recovery_executed:bool=False; quantum_recovery_executed:bool=False

@dataclass(frozen=True)
class PreparedSimulationState:
    request:SimulationRequest; result:SimulationResult; request_fingerprint:str; result_fingerprint:str; integrity_fingerprint:str

@dataclass(frozen=True)
class ParameterDelta:
    experiment_id:str; changed_fields:tuple[str,...]; from_request_fingerprint:str; to_request_fingerprint:str; delta_fingerprint:str

@dataclass(frozen=True)
class MissingOnlyPlan:
    missing_or_changed_record_ids:tuple[str,...]; metadata_bytes_required:int; full_resend_required:bool

# --- 4-qubit CPU state-vector model -------------------------------------------------
def _pure(n): return [0j]*(1<<n)
def _h(s,q):
    mask=1<<q; inv=math.sqrt(.5)
    for i in range(len(s)):
        if not i&mask:
            j=i|mask; a,b=s[i],s[j]; s[i]=(a+b)*inv; s[j]=(a-b)*inv

def _x(s,q):
    mask=1<<q
    for i in range(len(s)):
        if not i&mask:
            j=i|mask; s[i],s[j]=s[j],s[i]

def _z(s,q):
    mask=1<<q
    for i in range(len(s)):
        if i&mask: s[i]=-s[i]

def _y(s,q): _x(s,q); _z(s,q)
def _cnot(s,c,t):
    if c==t: raise ValueError('CNOT separate qubits required')
    cm,tm=1<<c,1<<t
    for i in range(len(s)):
        if i&cm and not i&tm:
            j=i|tm; s[i],s[j]=s[j],s[i]

def _cz(s,a,b):
    if a==b: raise ValueError('CZ separate qubits required')
    am,bm=1<<a,1<<b
    for i in range(len(s)):
        if i&am and i&bm: s[i]=-s[i]

def _measure(s,q,rng):
    m=1<<q; p=sum(abs(s[i])**2 for i in range(len(s)) if i&m); p=max(0.0,min(1.0,p)); bit=1 if rng.random()<p else 0; chosen=p if bit else 1-p
    if chosen<1e-14: raise ValueError('zero-probability measurement')
    k=1/math.sqrt(chosen)
    for i in range(len(s)): s[i]=s[i]*k if bool(i&m)==bool(bit) else 0j
    return bit

def _random_product(rng):
    th1=math.acos(1-2*rng.random()); ph1=2*math.pi*rng.random(); th2=math.acos(1-2*rng.random()); ph2=2*math.pi*rng.random()
    a=(math.cos(th1/2),math.sin(th1/2)*complex(math.cos(ph1),math.sin(ph1)))
    b=(math.cos(th2/2),math.sin(th2/2)*complex(math.cos(ph2),math.sin(ph2)))
    return [a[i]*b[j] for j in range(2) for i in range(2)]

def gate_trial(input_state, resource_fidelity=1.0, rng=None):
    f=_finite('resource_fidelity',resource_fidelity,.25,1); rng=rng or random.Random(0)
    if len(input_state)!=4: raise ValueError('two-qubit state required')
    s=_pure(4)
    for i,v in enumerate(input_state): s[i]=complex(v)
    _h(s,2); _cnot(s,2,3)
    u=rng.random(); pauli='I'
    if u>=f:
        width=(1-f)/3
        j=min(2,int((u-f)/width)) if width>0 else 0; pauli=('X','Y','Z')[j]
        (_x if pauli=='X' else _y if pauli=='Y' else _z)(s,3)
    _h(s,1); _cnot(s,0,2); mz=_measure(s,2,rng)
    if mz: _x(s,3)
    _cnot(s,3,1); _h(s,3); mx=_measure(s,3,rng)
    if mx: _z(s,0)
    _h(s,1)
    shift=(mz<<2)|(mx<<3); out=[s[i|shift] for i in range(4)]
    ideal=list(input_state); ideal[3]=-ideal[3]
    norm=sum(abs(v)**2 for v in out) or 1.0
    overlap=sum(complex(ideal[i]).conjugate()*out[i] for i in range(4))
    fidelity=max(0.0,min(1.0,(abs(overlap)**2)/norm))
    return fidelity,pauli,norm

def gate_benchmark(fidelity=1.0,trials=32,seed=105):
    _finite('fidelity',fidelity,.25,1)
    if isinstance(trials,bool) or not isinstance(trials,int) or not 1<=trials<=100000: raise ValueError('trials out of range')
    if isinstance(seed,bool) or not isinstance(seed,int) or seed<0 or seed>2**32-1: raise ValueError('seed out of range')
    rng=random.Random(seed); vals=[]; counts={'I':0,'X':0,'Y':0,'Z':0}
    for _ in range(trials):
        f,p,n=gate_trial(_random_product(rng),fidelity,rng); vals.append(f); counts[p]+=1
        if abs(n-1)>1e-9: raise ValueError('state norm drift')
    return GateMetrics(trials,seed,float(fidelity),sum(vals)/len(vals),min(vals),tuple(sorted(counts.items())))

# --- dynamical-decoupling toy model ------------------------------------------------
def _rotate(b,axis,theta):
    c,s=math.cos(theta),math.sin(theta); x,y,z=b
    if axis=='Z': b[0]=c*x-s*y; b[1]=s*x+c*y
    elif axis=='X': b[1]=c*y-s*z; b[2]=s*y+c*z
    elif axis=='Y': b[0]=c*x+s*z; b[2]=-s*x+c*z
    else: raise ValueError('unknown axis')

def _noise_trial(strategy,sigma,slow_fraction,pulse_error,t1,tphi,rng):
    seq={'free':(), 'echo':('X',), 'XY4':('X','Y','X','Y'), 'XY8':('X','Y','X','Y','Y','X','Y','X')}.get(strategy)
    if seq is None: raise ValueError('invalid strategy')
    n=len(seq); fractions=[1.0] if n==0 else [0.5/n]+[1/n]*(n-1)+[0.5/n]
    b=[1.0,0.0,0.0]; common=rng.gauss(0,1)
    for k,dt in enumerate(fractions):
        angle=sigma*(math.sqrt(slow_fraction)*common*dt+math.sqrt(max(0,1-slow_fraction))*rng.gauss(0,1)*math.sqrt(dt)); _rotate(b,'Z',angle)
        relax=1-math.exp(-dt/t1); dephase=math.exp(-dt/tphi); b[0]*=dephase*math.sqrt(max(0,1-relax)); b[1]*=dephase*math.sqrt(max(0,1-relax)); b[2]=b[2]*(1-relax)+relax
        if k<n: _rotate(b,seq[k],math.pi+math.pi*pulse_error*rng.gauss(0,1))
    return b[0]

def dd_candidates(sigma=1.5,slow_fraction=.9,pulse_error=.02,t1=100,tphi=100,min_quality=.70,max_pulses=8,trials=48,seed=150):
    _finite('sigma',sigma,0,20); _finite('slow_fraction',slow_fraction,0,1); _finite('pulse_error',pulse_error,0,1); _finite('t1',t1,.001,1e12); _finite('tphi',tphi,.001,1e12); _finite('min_quality',min_quality,0,1)
    if isinstance(max_pulses,bool) or not isinstance(max_pulses,int) or not 0<=max_pulses<=8: raise ValueError('max_pulses out of range')
    if isinstance(trials,bool) or not isinstance(trials,int) or not 2<=trials<=100000: raise ValueError('noise trials out of range')
    out=[]
    for name,pulses in [('free',0),('echo',1),('XY4',4),('XY8',8)]:
        rng=random.Random(seed); vals=[_noise_trial(name,sigma,slow_fraction,pulse_error,t1,tphi,rng) for _ in range(trials)]; mean=sum(vals)/trials; prob=(1+mean)/2; var=sum((x-mean)**2 for x in vals)/(trials-1); se=math.sqrt(var/trials)/2; lower=max(0,prob-1.96*se); feasible=pulses<=max_pulses and lower>=min_quality; score=prob-.004*pulses
        out.append(DDMetric(name,prob,se,pulses,lower,score,feasible))
    return tuple(out)

# --- routing toy model ---------------------------------------------------------------
def _evaluate_path(path,edges):
    success=1.0; visibility=1.0; latency=0.0; energy=0.0; links=[]
    for u,v in zip(path,path[1:]):
        e=next((x for x in edges if {x.a,x.b}=={u,v}),None)
        if e is None: raise ValueError('path edge missing')
        _finite('link fidelity',e.fidelity,.25,1); _finite('link success',e.success,.001,1); _finite('link latency',e.latency,.001,1e6); _finite('link energy',e.energy,0,1e6)
        links.append(e); success*=e.success; visibility*=(4*e.fidelity-1)/3; latency+=e.latency; energy+=e.energy
    swaps=max(0,len(links)-1); latency+=swaps*.2; success*=.9**swaps; decoherence=math.exp(-latency/20); pair=.25+.75*visibility*decoherence
    expected_latency=latency/success; expected_energy=energy/success; score=expected_latency+.3*expected_energy+8*(1-pair)+3*(1-success)
    return RouteMetric(tuple(path),len(links),swaps,pair,success,latency,expected_latency,energy,expected_energy,score)

def route_candidates(edges,start,goal,min_fidelity=0,min_success=0,max_expected_latency=math.inf,max_expected_energy=math.inf,max_hops=6):
    if not edges: raise ValueError('graph missing edges')
    if not start or not goal or start==goal: raise ValueError('invalid terminals')
    _finite('min_fidelity',min_fidelity,0,1); _finite('min_success',min_success,0,1)
    if max_expected_latency<=0 or max_expected_energy<0: raise ValueError('invalid route budget')
    if not 1<=max_hops<=12: raise ValueError('max_hops out of range')
    nodes=set(sum(([e.a,e.b] for e in edges),[]))
    if start not in nodes or goal not in nodes: raise ValueError('missing terminal')
    paths=[]
    def dfs(path):
        cur=path[-1]
        if cur==goal: paths.append(tuple(path)); return
        if len(path)-1>=max_hops: return
        for e in edges:
            nxt=e.b if e.a==cur else e.a if e.b==cur else None
            if nxt is not None and nxt not in path: dfs(path+[nxt])
    dfs([start]); metrics=[_evaluate_path(p,edges) for p in paths]
    feasible=[m for m in metrics if m.pair_fidelity>=min_fidelity-1e-12 and m.success_probability>=min_success-1e-12 and m.expected_latency<=max_expected_latency and m.expected_energy<=max_expected_energy]
    return tuple(sorted(feasible,key=lambda x:(x.score,x.path))),len(metrics)

def _validate_request(q):
    if not isinstance(q,SimulationRequest): raise ValueError('SimulationRequest required')
    if not q.experiment_id.strip(): raise ValueError('experiment_id required')
    if isinstance(q.seed,bool) or not isinstance(q.seed,int) or q.seed<0 or q.seed>2**32-1: raise ValueError('seed invalid')
    _finite('bell_fidelity',q.bell_fidelity,.25,1); _finite('noise_sigma',q.noise_sigma,0,20); _finite('slow_fraction',q.slow_fraction,0,1); _finite('pulse_error',q.pulse_error,0,1); _finite('t1',q.t1,.001,1e12); _finite('tphi',q.tphi,.001,1e12); _finite('min_gate_fidelity',q.min_gate_fidelity,0,1); _finite('min_dd_quality',q.min_dd_quality,0,1); _finite('min_route_fidelity',q.min_route_fidelity,0,1); _finite('min_route_success',q.min_route_success,0,1); _finite('resource_budget',q.resource_budget,0,1e18); _finite('estimated_classical_cost',q.estimated_classical_cost,0,1e18); _finite('estimated_qpu_cost',q.estimated_qpu_cost,0,1e18)
    if isinstance(q.gate_trials,bool) or not isinstance(q.gate_trials,int) or not 1<=q.gate_trials<=100000: raise ValueError('gate_trials invalid')
    if isinstance(q.noise_trials,bool) or not isinstance(q.noise_trials,int) or not 2<=q.noise_trials<=100000: raise ValueError('noise_trials invalid')
    if isinstance(q.max_pulses,bool) or not isinstance(q.max_pulses,int) or not 0<=q.max_pulses<=8: raise ValueError('max_pulses invalid')
    if not isinstance(q.permission_evidence_present,bool) or not isinstance(q.qpu_available,bool): raise ValueError('boolean flags required')
    return q

def evaluate(q):
    try: _validate_request(q)
    except (ValueError,TypeError) as e:
        return SimulationResult(Decision.DENY,NextAction.RETAIN_NO_EXECUTION_CANDIDATE,Escalation.INVALID_INPUT,EngineState.INVALID_REQUEST,getattr(q,'experiment_id','INVALID'),None,None,(),None,None,0,_fp(q) if is_dataclass(q) else _fp(str(q)),_fp(('INVALID',str(e))),False,False,(str(e),))
    reqfp=_fp(q)
    if not q.purpose.strip():
        return SimulationResult(Decision.HOLD,NextAction.ADJUST_CONSTRAINTS_CANDIDATE,Escalation.MISSING_PURPOSE,EngineState.QUALITY_HOLD_CANDIDATE,q.experiment_id,None,None,(),None,None,0,reqfp,_fp((reqfp,'MISSING_PURPOSE')),False,False,('Purpose required before model selection.',))
    if not q.permission_evidence_present:
        return SimulationResult(Decision.DENY,NextAction.REQUEST_PERMISSION_EVIDENCE_CANDIDATE,Escalation.PERMISSION_EVIDENCE_MISSING,EngineState.PERMISSION_EVIDENCE_DENIED,q.experiment_id,None,None,(),None,None,0,reqfp,_fp((reqfp,'PERMISSION_EVIDENCE_MISSING')),False,False,('Permission evidence absent; no simulation backend candidate.',))
    gate=gate_benchmark(q.bell_fidelity,q.gate_trials,q.seed)
    dds=dd_candidates(q.noise_sigma,q.slow_fraction,q.pulse_error,q.t1,q.tphi,q.min_dd_quality,q.max_pulses,q.noise_trials,q.seed+11)
    feasible_dd=sorted((d for d in dds if d.feasible),key=lambda x:(-x.score,x.pulse_count,x.name))
    try: routes,total=route_candidates(q.graph,q.start,q.goal,q.min_route_fidelity,q.min_route_success,q.max_expected_latency,q.max_expected_energy)
    except ValueError as e:
        return SimulationResult(Decision.DENY,NextAction.RETAIN_NO_EXECUTION_CANDIDATE,Escalation.INVALID_INPUT,EngineState.INVALID_REQUEST,q.experiment_id,None,gate,dds,None,None,0,reqfp,_fp((reqfp,'INVALID_ROUTE',str(e))),False,False,(str(e),))
    reasons=[]
    if gate.mean_state_fidelity<q.min_gate_fidelity: reasons.append('Remote-CZ model fidelity below minimum.')
    if not feasible_dd: reasons.append('No dynamical-decoupling strategy satisfies minimum quality/pulse constraints.')
    if not routes: reasons.append('No route satisfies hard fidelity/success/latency/energy constraints.')
    backend=None
    if q.estimated_classical_cost<=q.resource_budget and (not q.qpu_available or q.estimated_classical_cost<=q.estimated_qpu_cost): backend='CLASSICAL_MODEL_CANDIDATE'
    elif q.qpu_available and q.estimated_qpu_cost<=q.resource_budget and q.estimated_qpu_cost<q.estimated_classical_cost: backend='QPU_CANDIDATE'
    else: reasons.append('No backend candidate within resource budget.')
    if reasons:
        esc=Escalation.ROUTE_CONSTRAINT_UNSATISFIED if not routes else Escalation.QUALITY_CONSTRAINT_UNSATISFIED if gate.mean_state_fidelity<q.min_gate_fidelity or not feasible_dd else Escalation.RESOURCE_BUDGET_UNSATISFIED
        result=SimulationResult(Decision.HOLD,NextAction.ADJUST_CONSTRAINTS_CANDIDATE,esc,EngineState.QUALITY_HOLD_CANDIDATE,q.experiment_id,backend,gate,dds,feasible_dd[0].name if feasible_dd else None,routes[0] if routes else None,total,reqfp,'',False,False,tuple(reasons))
    else:
        result=SimulationResult(Decision.ALLOW,NextAction.CONTINUE_MODEL_REVIEW_CANDIDATE,Escalation.NONE,EngineState.SIMULATION_CANDIDATE,q.experiment_id,backend,gate,dds,feasible_dd[0].name,routes[0],total,reqfp,'',True,False,('All modeled constraints satisfied; candidate only.',))
    return replace(result,simulation_fingerprint=_fp(replace(result,simulation_fingerprint='')))

def default_graph():
    return (
        Link('A','B',.97,.88,2.1,1.2),Link('B','D',.965,.86,2.3,1.1),Link('A','C',.84,.96,1.1,.7),
        Link('C','D',.84,.95,1.2,.7),Link('A','D',.78,.72,1.0,1.9),Link('B','C',.96,.75,1.5,1.0),
    )

def make_request(**kw):
    d=dict(experiment_id='QSIM-184-A',seed=184,bell_fidelity=.9,gate_trials=8,noise_trials=12,noise_sigma=1.2,slow_fraction=.9,pulse_error=.02,t1=100.0,tphi=100.0,min_gate_fidelity=.65,min_dd_quality=.68,max_pulses=8,graph=default_graph(),start='A',goal='D',min_route_fidelity=.78,min_route_success=.5,max_expected_latency=20.0,max_expected_energy=10.0,purpose='CPU mathematical model verification',permission_evidence_present=True,resource_budget=10.0,estimated_classical_cost=2.0,estimated_qpu_cost=5.0,qpu_available=False)
    d.update(kw); return SimulationRequest(**d)

def default_request(): return make_request()
def default_evaluation(): return evaluate(default_request())

def prepare_state(q):
    r=evaluate(q); rf=_fp(r); qf=_fp(q); integ=_fp((qf,rf,'NOEPIN-AL-184-PREPARED-V1'))
    return PreparedSimulationState(q,r,qf,rf,integ)

def _stale(q,reason='Prepared state stale or integrity not independently validated.'):
    qf=_fp(q); return SimulationResult(Decision.HOLD,NextAction.FULL_RECOMPUTE_CANDIDATE,Escalation.PREPARED_STATE_STALE,EngineState.PREPARED_STATE_STALE,q.experiment_id,None,None,(),None,None,0,qf,_fp((qf,'STALE',reason)),False,True,(reason,))

def evaluate_prepared(st,*,integrity_validated,current_request_fingerprint,current_result_fingerprint,current_integrity_fingerprint,current_request):
    if not integrity_validated: return _stale(current_request,'Prepared integrity validation missing.')
    expected_integrity=_fp((st.request_fingerprint,st.result_fingerprint,'NOEPIN-AL-184-PREPARED-V1'))
    if current_request_fingerprint!=st.request_fingerprint or current_result_fingerprint!=st.result_fingerprint or current_integrity_fingerprint!=st.integrity_fingerprint or expected_integrity!=st.integrity_fingerprint or _fp(current_request)!=st.request_fingerprint:
        return _stale(current_request)
    return replace(st.result,prepared_state_reused=True)

def make_delta(old,new):
    if not isinstance(old,SimulationRequest) or not isinstance(new,SimulationRequest): raise ValueError('SimulationRequest required')
    changed=tuple(f.name for f in fields(SimulationRequest) if _canon(getattr(old,f.name))!=_canon(getattr(new,f.name)))
    payload=(old.experiment_id,changed,_fp(old),_fp(new)); return ParameterDelta(new.experiment_id,changed,_fp(old),_fp(new),_fp(payload))

def plan_missing_only(old,new):
    d=make_delta(old,new)
    full=old.experiment_id!=new.experiment_id
    ids=('FULL_EXPERIMENT_STATE',) if full else tuple(f'PARAMETER:{x}' for x in d.changed_fields)
    return MissingOnlyPlan(ids,len(_canon(d)),full)
