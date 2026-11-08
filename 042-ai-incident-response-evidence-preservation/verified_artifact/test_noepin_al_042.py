from __future__ import annotations
import ast
from dataclasses import replace
from pathlib import Path
import unittest

import noepin_al_042_incident_evidence as m

NOW = 1_800_000_000
REQUIRED = [
    m.EvidenceType.LOG,
    m.EvidenceType.INPUT,
    m.EvidenceType.AUTHORITY_STATE,
    m.EvidenceType.NETWORK_STATE,
    m.EvidenceType.CHANGE_DELTA,
]


def mk_state(*, omit=None, classification="INTERNAL", offset=0, integrity=True, extra=0):
    incident_id="INC-042-DEMO"; binding="INC-042-EVIDENCE-BINDING"
    items=[]; prev=""; seq=0
    for i, et in enumerate(REQUIRED):
        if et == omit:
            continue
        seg=m.build_segment(
            segment_id=f"S{seq}", incident_id=incident_id, evidence_type=et,
            captured_at=NOW-10+i+offset, source_id=f"SRC-{i}", source_version="1",
            classification=classification, payload=f"payload-{et.value}".encode(),
            sequence=seq, previous_segment_fingerprint=prev,
            evidence_binding=binding, integrity_verified=integrity,
        )
        items.append(seg); prev=m.segment_fingerprint(seg); seq+=1
    for j in range(extra):
        seg=m.build_segment(
            segment_id=f"X{j}", incident_id=incident_id, evidence_type=m.EvidenceType.OTHER,
            captured_at=NOW-3+offset, source_id=f"EXTRA-{j}", source_version="1",
            classification=classification, payload=f"extra-{j}".encode(),
            sequence=seq, previous_segment_fingerprint=prev,
            evidence_binding=binding, integrity_verified=integrity,
        )
        items.append(seg); prev=m.segment_fingerprint(seg); seq+=1
    return m.IncidentState(incident_id,"1",1,binding,tuple(items))


def req(*, severity=m.IncidentSeverity.HIGH, review=True):
    p=m.default_policy(NOW); s=mk_state()
    return m.IncidentRequest(s.incident_id,"NOEPIN",NOW,severity,"anomaly",p.policy_id,p.version,p.authority_epoch,s.evidence_binding,review)


def rebuild_state(state, payload_suffix="", change_last=0, remove_last=0, add=0, version="2"):
    source=list(state.segments)
    if remove_last:
        source=source[:-remove_last]
    specs=[]
    for idx, old in enumerate(source):
        changed = idx >= max(0, len(source)-change_last)
        payload=(old.content_sha256 + (payload_suffix if changed else "")).encode()
        specs.append((old.segment_id,old.evidence_type,old.captured_at,old.source_id,old.source_version,old.classification,payload,old.integrity_verified))
    for j in range(add):
        specs.append((f"ADD{j}",m.EvidenceType.OTHER,NOW,f"ADD-SRC-{j}","1","INTERNAL",f"add-{j}".encode(),True))
    items=[]; prev=""
    for seq,spec in enumerate(specs):
        sid,et,captured,src,sv,cl,payload,iv=spec
        seg=m.build_segment(segment_id=sid,incident_id=state.incident_id,evidence_type=et,captured_at=captured,source_id=src,source_version=sv,classification=cl,payload=payload,sequence=seq,previous_segment_fingerprint=prev,evidence_binding=state.evidence_binding,integrity_verified=iv)
        items.append(seg); prev=m.segment_fingerprint(seg)
    return m.IncidentState(state.incident_id,version,state.authority_epoch,state.evidence_binding,tuple(items))


class GeneratedTests(unittest.TestCase):
    pass


def make_test(i):
    def test(self):
        p=m.default_policy(NOW)
        # 0-15: normal decision and containment boundaries
        if i < 16:
            sev=list(m.IncidentSeverity)[i % 4]
            review=bool((i//4)%2)
            classification="RESTRICTED" if i>=8 else "INTERNAL"
            s=mk_state(classification=classification)
            r=req(severity=sev,review=review)
            a=m.assess(r,p,s,now=NOW)
            self.assertTrue(a.integrity_chain_valid)
            self.assertTrue(a.preservation_complete_candidate)
            self.assertEqual(a.decision, m.ControlDecision.HUMAN_APPROVAL if classification=="RESTRICTED" else m.ControlDecision.ALLOW)
            if not review:
                self.assertEqual(a.containment_candidate,m.ContainmentCandidate.NONE)
            self.assertFalse(a.evidence_preserved); self.assertFalse(a.persistence_performed); self.assertFalse(a.containment_executed)
        # 16-31: missing required evidence -> HOLD
        elif i < 32:
            et=REQUIRED[(i-16)%len(REQUIRED)]
            s=mk_state(omit=et)
            a=m.assess(req(severity=list(m.IncidentSeverity)[(i-16)%4]),p,s,now=NOW)
            self.assertEqual(a.decision,m.ControlDecision.HOLD)
            self.assertIn(et,a.missing_evidence_types)
            self.assertFalse(a.preservation_complete_candidate)
        # 32-47: version/authority/binding mismatches fail closed
        elif i < 48:
            s=mk_state(); r=req(); j=(i-32)%4
            if j==0: r=replace(r,expected_policy_id="WRONG")
            elif j==1: r=replace(r,expected_policy_version="WRONG")
            elif j==2: r=replace(r,expected_authority_epoch=99)
            else: r=replace(r,evidence_binding="WRONG")
            a=m.assess(r,p,s,now=NOW)
            self.assertEqual(a.decision,m.ControlDecision.HOLD)
            self.assertFalse(a.permission_granted); self.assertFalse(a.action_success)
        # 48-63: integrity chain tamper / invalidity
        elif i < 64:
            s=mk_state(); items=list(s.segments); j=(i-48)%4
            if j==0: items[2]=replace(items[2],previous_segment_fingerprint="0"*64)
            elif j==1: items[2]=replace(items[2],integrity_verified=False)
            elif j==2: items[2]=replace(items[2],sequence=8)
            else: items[2]=replace(items[2],evidence_binding="WRONG")
            bad=replace(s,segments=tuple(items))
            a=m.assess(req(),p,bad,now=NOW)
            self.assertEqual(a.decision,m.ControlDecision.HOLD)
            self.assertFalse(a.truth_proven)
        # 64-79: classification/timing policy boundaries
        elif i < 80:
            j=(i-64)%4
            if j==0:
                a=m.assess(req(),p,mk_state(classification="PUBLIC"),now=NOW); self.assertEqual(a.decision,m.ControlDecision.DENY)
            elif j==1:
                a=m.assess(req(),p,mk_state(offset=-(p.max_evidence_age_seconds+100)),now=NOW); self.assertEqual(a.decision,m.ControlDecision.HOLD)
            elif j==2:
                a=m.assess(req(),p,mk_state(offset=p.max_future_skew_seconds+1000),now=NOW); self.assertEqual(a.decision,m.ControlDecision.HOLD)
            else:
                a=m.assess(req(),p,mk_state(classification="RESTRICTED"),now=NOW); self.assertEqual(a.decision,m.ControlDecision.HUMAN_APPROVAL)
        # 80-95: delta reconstruction exactness and tamper rejection
        elif i < 96:
            base=mk_state(extra=8)
            target=rebuild_state(base,payload_suffix=f"-{i}",change_last=1+(i%4),remove_last=(i%2),add=(i%3),version=f"v{i}")
            d=m.make_evidence_delta(base,target)
            out=m.apply_evidence_delta(base,d)
            self.assertEqual(m.fingerprint(out),m.fingerprint(m.normalize_state(target)))
            if i%4==0:
                bad=replace(d,base_fingerprint="f"*64)
                with self.assertRaises(ValueError): m.apply_evidence_delta(base,bad)
        # 96-111: transfer planning sends only unknown fingerprints
        elif i < 112:
            s=mk_state(extra=12); pr=m.prepare_state(s); fps=list(pr.segment_fingerprints.values()); n=(i-96)%len(fps)
            known=frozenset(fps[:n]); plan=m.plan_evidence_transfer(pr,known)
            self.assertEqual(len(plan.already_known_segment_ids),n)
            self.assertEqual(len(plan.missing_segment_ids),len(fps)-n)
            self.assertFalse(plan.full_resend_required)
            self.assertEqual(plan.transfer_required,bool(len(fps)-n))
        # 112-127: determinism/canonical ordering
        elif i < 128:
            s=mk_state(extra=5); rev=replace(s,segments=tuple(reversed(s.segments)))
            n1=m.normalize_state(s); n2=m.normalize_state(rev)
            self.assertEqual(m.fingerprint(n1),m.fingerprint(n2))
            a1=m.assess(req(),p,s,now=NOW); a2=m.assess(req(),p,rev,now=NOW)
            self.assertEqual(a1.bundle_fingerprint,a2.bundle_fingerprint)
            self.assertEqual(m.assessment_digest((a1,a2)),m.assessment_digest((a1,a2)))
        # 128-143: static safety / provenance / no authority promotion
        elif i < 144:
            src=Path(m.__file__).read_text(encoding="utf-8"); tree=ast.parse(src); j=i-128
            forbidden_modules=["subprocess","socket","requests","urllib","shutil","webbrowser","ftplib","smtplib"]
            forbidden_calls=["system","popen","unlink","remove","rmtree","send","sendall","connect","execute"]
            if j < len(forbidden_modules):
                imports=[]
                for node in ast.walk(tree):
                    if isinstance(node,ast.Import): imports.extend(a.name.split('.')[0] for a in node.names)
                    if isinstance(node,ast.ImportFrom) and node.module: imports.append(node.module.split('.')[0])
                self.assertNotIn(forbidden_modules[j],imports)
            else:
                callnames=[]
                for node in ast.walk(tree):
                    if isinstance(node,ast.Call):
                        f=node.func
                        if isinstance(f,ast.Name): callnames.append(f.id)
                        elif isinstance(f,ast.Attribute): callnames.append(f.attr)
                self.assertNotIn(forbidden_calls[j-len(forbidden_modules)],callnames)
            self.assertEqual(m.CREATOR,"NOEPIN / のえぴん"); self.assertEqual(m.LICENSE_STATUS,"NOT SPECIFIED")
        # 144-159: validation + immutable authority flags
        else:
            j=(i-144)%8
            s=mk_state(); r=req(); a=m.assess(r,p,s,now=NOW)
            self.assertFalse(a.evidence_preserved); self.assertFalse(a.persistence_performed); self.assertFalse(a.incident_resolved)
            self.assertFalse(a.truth_proven); self.assertFalse(a.permission_granted); self.assertFalse(a.action_success)
            if j==0:
                with self.assertRaises(ValueError): replace(r,incident_id="").validate()
            elif j==1:
                with self.assertRaises(ValueError): replace(p,authority_epoch=0).validate(NOW)
            elif j==2:
                with self.assertRaises(ValueError): replace(p,expires_at=p.issued_at).validate(NOW)
            elif j==3:
                with self.assertRaises(ValueError): replace(s,authority_epoch=0).validate()
            elif j==4:
                bad=replace(s.segments[0],content_sha256="x")
                with self.assertRaises(ValueError): bad.validate()
            elif j==5:
                first=replace(s.segments[0],previous_segment_fingerprint="f"*64)
                with self.assertRaises(ValueError): first.validate()
            elif j==6:
                self.assertEqual(m.content_digest(b"abc"),"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad")
            else:
                self.assertEqual(m.default_request(NOW).expected_policy_id,p.policy_id)
    return test


for _i in range(160):
    setattr(GeneratedTests, f"test_{_i:03d}", make_test(_i))


if __name__ == "__main__":
    unittest.main(verbosity=1)
