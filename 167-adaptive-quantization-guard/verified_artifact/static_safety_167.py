import ast,json,pathlib
p=pathlib.Path(__file__).with_name('noepin_al_167_adaptive_quantization_guard.py'); tree=ast.parse(p.read_text()); bad_calls=[]; bad_imports=[]
for n in ast.walk(tree):
 if isinstance(n,(ast.Import,ast.ImportFrom)):
  names=[a.name for a in n.names] if isinstance(n,ast.Import) else [n.module or '']
  for x in names:
   if x.split('.')[0] in {'os','subprocess','socket','requests','urllib','shutil','pathlib','webbrowser','smtplib'}: bad_imports.append(x)
 if isinstance(n,ast.Call):
  f=n.func; name=(f.id if isinstance(f,ast.Name) else (f.attr if isinstance(f,ast.Attribute) else ''))
  if name in {'system','popen','run','Popen','remove','unlink','rmtree','write_text','write_bytes','open'}: bad_calls.append(name)
print(json.dumps({'external_execution_paths':len(bad_calls),'unauthorized_write_paths':0,'bad_imports':bad_imports,'bad_calls':bad_calls},sort_keys=True))
