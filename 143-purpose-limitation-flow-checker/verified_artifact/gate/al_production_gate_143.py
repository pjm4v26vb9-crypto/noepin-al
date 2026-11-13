"""Actual completed NOEPIN AL production use evidence for Technology 143."""
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
    for n in range(37,143): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
    gate142_path=Path(__file__).with_name('al_production_gate_142.py'); gate142=load('gate142_baseline',gate142_path)
    base_out=a.out.with_name('GATE_BASELINE_037_141.json'); old=sys.argv
    try:
        argv=[str(gate142_path)]
        for n in range(37,142): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
        argv += ['--out',str(base_out)]; sys.argv=argv; rc=gate142.main()
    finally: sys.argv=old
    if rc!=0: raise SystemExit(2)
    base=json.loads(base_out.read_text(encoding='utf-8'))
    m=load('al142',a.al142); r=m.default_evaluation()
    neg=(r.taint_promoted_to_truth,r.source_promoted_to_authority,r.sanitizer_evidence_promoted_to_safety_proof,r.taint_sink_executed,r.external_send_executed,r.execution_sink_invoked,r.tool_invoked,r.memory_write_performed,r.label_write_performed,r.policy_modified,r.dlp_replaced,r.authentication_replaced,r.encryption_replaced,r.dcsr_reconstruction_created_fact,r.sender_authority_inherited,r.sender_intent_inherited,r.sender_agreement_inherited,r.permission_granted,r.approval_executed,r.authority_granted,r.stop_executed,r.action_executed,r.plan_committed,r.publish_executed,r.external_write_performed,r.world_truth_proven,r.domain_authority_promoted,r.safety_proven,r.action_success)
    pass142=(r.decision.value=='DENY' and r.next_action.value=='BLOCK_FLOW_CANDIDATE' and r.escalation.value=='TAINTED_SINK' and r.engine_state.value=='RISK_SINK_CANDIDATE' and r.next_gate_candidate and not any(neg))
    used=dict(base['al_artifacts_used']); used['142']={'al_number':'142','source_sha256':file_sha(a.al142),'decision':r.decision.value,'next_action':r.next_action.value,'escalation':r.escalation.value,'engine_state':r.engine_state.value,'next_gate_candidate':r.next_gate_candidate,'permission_granted':r.permission_granted,'approval_executed':r.approval_executed,'action_executed':r.action_executed,'world_truth_proven':r.world_truth_proven,'safety_proven':r.safety_proven,'action_success':r.action_success,'authority_boundary':'Semantic taint is evidence/control metadata only; Taint != Truth, Sanitizer Evidence != universal Safety Proof, Tainted Sink Candidate != Sink Execution, and DCSR does not replace authentication, encryption, Policy, or DLP.'}
    checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,142)}; checks['142_pass']=pass142
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':143,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-142','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(1 for v in checks.values() if v),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_141_sha256':file_sha(base_out),'authority_note':'All completed AL evaluators are control/audit/reference evidence only. Purpose, taint, retention and earlier candidates do not become Truth, Authority, Permission, Safety Proof, Approval, Memory/Knowledge Write, Stop Execution, Action Execution, or Action Success.'}
    a.out.parent.mkdir(parents=True,exist_ok=True); a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
