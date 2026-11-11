t=open('/home/claude/lp2/template.html',encoding='utf-8').read()
obrig=[(':root{--bg:#0B0410;--card:#160921;--card2:#22102F;--mag:#FF2E88;--rosa:#FF5FA2;--ama:#FFE66D;--lar:#FFB347;--cia:#2EF2FF;--sub:#E9D7F3;--wa:#25D366}',
    ':root{--bg:#050505;--card:#0f0f0f;--card2:#181818;--mag:#E5152D;--rosa:#FF3347;--ama:#FFFFFF;--lar:#7A0A15;--cia:#E5152D;--sub:#CFCFCF;--wa:#25D366}'),
   ('family=Inter:wght@400;700;900','family=Space+Grotesk:wght@400;500;700&family=Space+Mono:wght@700'),
   ("font-family:Inter,system-ui","font-family:'Space Grotesk',system-ui"),
   ('<title>Nerd GTA · GTA 6 em português</title>','<title>Nerd GTA · GTA 6 em português · uma extensão Arche Agência</title>'),
   ('<span class="fan">Página de fã</span>','<a class="fan arche" href="https://archeagencia.com.br" target="_blank" rel="noopener">Uma extensão <b>ARCHE</b></a>')]
for a,b in obrig:
    assert a in t, a[:50]; t=t.replace(a,b)
for a,b in [('rgba(11,4,16','rgba(5,5,5'),('rgba(255,46,136','rgba(229,21,45'),('rgba(255,95,162','rgba(255,51,71'),('rgba(22,9,33','rgba(16,16,16'),
   ('#12051f','#050505'),('#ff2e88','#E5152D'),('#FF2E88','#E5152D'),('#FF5FA2','#FF3347'),('#FFE66D','#FFFFFF'),('#FFB347','#7A0A15'),
   ('#E9D7F3','#CFCFCF'),('#3b0c47','#2a0508'),('#2a0d3d','#160204'),('#2EF2FF','#E5152D'),('#22102F','#181818'),('#160921','#0f0f0f'),
   ('#0B0410','#050505'),('#ffd34d','#E5152D'),(' Inter,sans-serif'," 'Space Grotesk',sans-serif")]:
    t=t.replace(a,b)
css='''/* identidade Arche */
.cd b{color:var(--mag)}
.fan.arche{color:#fff;text-decoration:none;opacity:1;font-family:'Space Mono',monospace;border:1px solid rgba(255,255,255,.25);padding:6px 10px;border-radius:4px}
.fan.arche b{color:var(--mag)}
.cdlabel,.faseband,.ideal h4,.selo,.tagm{font-family:'Space Mono',monospace}
.selo,.prod .tagm{color:#050505}
.btn,.tabs button,.chips button,.perg input,.perg button,.msg a.mini,.prod a,.selo{border-radius:6px!important}
.card,.prod,.gal figure,.pers figure,.foto,.banner{border-radius:10px!important}
.arche-ext{margin:40px auto 0;max-width:560px;border:1px solid rgba(229,21,45,.5);border-radius:10px;padding:26px 22px;text-align:center;background:linear-gradient(180deg,rgba(229,21,45,.12),transparent)}
.arche-ext .marca{font:700 26px 'Space Grotesk',sans-serif;letter-spacing:.04em}
.arche-ext .marca b{color:var(--mag)}
.arche-ext .tag{font:700 11px 'Space Mono',monospace;letter-spacing:.18em;text-transform:uppercase;color:var(--sub);margin:4px 0 14px}
.arche-ext p{color:var(--sub);font-size:15px;margin-bottom:16px}
.btn.arche-btn{background:var(--mag);color:#fff;box-shadow:0 10px 30px rgba(229,21,45,.35)}
footer{opacity:1}footer>div>p{opacity:.6}
/* barra fixa */'''
t=t.replace('/* barra fixa */',css,1).replace('footer{padding:44px 0 110px;text-align:center;font-size:12px;opacity:.6}','footer{padding:44px 0 110px;text-align:center;font-size:12px}footer p{opacity:.6}')
t=t.replace('<footer><div class="wrap">','''<footer><div class="wrap">
  <div class="arche-ext">
    <div class="marca">ARCHE <b>AGÊNCIA</b></div>
    <div class="tag">Vendas &amp; Growth Marketing</div>
    <p>O Nerd GTA é uma extensão da Arche. Quer uma página assim, que vende sozinha, pro seu negócio?</p>
    <a class="btn arche-btn" id="archeBtn" href="#" target="_blank" rel="noopener">Falar com a Arche no WhatsApp</a>
  </div>''',1)
a='''  $("ano").textContent = new Date().getFullYear();'''
assert a in t
t=t.replace(a,a+'''
  $("archeBtn").href = wa("Vi a página do Nerd GTA e quero uma página assim pro meu negócio!");''',1)
open('/home/claude/lp2/template_arche.html','w',encoding='utf-8').write(t)
