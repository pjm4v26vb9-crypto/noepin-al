"""Actual completed NOEPIN AL production use evidence for Technology 071."""
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
    for n in range(37,71): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); now=1_800_000_000
    gate70_path=Path(__file__).with_name('al_production_gate_070.py'); gate70=load('gate70_baseline',gate70_path); base_out=a.out.with_name('GATE_BASELINE_037_069.json')
    old=sys.argv
    try:
        argv=[str(gate70_path)]
        for n in range(37,70): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--out',str(base_out)]; sys.argv=argv; rc=gate70.main()
    finally: sys.argv=old
    if rc!=0: raise SystemExit(2)
    base=json.loads(base_out.read_text(encoding='utf-8'))
    a70=load('al070',a.al070); r70=a70.default_request(now); d70=a70.evaluate(r70,a70.default_policy(now),a70.default_authorities(),(),now=now)
    pass70=(d70.decision.value=='ALLOW' and d70.next_gate_candidate and not any((d70.permission_granted,d70.role_changed,d70.scope_changed,d70.capability_activated,d70.credential_issued,d70.approval_executed,d70.action_executed,d70.world_truth_proven,d70.safety_proven,d70.action_success)))
    used=dict(base['al_artifacts_used']); used['070']={'al_number':'070','source_sha256':file_sha(a.al070),'decision':d70.decision.value,'next_gate_candidate':d70.next_gate_candidate,'permission_granted':d70.permission_granted,'action_executed':d70.action_executed,'action_success':d70.action_success,'authority_boundary':'Self-authority invariance is control evidence only; no Permission Grant/Authority Mutation/Execution/Action Success.'}
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,70)}; checks['070_pass']=pass70
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':71,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-070','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(1 for v in checks.values() if v),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_069_sha256':file_sha(base_out),'authority_note':'All completed AL evaluators are used as pre-execution/control evidence only. No truth, permission grant, external write, execution, policy commit, or action-success authority is promoted.'}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
