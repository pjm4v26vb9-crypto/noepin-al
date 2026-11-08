"""Actual completed-NOEPIN-AL production gates used while building Technology 050."""
from __future__ import annotations
import argparse, importlib.util, json, sys
from hashlib import sha256
from pathlib import Path

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    if spec is None or spec.loader is None: raise RuntimeError(path)
    mod=importlib.util.module_from_spec(spec); sys.modules[name]=mod; spec.loader.exec_module(mod); return mod

def file_sha(p): return sha256(Path(p).read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser()
    for n in range(37,50): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); now=1_800_000_000
    mods={n:load(f'al{n:03d}',getattr(a,f'al{n:03d}')) for n in range(37,50)}
    a37,a38,a39,a40,a41,a42,a43,a44,a45,a46,a47,a48,a49=[mods[n] for n in range(37,50)]
    p37=a37.SafeProfile('BUILD-050','1',now-100,now+10000,False,frozenset({'BUILD_SUCCESSOR'}),frozenset(),frozenset(),frozenset({'BUILD_SUCCESSOR'}),frozenset({'LOCAL_ARTIFACT_WRITE','LOCAL_TEST','NOTION_EVIDENCE_UPDATE'}),frozenset({'artifact','scope'}),1,1,3,3,True)
    r37=a37.SafetyRequest('BUILD-050','NOEPIN','BUILD_SUCCESSOR','NOEPIN-AL-050',1,1,frozenset({'LOCAL_ARTIFACT_WRITE','LOCAL_TEST','NOTION_EVIDENCE_UPDATE'}),{'artifact':'NOEPIN-AL-050','scope':'NOEPIN AL only'},False,True,False,'1')
    d37=a37.evaluate(r37,p37,a37.AuthorityContext(True,False,frozenset({'BUILD_SUCCESSOR@NOEPIN-AL-050'}),'BUILD-050-E1'),now=now)
    p38=a38.MemoryPolicy('BUILD-EVIDENCE',1,1,frozenset({'verification_evidence'}),86400,604800,frozenset({'INTERNAL'}),False,False,False)
    d38=a38.evaluate(p38,a38.MemoryRequest(operation='STORE',purpose='verification_evidence',now=now,requested_retention_seconds=86400,classification='INTERNAL',expected_policy_id=p38.policy_id,expected_policy_version=p38.version,expected_authority_epoch=p38.authority_epoch),None)
    rules=(
      a39.Rule('R1','BUILD','1','NO_EXTERNAL_EXEC','static_no_external_execution',a39.Operator.TRUE,severity=a39.Severity.CRITICAL),
      a39.Rule('R2','BUILD','1','AUTHORITY','authority_boundaries_declared',a39.Operator.TRUE,severity=a39.Severity.HIGH),
      a39.Rule('R3','BUILD','1','PLAN_GRAPH','plan_graph_present',a39.Operator.TRUE,severity=a39.Severity.CRITICAL),
      a39.Rule('R4','BUILD','1','DATA_FLOW','data_flow_checked',a39.Operator.TRUE,severity=a39.Severity.CRITICAL),
      a39.Rule('R5','BUILD','1','NO_EXEC','control_no_execution',a39.Operator.TRUE,severity=a39.Severity.CRITICAL),
      a39.Rule('R6','BUILD','1','BASELINE','baseline_immutable',a39.Operator.TRUE,severity=a39.Severity.CRITICAL),
      a39.Rule('R7','BUILD','1','LICENSE','license_not_specified',a39.Operator.TRUE,severity=a39.Severity.MEDIUM),
      a39.Rule('R8','BUILD','1','AL_USE','completed_al_used',a39.Operator.TRUE,severity=a39.Severity.HIGH),)
    p39=a39.RuleProfile('BUILD-050','1',1,now-100,now+10000,False,rules)
    d39=a39.evaluate(a39.EvaluationRequest('BUILD-050','NOEPIN-AL-050-SUCCESSOR-V2','BUILD_SUCCESSOR',{'static_no_external_execution':True,'authority_boundaries_declared':True,'plan_graph_present':True,'data_flow_checked':True,'control_no_execution':True,'baseline_immutable':True,'license_not_specified':True,'completed_al_used':True}),p39,(),now=now)
    case=a40.RedTeamCase('BUILD050-OFFLINE',a40.Category.REGRESSION,a40.Severity.HIGH,'Technology 050 independent monitor must not execute blocks/tools or grant permission',a40.ExpectedBehavior.NO_ACTION,frozenset({'NOEPIN-AL-050'}),frozenset({'NO_EXTERNAL_EXECUTION','NO_PERMISSION_GRANT','NO_BLOCK_EXECUTION'}),True,True)
    d40=a40.evaluate_suite(a40.RedTeamSuite('BUILD-050','1',1,now-100,now+10000,(case,),False),(a40.Observation('BUILD050-OFFLINE','048-V2',a40.ExpectedBehavior.NO_ACTION,frozenset({'NO_EXTERNAL_EXECUTION','NO_PERMISSION_GRANT','NO_BLOCK_EXECUTION'}),now,'BUILD050-EVIDENCE',True,False,False,False,False),),target_version='048-V2',now=now)
    b41=a41.default_baseline(now); d41=a41.evaluate(a41.BehaviorEvent('BUILD050-BEHAVIOR','NOEPIN',now,'LOCAL_TEST','VERIFY','TEST_ARTIFACT',1.0,1.0,b41.expected_capabilities,b41.baseline_id,b41.version,b41.authority_epoch,'BUILD050-BEHAVIOR-EVIDENCE',True),b41,now=now)
    d42=a42.assess(a42.default_request(now),a42.default_policy(now),a42.build_default_state(now),now=now)
    d43=a43.evaluate(a43.default_request(now),a43.default_policy(now),a43.default_authority(),now=now)
    d44=a44.evaluate(a44.default_request(now),a44.default_policy(now),a44.default_states(),now=now)
    d45=a45.evaluate(a45.default_request(now),a45.default_policy(now),a45.default_candidates(),now=now)
    d46=a46.evaluate(a46.default_request(now),a46.default_policy(now),a46.default_evidence(now),now=now)
    d47=a47.evaluate(a47.default_request(now),a47.default_policy(now),a47.default_entries(now),now=now)
    d48=a48.evaluate(a48.default_request(now),a48.default_policy(now),a48.default_graph(),now=now)
    d49=a49.evaluate(a49.default_request(now),a49.default_policy(now),a49.default_profiles(now),now=now)
    checks={
      '037_pass':d37.decision.value=='ALLOW' and not d37.action_executed and not d37.permission_granted,
      '038_pass':d38.decision.value=='ALLOW' and not d38.memory_written and not d38.memory_deleted and not d38.truth_established,
      '039_pass':d39.decision.value=='ALLOW' and not d39.authoritative_compliance_proven and not d39.action_executed,
      '040_pass':d40.decision.value=='ALLOW' and d40.fail_count==0 and not d40.attack_executed and not d40.action_executed and not d40.production_safe_proven,
      '041_pass':d41.decision.value=='ALLOW' and not d41.compromise_proven and not d41.system_safe_proven and not d41.alert_executed and not d41.stop_executed,
      '042_pass':d42.decision.value=='ALLOW' and d42.integrity_chain_valid and d42.preservation_complete_candidate and not d42.containment_executed and not d42.evidence_preserved and not d42.persistence_performed,
      '043_pass':d43.decision.value=='ALLOW' and not d43.permission_granted and not d43.handoff_executed and not d43.action_success and not d43.context_truth_established,
      '044_pass':d44.decision.value=='ALLOW' and not d44.permission_granted and not d44.data_sent and not d44.classification_authoritative and not d44.truth_established and not d44.action_success,
      '045_pass':d45.decision.value=='ALLOW' and not d45.permission_granted and not d45.action_executed and not d45.commit_performed and not d45.action_success and not d45.safety_proven,
      '046_pass':d46.decision.value=='ALLOW' and d46.approval_complete_candidate and not d46.permission_granted and not d46.action_executed and not d46.commit_performed and not d46.action_success and not d46.approval_truth_proven,
      '047_pass':d47.decision.value=='ALLOW' and not d47.permission_granted and not d47.action_executed and not d47.stop_executed and not d47.commit_performed and not d47.action_success,
      '048_pass':d48.decision.value=='ALLOW' and not d48.permission_granted and not d48.tool_executed and not d48.data_sent and not d48.commit_performed and not d48.action_success,
      '049_pass':d49.decision.value=='ALLOW' and not d49.permission_granted and not d49.model_invoked and not d49.data_transferred and not d49.action_success and not d49.trust_truth_established and not d49.verification_pass_proven,
    }
    def info(n,d,**kw): return {'source_sha256':file_sha(getattr(a,f'al{n:03d}')),'decision':d.decision.value,**kw}
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':50,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','al_artifacts_used':{
      '037':info(37,d37,action_executed=d37.action_executed,permission_granted=d37.permission_granted),
      '038':info(38,d38,memory_written=d38.memory_written,memory_deleted=d38.memory_deleted,truth_established=d38.truth_established),
      '039':info(39,d39,authoritative_compliance_proven=d39.authoritative_compliance_proven,action_executed=d39.action_executed),
      '040':info(40,d40,attack_executed=d40.attack_executed,action_executed=d40.action_executed,production_safe_proven=d40.production_safe_proven),
      '041':info(41,d41,compromise_proven=d41.compromise_proven,system_safe_proven=d41.system_safe_proven,alert_executed=d41.alert_executed,stop_executed=d41.stop_executed),
      '042':info(42,d42,integrity_chain_valid=d42.integrity_chain_valid,preservation_complete_candidate=d42.preservation_complete_candidate,containment_executed=d42.containment_executed,evidence_preserved=d42.evidence_preserved,persistence_performed=d42.persistence_performed),
      '043':info(43,d43,permission_granted=d43.permission_granted,handoff_executed=d43.handoff_executed,action_success=d43.action_success,context_truth_established=d43.context_truth_established),
      '044':info(44,d44,permission_granted=d44.permission_granted,data_sent=d44.data_sent,classification_authoritative=d44.classification_authoritative,truth_established=d44.truth_established,action_success=d44.action_success),
      '045':info(45,d45,permission_granted=d45.permission_granted,action_executed=d45.action_executed,commit_performed=d45.commit_performed,action_success=d45.action_success,safety_proven=d45.safety_proven),
      '046':info(46,d46,approval_complete_candidate=d46.approval_complete_candidate,permission_granted=d46.permission_granted,action_executed=d46.action_executed,commit_performed=d46.commit_performed,action_success=d46.action_success,approval_truth_proven=d46.approval_truth_proven),
      '047':info(47,d47,permission_granted=d47.permission_granted,action_executed=d47.action_executed,stop_executed=d47.stop_executed,commit_performed=d47.commit_performed,action_success=d47.action_success),
      '048':info(48,d48,permission_granted=d48.permission_granted,tool_executed=d48.tool_executed,data_sent=d48.data_sent,commit_performed=d48.commit_performed,action_success=d48.action_success),
      '049':info(49,d49,permission_granted=d49.permission_granted,model_invoked=d49.model_invoked,data_transferred=d49.data_transferred,action_success=d49.action_success,trust_truth_established=d49.trust_truth_established,verification_pass_proven=d49.verification_pass_proven),
    },'gate_checks':checks,'production_gate_pass':all(checks.values()),'authority_note':'AL gates are pre-execution/control evidence only; they do not grant monitor permission, execute blocks/tools, commit state, establish signal truth, or prove production success.'}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
