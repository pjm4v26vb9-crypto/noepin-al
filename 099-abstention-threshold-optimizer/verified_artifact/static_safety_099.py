import ast,json,pathlib
p=pathlib.Path(__file__).with_name('noepin_al_099_abstention_threshold_optimizer.py'); t=ast.parse(p.read_text(encoding='utf-8'))
forbidden_imports={'subprocess','socket','requests','urllib','http.client','ftplib','smtplib','webbrowser'}
forbidden_calls={'system','popen','spawn','exec','eval','compile','remove','unlink','rmdir','rmtree'}
external=[]; writes=[]
for n in ast.walk(t):
    if isinstance(n,(ast.Import,ast.ImportFrom)):
        names=[x.name for x in n.names] if isinstance(n,ast.Import) else [n.module or '']
        for x in names:
            if any(x==f or x.startswith(f+'.') for f in forbidden_imports): external.append(f'import:{x}')
    if isinstance(n,ast.Call):
        fn=''
        if isinstance(n.func,ast.Name): fn=n.func.id
        elif isinstance(n.func,ast.Attribute): fn=n.func.attr
        if fn in forbidden_calls: external.append(f'call:{fn}')
        if fn in {'write_text','write_bytes','open'}: writes.append(f'call:{fn}')
print(json.dumps({'external_execution_paths':len(external),'unauthorized_write_paths':len(writes),'external_details':external,'write_details':writes},sort_keys=True))
