import hashlib,json
import noepin_al_187_security_gateway as m
items=[]
for run in range(3):
    rows=[]
    for i in range(1000):
        req=m.GatewayRequest(f'R{i}','agent-safe','key-safe-001',f'N{i}','tool.read','workspace://safe/item',(('mode','metadata'),),1_000_000+i)
        r=m.evaluate(req,m.default_policy(),m.default_dynamic())
        rows.append(m.fingerprint(r))
    items.append(rows)
div=sum(1 for i in range(1000) if len({items[r][i] for r in range(3)})!=1)
digest=hashlib.sha256(json.dumps(items[0],separators=(',',':')).encode()).hexdigest()
print(json.dumps({'runs':3000,'snapshots':1000,'divergence':div,'digest':digest},sort_keys=True))
raise SystemExit(0 if div==0 else 2)
