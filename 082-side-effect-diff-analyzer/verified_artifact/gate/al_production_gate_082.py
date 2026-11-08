"""Actual completed NOEPIN AL production use evidence for Technology 082."""
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
    for n in range(37,82): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    gate81_path=Path(__file__).with_name('al_production_gate_081.py'); gate81=load('gate81_baseline',gate81_path)
    base_out=a.out.with_name('GATE_BASELINE_037_080.json'); old=sys.argv
    try:
        argv=[str(gate81_path)]
        for n in range(37,81): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--out',str(base_out)]; sys.argv=argv; rc=gate81.main()
    finally: sys.argv=old
    if rc!=0: raise SystemExit(2)
    base=json.loads(base_out.read_text(encoding='utf-8'))
    m=load('al081',a.al081)
    z=m.evaluate(m.default_request(),m.default_intent(),m.default_permit(),m.default_receipt(),m.default_policy(),m.default_conditions(),m.default_observed_state(),m.default_diff())
    negatives=(z.permission_granted,z.rollback_executed,z.state_committed,z.external_write_performed,z.action_executed,z.receipt_promoted_to_truth,z.world_truth_proven,z.safety_proven,z.action_success)
    pass81=(z.decision.value=='ALLOW' and z.success_state.value=='SUCCESS' and z.next_gate_candidate and z.atomic_publish_candidate and not any(negatives))
    used=dict(base['al_artifacts_used']); used['081']={'al_number':'081','source_sha256':file_sha(a.al081),'decision':z.decision.value,'success_state':z.success_state.value,'next_gate_candidate':z.next_gate_candidate,'rollback_candidate':z.rollback_candidate,'atomic_publish_candidate':z.atomic_publish_candidate,'permission_granted':z.permission_granted,'rollback_executed':z.rollback_executed,'state_committed':z.state_committed,'external_write_performed':z.external_write_performed,'action_executed':z.action_executed,'receipt_promoted_to_truth':z.receipt_promoted_to_truth,'world_truth_proven':z.world_truth_proven,'safety_proven':z.safety_proven,'action_success':z.action_success,'authority_boundary':'Postcondition success is control evidence only; no Permission Grant, rollback execution, commit, external write, action execution, receipt-to-truth promotion, World Truth, Safety Proof, or Action Success.'}
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,81)}; checks['081_pass']=pass81
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':82,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-081','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(1 for v in checks.values() if v),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_080_sha256':file_sha(base_out),'authority_note':'All completed AL evaluators are used as control evidence only. No truth, permission grant, approval execution, external write, rollback execution, transaction commit, publish, tool execution, or action-success authority is promoted.'}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
