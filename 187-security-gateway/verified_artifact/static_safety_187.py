import ast,json,pathlib
p=pathlib.Path(__file__).with_name('noepin_al_187_security_gateway.py'); tree=ast.parse(p.read_text()); bad_calls=[]; bad_imports=[]; writes=[]; mint=[]
for n in ast.walk(tree):
    if isinstance(n,(ast.Import,ast.ImportFrom)):
        names=[a.name for a in n.names] if isinstance(n,ast.Import) else [n.module or '']
        for x in names:
            if x.split('.')[0] in {'os','subprocess','socket','requests','urllib','shutil','pathlib','webbrowser','smtplib','http','ssl'}: bad_imports.append(x)
    if isinstance(n,ast.Call):
        f=n.func; name=(f.id if isinstance(f,ast.Name) else (f.attr if isinstance(f,ast.Attribute) else ''))
        if name in {'system','popen','run','Popen','remove','unlink','rmtree','send','sendall','connect','request','urlopen'}: bad_calls.append(name)
        if name in {'write_text','write_bytes','open'}: writes.append(name)
        if name in {'issue_permit','mint_token','mint_credential','grant_permission','execute_action','invoke_tool'}: mint.append(name)
print(json.dumps({'external_execution_paths':len(bad_calls),'unauthorized_write_paths':len(writes),'permission_token_credential_mint_paths':len(mint),'bad_imports':bad_imports,'bad_calls':bad_calls,'write_calls':writes,'mint_calls':mint},sort_keys=True))
