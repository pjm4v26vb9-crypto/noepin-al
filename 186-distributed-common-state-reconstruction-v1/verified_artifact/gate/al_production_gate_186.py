"""Actual completed NOEPIN AL production use evidence for Technology 186."""
from __future__ import annotations
import argparse,importlib.util,json,sys
from hashlib import sha256
from pathlib import Path

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod
def file_sha(p): return sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser()
 for n in range(37,186): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
 ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
 gp=Path(__file__).with_name('al_production_gate_185.py'); g=load('gate185_baseline',gp); bo=a.out.with_name('GATE_BASELINE_037_184.json'); old=sys.argv
 try:
  argv=[str(gp)]
  for n in range(37,185): argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
  argv += ['--out',str(bo)]; sys.argv=argv; rc=g.main()
 finally: sys.argv=old
 if rc!=0: raise SystemExit(2)
 base=json.loads(bo.read_text()); m=load('al185',a.al185); r=m.default_evaluation()
 neg=[getattr(r,n) for n in ('permission_granted','permit_issued','approval_executed','human_approval_executed','tool_invoked','action_executed','action_success','stop_executed','file_write_executed','network_send_executed','external_write_performed','world_truth_proven','domain_authority_promoted','memory_promoted_to_truth','belief_promoted_to_truth','candidate_promoted_to_actual','intent_promoted_to_action','action_request_promoted_to_success','private_state_promoted_to_world_fact','cached_result_promoted_to_authoritative','materialized_state_promoted_to_semantically_existing','unknown_promoted_to_known','safety_proven','dcsr_invented_state','dcsr_bypassed_authority','dcsr_bypassed_schema','dcsr_bypassed_dependency','dcsr_promoted_cache_to_truth')]
 p185=(file_sha(a.al185)=='6d7c087fcd4d8f322e24623c0ab85a20a93b95f75fe4643182c652e34a7132af' and r.decision.value=='ALLOW' and r.next_action.value=='USE_DIRECT_STATE_CANDIDATE' and r.escalation.value=='NONE' and r.engine_state.value=='DIRECT_STATE_CANDIDATE' and r.kernel_id=='CSK-185-A' and r.next_gate_candidate and not r.authoritative and not any(neg))
 used=dict(base['al_artifacts_used']); used['185']={'al_number':'185','source_sha256':file_sha(a.al185),'decision':r.decision.value,'next_action':r.next_action.value,'escalation':r.escalation.value,'engine_state':r.engine_state.value,'next_gate_candidate':r.next_gate_candidate,'permission_granted':r.permission_granted,'action_executed':r.action_executed,'action_success':r.action_success,'authority_boundary':'Common State Kernel is State Infrastructure Authority only; Kernel state/cache/prepared/materialized state != Domain Truth/Permission/Action Success.'}
 checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,185)}; checks['185_pass']=p185
 out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':186,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','actual_al_range':'037-185','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(checks.values()),'total':len(checks),'production_gate_pass':all(checks.values()),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'baseline_gate_037_184_sha256':file_sha(bo),'authority_note':'DCSR is State Infrastructure/Transport/Reconstruction planning only. Shared/Transferred/Reconstructed/Partial/Fingerprint-matched state does not become Domain Authority, Truth, Approval, Permission, Action Execution, Action Success, or universal Safety Proof.'}
 a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
