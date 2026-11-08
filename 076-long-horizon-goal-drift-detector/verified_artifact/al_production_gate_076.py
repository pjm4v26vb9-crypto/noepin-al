"""Actual completed NOEPIN AL production use evidence for Technology 076."""
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
    for n in range(37,76): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    gate75_path=Path(__file__).with_name('al_production_gate_075.py'); gate75=load('gate75_baseline',gate75_path)
    base_out=a.out.with_name('GATE_BASELINE_037_074.json'); old=sys.argv
    try:
        argv=[str(gate75_path)]
        for n in range(37,75): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--out',str(base_out)]; sys.argv=argv; rc=gate75.main()
    finally: sys.argv=old
    if rc!=0: raise SystemExit(2)
    base=json.loads(base_out.read_text(encoding='utf-8'))
    m=load('al075',a.al075); p=m.default_policy(); goals=m.default_goals(); effects=m.default_effects(); actions=m.default_actions(); approvals=m.default_approvals(); q=m.default_request(); z=m.evaluate(q,p,goals,effects,actions,approvals)
    negatives=(z.permission_granted,z.goal_changed,z.human_approval_executed,z.tool_executed,z.transaction_committed,z.external_write_performed,z.world_truth_proven,z.safety_proven,z.action_success)
    pass75=(z.decision.value=='ALLOW' and z.next_gate_candidate and not any(negatives))
    used=dict(base['al_artifacts_used']); used['075']={'al_number':'075','source_sha256':file_sha(a.al075),'decision':z.decision.value,'next_gate_candidate':z.next_gate_candidate,'permission_granted':z.permission_granted,'action_executed':z.tool_executed,'action_success':z.action_success,'authority_boundary':'Latent goal alignment is typed control evidence only; no mental-state truth, Permission Grant, Goal Mutation, Approval Execution, Tool Execution, Transaction Commit, Safety Proof, or Action Success.'}
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,75)}; checks['075_pass']=pass75
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':76,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-075','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(1 for v in checks.values() if v),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_074_sha256':file_sha(base_out),'authority_note':'All completed AL evaluators are used as control evidence only. No world truth, mental-state truth, permission grant, approval execution, goal mutation, external write, transaction commit, tool execution, or action-success authority is promoted.'}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
