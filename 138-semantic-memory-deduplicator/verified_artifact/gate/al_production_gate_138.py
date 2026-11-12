"""Actual completed NOEPIN AL production use evidence for Technology 138."""
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
    for n in range(37,138): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    gate137_path=Path(__file__).with_name('al_production_gate_137.py'); gate137=load('gate137_baseline',gate137_path)
    base_out=a.out.with_name('GATE_BASELINE_037_136.json'); old=sys.argv
    try:
        argv=[str(gate137_path)]
        for n in range(37,137): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--out',str(base_out)]; sys.argv=argv; rc=gate137.main()
    finally: sys.argv=old
    if rc!=0: raise SystemExit(2)
    base=json.loads(base_out.read_text(encoding='utf-8'))
    m=load('al137',a.al137); r=m.default_evaluation()
    neg=(r.memory_promoted_to_truth,r.mention_promoted_to_memory,r.allowed_set_transferred_to_reasoner,r.purpose_match_promoted_to_permission,r.permission_evidence_promoted_to_permission_execution,r.sensitivity_promoted_to_truth,r.external_retrieval_executed,r.memory_write_performed,r.dcsr_reconstruction_created_memory,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success)
    pass137=(r.decision.value=='ALLOW' and r.next_action.value=='MEMORY_SUPPLY_CANDIDATE' and r.escalation.value=='NONE' and r.gate_state.value=='ALLOWED_SET_CANDIDATE' and r.allowed_memory_ids==('MEM-1',) and r.next_gate_candidate and not any(neg))
    used=dict(base['al_artifacts_used']); used['137']={'al_number':'137','source_sha256':file_sha(a.al137),'decision':r.decision.value,'next_action':r.next_action.value,'escalation':r.escalation.value,'gate_state':r.gate_state.value,'allowed_memory_ids':list(r.allowed_memory_ids),'next_gate_candidate':r.next_gate_candidate,'permission_granted':r.permission_granted,'approval_executed':r.approval_executed,'action_executed':r.action_executed,'world_truth_proven':r.world_truth_proven,'safety_proven':r.safety_proven,'action_success':r.action_success,'authority_boundary':'Allowed Memory Set is a candidate only; Purpose Match is not Permission Grant, Permission Evidence is not Permission Execution, Memory is not Truth, and no Reasoner Transfer, Memory Write, Approval, Authority, Safety Proof, Action Execution, or Action Success occurs.'}
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,137)}; checks['137_pass']=pass137
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':138,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-137','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(1 for v in checks.values() if v),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_136_sha256':file_sha(base_out),'authority_note':'All completed AL evaluators are control/audit/reference evidence only. Semantic Memory deduplication, purpose-scoped Memory supply, episodic isolation, contradiction resolution, temporal current, retention, provenance merge and all earlier candidate outputs do not become Truth, Authority, Permission, Safety Proof, Approval, Memory Write, Reasoner Transfer, destructive merge, Action Execution, or Action Success.'}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
