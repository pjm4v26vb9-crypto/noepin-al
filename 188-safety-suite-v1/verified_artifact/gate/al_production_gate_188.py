from __future__ import annotations
import argparse,importlib.util,json,sys
from hashlib import sha256
from pathlib import Path
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod
def fsha(p):return sha256(Path(p).read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser()
 for n in range(37,188):ap.add_argument(f'--al{n:03d}',type=Path,required=True)
 ap.add_argument('--suite-evidence',type=Path,required=True); ap.add_argument('--out',type=Path,required=True); a=ap.parse_args()
 gp=Path(__file__).with_name('al_production_gate_187.py'); g=load('gate187_baseline',gp); bo=a.out.with_name('GATE_BASELINE_037_186.json'); old=sys.argv
 try:
  argv=[str(gp)]
  for n in range(37,187):argv += [f'--al{n:03d}',str(getattr(a,f'al{n:03d}'))]
  argv += ['--out',str(bo)]; sys.argv=argv; rc=g.main()
 finally:sys.argv=old
 if rc!=0:raise SystemExit(2)
 base=json.loads(bo.read_text()); m=load('al187',a.al187); r=m.default_evaluation()
 neg=[getattr(r,n) for n in m.FALSE_FIELDS]
 p187=(fsha(a.al187)=='ffba29fd277c81a354c89be6de82f86b8943a310fd225f81dbc1013982d78d85' and r.decision.value=='ALLOW' and r.next_action.value=='CONTINUE_TO_PERMIT_GATE_CANDIDATE' and r.escalation.value=='NONE' and r.engine_state.value=='SECURITY_CHAIN_CANDIDATE' and r.request_id=='REQ-00-A' and r.next_gate_candidate and not r.authoritative and not any(neg))
 suite=json.loads(a.suite_evidence.read_text()); suite_ok=bool(suite.get('overall_pass')) and suite.get('controls') and sum(1 for x in suite['controls'] if x.get('ok'))==61
 used=dict(base['al_artifacts_used']); used['187']={'al_number':'187/AUX-00','source_sha256':fsha(a.al187),'decision':r.decision.value,'next_action':r.next_action.value,'next_gate_candidate':r.next_gate_candidate,'authority_boundary':'Gateway ALLOW is candidate-only; no Permission/Permit/Tool execution.'}
 checks={f'{n:03d}_pass':bool(base['gate_checks'].get(f'{n:03d}_pass')) for n in range(37,187)}; checks['187_pass']=p187
 out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':'188 / Safety Suite V1','creator':'NOEPIN / のえぴん','actual_al_range':'037-187','al_artifacts_used':used,'gate_checks':checks,'pass_count':sum(checks.values()),'total':len(checks),'production_gate_pass':all(checks.values()) and suite_ok,'canonical_suite_recheck_pass':suite_ok,'canonical_suite_recheck_sha256':fsha(a.suite_evidence),'execution_performed':False,'permission_elevation':False,'write_performed':False,'action_success_promoted':False,'authority_note':'Safety Suite distribution aggregates completed Controls without acquiring Domain Truth/Permission/Action authority.'}
 a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__':raise SystemExit(main())
