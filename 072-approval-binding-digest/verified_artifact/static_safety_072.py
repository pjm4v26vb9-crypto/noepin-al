from pathlib import Path
import ast,json,re
p=Path(__file__).with_name('noepin_al_072_approval_binding_digest.py'); t=p.read_text(encoding='utf-8'); tree=ast.parse(t)
forbidden_names={'subprocess','socket','requests','urllib','http','ftplib','smtplib'}
forbidden_calls={'system','popen','remove','unlink','rmtree','rename','replace_file'}
imports=[]; calls=[]
for n in ast.walk(tree):
    if isinstance(n,(ast.Import,ast.ImportFrom)):
        names=[a.name.split('.')[0] for a in n.names] if isinstance(n,ast.Import) else [(n.module or '').split('.')[0]]
        imports += [x for x in names if x in forbidden_names]
    if isinstance(n,ast.Call):
        f=n.func; name=f.id if isinstance(f,ast.Name) else (f.attr if isinstance(f,ast.Attribute) else '')
        if name in forbidden_calls: calls.append(name)
write_tokens=re.findall(r'\b(?:commit|deploy|publish|send|persist|grant|mint|issue_credential|execute_action)\s*\(',t)
out={'schema':'NOEPIN_AL_STATIC_SAFETY_V1','technology':72,'forbidden_imports':sorted(set(imports)),'forbidden_calls':sorted(set(calls)),'external_execution_paths':0 if not imports and not calls else len(set(imports+calls)),'unauthorized_write_paths':0 if not write_tokens else len(write_tokens),'pass':not imports and not calls and not write_tokens}
print(json.dumps(out,ensure_ascii=False,sort_keys=True))
