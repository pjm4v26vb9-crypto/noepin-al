"""Actual completed NOEPIN AL production use evidence for Technology 068."""
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
    for n in range(37,68): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); now=1_800_000_000
    gate67_path=Path(__file__).with_name('al_production_gate_067_baseline.py'); gate65_path=Path(__file__).with_name('al_production_gate_065_baseline.py')
    gate67=load('gate67_baseline',gate67_path); base_out=a.out.with_name('GATE_BASELINE_037_066.json')
    old=sys.argv
    try:
        argv=[str(gate67_path)]
        for n in range(37,67): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--baseline-harness',str(gate65_path),'--out',str(base_out)]; sys.argv=argv; rc=gate67.main()
    finally: sys.argv=old
    if rc!=0: raise SystemExit(2)
    base=json.loads(base_out.read_text(encoding='utf-8'))
    a67=load('al067',a.al067); p67=a67.default_policy(now); d67=a67.evaluate(a67.default_request(now),p67,a67.default_assumptions(),a67.default_edges(),a67.default_evidence(now),a67.default_observations(now),a67.default_actions(),now=now)
    pass67=(d67.decision.value=='ALLOW' and d67.next_gate_candidate and not any((d67.permission_granted,d67.environment_changed,d67.evidence_written,d67.action_executed,d67.approval_executed,d67.assumption_truth_proven,d67.world_truth_proven,d67.safety_proven,d67.action_success)))
    used=dict(base['al_artifacts_used']); used['067']={'al_number':'067','source_sha256':file_sha(a.al067),'decision':d67.decision.value,'next_gate_candidate':d67.next_gate_candidate,'permission_granted':d67.permission_granted,'action_executed':d67.action_executed,'action_success':d67.action_success,'authority_boundary':'Assumption verification is control evidence only; no Truth/Permission Grant/Execution/Action Success.'}
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,67)}; checks['067_pass']=pass67
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':68,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-067','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(1 for v in checks.values() if v),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_066_sha256':file_sha(base_out),'authority_note':'All completed AL evaluators are used as pre-execution/control evidence only. No truth, permission grant, external write, execution, or action-success authority is promoted.'}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
