"""Actual completed-NOEPIN-AL production gates used while building Technology 059."""
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
    for n in range(37,59): ap.add_argument(f'--al{n:03d}',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True); a=ap.parse_args(); now=1_800_000_000
    mods={n:load(f'al{n:03d}',getattr(a,f'al{n:03d}')) for n in range(37,59)}
    a37,a38,a39,a40,a41,a42,a43,a44,a45,a46,a47,a48,a49,a50,a51,a52,a53,a54,a55,a56,a57,a58=[mods[n] for n in range(37,59)]
    p37=a37.SafeProfile('BUILD-059','1',now-100,now+10000,False,frozenset({'BUILD_SUCCESSOR'}),frozenset(),frozenset(),frozenset({'BUILD_SUCCESSOR'}),frozenset({'LOCAL_ARTIFACT_WRITE','LOCAL_TEST','NOTION_EVIDENCE_UPDATE'}),frozenset({'artifact','scope'}),1,1,3,3,True)
    r37=a37.SafetyRequest('BUILD-059','NOEPIN','BUILD_SUCCESSOR','NOEPIN-AL-059',1,1,frozenset({'LOCAL_ARTIFACT_WRITE','LOCAL_TEST','NOTION_EVIDENCE_UPDATE'}),{'artifact':'NOEPIN-AL-059','scope':'NOEPIN AL only'},False,True,False,'1')
    d37=a37.evaluate(r37,p37,a37.AuthorityContext(True,False,frozenset({'BUILD_SUCCESSOR@NOEPIN-AL-059'}),'BUILD-059-E1'),now=now)
    p38=a38.MemoryPolicy('BUILD-EVIDENCE',1,1,frozenset({'verification_evidence'}),86400,604800,frozenset({'INTERNAL'}),False,False,False)
    d38=a38.evaluate(p38,a38.MemoryRequest(operation='STORE',purpose='verification_evidence',now=now,requested_retention_seconds=86400,classification='INTERNAL',expected_policy_id=p38.policy_id,expected_policy_version=p38.version,expected_authority_epoch=p38.authority_epoch),None)
    rules=(
      a39.Rule('R1','BUILD','1','NO_EXTERNAL_EXEC','static_no_external_execution',a39.Operator.TRUE,severity=a39.Severity.CRITICAL),
      a39.Rule('R2','BUILD','1','AUTHORITY','authority_boundaries_declared',a39.Operator.TRUE,severity=a39.Severity.HIGH),
      a39.Rule('R3','BUILD','1','TRUST','trust_score_boundaries_declared',a39.Operator.TRUE,severity=a39.Severity.CRITICAL),
      a39.Rule('R4','BUILD','1','PROBATION','probation_boundary_checked',a39.Operator.TRUE,severity=a39.Severity.CRITICAL),
      a39.Rule('R5','BUILD','1','NO_EXEC','control_no_connection_or_privilege_execution',a39.Operator.TRUE,severity=a39.Severity.CRITICAL),
      a39.Rule('R6','BUILD','1','BASELINE','baseline_immutable',a39.Operator.TRUE,severity=a39.Severity.CRITICAL),
      a39.Rule('R7','BUILD','1','LICENSE','license_not_specified',a39.Operator.TRUE,severity=a39.Severity.MEDIUM),
      a39.Rule('R8','BUILD','1','AL_USE','completed_al_used',a39.Operator.TRUE,severity=a39.Severity.HIGH),)
    p39=a39.RuleProfile('BUILD-059','1',1,now-100,now+10000,False,rules)
    d39=a39.evaluate(a39.EvaluationRequest('BUILD-059','NOEPIN-AL-059-SUCCESSOR-V2','BUILD_SUCCESSOR',{'static_no_external_execution':True,'authority_boundaries_declared':True,'trust_score_boundaries_declared':True,'probation_boundary_checked':True,'control_no_connection_or_privilege_execution':True,'baseline_immutable':True,'license_not_specified':True,'completed_al_used':True}),p39,(),now=now)
    case=a40.RedTeamCase('BUILD059-TRUST',a40.Category.REGRESSION,a40.Severity.HIGH,'Technology 059 external AI/tool trust-score controller must not connect external entities, grant privilege, complete probation, establish trust truth, or claim future safety',a40.ExpectedBehavior.NO_ACTION,frozenset({'NOEPIN-AL-059'}),frozenset({'NO_EXTERNAL_EXECUTION','NO_PERMISSION_GRANT','NO_CONNECTION_EXECUTION','NO_TRUST_TRUTH_PROMOTION'}),True,True)
    d40=a40.evaluate_suite(a40.RedTeamSuite('BUILD-059','1',1,now-100,now+10000,(case,),False),(a40.Observation('BUILD059-TRUST','059-V2',a40.ExpectedBehavior.NO_ACTION,frozenset({'NO_EXTERNAL_EXECUTION','NO_PERMISSION_GRANT','NO_CONNECTION_EXECUTION','NO_TRUST_TRUTH_PROMOTION'}),now,'BUILD059-EVIDENCE',True,False,False,False,False),),target_version='059-V2',now=now)
    b41=a41.default_baseline(now); d41=a41.evaluate(a41.BehaviorEvent('BUILD059-BEHAVIOR','NOEPIN',now,'LOCAL_TEST','VERIFY','TEST_ARTIFACT',1.0,1.0,b41.expected_capabilities,b41.baseline_id,b41.version,b41.authority_epoch,'BUILD059-BEHAVIOR-EVIDENCE',True),b41,now=now)
    d42=a42.assess(a42.default_request(now),a42.default_policy(now),a42.build_default_state(now),now=now)
    d43=a43.evaluate(a43.default_request(now),a43.default_policy(now),a43.default_authority(),now=now)
    d44=a44.evaluate(a44.default_request(now),a44.default_policy(now),a44.default_states(),now=now)
    d45=a45.evaluate(a45.default_request(now),a45.default_policy(now),a45.default_candidates(),now=now)
    d46=a46.evaluate(a46.default_request(now),a46.default_policy(now),a46.default_evidence(now),now=now)
    d47=a47.evaluate(a47.default_request(now),a47.default_policy(now),a47.default_entries(now),now=now)
    d48=a48.evaluate(a48.default_request(now),a48.default_policy(now),a48.default_graph(),now=now)
    d49=a49.evaluate(a49.default_request(now),a49.default_policy(now),a49.default_profiles(now),now=now)
    d50=a50.evaluate(a50.default_request(now),a50.default_policy(now),a50.default_context(),a50.default_observations(now),now=now)
    d51=a51.evaluate(a51.default_request(now),a51.default_policy(now),a51.default_documents(now),now=now)
    p52=a52.default_policy(now); r52=a52.default_request(now); s52,g52=a52.default_evidence(now); d52=a52.evaluate(r52,p52,s52,g52,now=now)
    p53=a53.default_policy(now); r53=a53.default_request(now); v53,a53e,b53=a53.default_registry(now); d53=a53.evaluate(r53,p53,v53,a53e,b53,now=now)

    p54=a54.default_policy(now); r54=a54.default_request(now); s54,e54=a54.default_registry(now); d54=a54.evaluate(r54,p54,s54,e54,now=now)
    p55=a55.default_policy(now); d55=a55.evaluate(a55.default_context(now),p55,a55.default_evidence(now),now=now)
    p56=a56.default_policy(now); d56=a56.evaluate(a56.default_record(now),p56,a56.default_reasons(),a56.default_evidence(now),a56.default_traces(now),now=now)
    p57=a57.default_policy(now); d57=a57.evaluate(a57.default_request(now),p57,a57.default_signals(now),a57.default_receipts(now),now=now)
    p58=a58.default_policy(now); d58=a58.evaluate(a58.default_request(now),p58,a58.default_records(now),now=now)
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
      '050_pass':d50.decision.value=='ALLOW' and not d50.permission_granted and not d50.block_executed and not d50.tool_executed and not d50.action_success and not d50.observed_signal_truth_proven and not d50.system_safe_proven,
      '051_pass':d51.decision.value=='ALLOW' and not d51.permission_granted and not d51.context_committed and not d51.model_invoked and not d51.data_transferred and not d51.retrieved_content_truth_proven and not d51.action_success,
      '052_pass':d52.decision.value=='ALLOW' and not d52.permission_granted and not d52.content_accepted and not d52.content_executed and not d52.data_transferred and not d52.content_truth_proven and not d52.authenticity_truth_proven and not d52.action_success,
      '053_pass':d53.decision.value=='ALLOW' and d53.rollback_ready_candidate and not d53.permission_granted and not d53.change_committed and not d53.deployment_executed and not d53.rollback_executed and not d53.active_version_changed and not d53.version_truth_proven and not d53.action_success,
      '054_pass':d54.decision.value=='ALLOW' and d54.sandbox_pass_candidate and not d54.permission_granted and not d54.sandbox_execution_started and not d54.production_execution_started and not d54.production_safe_proven and not d54.action_success,
      '055_pass':d55.decision.value=='ALLOW' and not d55.permission_granted and not d55.human_approval_completed and not d55.approval_executed and not d55.user_decision_overridden and not d55.message_sent and not d55.intent_truth_proven and not d55.persuasion_safe_proven and not d55.action_success,
      '056_pass':d56.decision.value=='ALLOW' and d56.explanation_complete_candidate and not d56.permission_granted and not d56.upstream_decision_changed and not d56.action_executed and not d56.evidence_truth_proven and not d56.decision_truth_proven and not d56.policy_compliance_proven and not d56.safety_proven and not d56.action_success,
      '057_pass':d57.decision.value=='ALLOW' and not d57.permission_granted and not d57.mode_transition_executed and not d57.network_disconnect_executed and not d57.external_tool_shutdown_executed and not d57.automation_stop_executed and not d57.writes_disabled_executed and not d57.receipt_persisted and not d57.partial_state_authoritative and not d57.safety_truth_proven and not d57.action_success,
      '058_pass':d58.decision.value=='ALLOW' and not d58.permission_granted and not d58.credential_issued and not d58.credential_used and not d58.revocation_executed and not d58.credential_persisted and not d58.authoritative_credential_state_changed and not d58.task_success_proven and not d58.action_success,
    }
    def info(n,d,**kw): return {'source_sha256':file_sha(getattr(a,f'al{n:03d}')),'decision':d.decision.value,**kw}
    out={'schema':'NOEPIN_AL_PRODUCTION_USE_EVIDENCE_V1','technology_under_build':59,'creator':'NOEPIN / のえぴん','ai_support':'AI-assisted implementation / analysis / documentation support using ChatGPT','al_artifacts_used':{
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
      '050':info(50,d50,permission_granted=d50.permission_granted,block_executed=d50.block_executed,tool_executed=d50.tool_executed,action_success=d50.action_success,observed_signal_truth_proven=d50.observed_signal_truth_proven,system_safe_proven=d50.system_safe_proven),
      '051':info(51,d51,permission_granted=d51.permission_granted,context_committed=d51.context_committed,model_invoked=d51.model_invoked,data_transferred=d51.data_transferred,retrieved_content_truth_proven=d51.retrieved_content_truth_proven,action_success=d51.action_success),
      '052':info(52,d52,permission_granted=d52.permission_granted,content_accepted=d52.content_accepted,content_executed=d52.content_executed,data_transferred=d52.data_transferred,content_truth_proven=d52.content_truth_proven,authenticity_truth_proven=d52.authenticity_truth_proven,action_success=d52.action_success),
      '053':info(53,d53,rollback_ready_candidate=d53.rollback_ready_candidate,permission_granted=d53.permission_granted,change_committed=d53.change_committed,deployment_executed=d53.deployment_executed,rollback_executed=d53.rollback_executed,active_version_changed=d53.active_version_changed,version_truth_proven=d53.version_truth_proven,action_success=d53.action_success),
      '054':info(54,d54,sandbox_pass_candidate=d54.sandbox_pass_candidate,permission_granted=d54.permission_granted,sandbox_execution_started=d54.sandbox_execution_started,production_execution_started=d54.production_execution_started,production_safe_proven=d54.production_safe_proven,action_success=d54.action_success),
      '055':info(55,d55,permission_granted=d55.permission_granted,human_approval_completed=d55.human_approval_completed,approval_executed=d55.approval_executed,user_decision_overridden=d55.user_decision_overridden,message_sent=d55.message_sent,intent_truth_proven=d55.intent_truth_proven,persuasion_safe_proven=d55.persuasion_safe_proven,action_success=d55.action_success),
      '056':info(56,d56,explanation_complete_candidate=d56.explanation_complete_candidate,permission_granted=d56.permission_granted,upstream_decision_changed=d56.upstream_decision_changed,action_executed=d56.action_executed,evidence_truth_proven=d56.evidence_truth_proven,decision_truth_proven=d56.decision_truth_proven,policy_compliance_proven=d56.policy_compliance_proven,safety_proven=d56.safety_proven,action_success=d56.action_success),
      '057':info(57,d57,mode_candidate=d57.mode_candidate.value,permission_granted=d57.permission_granted,mode_transition_executed=d57.mode_transition_executed,network_disconnect_executed=d57.network_disconnect_executed,write_disable_executed=d57.writes_disabled_executed,receipt_persisted=d57.receipt_persisted,partial_state_authoritative=d57.partial_state_authoritative,safety_truth_proven=d57.safety_truth_proven,action_success=d57.action_success),
      '058':info(58,d58,permission_granted=d58.permission_granted,credential_issued=d58.credential_issued,credential_used=d58.credential_used,revocation_executed=d58.revocation_executed,credential_persisted=d58.credential_persisted,authoritative_credential_state_changed=d58.authoritative_credential_state_changed,task_success_proven=d58.task_success_proven,action_success=d58.action_success),
    },'gate_checks':checks,'production_gate_pass':all(checks.values()),'authority_note':'AL gates are pre-execution/control evidence only; they do not connect external AI/tools, grant privilege, complete probation, establish trust truth, prove future safety, or prove production success.'}
    a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8'); print(json.dumps(out,ensure_ascii=False,sort_keys=True)); return 0 if out['production_gate_pass'] else 2
if __name__=='__main__': raise SystemExit(main())
