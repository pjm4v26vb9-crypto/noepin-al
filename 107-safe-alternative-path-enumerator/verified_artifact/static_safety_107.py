import ast,json,pathlib
root=pathlib.Path(__file__).resolve().parent
bad_imports={'subprocess','socket','requests','urllib','http.client','ftplib','smtplib','webbrowser'}
bad_calls={'os.system','os.popen','subprocess.run','subprocess.Popen','subprocess.call','subprocess.check_call','subprocess.check_output'}
ext_paths=0; unauthorized=0; findings=[]
for p in [root/'noepin_al_107_safe_alternative_path_enumerator.py']:
    tree=ast.parse(p.read_text(encoding='utf-8'))
    for n in ast.walk(tree):
        if isinstance(n,(ast.Import,ast.ImportFrom)):
            names=[a.name for a in n.names] if isinstance(n,ast.Import) else [n.module or '']
            for name in names:
                if any(name==x or name.startswith(x+'.') for x in bad_imports): ext_paths+=1; findings.append(['import',name])
        if isinstance(n,ast.Call):
            f=n.func; name=''
            if isinstance(f,ast.Name): name=f.id
            elif isinstance(f,ast.Attribute) and isinstance(f.value,ast.Name): name=f.value.id+'.'+f.attr
            if name in bad_calls: ext_paths+=1; findings.append(['call',name])
out={'external_execution_paths':ext_paths,'unauthorized_write_paths':unauthorized,'findings':findings}
print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if ext_paths==0 and unauthorized==0 else 2)
