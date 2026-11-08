"""Actual completed NOEPIN AL production use evidence for Technology 086."""
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
    for n in range(37,86): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    gate85_path=Path(__file__).with_name('al_production_gate_085.py'); gate85=load('gate85_baseline',gate85_path)
    base_out=a.out.with_name('GATE_BASELINE_037_084.json'); old=sys.argv
    try:
        argv=[str(gate85_path)]
        for n in range(37,85): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--out',str(base_out)]; sys.argv=argv; rc=gate85.main()
    finally: sys.argv=old
    if rc!=0: raise SystemExit(2)
    base=json.loads(base_out.read_text(encoding='utf-8'))
    m=load('al085',a.al085); z=m.default_evaluation()
    negatives=(z.request_promoted_to_success,z.intent_promoted_to_action,z.permission_granted,z.action_executed,z.commit_executed,z.rollback_executed,z.external_write_performed,z.receipt_promoted_to_truth,z.world_truth_proven,z.safety_proven,z.action_success)
    pass85=(z.decision.value=='ALLOW' and z.transaction_state.value=='COMMIT_CANDIDATE' and z.commit_candidate and not z.rollback_candidate and z.commit_result=='CANDIDATE_ONLY' and z.next_gate_candidate and not any(negatives))
    used=dict(base['al_artifacts_used']); used['085']={'al_number':'085','source_sha256':file_sha(a.al085),'decision':z.decision.value,'transaction_state':z.transaction_state.value,'commit_candidate':z.commit_candidate,'rollback_candidate':z.rollback_candidate,'commit_result':z.commit_result,'next_gate_candidate':z.next_gate_candidate,'request_promoted_to_success':z.request_promoted_to_success,'intent_promoted_to_action':z.intent_promoted_to_action,'permission_granted':z.permission_granted,'action_executed':z.action_executed,'commit_executed':z.commit_executed,'rollback_executed':z.rollback_executed,'external_write_performed':z.external_write_performed,'receipt_promoted_to_truth':z.receipt_promoted_to_truth,'world_truth_proven':z.world_truth_proven,'safety_proven':z.safety_proven,'action_success':z.action_success,'authority_boundary':'Transaction output is candidate/evidence only; Commit Candidate is not Commit Execution, Rollback Candidate is not Rollback Execution, Receipt is not Action Success, and no permission/action/write/publish authority is promoted.'}
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,85)}; checks['085_pass']=pass85
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':86,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-085','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(1 for v in checks.values() if v),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_084_sha256':file_sha(base_out),'authority_note':'All completed AL evaluators are used as control evidence only. No Truth, Permission Grant, Approval Execution, Action Execution, External Write, Compensation Execution, Rollback Execution, Transaction Commit, Atomic Publish, or Action Success authority is promoted.'}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
