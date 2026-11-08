"""Actual completed NOEPIN AL production use evidence for Technology 074."""
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
    for n in range(37,74): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); now=1_800_000_000
    gate73_path=Path(__file__).with_name('al_production_gate_073.py'); gate73=load('gate73_baseline',gate73_path)
    base_out=a.out.with_name('GATE_BASELINE_037_072.json'); old=sys.argv
    try:
        argv=[str(gate73_path)]
        for n in range(37,73): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--out',str(base_out)]; sys.argv=argv; rc=gate73.main()
    finally: sys.argv=old
    if rc!=0: raise SystemExit(2)
    base=json.loads(base_out.read_text(encoding='utf-8'))
    m=load('al073',a.al073); pol=m.default_policy(); d=m.default_decision_snapshot(now); pre=m.matching_preexecution_snapshot(d,now); keys=m.default_dependency_keys(); z=m.evaluate(d,pre,keys,pol,now=now)
    negatives=(z.permission_granted,z.permit_refreshed,z.snapshot_written,z.state_mutated,z.tool_executed,z.transaction_committed,z.external_write_performed,z.world_truth_proven,z.safety_proven,z.action_success)
    pass73=(z.decision.value=='ALLOW' and z.next_gate_candidate and not any(negatives))
    used=dict(base['al_artifacts_used']); used['073']={'al_number':'073','source_sha256':file_sha(a.al073),'decision':z.decision.value,'next_gate_candidate':z.next_gate_candidate,'permission_granted':z.permission_granted,'action_executed':z.tool_executed,'action_success':z.action_success,'authority_boundary':'Pre-execution snapshot match is control evidence only; no Permission Grant/Permit Refresh/State Mutation/Tool Execution/Transaction Commit/Action Success.'}
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,73)}; checks['073_pass']=pass73
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':74,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-073','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(1 for v in checks.values() if v),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_072_sha256':file_sha(base_out),'authority_note':'All completed AL evaluators are used as control evidence only. No truth, permission grant, approval execution, risk-budget spending, external write, transaction commit, tool execution, or action-success authority is promoted.'}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
