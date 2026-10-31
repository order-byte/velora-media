import json, sys
S=sys.argv[1]
starts=[13-64.5,13,78,142,207,271]
fm={}; uniq={}
for f in range(316):
    s=max(x for x in starts if x<=f)
    off=f-s; name=f"{off:05.1f}".replace('.','_')
    fm[f]=name; uniq[name]=off/30
json.dump(fm,open(f'{S}/framemap.json','w'))
json.dump([{'name':k,'u':v} for k,v in sorted(uniq.items())],open(f'{S}/ulist.json','w'))
print(len(uniq))
