"""Actual completed NOEPIN AL production use evidence for Technology 107."""
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
    for n in range(37,107): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    gate106_path=Path(__file__).with_name('al_production_gate_106.py'); gate106=load('gate106_baseline',gate106_path)
    base_out=a.out.with_name('GATE_BASELINE_037_105.json'); old=sys.argv
    try:
        argv=[str(gate106_path)]
        for n in range(37,106): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--out',str(base_out)]; sys.argv=argv; rc=gate106.main()
    finally: sys.argv=old
    if rc!=0: raise SystemExit(2)
    base=json.loads(base_out.read_text(encoding='utf-8'))
    m=load('al106',a.al106); z=m.default_evaluation()
    neg=(z.repair_promoted_to_permission,z.permission_granted,z.action_executed,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.world_truth_proven,z.global_constraint_proven,z.domain_authority_promoted,z.safety_proven,z.action_success)
    pass106=(z.decision.value=='ALLOW' and z.next_action.value=='LOCAL_REPAIR_CANDIDATE' and z.chosen_candidate=='BUILD-SAFE' and z.affected_range==('BUILD','TEST','PUBLISH') and z.next_gate_candidate and not z.full_replan_required and not any(neg))
    used=dict(base['al_artifacts_used']); used['106']={'al_number':'106','source_sha256':file_sha(a.al106),'decision':z.decision.value,'next_action':z.next_action.value,'chosen_candidate':z.chosen_candidate,'affected_range':list(z.affected_range),'residual_risk':z.residual_risk,'next_gate_candidate':z.next_gate_candidate,'permission_granted':z.permission_granted,'action_executed':z.action_executed,'world_truth_proven':z.world_truth_proven,'safety_proven':z.safety_proven,'action_success':z.action_success,'authority_boundary':'Repaired Subplan remains candidate evidence only; Local Compatibility is not Global Constraint Proof.'}
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,106)}; checks['106_pass']=pass106
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':107,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-106','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(1 for v in checks.values() if v),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_105_sha256':file_sha(base_out),'authority_note':'All completed AL evaluators are used as control evidence only. No Truth, Authority, Permission Grant, Action Execution, Commit/Publish, External Write, Safety Proof, or Action Success authority is promoted.'}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
