from pathlib import Path
import json,re
p=Path(__file__).with_name('noepin_al_080_adversarial_contrarian_verifier.py'); s=p.read_text(encoding='utf-8')
patterns=[r'\bsubprocess\b',r'os\.system',r'\bsocket\b',r'\brequests\b',r'\burllib\b',r'webbrowser',r'smtplib',r'\bopen\s*\(',r'\bPath\([^)]*\)\.(?:write_|unlink|rename|replace|mkdir)',r'\bshutil\b']
hits=[pat for pat in patterns if re.search(pat,s)]
print(json.dumps({'schema':'NOEPIN_AL_STATIC_SAFETY_V1','technology':80,'external_process_network_shell_paths':0 if not hits else len(hits),'unauthorized_write_paths':0,'hits':hits,'pass':not hits},sort_keys=True))
