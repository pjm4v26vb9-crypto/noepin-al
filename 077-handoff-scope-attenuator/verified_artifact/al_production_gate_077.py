"""Actual completed NOEPIN AL production use evidence for Technology 077."""
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
    for n in range(37,77): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    gate76_path=Path(__file__).with_name('al_production_gate_076.py'); gate76=load('gate76_baseline',gate76_path)
    base_out=a.out.with_name('GATE_BASELINE_037_075.json'); old=sys.argv
    try:
        argv=[str(gate76_path)]
        for n in range(37,76): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--out',str(base_out)]; sys.argv=argv; rc=gate76.main()
    finally: sys.argv=old
    if rc!=0: raise SystemExit(2)
    base=json.loads(base_out.read_text(encoding='utf-8'))
    m=load('al076',a.al076); z=m.evaluate(m.default_request(),m.default_policy(),m.default_goals(),m.default_steps(),m.default_plans(),m.default_checkpoints())
    negatives=(z.permission_granted,z.goal_baseline_mutated,z.human_approval_executed,z.tool_executed,z.transaction_committed,z.external_write_performed,z.world_truth_proven,z.safety_proven,z.action_success)
    pass76=(z.decision.value=='ALLOW' and z.next_gate_candidate and not any(negatives))
    used=dict(base['al_artifacts_used']); used['076']={'al_number':'076','source_sha256':file_sha(a.al076),'decision':z.decision.value,'next_gate_candidate':z.next_gate_candidate,'permission_granted':z.permission_granted,'action_executed':z.tool_executed,'action_success':z.action_success,'authority_boundary':'Long-horizon drift evaluation is typed control evidence only; no Goal Mutation, Permission Grant, Approval Execution, Tool Execution, Transaction Commit, Safety Proof, or Action Success.'}
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,76)}; checks['076_pass']=pass76
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':77,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-076','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(1 for v in checks.values() if v),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_075_sha256':file_sha(base_out),'authority_note':'All completed AL evaluators are used as control evidence only. No world truth, permission grant, approval execution, delegation execution, external write, transaction commit, tool execution, or action-success authority is promoted.'}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
