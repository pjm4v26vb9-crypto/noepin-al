"""Actual completed NOEPIN AL production use evidence for Technology 073."""
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
    for n in range(37,73): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); now=1_800_000_000

    gate72_path=Path(__file__).with_name('al_production_gate_072.py')
    gate72=load('gate72_baseline',gate72_path)
    base_out=a.out.with_name('GATE_BASELINE_037_071.json')
    old=sys.argv
    try:
        argv=[str(gate72_path)]
        for n in range(37,72): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--out',str(base_out)]
        sys.argv=argv
        rc=gate72.main()
    finally:
        sys.argv=old
    if rc!=0: raise SystemExit(2)

    base=json.loads(base_out.read_text(encoding='utf-8'))
    a72=load('al072',a.al072)
    p=a72.default_policy(now)
    r=a72.default_request(now)
    au=a72.default_authorities()
    k=a72.default_keys(now)
    apr=(a72.reference_approval(r,issued_at=now),)
    d=a72.evaluate(r,'APR-72',p,apr,au,k,(),current_policy_fingerprint=r.policy_fingerprint,now=now)
    negatives=(
        d.approval_executed,d.nonce_consumed,d.replay_ledger_written,d.permission_granted,
        d.tool_executed,d.external_send_performed,d.atomic_publish_performed,
        d.world_truth_proven,d.safety_proven,d.action_success
    )
    pass72=(d.decision.value=='ALLOW' and d.next_gate_candidate and d.atomic_publish_candidate and not any(negatives))

    used=dict(base['al_artifacts_used'])
    used['072']={
        'al_number':'072','source_sha256':file_sha(a.al072),
        'decision':d.decision.value,'next_gate_candidate':d.next_gate_candidate,
        'permission_granted':d.permission_granted,'action_executed':d.tool_executed,
        'action_success':d.action_success,
        'authority_boundary':'Approval binding verification is control evidence only; no Permission Grant/Approval Execution/Nonce Consumption/Tool Execution/Atomic Publish/Action Success.'
    }
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,72)}
    checks['072_pass']=pass72
    out={
        'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1',
        'technology_under_build':73,
        'creator':'NOEPIN / のえぴん',
        'ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT',
        'actual_al_range':'037-072',
        'al_artifacts_used':used,
        'gate_checks':checks,
        'pass_count':sum(1 for v in checks.values() if v),
        'total':len(checks),
        'production_gate_pass':all(checks.values()),
        'execution_performed':False,
        'permission_elevation':False,
        'write_performed':False,
        'action_success_promoted':False,
        'baseline_gate_037_071_sha256':file_sha(base_out),
        'authority_note':'All completed AL evaluators are used as pre-execution/control evidence only. No truth, permission grant, approval execution, external write, transaction commit, tool execution, atomic publish, or action-success authority is promoted.'
    }
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False,sort_keys=True))
    return 0 if out['production_gate_pass'] else 2

if __name__=='__main__': raise SystemExit(main())
