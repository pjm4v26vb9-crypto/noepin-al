"""Actual completed NOEPIN AL production use evidence for Technology 067."""
from __future__ import annotations
import argparse, importlib.util, json, sys
from hashlib import sha256
from pathlib import Path

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod

def file_sha(p): return sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    for n in range(37,67): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--baseline-harness',type=Path,required=True); ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args(); now=1_800_000_000
    # AL037–064 are actually executed by the frozen Technology-065 gate harness against their extracted final core sources.
    gate65=load('gate65_baseline',a.baseline_harness); base_out=a.out.with_name('GATE_BASELINE_037_064.json')
    old=sys.argv
    try:
        argv=[str(a.baseline_harness)]
        for n in range(37,65): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--out',str(base_out)]; sys.argv=argv; rc=gate65.main()
    finally: sys.argv=old
    if rc!=0: raise SystemExit(2)
    base=json.loads(base_out.read_text(encoding='utf-8'))
    # Technology 065 actual evaluator.
    a65=load('al065',a.al065); p65=a65.default_policy(now)
    d65=a65.evaluate(a65.default_request(now),p65,a65.default_changes(),a65.default_goals(),a65.default_approval(now),now=now)
    pass65=(d65.decision.value=='ALLOW' and d65.next_gate_candidate and d65.minimality_confirmed_under_supplied_model and not any((d65.permission_granted,d65.write_performed,d65.patch_committed,d65.deployment_executed,d65.approval_executed,d65.world_truth_proven,d65.safety_proven,d65.action_success)))
    # Technology 066 actual evaluator.
    a66=load('al066',a.al066)
    I=a66.Intent('user','read','report','section-a','summarize'); r66=a66.IntentRequest(I,I,I,I); d66=a66.evaluate(r66,a66.IntentPolicy())
    pass66=(d66.decision.value=='ALLOW' and not any((d66.permission_granted,d66.tool_executed,d66.approval_executed,d66.world_truth_proven,d66.safety_proven,d66.action_success)))
    used=dict(base['al_artifacts_used'])
    used['065']={'al_number':'065','source_sha256':file_sha(a.al065),'decision':d65.decision.value,'next_gate_candidate':d65.next_gate_candidate,'permission_granted':d65.permission_granted,'write_performed':d65.write_performed,'action_success':d65.action_success,'authority_boundary':'Minimal Change Candidate is control evidence only; no Permission Grant/Write/Execution/Action Success.'}
    used['066']={'al_number':'066','source_sha256':file_sha(a.al066),'decision':d66.decision.value,'consistency_score':d66.consistency_score,'permission_granted':d66.permission_granted,'tool_executed':d66.tool_executed,'action_success':d66.action_success,'authority_boundary':'Intent consistency is control evidence only; no Permission Grant/Tool Execution/Truth/Action Success.'}
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,65)}; checks['065_pass']=pass65; checks['066_pass']=pass66
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':67,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-066','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(1 for v in checks.values() if v),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_064_sha256':file_sha(base_out),'authority_note':'All completed AL evaluators are used as pre-execution/control evidence only. No truth, permission grant, external write, execution, or action-success authority is promoted.'}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
