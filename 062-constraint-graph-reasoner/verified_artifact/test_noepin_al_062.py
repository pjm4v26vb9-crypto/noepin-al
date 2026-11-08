from __future__ import annotations
import inspect,re,unittest
from dataclasses import replace
import noepin_al_062_constraint_graph_reasoner as m
NOW=1_800_000_000

def base():
    p=m.default_policy(NOW); g=m.default_graph(NOW,p); r=m.default_request(NOW,p); return p,g,r

def nmap(g): return {n.node_id:n for n in g.nodes}
def emap(g): return {e.edge_id:e for e in g.edges}
def with_node(g,nid,**kw):
    ns=tuple(replace(n,**kw) if n.node_id==nid else n for n in g.nodes); return replace(g,nodes=ns)
def with_edge(g,eid,**kw):
    es=tuple(replace(e,**kw) if e.edge_id==eid else e for e in g.edges); return replace(g,edges=es)
def add_node(g,n): return replace(g,nodes=g.nodes+(n,))
def add_edge(g,e): return replace(g,edges=g.edges+(e,))

def scenario(i):
    p,g,r=base(); k=i%32
    if k==0:
        x=m.evaluate(r,p,g,now=NOW); assert x.decision is m.Decision.ALLOW and x.next_gate_candidate and x.candidate_path==('ACTION','TARGET','GOAL')
    elif k==1:
        x=m.evaluate(r,p,with_node(g,'SCOPE',state=m.NodeState.UNSATISFIED),now=NOW); assert x.decision is m.Decision.DENY
    elif k==2:
        x=m.evaluate(r,p,with_node(g,'AUTH',state=m.NodeState.UNSATISFIED),now=NOW); assert x.decision is m.Decision.DENY
    elif k==3:
        x=m.evaluate(r,p,with_node(g,'SAFE',state=m.NodeState.UNSATISFIED),now=NOW); assert x.decision is m.Decision.DENY
    elif k==4:
        x=m.evaluate(r,p,with_node(g,'PRE',state=m.NodeState.UNKNOWN),now=NOW); assert x.decision is m.Decision.HOLD and 'PRE' in x.unsatisfied
    elif k==5:
        x=m.evaluate(r,p,replace(g,complete=False),now=NOW); assert x.decision is m.Decision.HOLD
    elif k==6:
        bad=replace(g,edges=g.edges+(m.ConstraintEdge('BAD','ACTION','MISSING',m.EdgeKind.REQUIRES,False,True,False,g.binding),)); x=m.evaluate(r,p,bad,now=NOW); assert x.decision is m.Decision.HOLD
    elif k==7:
        x=m.evaluate(replace(r,expected_policy_version='OLD'),p,g,now=NOW); assert x.decision is m.Decision.HOLD
    elif k==8:
        x=m.evaluate(replace(r,expected_authority_epoch='OLD'),p,g,now=NOW); assert x.decision is m.Decision.HOLD
    elif k==9:
        x=m.evaluate(replace(r,expires_at=NOW-1),p,g,now=NOW); assert x.decision is m.Decision.HOLD
    elif k==10:
        x=m.evaluate(r,p,with_node(g,'PRE',verified=False),now=NOW); assert x.decision is m.Decision.HOLD
    elif k==11:
        x=m.evaluate(r,p,with_node(g,'PRE',revoked=True),now=NOW); assert x.decision is m.Decision.HOLD
    elif k==12:
        x=m.evaluate(r,p,with_node(g,'PRE',binding='WRONG'),now=NOW); assert x.decision is m.Decision.HOLD
    elif k==13:
        x=m.evaluate(r,p,with_edge(g,'E1',verified=False),now=NOW); assert x.decision is m.Decision.HOLD
    elif k==14:
        e=m.ConstraintEdge('F','ACTION','TARGET',m.EdgeKind.FORBIDS,True,True,False,g.binding); x=m.evaluate(r,p,add_edge(g,e),now=NOW); assert x.decision is m.Decision.DENY and 'F' in x.violations
    elif k==15:
        e=m.ConstraintEdge('C','ACTION','TARGET',m.EdgeKind.CONFLICTS,True,True,False,g.binding); x=m.evaluate(r,p,add_edge(g,e),now=NOW); assert x.decision is m.Decision.DENY and x.conflict_set
    elif k==16:
        # unresolved dependency cycle ACTION <-> PRE
        e=m.ConstraintEdge('CY','PRE','ACTION',m.EdgeKind.REQUIRES,False,True,False,g.binding); x=m.evaluate(r,p,add_edge(g,e),now=NOW); assert x.decision is m.Decision.HOLD and x.unresolved_cycles
    elif k==17:
        gg=with_node(g,'ACTION',cycle_resolved=True); gg=with_node(gg,'PRE',cycle_resolved=True); gg=add_edge(gg,m.ConstraintEdge('CY','PRE','ACTION',m.EdgeKind.REQUIRES,False,True,False,g.binding)); x=m.evaluate(r,p,gg,now=NOW); assert x.decision is m.Decision.ALLOW
    elif k==18:
        ap=m.ConstraintNode('APP',m.NodeKind.APPROVAL,m.NodeState.UNKNOWN,False,True,False,g.binding,p.policy_id,p.version,p.authority_epoch,NOW-1,NOW+100,5,False,'OWNER approval'); gg=add_node(g,ap); gg=add_edge(gg,m.ConstraintEdge('APR','ACTION','APP',m.EdgeKind.APPROVAL_REQUIRED,False,True,False,g.binding)); x=m.evaluate(r,p,gg,now=NOW); assert x.decision is m.Decision.HUMAN_APPROVAL and x.approval_required
    elif k==19:
        ap=m.ConstraintNode('APP',m.NodeKind.APPROVAL,m.NodeState.SATISFIED,False,True,False,g.binding,p.policy_id,p.version,p.authority_epoch,NOW-1,NOW+100,5,False,'OWNER approval'); gg=add_node(g,ap); gg=add_edge(gg,m.ConstraintEdge('APR','ACTION','APP',m.EdgeKind.APPROVAL_REQUIRED,False,True,False,g.binding)); x=m.evaluate(r,p,gg,now=NOW); assert x.decision is m.Decision.ALLOW and not x.approval_executed
    elif k==20:
        x=m.evaluate(replace(r,high_risk=True),p,g,now=NOW); assert x.decision is m.Decision.HUMAN_APPROVAL
    elif k==21:
        gg=replace(g,edges=tuple(e for e in g.edges if e.edge_id in ('E1','E2','E3','E6'))); x=m.evaluate(r,p,gg,now=NOW); assert x.decision is m.Decision.HOLD and not x.candidate_path
    elif k==22:
        reg=m.prepare_graph(p,g,now=NOW); assert m.validate_prepared_state(reg); x=m.evaluate_prepared(r,p,reg,current_graph_fingerprint=m.graph_fingerprint(g),now=NOW); y=m.evaluate(r,p,g,now=NOW); assert m.canonical_json(x)==m.canonical_json(y)
    elif k==23:
        reg=m.prepare_graph(p,g,now=NOW); bad=replace(reg,graph=replace(reg.graph,graph_id='TAMPERED')); assert not m.validate_prepared_state(bad); x=m.evaluate_prepared(r,p,reg,current_graph_fingerprint='0'*64,now=NOW); assert x.decision is m.Decision.HOLD
    elif k==24:
        reg=m.prepare_graph(p,g,now=NOW); pp=replace(p,version='X'); x=m.evaluate_prepared(r,pp,reg,current_graph_fingerprint=m.graph_fingerprint(g),now=NOW); assert x.decision is m.Decision.HOLD
    elif k==25:
        t=with_node(g,'PRE',label='changed'); d=m.make_graph_delta(g,t); z=m.apply_graph_delta(g,d); assert m.graph_fingerprint(z)==m.graph_fingerprint(t) and d.changed_nodes
    elif k==26:
        iso=m.ConstraintNode('ISO',m.NodeKind.CONSTRAINT,m.NodeState.SATISFIED,False,True,False,g.binding,p.policy_id,p.version,p.authority_epoch,NOW-1,NOW+100); t=add_node(g,iso); d=m.make_graph_delta(g,t); z=m.apply_graph_delta(g,d); assert any(n.node_id=='ISO' for n in z.nodes) and d.added_nodes
    elif k==27:
        iso=m.ConstraintNode('ISO',m.NodeKind.CONSTRAINT,m.NodeState.SATISFIED,False,True,False,g.binding,p.policy_id,p.version,p.authority_epoch,NOW-1,NOW+100); b=add_node(g,iso); t=replace(b,nodes=tuple(n for n in b.nodes if n.node_id!='ISO')); d=m.make_graph_delta(b,t); z=m.apply_graph_delta(b,d); assert all(n.node_id!='ISO' for n in z.nodes) and d.removed_node_ids==('ISO',)
    elif k==28:
        t=with_node(g,'PRE',label='changed'); d=m.make_graph_delta(g,t)
        try: m.apply_graph_delta(replace(g,graph_id='OTHER'),d); assert False
        except ValueError as e: assert 'DELTA_WRONG_BASE' in str(e)
    elif k==29:
        reg=m.prepare_graph(p,g,now=NOW); plan=m.plan_graph_sync(g,dict(reg.node_fingerprints),dict(reg.edge_fingerprints)); assert not plan.missing_or_changed_node_ids and not plan.missing_or_changed_edge_ids and not plan.full_resend_required
    elif k==30:
        reg=m.prepare_graph(p,g,now=NOW); rn=dict(reg.node_fingerprints); rn['PRE']='0'*64; plan=m.plan_graph_sync(g,rn,dict(reg.edge_fingerprints)); assert plan.missing_or_changed_node_ids==('PRE',) and not plan.permission_granted and not plan.action_execution_authorized
    elif k==31:
        src=inspect.getsource(m); forbidden=[r'\bsubprocess\b',r'os\.system',r'\bsocket\b',r'\brequests\b',r'\burllib\b',r'\bPopen\b',r'\.unlink\(',r'\bshutil\b',r'\bwebbrowser\b',r'\bsmtplib\b',r'\bopen\(']; assert not any(re.search(z,src) for z in forbidden); x=m.evaluate(r,p,g,now=NOW); assert not x.permission_granted and not x.action_executed and not x.commit_performed and not x.approval_executed and not x.constraint_truth_proven and not x.graph_truth_proven and not x.world_fact_proven and not x.safety_proven and not x.action_success

class T(unittest.TestCase): pass
for i in range(160):
    def make(n):
        def test(self): scenario(n)
        test.__name__=f'test_case_{n:03d}'; return test
    setattr(T,f'test_case_{i:03d}',make(i))
if __name__=='__main__': unittest.main(verbosity=1)
