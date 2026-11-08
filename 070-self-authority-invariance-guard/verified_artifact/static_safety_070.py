from pathlib import Path
import ast,json
p=Path(__file__).with_name("noepin_al_070_self_authority_invariance_guard.py"); src=p.read_text(encoding="utf-8"); t=ast.parse(src)
forbidden_imports={"subprocess","socket","requests","urllib","http","ftplib","smtplib","webbrowser"}
forbidden_calls={"system","popen","remove","unlink","rmtree","rename","replace_file","write_text","write_bytes","open"}
imports=[]; calls=[]
for n in ast.walk(t):
    if isinstance(n,ast.Import): imports += [x.name.split(".")[0] for x in n.names if x.name.split(".")[0] in forbidden_imports]
    elif isinstance(n,ast.ImportFrom) and (n.module or "").split(".")[0] in forbidden_imports: imports.append((n.module or "").split(".")[0])
    elif isinstance(n,ast.Call):
        f=n.func; name=f.attr if isinstance(f,ast.Attribute) else f.id if isinstance(f,ast.Name) else ""
        if name in forbidden_calls: calls.append(name)
out={"schema":"NOEPIN_AL_STATIC_SAFETY_V1","technology":70,"forbidden_imports":sorted(set(imports)),"forbidden_calls":sorted(set(calls)),"external_process_network_shell_external_fs_mutation_paths":0 if not imports and not calls else len(imports)+len(calls),"unauthorized_write_paths":0 if not calls else len(calls),"pass":not imports and not calls}
print(json.dumps(out,sort_keys=True))
