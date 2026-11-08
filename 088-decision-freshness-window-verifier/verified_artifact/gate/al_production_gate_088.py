"""Actual completed NOEPIN AL production use evidence for Technology 088."""
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
    for n in range(37,88): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    gate87_path=Path(__file__).with_name('al_production_gate_087.py'); gate87=load('gate87_baseline',gate87_path)
    base_out=a.out.with_name('GATE_BASELINE_037_086.json'); old=sys.argv
    try:
        argv=[str(gate87_path)]
        for n in range(37,87): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--out',str(base_out)]; sys.argv=argv; rc=gate87.main()
    finally: sys.argv=old
    if rc!=0: raise SystemExit(2)
    base=json.loads(base_out.read_text(encoding='utf-8'))
    m=load('al087',a.al087); z=m.default_evaluation()
    negatives=(z.request_promoted_to_success,z.permit_promoted_to_permission,z.nonce_store_mutated,z.usage_consumed,z.permission_granted,z.action_executed,z.plan_committed,z.atomic_publish_executed,z.external_write_performed,z.receipt_promoted_to_truth,z.world_truth_proven,z.safety_proven,z.action_success)
    pass87=(z.decision.value=='ALLOW' and z.lease_state.value=='ACTIVE' and z.consume_state.value=='CONSUME_CANDIDATE' and z.consume_candidate and z.next_gate_candidate and z.next_usage_count==1 and not z.reissue_required and not z.replay_detected and not any(negatives))
    used=dict(base['al_artifacts_used']); used['087']={'al_number':'087','source_sha256':file_sha(a.al087),'decision':z.decision.value,'lease_state':z.lease_state.value,'consume_state':z.consume_state.value,'consume_candidate':z.consume_candidate,'next_gate_candidate':z.next_gate_candidate,'next_usage_count':z.next_usage_count,'reissue_required':z.reissue_required,'replay_detected':z.replay_detected,'nonce_store_mutated':z.nonce_store_mutated,'usage_consumed':z.usage_consumed,'permission_granted':z.permission_granted,'action_executed':z.action_executed,'plan_committed':z.plan_committed,'atomic_publish_executed':z.atomic_publish_executed,'external_write_performed':z.external_write_performed,'world_truth_proven':z.world_truth_proven,'safety_proven':z.safety_proven,'action_success':z.action_success,'authority_boundary':'Lease Valid/Consume Candidate are evidence only; no Permit Consumption, Nonce Store Mutation, Permission Grant, Action Execution, Commit, Publish, World Truth, Safety Proof, or Action Success is promoted.'}
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,87)}; checks['087_pass']=pass87
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':88,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-087','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(1 for v in checks.values() if v),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_086_sha256':file_sha(base_out),'authority_note':'All completed AL evaluators are used as control evidence only. No Truth, Permission Grant, Permit Consumption, Cache-to-Truth Promotion, Approval Execution, Action Execution, External Write, Compensation Execution, Rollback Execution, Transaction Commit, Atomic Publish, or Action Success authority is promoted.'}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
