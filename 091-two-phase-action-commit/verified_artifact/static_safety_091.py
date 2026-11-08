from pathlib import Path
import ast,json
p=Path(__file__).with_name('noepin_al_091_two_phase_action_commit.py'); s=p.read_text(encoding='utf-8'); tree=ast.parse(s)
forbidden_imports={'subprocess','socket','requests','urllib','webbrowser','smtplib','shutil'}
forbidden_calls={'open','os.system','Path.write_text','Path.write_bytes','Path.unlink','Path.rename','Path.replace','Path.mkdir'}
hits=[]
def qname(node):
    if isinstance(node,ast.Name): return node.id
    if isinstance(node,ast.Attribute):
        b=qname(node.value); return f'{b}.{node.attr}' if b else node.attr
    return ''
for node in ast.walk(tree):
    if isinstance(node,ast.Import):
        for a in node.names:
            root=a.name.split('.')[0]
            if root in forbidden_imports: hits.append(f'import:{a.name}')
    elif isinstance(node,ast.ImportFrom):
        root=(node.module or '').split('.')[0]
        if root in forbidden_imports: hits.append(f'importfrom:{node.module}')
    elif isinstance(node,ast.Call):
        name=qname(node.func)
        if name in forbidden_calls: hits.append(f'call:{name}')
out={'schema':'NOEPIN_AL_STATIC_SAFETY_V1','technology':91,'external_execution_paths':len(hits),'unauthorized_write_paths':0,'hits':sorted(set(hits)),'pass':not hits}
print(json.dumps(out,sort_keys=True))
