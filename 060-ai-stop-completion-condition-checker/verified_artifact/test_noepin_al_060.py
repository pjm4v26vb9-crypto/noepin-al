from __future__ import annotations
import inspect,re,unittest
from dataclasses import replace
import noepin_al_060_stop_completion_checker as m
NOW=1_800_000_000

def base(): return m.default_policy(NOW),m.default_request(NOW),m.default_progress(NOW),m.default_criteria(NOW),m.default_dependencies(NOW)
class T(unittest.TestCase): pass

def scenario(i):
    k=i%32; p,r,ps,cs,ds=base()
    if k==0:
        x=m.evaluate(r,p,ps,cs,ds,now=NOW); assert x.decision is m.ControlDecision.ALLOW and x.completion_candidate and x.disposition is m.TaskDisposition.COMPLETE_CANDIDATE and not x.task_success_committed
    elif k==1:
        c=(replace(cs[0],satisfied=False),cs[1]); x=m.evaluate(r,p,ps,c,ds,now=NOW); assert x.decision is m.ControlDecision.ALLOW and x.continue_candidate and not x.completion_candidate
    elif k==2:
        x=m.evaluate(r,p,(replace(ps[0],current_step=p.max_steps),),cs,ds,now=NOW); assert x.decision is m.ControlDecision.DENY and x.stop_candidate and 'MAX_STEPS_REACHED' in x.reasons and not x.stop_executed
    elif k==3:
        x=m.evaluate(r,p,(replace(ps[0],elapsed_seconds=p.max_elapsed_seconds),),cs,ds,now=NOW); assert x.decision is m.ControlDecision.DENY and x.stop_candidate
    elif k==4:
        x=m.evaluate(r,p,(replace(ps[0],no_progress_steps=p.max_no_progress_steps),),cs,ds,now=NOW); assert x.decision is m.ControlDecision.HUMAN_APPROVAL and x.stop_candidate
    elif k==5:
        x=m.evaluate(r,p,(replace(ps[0],requested_extra_work=True),),cs,ds,now=NOW); assert x.decision is m.ControlDecision.DENY and x.scope_creep_detected and x.stop_candidate
    elif k==6:
        x=m.evaluate(r,p,(replace(ps[0],scope_fingerprint='BAD'),),cs,ds,now=NOW); assert x.decision is m.ControlDecision.DENY and x.scope_creep_detected
    elif k==7:
        x=m.evaluate(r,p,(replace(ps[0],cancelled=True),),cs,ds,now=NOW); assert x.decision is m.ControlDecision.DENY and x.stop_candidate
    elif k==8:
        x=m.evaluate(r,p,(replace(ps[0],fatal_error=True),),cs,ds,now=NOW); assert x.decision is m.ControlDecision.DENY and x.stop_candidate
    elif k==9:
        d=(replace(ds[0],completed=False,failed=True),); x=m.evaluate(r,p,ps,cs,d,now=NOW); assert x.decision is m.ControlDecision.DENY and 'REQUIRED_DEPENDENCY_FAILED' in x.reasons
    elif k==10:
        d=(replace(ds[0],completed=False),); x=m.evaluate(r,p,ps,cs,d,now=NOW); assert x.decision is m.ControlDecision.ALLOW and x.continue_candidate and 'DEPENDENCIES_PENDING' in x.reasons
    elif k==11:
        x=m.evaluate(r,p,ps,(cs[0],),ds,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'INSUFFICIENT_REQUIRED_CRITERIA' in x.reasons
    elif k==12:
        stale=tuple(replace(c,observed_at=NOW-5000,expires_at=NOW+10) for c in cs); x=m.evaluate(r,p,ps,stale,ds,now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==13:
        bad=(replace(ps[0],verified=False),); x=m.evaluate(r,p,bad,cs,ds,now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==14:
        bad=(replace(ps[0],independent=False),); x=m.evaluate(r,p,bad,cs,ds,now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==15:
        bad=(replace(ps[0],evidence_binding='BAD'),); x=m.evaluate(r,p,bad,cs,ds,now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==16:
        x=m.evaluate(replace(r,expected_policy_version='BAD'),p,ps,cs,ds,now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==17:
        reg=m.prepare_registry(p,ps,cs,ds,now=NOW); x=m.evaluate_prepared(r,p,replace(reg,registry_fingerprint='0'*64),now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==18:
        reg=m.prepare_registry(p,ps,cs,ds,now=NOW); x=m.evaluate_prepared(r,p,replace(reg,policy_fingerprint='0'*64),now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==19:
        reg=m.prepare_registry(p,ps,cs,ds,now=NOW); a=m.evaluate(r,p,ps,cs,ds,now=NOW); b=m.evaluate_prepared(r,p,reg,now=NOW); assert m.canonical_json(a)==m.canonical_json(b)
    elif k==20:
        p2=replace(ps[0],progress_id='PROG-2',task_id='TASK-2',scope_fingerprint='S2',evidence_binding='B2'); c2=replace(cs[0],criterion_id='CRIT-2',task_id='TASK-2',evidence_binding='B2'); d2=replace(ds[0],dependency_id='DEP-2',task_id='TASK-2',evidence_binding='B2'); delta=m.make_registry_delta(ps,cs,ds,ps+(p2,),cs+(c2,),ds+(d2,)); op,oc,od=m.apply_registry_delta(ps,cs,ds,delta); assert m.registry_fingerprint(op,oc,od)==m.registry_fingerprint(ps+(p2,),cs+(c2,),ds+(d2,))
    elif k==21:
        reg=m.prepare_registry(p,ps,cs,ds,now=NOW); plan=m.plan_registry_sync(ps,cs,ds,reg.progress_fingerprints,reg.criterion_fingerprints,reg.dependency_fingerprints); assert not plan.missing_or_changed_progress_ids and not plan.missing_or_changed_criterion_ids and not plan.missing_or_changed_dependency_ids and not plan.permission_granted
    elif k==22:
        reg=m.prepare_registry(p,ps,cs,ds,now=NOW); bad=dict(reg.criterion_fingerprints); bad['CRIT-060-A']='0'*64; plan=m.plan_registry_sync(ps,cs,ds,reg.progress_fingerprints,bad,reg.dependency_fingerprints); assert plan.missing_or_changed_criterion_ids==('CRIT-060-A',)
    elif k==23:
        src=inspect.getsource(m); forbidden=[r'\bsubprocess\b',r'os\.system',r'\bsocket\b',r'\brequests\b',r'\burllib\b',r'\bPopen\b',r'\.unlink\(',r'\bshutil\b',r'\bwebbrowser\b',r'\bsmtplib\b']; assert not any(re.search(x,src) for x in forbidden)
    elif k==24:
        x=m.evaluate(r,p,ps,cs,ds,now=NOW); assert not x.permission_granted and not x.task_success_committed and not x.stop_executed and not x.scope_expansion_committed and not x.cleanup_executed and not x.partial_state_authoritative and not x.success_truth_proven and not x.safety_proven and not x.action_success
    elif k==25:
        d=m.DependencyState('BAD','MISSING',True,False,False,True,True,NOW-1,NOW+10,'BIND'); x=m.evaluate(r,p,ps,cs,ds+(d,),now=NOW); assert x.decision is m.ControlDecision.HOLD and x.reasons[0].startswith('INVALID_REGISTRY:')
    elif k==26:
        prog2=replace(ps[0],progress_id='P2'); x=m.evaluate(r,p,ps+(prog2,),cs,ds,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'TASK_PROGRESS_NOT_UNIQUE' in x.reasons
    elif k==27:
        p2=replace(p,require_all_required_dependencies=False); d=(replace(ds[0],completed=False),); x=m.evaluate(r,p2,ps,cs,d,now=NOW); assert x.completion_candidate and x.decision is m.ControlDecision.ALLOW
    elif k==28:
        p2=replace(p,deny_scope_creep=False); x=m.evaluate(r,p2,(replace(ps[0],requested_extra_work=True),),cs,ds,now=NOW); assert x.completion_candidate and not x.scope_creep_detected
    elif k==29:
        dep=(replace(ds[0],verified=False),); x=m.evaluate(r,p,ps,cs,dep,now=NOW); assert x.decision is m.ControlDecision.HOLD and 'REQUIRED_DEPENDENCY_EVIDENCE_INVALID' in x.reasons
    elif k==30:
        c=(replace(cs[0],revoked=True),cs[1]); x=m.evaluate(r,p,ps,c,ds,now=NOW); assert x.decision is m.ControlDecision.HOLD
    elif k==31:
        p2=replace(ps[0],progress_id='P2',task_id='TASK-2',scope_fingerprint='S2',evidence_binding='B2'); c2=replace(cs[0],criterion_id='C2',task_id='TASK-2',evidence_binding='B2'); d2=replace(ds[0],dependency_id='D2',task_id='TASK-2',evidence_binding='B2'); delta=m.make_registry_delta(ps,cs,ds,ps+(p2,),cs+(c2,),ds+(d2,));
        try: m.apply_registry_delta((p2,),cs,ds,delta); assert False
        except ValueError: pass

for i in range(160):
    def make(n):
        def test(self): scenario(n)
        test.__name__=f'test_case_{n:03d}'; return test
    setattr(T,f'test_case_{i:03d}',make(i))
if __name__=='__main__': unittest.main(verbosity=1)
