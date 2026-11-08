"""Actual completed NOEPIN AL production use evidence for Technology 070."""
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
    for n in range(37,70): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); now=1_800_000_000
    gate69_path=Path(__file__).with_name('al_production_gate_069.py')
    gate69=load('gate69_baseline',gate69_path); base_out=a.out.with_name('GATE_BASELINE_037_068.json')
    old=sys.argv
    try:
        argv=[str(gate69_path)]
        for n in range(37,69): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--out',str(base_out)]; sys.argv=argv; rc=gate69.main()
    finally: sys.argv=old
    if rc!=0: raise SystemExit(2)
    base=json.loads(base_out.read_text(encoding='utf-8'))
    a69=load('al069',a.al069)
    p69=a69.default_policy(now); d69=a69.evaluate(a69.default_request(now),p69,a69.default_actions(),a69.default_observations(),a69.default_forbidden_orders(),now=now)
    pass69=(d69.decision.value=='ALLOW' and d69.next_gate_candidate and not any((d69.permission_granted,d69.plan_rewritten,d69.state_written,d69.action_executed,d69.deployment_executed,d69.approval_executed,d69.world_truth_proven,d69.safety_proven,d69.action_success)))
    used=dict(base['al_artifacts_used']); used['069']={'al_number':'069','source_sha256':file_sha(a.al069),'decision':d69.decision.value,'next_gate_candidate':d69.next_gate_candidate,'permission_granted':d69.permission_granted,'action_executed':d69.action_executed,'action_success':d69.action_success,'authority_boundary':'Dependency order is control evidence only; no Permission Grant/Plan Commit/Execution/Action Success.'}
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,69)}; checks['069_pass']=pass69
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':70,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-069','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(1 for v in checks.values() if v),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_068_sha256':file_sha(base_out),'authority_note':'All completed AL evaluators are used as pre-execution/control evidence only. No truth, permission grant, external write, execution, or action-success authority is promoted.'}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
