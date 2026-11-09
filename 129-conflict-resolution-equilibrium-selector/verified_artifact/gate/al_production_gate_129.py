"""Actual completed NOEPIN AL production use evidence for Technology 129."""
from __future__ import annotations
import argparse,importlib.util,json,sys
from hashlib import sha256
from pathlib import Path

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod

def file_sha(p): return sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    for n in range(37,129): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    gate128_path=Path(__file__).with_name('al_production_gate_128.py'); gate128=load('gate128_baseline',gate128_path)
    base_out=a.out.with_name('GATE_BASELINE_037_127.json'); old=sys.argv
    try:
        argv=[str(gate128_path)]
        for n in range(37,128): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--out',str(base_out)]; sys.argv=argv; rc=gate128.main()
    finally: sys.argv=old
    if rc!=0: raise SystemExit(2)
    base=json.loads(base_out.read_text(encoding='utf-8'))
    m=load('al128',a.al128); r=m.default_evaluation()
    neg=(r.contribution_promoted_to_liability,r.critical_contributor_promoted_to_sole_responsibility,r.trust_update_executed,r.penalty_executed,r.authority_restriction_executed,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success)
    pass128=(r.decision.value=='ALLOW' and r.next_action.value=='RESPONSIBILITY_CONTRIBUTION_CANDIDATE' and r.attribution_state.value in {'ATTRIBUTABLE','PARTIAL'} and r.next_gate_candidate and not any(neg))
    used=dict(base['al_artifacts_used']); used['128']={'al_number':'128','source_sha256':file_sha(a.al128),'decision':r.decision.value,'next_action':r.next_action.value,'escalation':r.escalation.value,'attribution_state':r.attribution_state.value,'critical_contributors':list(r.critical_contributors),'causal_coverage':r.causal_coverage,'next_gate_candidate':r.next_gate_candidate,'permission_granted':r.permission_granted,'approval_executed':r.approval_executed,'action_executed':r.action_executed,'world_truth_proven':r.world_truth_proven,'safety_proven':r.safety_proven,'action_success':r.action_success,'authority_boundary':'Contribution attribution is audit evidence only; no Liability, Penalty, Trust/Authority change, Permission, Execution, Truth, Safety Proof, or Action Success.'}
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,128)}; checks['128_pass']=pass128
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':129,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-128','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(1 for v in checks.values() if v),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_127_sha256':file_sha(base_out),'authority_note':'All completed AL evaluators are control/audit evidence only. Equilibrium/Delegation/Attribution/Manipulation/Convergence/Assignment/Consensus/Quorum candidates do not become Truth, Authority, Permission, Safety Proof, Execution, Liability, or Action Success.'}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
