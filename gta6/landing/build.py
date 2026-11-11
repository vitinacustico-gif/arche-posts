import json, re
A=json.load(open('/home/claude/lp2/assets.json'))
t=open('/home/claude/lp2/template.html',encoding='utf-8').read()
old=open('/home/claude/lp2/template_v1.html',encoding='utf-8').read()
svg='<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 3.2c-4.9 0-8.8 3.5-8.8 7.9 0 2.3 1.1 4.4 2.9 5.9L5.4 21l4.3-2.1c.7.2 1.5.3 2.3.3 4.9 0 8.8-3.5 8.8-7.9S16.9 3.2 12 3.2z"/></svg>'
h=t
for k in ['hero1','hero2','hero3','vip','guia','setup']: h=h.replace('{{%s}}'%k.upper(),A[k])
h=h.replace('{{GAL}}',json.dumps(A['gal'])).replace('{{PERS}}',json.dumps(A['pers']))
for k,v in A.items():
    if isinstance(v,dict): h=h.replace('{{T_%s}}'%k,v['b'])
h=h.replace('rel="noopener">Votar no meu favorito','rel="noopener">{{WA}}Votar no meu favorito').replace('{{WA}}',svg)
falta=set(re.findall(r'{{[A-Za-z_]+}}',h)); assert not falta, falta
open('/home/claude/lp2/NERDGTA.html','w',encoding='utf-8').write(h); print(len(h)//1024,'KB')
