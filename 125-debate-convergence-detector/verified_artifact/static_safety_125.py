import ast,json
from pathlib import Path
p=Path(__file__).with_name('noepin_al_125_debate_convergence_detector.py'); tree=ast.parse(p.read_text())
blocked={'subprocess','socket','requests','urllib','browser','smtplib'}; calls=[]; writes=[]
for n in ast.walk(tree):
    if isinstance(n,(ast.Import,ast.ImportFrom)):
        names=[a.name.split('.')[0] for a in n.names] if isinstance(n,ast.Import) else [(n.module or '').split('.')[0]]
        calls += [x for x in names if x in blocked]
    if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in {'write_text','write_bytes','unlink','rmdir','rename','replace'}: writes.append(n.func.attr)
print(json.dumps({'external_execution_paths':len(calls),'unauthorized_write_paths':len(writes),'blocked_imports':calls,'write_calls':writes},sort_keys=True))
