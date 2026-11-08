"""Actual completed NOEPIN AL production use evidence for Technology 085."""
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
    for n in range(37,85): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    gate84_path=Path(__file__).with_name('al_production_gate_084.py'); gate84=load('gate84_baseline',gate84_path)
    base_out=a.out.with_name('GATE_BASELINE_037_083.json'); old=sys.argv
    try:
        argv=[str(gate84_path)]
        for n in range(37,84): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--out',str(base_out)]; sys.argv=argv; rc=gate84.main()
    finally: sys.argv=old
    if rc!=0: raise SystemExit(2)
    base=json.loads(base_out.read_text(encoding='utf-8'))
    m=load('al084',a.al084); z=m.default_evaluation()
    negatives=(z.permission_granted,z.approval_executed,z.action_executed,z.plan_committed,z.external_write_performed,z.world_truth_proven,z.safety_proven,z.action_success,z.sender_authority_inherited,z.sender_intent_inherited,z.consent_inherited)
    pass84=(z.decision.value=='ALLOW' and z.next_gate_candidate and z.quorum_satisfied and z.roles_satisfied and z.approval_state.value=='SATISFIED' and z.required_quorum==2 and not any(negatives))
    used=dict(base['al_artifacts_used']); used['084']={'al_number':'084','source_sha256':file_sha(a.al084),'decision':z.decision.value,'required_quorum':z.required_quorum,'quorum_satisfied':z.quorum_satisfied,'roles_satisfied':z.roles_satisfied,'approval_state':z.approval_state.value,'next_gate_candidate':z.next_gate_candidate,'permission_granted':z.permission_granted,'approval_executed':z.approval_executed,'action_executed':z.action_executed,'plan_committed':z.plan_committed,'external_write_performed':z.external_write_performed,'world_truth_proven':z.world_truth_proven,'safety_proven':z.safety_proven,'action_success':z.action_success,'sender_authority_inherited':z.sender_authority_inherited,'sender_intent_inherited':z.sender_intent_inherited,'consent_inherited':z.consent_inherited,'authority_boundary':'Approval quorum output is approval-control evidence only; quorum satisfaction is not permission grant, approval execution, action execution, world truth, safety proof, or action success.'}
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,84)}; checks['084_pass']=pass84
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':85,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-084','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(1 for v in checks.values() if v),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_083_sha256':file_sha(base_out),'authority_note':'All completed AL evaluators are used as control evidence only. No Truth, Permission Grant, Approval Execution, Action Execution, External Write, Rollback Execution, Transaction Commit, Publish, or Action Success authority is promoted.'}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
