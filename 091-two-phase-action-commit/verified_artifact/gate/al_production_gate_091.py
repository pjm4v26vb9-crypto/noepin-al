"""Actual completed NOEPIN AL production use evidence for Technology 091."""
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
    for n in range(37,91): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    gate90_path=Path(__file__).with_name('al_production_gate_090.py'); gate90=load('gate90_baseline',gate90_path)
    base_out=a.out.with_name('GATE_BASELINE_037_089.json'); old=sys.argv
    try:
        argv=[str(gate90_path)]
        for n in range(37,90): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--out',str(base_out)]; sys.argv=argv; rc=gate90.main()
    finally: sys.argv=old
    if rc!=0: raise SystemExit(2)
    base=json.loads(base_out.read_text(encoding='utf-8'))
    m=load('al090',a.al090); z=m.default_evaluation()
    negatives=(z.permission_granted,z.action_executed,z.branch_execution_started,z.isolation_executed,z.compensation_executed,z.resource_lock_mutated,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.world_truth_proven,z.safety_proven,z.action_success)
    pass90=(z.decision.value=='ALLOW' and z.containment_state.value=='SAFE_CONTINUE' and z.next_gate_candidate and z.continue_candidate and not z.full_stop_candidate and not any(negatives))
    used=dict(base['al_artifacts_used']); used['090']={'al_number':'090','source_sha256':file_sha(a.al090),'decision':z.decision.value,'containment_state':z.containment_state.value,'next_gate_candidate':z.next_gate_candidate,'continue_candidate':z.continue_candidate,'full_stop_candidate':z.full_stop_candidate,'recovery_candidate':z.recovery_candidate,'permission_granted':z.permission_granted,'action_executed':z.action_executed,'branch_execution_started':z.branch_execution_started,'isolation_executed':z.isolation_executed,'compensation_executed':z.compensation_executed,'resource_lock_mutated':z.resource_lock_mutated,'plan_committed':z.plan_committed,'atomic_publish_executed':z.atomic_publish_executed,'external_write_performed':z.external_write_performed,'world_truth_proven':z.world_truth_proven,'safety_proven':z.safety_proven,'action_success':z.action_success,'authority_boundary':'Containment / Continue / Full Stop / Recovery candidates are not Permission Grant, Isolation, Branch Execution, Compensation, Commit, Publish, Truth, Safety Proof, or Action Success.'}
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,90)}; checks['090_pass']=pass90
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':91,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-090','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(1 for v in checks.values() if v),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_089_sha256':file_sha(base_out),'authority_note':'All completed AL evaluators are used as control evidence only. No Truth, Permission Grant, Approval Execution, Prepare Request, Resource Lock Mutation, Store Mutation, Permit Consumption, Action Execution, Branch Execution, Isolation Execution, Compensation Execution, Abort Execution, Transaction Commit, Atomic Publish, External Write, or Action Success authority is promoted.'}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
