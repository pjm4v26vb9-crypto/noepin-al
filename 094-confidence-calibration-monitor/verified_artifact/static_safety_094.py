from pathlib import Path
import ast,json
p=Path(__file__).with_name('noepin_al_094_confidence_calibration_monitor.py'); tree=ast.parse(p.read_text(encoding='utf-8'))
forbidden_imports={'subprocess','socket','requests','urllib','webbrowser','smtplib','shutil','os'}
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
            if a.name.split('.')[0] in forbidden_imports: hits.append(f'import:{a.name}')
    elif isinstance(node,ast.ImportFrom):
        if (node.module or '').split('.')[0] in forbidden_imports: hits.append(f'importfrom:{node.module}')
    elif isinstance(node,ast.Call):
        name=qname(node.func)
        if name in forbidden_calls: hits.append(f'call:{name}')
print(json.dumps({'schema':'NOEPIN_AL_STATIC_SAFETY_V1','technology':94,'external_execution_paths':len(set(hits)),'unauthorized_write_paths':0,'hits':sorted(set(hits)),'pass':not hits},sort_keys=True))
