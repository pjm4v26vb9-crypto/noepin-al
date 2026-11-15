import ast,json,pathlib
p=pathlib.Path(__file__).with_name('noepin_al_188_safety_suite_distribution.py'); s=p.read_text(); t=ast.parse(s)
banned_import={'subprocess','socket','requests','urllib','http','os'}; imports=[]; external=0; writes=0; mint=0
for n in ast.walk(t):
    if isinstance(n,ast.Import):
        roots=[x.name.split('.')[0] for x in n.names]; imports += roots; external += sum(x in banned_import for x in roots)
    elif isinstance(n,ast.ImportFrom) and n.module:
        root=n.module.split('.')[0]; imports.append(root); external += int(root in banned_import)
    elif isinstance(n,ast.Call):
        name=''
        if isinstance(n.func,ast.Name): name=n.func.id
        elif isinstance(n.func,ast.Attribute): name=n.func.attr
        if name in {'open','write_text','write_bytes','unlink','remove','rename','system','popen','urlopen'}: writes += 1
        if name in {'mint_token','mint_credential','grant_permission','issue_permit'}: mint += 1
out={'external_execution_paths':external,'unauthorized_write_paths':writes,'permission_token_credential_mint_paths':mint,'imports':imports}
print(json.dumps(out,sort_keys=True)); raise SystemExit(0 if external==0 and writes==0 and mint==0 else 2)
