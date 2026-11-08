"""Actual completed NOEPIN AL production use evidence for Technology 069."""
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
    for n in range(37,69): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); now=1_800_000_000
    gate68_path=Path(__file__).with_name('al_production_gate_068_baseline.py'); gate67_path=Path(__file__).with_name('al_production_gate_067_baseline.py'); gate65_path=Path(__file__).with_name('al_production_gate_065_baseline.py')
    gate68=load('gate68_baseline',gate68_path); base_out=a.out.with_name('GATE_BASELINE_037_067.json')
    old=sys.argv
    try:
        argv=[str(gate68_path)]
        for n in range(37,68): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--out',str(base_out)]; sys.argv=argv; rc=gate68.main()
    finally: sys.argv=old
    if rc!=0: raise SystemExit(2)
    base=json.loads(base_out.read_text(encoding='utf-8'))
    a68=load('al068',a.al068); p68=a68.default_policy(now); d68=a68.evaluate(a68.default_request(now),p68,a68.default_claims(),a68.default_sources(),a68.default_evidence(now),now=now)
    pass68=(d68.decision.value=='ALLOW' and d68.next_gate_candidate and not any((d68.permission_granted,d68.truth_proven,d68.evidence_written,d68.approval_executed,d68.data_sent,d68.action_executed,d68.safety_proven,d68.action_success)))
    used=dict(base['al_artifacts_used']); used['068']={'al_number':'068','source_sha256':file_sha(a.al068),'decision':d68.decision.value,'next_gate_candidate':d68.next_gate_candidate,'permission_granted':d68.permission_granted,'action_executed':d68.action_executed,'action_success':d68.action_success,'authority_boundary':'Evidence sufficiency is control evidence only; no Truth/Permission Grant/Execution/Action Success.'}
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,68)}; checks['068_pass']=pass68
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':69,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-068','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(1 for v in checks.values() if v),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_067_sha256':file_sha(base_out),'authority_note':'All completed AL evaluators are used as pre-execution/control evidence only. No truth, permission grant, external write, execution, or action-success authority is promoted.'}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
