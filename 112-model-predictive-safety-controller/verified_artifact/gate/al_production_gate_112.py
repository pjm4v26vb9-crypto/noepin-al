"""Actual completed NOEPIN AL production use evidence for Technology 112."""
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
    for n in range(37,112): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    gate111_path=Path(__file__).with_name('al_production_gate_111.py'); gate111=load('gate111_baseline',gate111_path)
    base_out=a.out.with_name('GATE_BASELINE_037_110.json'); old=sys.argv
    try:
        argv=[str(gate111_path)]
        for n in range(37,111): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--out',str(base_out)]; sys.argv=argv; rc=gate111.main()
    finally: sys.argv=old
    if rc!=0: raise SystemExit(2)
    base=json.loads(base_out.read_text(encoding='utf-8'))
    m=load('al111',a.al111); s=m.default_synthesis(); r=m.default_runtime_evaluation()
    neg=(s.permission_granted,s.approval_executed,s.stop_executed,s.action_executed,s.plan_committed,s.external_write_performed,s.world_truth_proven,s.domain_authority_promoted,s.safety_proven,s.action_success,r.permission_granted,r.approval_executed,r.stop_executed,r.action_executed,r.external_write_performed,r.world_truth_proven,r.safety_proven,r.action_success)
    pass111=(s.decision.value=='ALLOW' and s.next_action.value=='MONITOR_READY_CANDIDATE' and s.escalation.value=='NONE' and s.runtime_monitor_ready and s.observable_coverage_complete and s.conflict_free and s.next_gate_candidate and r.decision.value=='ALLOW' and r.next_action.value=='CONTINUE_CANDIDATE' and r.escalation.value=='NONE' and r.next_gate_candidate and not any(neg))
    used=dict(base['al_artifacts_used']); used['111']={'al_number':'111','source_sha256':file_sha(a.al111),'synthesis_decision':s.decision.value,'synthesis_next_action':s.next_action.value,'runtime_decision':r.decision.value,'runtime_next_action':r.next_action.value,'runtime_monitor_ready':s.runtime_monitor_ready,'observable_coverage_complete':s.observable_coverage_complete,'conflict_free':s.conflict_free,'next_gate_candidate':s.next_gate_candidate and r.next_gate_candidate,'permission_granted':s.permission_granted or r.permission_granted,'stop_executed':s.stop_executed or r.stop_executed,'action_executed':s.action_executed or r.action_executed,'world_truth_proven':s.world_truth_proven or r.world_truth_proven,'safety_proven':s.safety_proven or r.safety_proven,'action_success':s.action_success or r.action_success,'authority_boundary':'Monitor Ready / Stop / Continue Candidates remain control evidence only; no Permission Grant, Stop Execution, Action Execution, World Truth, Safety Proof, or Action Success.'}
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,111)}; checks['111_pass']=pass111
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':112,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-111','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(1 for v in checks.values() if v),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_110_sha256':file_sha(base_out),'authority_note':'All completed AL evaluators are used as control evidence only. No Truth, Authority, Permission Grant, Budget/Credential Grant, Stop Execution, Action Execution, Commit/Publish, External Write, Safety Proof, or Action Success authority is promoted.'}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
