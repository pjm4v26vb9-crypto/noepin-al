"""Actual completed NOEPIN AL production use evidence for Technology 094."""
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
    for n in range(37,94): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    gate93_path=Path(__file__).with_name('al_production_gate_093.py'); gate93=load('gate93_baseline',gate93_path)
    base_out=a.out.with_name('GATE_BASELINE_037_092.json'); old=sys.argv
    try:
        argv=[str(gate93_path)]
        for n in range(37,93): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--out',str(base_out)]; sys.argv=argv; rc=gate93.main()
    finally: sys.argv=old
    if rc!=0: raise SystemExit(2)
    base=json.loads(base_out.read_text(encoding='utf-8'))
    m=load('al093',a.al093); z=m.default_evaluation()
    negatives=(z.permission_granted,z.action_executed,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.world_truth_proven,z.authority_promoted,z.safety_proven,z.action_success)
    pass93=(z.decision.value=='ALLOW' and z.next_gate_candidate and not z.reevaluation_candidate and z.effective_evidence_count>=4.0 and not any(negatives))
    used=dict(base['al_artifacts_used']); used['093']={'al_number':'093','source_sha256':file_sha(a.al093),'decision':z.decision.value,'effective_evidence_count':z.effective_evidence_count,'mean_independence':z.mean_independence,'next_gate_candidate':z.next_gate_candidate,'permission_granted':z.permission_granted,'action_executed':z.action_executed,'world_truth_proven':z.world_truth_proven,'authority_promoted':z.authority_promoted,'safety_proven':z.safety_proven,'action_success':z.action_success,'authority_boundary':'Independence estimates and effective evidence counts are uncertainty evidence only, not Truth, Authority, Permission, Safety Proof, Action Execution, or Action Success.'}
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,93)}; checks['093_pass']=pass93
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':94,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-093','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(1 for v in checks.values() if v),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_092_sha256':file_sha(base_out),'authority_note':'All completed AL evaluators are used as control evidence only. No Truth, Authority, Permission Grant, Action Execution, Commit/Publish, External Write, Safety Proof, or Action Success authority is promoted.'}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
