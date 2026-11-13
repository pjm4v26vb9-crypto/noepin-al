"""Actual completed NOEPIN AL production use evidence for Technology 139."""
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
    for n in range(37,139): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    gate138_path=Path(__file__).with_name('al_production_gate_138.py'); gate138=load('gate138_baseline',gate138_path)
    base_out=a.out.with_name('GATE_BASELINE_037_137.json'); old=sys.argv
    try:
        argv=[str(gate138_path)]
        for n in range(37,138): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--out',str(base_out)]; sys.argv=argv; rc=gate138.main()
    finally: sys.argv=old
    if rc!=0: raise SystemExit(2)
    base=json.loads(base_out.read_text(encoding='utf-8'))
    m=load('al138',a.al138); r=m.default_evaluation()
    neg=(r.memory_promoted_to_truth,r.mention_promoted_to_memory,r.semantic_similarity_promoted_to_fact_identity,r.canonical_memory_written,r.destructive_merge_executed,r.provenance_dropped,r.difference_suppressed,r.dcsr_reconstruction_created_memory,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success)
    pass138=(r.decision.value=='ALLOW' and r.next_action.value=='CANONICAL_MEMORY_CANDIDATE' and r.escalation.value=='NONE' and r.dedup_state.value=='DEDUPLICATION_CANDIDATE' and len(r.merged_links)==1 and r.next_gate_candidate and not any(neg))
    used=dict(base['al_artifacts_used']); used['138']={'al_number':'138','source_sha256':file_sha(a.al138),'decision':r.decision.value,'next_action':r.next_action.value,'escalation':r.escalation.value,'dedup_state':r.dedup_state.value,'merged_link_count':len(r.merged_links),'next_gate_candidate':r.next_gate_candidate,'permission_granted':r.permission_granted,'approval_executed':r.approval_executed,'action_executed':r.action_executed,'world_truth_proven':r.world_truth_proven,'safety_proven':r.safety_proven,'action_success':r.action_success,'authority_boundary':'Semantic Memory deduplication is candidate-only; Memory is not Truth, Similarity is not Fact Identity, Canonical Memory Candidate is not Memory Write, Merge Link is not Destructive Merge, and no Permission, Approval, Authority, Safety Proof, Action Execution, or Action Success occurs.'}
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,138)}; checks['138_pass']=pass138
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':139,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-138','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(1 for v in checks.values() if v),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_137_sha256':file_sha(base_out),'authority_note':'All completed AL evaluators are control/audit/reference evidence only. Memory deduplication and earlier candidate outputs do not become Truth, Authority, Permission, Safety Proof, Approval, Memory Write, destructive merge, Action Execution, or Action Success.'}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
