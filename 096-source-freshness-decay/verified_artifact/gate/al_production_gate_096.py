"""Actual completed NOEPIN AL production use evidence for Technology 096."""
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
    for n in range(37,96): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    gate95_path=Path(__file__).with_name('al_production_gate_095.py'); gate95=load('gate95_baseline',gate95_path)
    base_out=a.out.with_name('GATE_BASELINE_037_094.json'); old=sys.argv
    try:
        argv=[str(gate95_path)]
        for n in range(37,95): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--out',str(base_out)]; sys.argv=argv; rc=gate95.main()
    finally: sys.argv=old
    if rc!=0: raise SystemExit(2)
    base=json.loads(base_out.read_text(encoding='utf-8'))
    m=load('al095',a.al095); z=m.default_evaluation()
    negatives=(z.authority_granted,z.permission_granted,z.approval_executed,z.capability_mutated,z.action_executed,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.world_truth_proven,z.safety_proven,z.action_success)
    pass95=(z.decision.value=='ALLOW' and z.authority_tier_candidate.name=='AUTONOMOUS' and z.action_risk.name=='LOW' and z.next_gate_candidate and not z.reevaluation_candidate and not any(negatives))
    used=dict(base['al_artifacts_used']); used['095']={'al_number':'095','source_sha256':file_sha(a.al095),'decision':z.decision.value,'authority_tier_candidate':z.authority_tier_candidate.name,'action_risk':z.action_risk.name,'next_gate_candidate':z.next_gate_candidate,'permission_granted':z.permission_granted,'action_executed':z.action_executed,'authority_granted':z.authority_granted,'world_truth_proven':z.world_truth_proven,'safety_proven':z.safety_proven,'action_success':z.action_success,'authority_boundary':'Confidence-to-authority output is candidate control evidence only, not actual Authority, Permission Grant, Approval Execution, Action Execution, Safety Proof, or Action Success.'}
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,95)}; checks['095_pass']=pass95
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':96,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-095','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(1 for v in checks.values() if v),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_094_sha256':file_sha(base_out),'authority_note':'All completed AL evaluators are used as control evidence only. No Truth, Authority, Permission Grant, Action Execution, Commit/Publish, External Write, Safety Proof, or Action Success authority is promoted.'}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
