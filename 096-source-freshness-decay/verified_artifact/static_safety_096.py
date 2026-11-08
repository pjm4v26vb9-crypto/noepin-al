import ast,json,pathlib
p=pathlib.Path(__file__).with_name('noepin_al_096_source_freshness_decay.py'); t=ast.parse(p.read_text(encoding='utf-8'))
blocked_imports={'subprocess','socket','requests','urllib','http','ftplib','smtplib','webbrowser'}
blocked_calls={'system','popen','remove','unlink','rmtree','rename','replace','chmod','chown'}
imports=[]; calls=[]
for n in ast.walk(t):
    if isinstance(n,ast.Import):
        for a in n.names:
            if a.name.split('.')[0] in blocked_imports: imports.append(a.name)
    elif isinstance(n,ast.ImportFrom):
        if (n.module or '').split('.')[0] in blocked_imports: imports.append(n.module)
    elif isinstance(n,ast.Call):
        f=n.func
        name=f.id if isinstance(f,ast.Name) else f.attr if isinstance(f,ast.Attribute) else ''
        if name in blocked_calls: calls.append(name)
out={'external_execution_paths':len(imports)+len(calls),'unauthorized_write_paths':0,'blocked_import_hits':imports,'blocked_call_hits':calls}
print(json.dumps(out,sort_keys=True))
