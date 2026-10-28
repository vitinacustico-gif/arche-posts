# -*- coding: utf-8 -*-
"""Modelos HTML (1080x1440) dos 3 formatos diários: DIA (data do dia), MASC (mascote + banco de imagens), PRINT."""
import os, json, html, itertools
from mascote import mascote, emoji
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, ".."))
F = "file://" + RAIZ + "/ex/fonts/"
LOGO = "file://" + RAIZ + "/ex/logo.png"
AVATAR = "file://" + RAIZ + "/ex/avatar.png"
BANCO = RAIZ + "/banco/"
IDX = json.load(open(RAIZ + "/banco_index.json"))
GRUPO = {}
for g, i in IDX:
    GRUPO.setdefault(g, []).append(i)
_uso = {}

def foto(grupo, salto=0):
    """devolve URL de uma foto do grupo, girando para não repetir em sequência"""
    lista = GRUPO.get(grupo) or GRUPO["final"]
    n = _uso.get(grupo, 0) + salto
    _uso[grupo] = n + 1
    return "file://" + BANCO + f"{lista[n % len(lista)]}.jpg"

def e(t):
    """escapa e permite *destaque* (vermelho) e quebra de linha com |"""
    t = html.escape(t)
    out, on = "", False
    for ch in t:
        if ch == "*":
            out += "</em>" if on else "<em>"; on = not on
        else:
            out += ch
    return out.replace("|", "<br>")

CSS_BASE = f"""
@font-face{{font-family:Hwt;src:url({F}hwt.woff2)}}
@font-face{{font-family:SG;font-weight:500;src:url({F}sg500.woff2)}}
@font-face{{font-family:SG;font-weight:700;src:url({F}sg700.woff2)}}
@font-face{{font-family:SM;font-weight:700;src:url({F}sm700.woff2)}}
@font-face{{font-family:Inter;font-weight:400;src:url({F}inter-latin-400-normal.woff2)}}
@font-face{{font-family:Inter;font-weight:500;src:url({F}inter-latin-500-normal.woff2)}}
@font-face{{font-family:Inter;font-weight:700;src:url({F}inter-latin-700-normal.woff2)}}
@font-face{{font-family:Inter;font-weight:800;src:url({F}inter-latin-800-normal.woff2)}}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:1080px;height:1440px;overflow:hidden}}
.a{{width:1080px;height:1440px;position:relative;overflow:hidden}}
em{{font-style:normal;color:#E5152D}}
.grao::after{{content:"";position:absolute;inset:0;z-index:50;opacity:.13;mix-blend-mode:overlay;pointer-events:none;
 background:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .9 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>")}}
.fit{{overflow:hidden}}
.st{{filter:drop-shadow(6px 0 0 #fff) drop-shadow(-6px 0 0 #fff) drop-shadow(0 6px 0 #fff) drop-shadow(0 -6px 0 #fff) drop-shadow(0 18px 22px rgba(40,10,10,.32))}}
.st svg{{width:100%;height:100%;display:block}}
.e3d{{position:absolute;filter:drop-shadow(0 18px 24px rgba(0,0,0,.35))}}
"""
FIT_JS = """<script>
document.fonts.ready.then(()=>{
 document.querySelectorAll('.fit').forEach(el=>{
   let s=parseFloat(getComputedStyle(el).fontSize), min=+(el.dataset.min||22);
   while((el.scrollHeight>el.clientHeight+1||el.scrollWidth>el.clientWidth+1)&&s>min){s-=1;el.style.fontSize=s+'px';}
   if(el.scrollHeight>el.clientHeight+1||el.scrollWidth>el.clientWidth+1) el.dataset.estouro='1';
 });
 window.__pronto=true;
});
</script>"""

def pagina(corpo, css):
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS_BASE}{css}</style></head><body>{corpo}{FIT_JS}</body></html>"

def sticker(svg, x, y, w, h, rot=0, z=10, extra=""):
    return f'<div class="st" style="position:absolute;left:{x}px;top:{y}px;width:{w}px;height:{h}px;transform:rotate({rot}deg);z-index:{z};{extra}">{svg}</div>'

def e3d(nome, x, y, t, rot=0, z=8):
    return f'<img class="e3d" src="{emoji(nome)}" style="left:{x}px;top:{y}px;width:{t}px;height:{t}px;transform:rotate({rot}deg);z-index:{z}">'

# =====================================================================================
# 1) DATA DO DIA  (escuro, cinematográfico)
# =====================================================================================
CSS_DIA = """
.dia{background:#050505;color:#fff}
.dia .bg{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;filter:grayscale(1) contrast(1.15) brightness(.36)}
.dia .fog{position:absolute;inset:0;background:radial-gradient(70% 40% at 50% 42%,rgba(229,21,45,.40),transparent 70%),radial-gradient(100% 45% at 50% 100%,rgba(110,6,18,.6),transparent 72%),radial-gradient(120% 85% at 50% 50%,transparent 50%,rgba(0,0,0,.88) 100%)}
.dia .barra{position:absolute;top:52px;left:60px;right:60px;display:flex;justify-content:space-between;align-items:center;font:700 26px SM;letter-spacing:.2em;color:#cfcfcf;z-index:5}
.dia .barra b{color:#FF2040}
.dia .marca{position:absolute;bottom:44px;left:0;right:0;display:flex;justify-content:center;align-items:center;gap:12px;font:500 24px SG;color:#9a9a9a;z-index:5;letter-spacing:.04em}
.dia .marca img{height:26px}
/* hoje */
.h-kick{position:absolute;top:150px;left:70px;right:70px;font:700 32px SG;letter-spacing:.24em;color:#fff;z-index:5;text-shadow:0 2px 12px rgba(0,0,0,.6)}
.h-kick::before{content:'';display:inline-block;width:16px;height:16px;border-radius:50%;background:#FF2040;margin-right:14px;vertical-align:2px}
.h-tit{position:absolute;top:200px;left:66px;right:66px;height:330px;font:400 132px/0.96 Hwt;text-transform:uppercase;z-index:5;display:flex;align-items:flex-start}
.h-risco{position:absolute;left:70px;width:180px;height:12px;background:#E5152D;z-index:5;border-radius:6px}
.h-piada{position:absolute;left:66px;right:66px;bottom:130px;height:520px;z-index:6;display:flex;flex-direction:column;justify-content:flex-end;font-size:48px}
.h-piada .s{font:500 1em/1.28 SG;color:#f1f1f1}
.h-piada .p{font:400 1.62em/1.0 Hwt;color:#FF2040;margin-top:.45em;text-transform:uppercase;text-shadow:0 0 30px rgba(229,21,45,.35)}
/* poster */
.p-topo{position:absolute;top:120px;left:0;right:0;text-align:center;font:700 26px SM;letter-spacing:.4em;color:#bdbdbd;z-index:5}
.p-apr{position:absolute;top:164px;left:0;right:0;text-align:center;font:500 24px SG;letter-spacing:.3em;color:#8d8d8d;z-index:5}
.p-tit{position:absolute;top:760px;left:50px;right:50px;height:330px;text-align:center;font:400 190px/0.9 Hwt;color:#E5152D;text-shadow:0 0 50px rgba(229,21,45,.45);z-index:5;display:flex;align-items:center;justify-content:center;text-transform:uppercase}
.p-tag{position:absolute;top:1100px;left:90px;right:90px;height:110px;text-align:center;font:500 40px/1.28 SG;color:#f2f2f2;z-index:5}
.p-cred{position:absolute;top:1222px;left:70px;right:70px;height:100px;text-align:center;font:500 22px/1.45 SG;letter-spacing:.06em;color:#9a9a9a;text-transform:uppercase;z-index:5}
.p-cred b{font-weight:700;color:#d6d6d6}
.p-data{position:absolute;top:1336px;left:0;right:0;text-align:center;font:700 23px SM;letter-spacing:.14em;color:#FF2040;z-index:5}
.dia.poster .marca{display:none}
.p-mini{position:absolute;right:40px;bottom:26px;display:flex;align-items:center;gap:8px;font:500 19px SG;color:#9a9a9a;z-index:6}
.p-mini img{height:20px}
/* plantão */
.pl-top{position:absolute;top:120px;left:60px;right:60px;height:86px;display:flex;align-items:center;gap:22px;z-index:6}
.pl-top .tag{background:#E5152D;color:#fff;font:400 62px/1 Hwt;padding:12px 26px 6px;border-radius:10px;letter-spacing:.02em}
.pl-top .vivo{display:flex;align-items:center;gap:12px;font:700 28px SM;letter-spacing:.2em;color:#fff}
.pl-top .vivo i{width:20px;height:20px;border-radius:50%;background:#FF2040;box-shadow:0 0 0 8px rgba(255,32,64,.25)}
.pl-tela{position:absolute;top:236px;left:60px;right:60px;height:620px;border-radius:26px;overflow:hidden;border:4px solid #2a2a2a;z-index:5;box-shadow:0 30px 80px rgba(0,0,0,.6)}
.pl-tela img{width:100%;height:100%;object-fit:cover;filter:grayscale(.35) contrast(1.1) brightness(.85)}
.pl-tela .scan{position:absolute;inset:0;background:repeating-linear-gradient(0deg,rgba(0,0,0,.12) 0 2px,transparent 2px 5px)}
.pl-urg{position:absolute;top:888px;left:60px;z-index:6;background:#fff;color:#E5152D;font:800 30px Inter;letter-spacing:.12em;padding:10px 20px;border-radius:8px}
.pl-head{position:absolute;top:950px;left:60px;right:60px;height:300px;background:#fff;color:#0d0d0d;border-left:16px solid #E5152D;border-radius:10px;padding:26px 34px;font:800 58px/1.12 Inter;z-index:6;letter-spacing:-.015em}
.pl-tick{position:absolute;top:1272px;left:60px;right:60px;height:66px;background:#111;border-radius:10px;display:flex;align-items:center;overflow:hidden;z-index:6}
.pl-tick b{background:#E5152D;height:100%;display:flex;align-items:center;padding:0 20px;font:700 22px SM;letter-spacing:.14em}
.pl-tick span{padding:0 22px;font:500 25px SG;color:#ddd;white-space:nowrap}
/* ranking */
.r-tit{position:absolute;top:150px;left:66px;right:66px;height:250px;font:400 108px/0.95 Hwt;text-transform:uppercase;z-index:5;display:flex;align-items:flex-end}
.r-sub{position:absolute;top:418px;left:70px;right:300px;font:500 34px/1.3 SG;color:#cfcfcf;z-index:5}
.r-lista{position:absolute;top:540px;left:66px;right:66px;height:740px;z-index:6;font-size:44px;display:flex;flex-direction:column;justify-content:flex-start;gap:.5em}
.r-lista .it{display:flex;gap:.5em;align-items:baseline;border-bottom:2px solid rgba(255,255,255,.12);padding-bottom:.42em}
.r-lista .n{font:400 1.5em/1 Hwt;color:#FF2040;min-width:1.1em}
.r-lista .t{font:500 1em/1.25 SG;color:#f3f3f3}
.r-lista .t s{color:#8d8d8d}
"""

def _dia_base(cls, foto_url, barra_esq, corpo):
    return f'''<div class="a dia grao {cls}">
 <img class="bg" src="{foto_url}"><div class="fog"></div>
 <div class="barra"><span>{barra_esq}</span><span>@ARCHEAGENCIA</span></div>
 {corpo}
 <div class="marca"><img src="{LOGO}">archeagencia</div>
</div>'''

def dia_hoje(d):
    c = f'''<div class="h-kick">{e(d.get("kicker","HOJE É"))}</div>
 <div class="h-tit fit" data-min="70">{e(d["titulo"])}</div>
 {e3d(d.get("emoji","sparkles"), d.get("ex",700), d.get("ey",520), d.get("et",300), d.get("erot",-8))}
 <div class="h-piada fit" data-min="30"><div class="s">{e(d["setup"])}</div>{('<div class="p">'+e(d["punch"])+'</div>') if d.get("punch") else ""}</div>'''
    return pagina(_dia_base("hoje", d["foto"], d["barra"], c), CSS_DIA)

def dia_poster(d):
    c = f'''<div class="p-topo">{e(d["topo"])}</div><div class="p-apr">{e(d.get("apresenta","O ALGORITMO APRESENTA"))}</div>
 {e3d(d.get("emoji","fire"), 340, 260, 400, d.get("erot",-6))}
 <div class="p-tit fit" data-min="90">{e(d["titulo"])}</div>
 <div class="p-tag fit" data-min="28">{e(d["tag"])}</div>
 <div class="p-cred fit" data-min="16">{d["cred"]}</div>
 <div class="p-data">{e(d["rodape"])}</div>
 <div class="p-mini"><img src="{LOGO}">@archeagencia</div>'''
    return pagina(_dia_base("poster", d["foto"], "", c).replace('<div class="barra"><span></span><span>@ARCHEAGENCIA</span></div>', ""), CSS_DIA)

def dia_plantao(d):
    c = f'''<div class="pl-top"><div class="tag">PLANTÃO</div><div class="vivo"><i></i>AO VIVO · {e(d["barra"])}</div></div>
 <div class="pl-tela"><img src="{d["foto2"]}"><div class="scan"></div></div>
 {e3d(d.get("emoji","police_car_light"), 820, 690, 200, 10, 7)}
 <div class="pl-urg">URGENTE</div>
 <div class="pl-head fit" data-min="34">{e(d["manchete"])}</div>
 <div class="pl-tick"><b>{e(d.get("tick_tag","HOJE"))}</b><span>{e(d["ticker"])}</span></div>'''
    pg = _dia_base("plantao", d["foto"], "", c).replace('<div class="barra"><span></span><span>@ARCHEAGENCIA</span></div>', "")
    return pagina(pg.replace('<div class="marca">', '<div class="marca" style="bottom:30px">'), CSS_DIA + ".dia.plantao .marca{display:none}")

def dia_ranking(d):
    itens = "".join(f'<div class="it"><span class="n">{i+1}</span><span class="t">{e(t)}</span></div>' for i, t in enumerate(d["itens"]))
    c = f'''<div class="r-tit fit" data-min="60">{e(d["titulo"])}</div>
 <div class="r-sub">{e(d["sub"])}</div>
 {e3d(d.get("emoji","trophy"), 790, 360, 230, 8)}
 <div class="r-lista fit" data-min="28">{itens}</div>'''
    return pagina(_dia_base("ranking", d["foto"], d["barra"], c), CSS_DIA)

# =====================================================================================
# 2) MASCOTE + BANCO DE IMAGENS  (claro, colagem gráfica)
# =====================================================================================
CSS_M = """
.m{background:#F3EADF;color:#111;font-family:Inter}
.m .papel{position:absolute;inset:0;background:radial-gradient(#d9c9b8 1.6px,transparent 1.7px) 0 0/34px 34px;opacity:.55}
.m .marca{position:absolute;left:44px;bottom:30px;display:flex;align-items:center;gap:10px;font:700 24px Inter;color:#7a5a4c;z-index:30}
.m .marca img{height:26px}
.m .canto{position:absolute;right:44px;bottom:34px;font:700 20px SM;letter-spacing:.2em;color:#b49a88;z-index:30}
.fr{position:absolute;border:7px solid #141414;border-radius:30px;overflow:hidden;background:#222;box-shadow:10px 12px 0 #141414}
.fr img{width:100%;height:100%;object-fit:cover;filter:saturate(1.05) contrast(1.04)}
.fita{position:absolute;width:150px;height:44px;background:rgba(245,226,190,.82);z-index:25;box-shadow:0 2px 6px rgba(0,0,0,.12)}
.topo{position:absolute;left:60px;right:60px;font:800 58px/1.14 Inter;letter-spacing:-.02em;z-index:20}
.chip{position:absolute;z-index:24;background:#141414;color:#fff;font:400 44px/1 Hwt;padding:14px 22px 8px;border-radius:12px;letter-spacing:.02em;transform:rotate(-3deg)}
.chip.r{background:#E5152D}
.card{position:absolute;background:#fff;border:6px solid #141414;border-radius:26px;box-shadow:8px 10px 0 #141414;z-index:15}
.txt{font:800 52px/1.14 Inter;letter-spacing:-.015em}
.bal{position:absolute;background:#fff;border:6px solid #141414;border-radius:36px;padding:26px 32px;font:800 48px/1.12 Inter;z-index:26;box-shadow:6px 8px 0 #141414}
.bal::after{content:"";position:absolute;width:44px;height:44px;background:#fff;border-right:6px solid #141414;border-bottom:6px solid #141414;bottom:-27px;left:80px;transform:rotate(45deg)}
"""

def _m(corpo, extra_css=""):
    return pagina(f'''<div class="a m grao"><div class="papel"></div>{corpo}
 <div class="marca"><img src="{LOGO}">@archeagencia</div><div class="canto">MANDA PRA ALGUÉM</div></div>''', CSS_M + extra_css)

def fita(x, y, rot):
    return f'<div class="fita" style="left:{x}px;top:{y}px;transform:rotate({rot}deg)"></div>'

def frame(url, x, y, w, h, rot=0, z=5, pos="center"):
    return f'<div class="fr" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;transform:rotate({rot}deg);z-index:{z}"><img src="{url}" style="object-position:{pos}"></div>'

def m_drake(d):
    topo = f'<div class="topo fit" style="top:56px;height:150px" data-min="34">{e(d["topo"])}</div>' if d.get("topo") else ""
    y0 = 236 if d.get("topo") else 120
    hrow = (1280 - y0) // 2 - 20
    c = topo
    for i, (k, exp, be, bd) in enumerate([("nao", "nojo", "baixo", "pare"), ("sim", "orgulho", "baixo", "aponta")]):
        y = y0 + i * (hrow + 34)
        c += frame(d["foto"][i], 52, y, 470, hrow, -1.5 if i == 0 else 1.2)
        c += sticker(mascote(exp, be, bd if bd != "pare" else "pare"), 70, y + hrow - 380, 400, 380, -4 if i == 0 else 3, 12)
        c += f'<div class="card" style="left:556px;top:{y}px;width:470px;height:{hrow}px;display:flex;align-items:center;padding:34px"><div class="txt fit" data-min="28" style="height:100%;width:100%;display:flex;align-items:center">{e(d[k])}</div></div>'
        c += fita(250, y - 16, -6 if i == 0 else 5)
    return _m(c)

def m_expec(d):
    c = f'<div class="topo fit" style="top:52px;height:120px" data-min="34">{e(d["tema"])}</div>'
    for i, (lab, txt, exp, cls) in enumerate([("EXPECTATIVA", d["exp"], "estrela", ""), ("REALIDADE", d["real"], d.get("exp_real", "chorando"), "r")]):
        y = 200 + i * 600
        c += frame(d["foto"][i], 60, y, 960, 540, -1 if i == 0 else 1)
        c += f'<div class="chip {cls}" style="left:84px;top:{y+26}px">{lab}</div>'
        c += f'<div class="card" style="left:96px;top:{y+330}px;width:610px;height:186px;padding:20px 28px;display:flex;align-items:center"><div class="txt fit" data-min="26" style="font-size:44px;height:100%;width:100%;display:flex;align-items:center">{e(txt)}</div></div>'
        c += sticker(mascote(exp, "cima" if i == 0 else "cabeca", "cima" if i == 0 else "baixo"), 700, y + 210, 330, 330, 5 if i == 0 else -5, 14)
    return _m(c)

def m_pov(d):
    c = f'<div class="topo fit" style="top:56px;height:310px;display:flex;align-items:center;font-size:76px" data-min="34"><div><em>POV:</em> {e(d["texto"])}</div></div>'
    c += frame(d["foto"][0], 60, 400, 960, 900, -1)
    c += fita(460, 384, -3)
    for i, nm in enumerate(d.get("emojis", [])[:2]):
        c += e3d(nm, [90, 760][i], [460, 520][i], 210, [-12, 10][i], 9)
    c += sticker(mascote(d["exp"], d.get("be", "baixo"), d.get("bd", "baixo"), prop=d.get("prop")), 560, 860, 470, 460, 4, 14)
    return _m(c)

def m_botoes(d):
    topo = f'<div class="topo fit" style="top:56px;height:130px" data-min="34">{e(d["topo"])}</div>' if d.get("topo") else ""
    c = topo + frame(d["foto"][0], 60, 210, 960, 1080, 0.8)
    c += '<div style="position:absolute;left:67px;top:217px;width:946px;height:1066px;border-radius:24px;background:linear-gradient(180deg,rgba(0,0,0,.45),rgba(0,0,0,.1) 45%,rgba(0,0,0,.35));z-index:6"></div>'
    for i, t in enumerate([d["b1"], d["b2"]]):
        x = 120 + i * 440
        c += f'<div style="position:absolute;left:{x+20}px;top:590px;width:340px;height:170px;border-radius:26px;background:linear-gradient(180deg,#3a3a3a,#1b1b1b);border:6px solid #141414;z-index:8;box-shadow:8px 10px 0 rgba(0,0,0,.5)"></div>'
        c += f'<div style="position:absolute;left:{x+60}px;top:600px;width:260px;height:120px;border-radius:50%;background:#7a0b18;z-index:9"></div>'
        c += f'<div style="position:absolute;left:{x+60}px;top:560px;width:260px;height:120px;border-radius:50%;background:radial-gradient(60% 60% at 40% 35%,#ff5a6e,#E5152D 60%,#a10b1e);z-index:10;box-shadow:inset 0 -10px 0 rgba(0,0,0,.18)"></div>'
        c += f'<div class="card" style="left:{x}px;top:300px;width:380px;height:230px;transform:rotate({-4 if i==0 else 4}deg);padding:22px;display:flex;align-items:center;justify-content:center;text-align:center"><div class="txt fit" data-min="24" style="font-size:44px;height:100%;width:100%;display:flex;align-items:center;justify-content:center">{e(t)}</div></div>'
    c += sticker(mascote("nervoso", "cabeca", "baixo"), 300, 780, 480, 470, 0, 14)
    if d.get("quem"):
        c += f'<div class="chip r" style="left:120px;top:1150px">{e(d["quem"])}</div>'
    return _m(c)

def m_kit(d):
    c = f'''<div style="position:absolute;left:60px;top:60px;font:400 96px/0.9 Hwt;color:#E5152D;z-index:20">KIT BÁSICO</div>
 <div class="topo fit" style="top:160px;height:150px;right:440px" data-min="30">{e(d["titulo"])}</div>'''
    c += frame(d["foto"][0], 690, 56, 330, 300, 4)
    c += fita(800, 44, 8)
    itens = d["itens"][:6]
    for k, (nm, lab) in enumerate(itens):
        col, row = k % 3, k // 3
        x, y = 60 + col * 330, 400 + row * 420
        c += f'<div class="card" style="left:{x}px;top:{y}px;width:300px;height:380px;display:flex;flex-direction:column;align-items:center;justify-content:flex-end;padding:18px 18px 22px">'
        c += f'<img src="{emoji(nm)}" style="width:190px;height:190px;position:absolute;top:30px;left:55px;filter:drop-shadow(0 10px 14px rgba(0,0,0,.25))">'
        c += f'<div class="fit" data-min="20" style="font:800 32px/1.12 Inter;text-align:center;height:120px;width:100%;display:flex;align-items:center;justify-content:center">{e(lab)}</div></div>'
    c += sticker(mascote(d.get("exp", "orgulho"), "baixo", "aponta"), 800, 1150, 230, 220, 6, 22)
    return _m(c).replace('<div class="canto">', '<div class="canto" style="display:none">')

TIERS = [("S", "#E5152D"), ("A", "#ff8a3d"), ("B", "#ffd23f"), ("C", "#7ad36b"), ("D", "#5fa8ff")]
def m_tier(d):
    c = frame(d["foto"][0], 60, 50, 960, 300, -0.6)
    c += '<div style="position:absolute;left:67px;top:57px;width:946px;height:286px;border-radius:24px;background:linear-gradient(90deg,rgba(0,0,0,.78),rgba(0,0,0,.2));z-index:6"></div>'
    c += f'<div class="fit" data-min="30" style="position:absolute;left:100px;top:80px;width:620px;height:240px;color:#fff;font:800 56px/1.1 Inter;z-index:7;display:flex;align-items:center">{e(d["titulo"])}</div>'
    for i, (t, cor) in enumerate(TIERS):
        y = 400 + i * 182
        itens = d["tiers"].get(t, [])
        c += f'<div style="position:absolute;left:60px;top:{y}px;width:140px;height:160px;background:{cor};border:6px solid #141414;border-radius:18px;font:400 96px/1 Hwt;display:flex;align-items:center;justify-content:center;z-index:10;color:#141414">{t}</div>'
        c += f'<div class="card" style="left:220px;top:{y}px;width:{800 if i>2 else 560}px;height:160px;padding:14px 26px;display:flex;align-items:center"><div class="fit" data-min="22" style="font:700 36px/1.15 Inter;height:100%;width:100%;display:flex;align-items:center">{e(" · ".join(itens))}</div></div>'
    c += sticker(mascote("cool", "baixo", "aponta", prop=None, extra=f'<image href="{emoji("crown")}" x="230" y="30" width="140" height="140"/>'), 760, 360, 300, 330, 6, 22)
    return _m(c)

def m_aura(d):
    c = frame(d["foto"][0], 60, 60, 960, 560, -1)
    c += f'<div class="chip r" style="left:90px;top:84px;font-size:52px">{e(d["titulo"])}</div>'
    c += f'<div style="position:absolute;left:560px;top:250px;width:440px;height:440px;border-radius:50%;background:radial-gradient(circle,rgba(255,236,120,.95),rgba(255,180,60,.45) 45%,transparent 70%);z-index:12"></div>'
    c += sticker(mascote("cool", "cima", "cima"), 600, 300, 380, 380, 0, 14)
    rows = ""
    for t, pts in d["itens"]:
        pos = pts > 0
        rows += f'<div style="display:flex;align-items:center;gap:.5em;padding:.32em 0;border-bottom:3px dashed #d9c9b8"><span style="font:400 1.22em/1 Hwt;min-width:3.4em;color:{"#1f9d4c" if pos else "#E5152D"}">{"+" if pos else "−"}{abs(pts)}</span><span style="font:700 1em/1.15 Inter">{e(t)}</span></div>'
    c += f'<div class="card" style="left:60px;top:680px;width:960px;height:620px;padding:28px 36px"><div class="fit" data-min="24" style="font-size:44px;height:100%;width:100%">{rows}</div></div>'
    return _m(c)

def m_flags(d):
    c = f'<div class="topo fit" style="top:50px;height:140px;right:400px" data-min="32">{e(d["titulo"])}</div>'
    c += frame(d["foto"][0], 700, 40, 320, 300, 4)
    c += sticker(mascote(d.get("exp", "desconfiado"), "baixo", "segura", prop="triangular_flag", prop_tam=190), 560, 200, 260, 260, -4, 16)
    for i, (k, cor, lab) in enumerate([("red", "#E5152D", "RED FLAG"), ("green", "#1f9d4c", "GREEN FLAG")]):
        x = 60 + i * 490
        itens = "".join(f'<div style="padding:.38em 0;border-bottom:3px solid #eee;display:flex;gap:.4em"><span style="color:{cor}">●</span><span>{e(t)}</span></div>' for t in d[k])
        c += f'<div class="card" style="left:{x}px;top:500px;width:470px;height:800px;padding:0;overflow:hidden">'
        c += f'<div style="background:{cor};color:#fff;font:400 64px/1 Hwt;padding:26px 28px 18px;border-bottom:6px solid #141414">{lab}</div>'
        c += f'<div class="fit" data-min="22" style="font:700 50px/1.18 Inter;padding:18px 28px;height:660px">{itens}</div></div>'
    return _m(c)

def m_isso(d):
    c = frame(d["foto"][0], 40, 60, 1000, 1160, 0)
    c += '<div style="position:absolute;left:47px;top:67px;width:986px;height:1146px;border-radius:24px;background:linear-gradient(180deg,rgba(20,20,40,.15),rgba(0,0,0,.05) 50%,rgba(0,0,0,.55));z-index:6"></div>'
    c += sticker(mascote("choque", "baixo", "aponta"), 70, 560, 520, 520, -3, 14)
    c += e3d(d["emoji"], 640, 260, 300, 8, 12)
    c += f'<div class="chip" style="left:120px;top:1010px;font-size:46px;z-index:20">{e(d["quem"])}</div>'
    c += f'<div class="chip r fit" data-min="26" style="left:560px;top:560px;max-width:440px;font-size:44px;line-height:1.05;z-index:20;transform:rotate(3deg)">{e(d["obj"])}</div>'
    c += f'<div class="fit" data-min="40" style="position:absolute;left:40px;right:40px;top:1240px;height:150px;text-align:center;font:800 italic 84px/1.05 Inter;color:#FFE600;-webkit-text-stroke:5px #141414;paint-order:stroke fill;z-index:22;display:flex;align-items:center;justify-content:center">{e(d["pergunta"])}</div>'
    return _m(c.replace('<div class="canto">', '<div class="canto" style="display:none">'))

PALETA = ["#E5152D", "#141414", "#ff8a3d", "#ffd23f", "#9a9a9a", "#ff8fb1"]
def m_pizza(d):
    tot, ang, segs = 0, 0, []
    for i, (lab, p) in enumerate(d["fatias"]):
        segs.append(f"{PALETA[i]} {ang}% {ang+p}%"); ang += p
    c = f'<div class="topo fit" style="top:56px;height:150px" data-min="32">{e(d["titulo"])}</div>'
    c += frame(d["foto"][0], 700, 230, 320, 380, 5)
    c += fita(780, 216, -6)
    c += f'<div style="position:absolute;left:70px;top:250px;width:560px;height:560px;border-radius:50%;border:8px solid #141414;background:conic-gradient({",".join(segs)});box-shadow:10px 12px 0 #141414;z-index:10"></div>'
    leg = "".join(f'<div style="display:flex;align-items:center;gap:.5em;padding:.28em 0"><span style="width:1em;height:1em;border-radius:6px;border:4px solid #141414;background:{PALETA[i]};flex:none"></span><span style="font:400 1.2em/1 Hwt;min-width:2.6em">{p}%</span><span style="font:700 1em/1.15 Inter">{e(lab)}</span></div>' for i, (lab, p) in enumerate(d["fatias"]))
    c += f'<div class="card" style="left:60px;top:880px;width:700px;height:420px;padding:24px 30px"><div class="fit" data-min="22" style="font-size:40px;height:100%;width:100%">{leg}</div></div>'
    c += sticker(mascote(d.get("exp", "confuso"), "baixo", "aponta"), 740, 760, 320, 340, -3, 16)
    c += '<div style="position:absolute;left:784px;top:1120px;font:700 22px SM;color:#7a5a4c;z-index:16;width:240px;letter-spacing:.06em">*DADOS 100% SINCEROS, 0% CIENTÍFICOS</div>'
    return _m(c)

def m_niveis(d):
    c = f'<div class="topo fit" style="top:44px;height:120px" data-min="32">{e(d["titulo"])}</div>'
    exps = [("sorriso", 0), ("feliz", .25), ("estrela", .55), ("estrela", 1)]
    for i, t in enumerate(d["niveis"][:4]):
        y = 190 + i * 282
        c += f'<div class="card" style="left:60px;top:{y}px;width:560px;height:250px;padding:20px 28px;display:flex;align-items:center"><div class="txt fit" data-min="24" style="font-size:42px;height:100%;width:100%;display:flex;align-items:center">{e(t)}</div></div>'
        c += frame(d["foto"][i % len(d["foto"])], 650, y, 370, 250, 0)
        exp, glow = exps[i]
        if glow:
            c += f'<div style="position:absolute;left:{835-140-int(glow*80)}px;top:{y+125-140-int(glow*80)}px;width:{280+int(glow*160)}px;height:{280+int(glow*160)}px;border-radius:50%;background:radial-gradient(circle,rgba(255,240,150,{.5+glow*.45}),rgba(255,190,60,{glow*.5}) 45%,transparent 70%);z-index:11"></div>'
        c += sticker(mascote(exp, "baixo" if i < 2 else "cima", "baixo" if i < 2 else "cima"), 730, y + 20, 220, 220, 0, 13)
    return _m(c)

def m_ninguem(d):
    linhas = "".join(f'<div style="margin-bottom:.3em">{e(l)}</div>' for l in d["linhas"])
    c = f'<div class="topo fit" style="top:56px;height:330px;font-weight:700" data-min="30">{linhas}</div>'
    c += frame(d["foto"][0], 60, 410, 960, 900, 1)
    c += f'<div class="bal" style="left:110px;top:470px;width:620px;height:250px;display:flex;align-items:center"><div class="fit" data-min="26" style="height:100%;width:100%;display:flex;align-items:center">{e(d["fala"])}</div></div>'
    c += sticker(mascote(d.get("exp", "feliz"), d.get("be", "baixo"), d.get("bd", "cima"), prop=d.get("prop")), 520, 820, 480, 470, 3, 16)
    return _m(c)

def m_celular(d):
    linhas = "".join(f'''<div style="display:flex;align-items:center;gap:16px;padding:14px 0;border-bottom:2px solid #f0f0f0"><span style="width:62px;height:62px;border-radius:50%;background:{cor};color:#fff;font:700 28px Inter;display:flex;align-items:center;justify-content:center;flex:none">{ini}</span><span><b style="font:700 27px Inter;display:block">{e(n)}</b><span style="font:400 21px Inter;color:#777">{e(s)}</span></span></div>''' for ini, cor, n, s in d["linhas"])
    c = f'<div class="topo fit" style="top:60px;height:170px;font-weight:500;font-size:62px" data-min="30">{e(d["topo"])}</div>'
    c += frame(d["foto"][0], 60, 260, 960, 1060, -0.8)
    c += sticker(mascote(d.get("exp", "nervoso"), "cabeca", "segura"), 60, 760, 520, 520, -2, 14)
    c += f'''<div style="position:absolute;left:560px;top:330px;width:420px;height:800px;background:#141414;border-radius:58px;padding:16px;transform:rotate(4deg);z-index:16;box-shadow:12px 14px 0 rgba(0,0,0,.35)">
 <div style="background:#fff;width:100%;height:100%;border-radius:44px;padding:70px 28px 24px;position:relative">
  <div style="position:absolute;top:18px;left:50%;margin-left:-50px;width:100px;height:26px;border-radius:13px;background:#141414"></div>
  <div style="font:700 30px Inter;text-align:center;padding-bottom:14px;border-bottom:2px solid #eee">{e(d["tela_tit"])}</div>{linhas}
  <div style="margin-top:18px;background:#f2f2f2;border-radius:20px;padding:16px 20px;font:400 23px/1.3 Inter"><b>{e(d["coment_nome"])}</b><br>{e(d["coment"])}</div>
  <div style="position:absolute;bottom:30px;left:28px;right:28px;display:flex;justify-content:space-between;align-items:center;font:700 28px Inter"><span><span style="color:#E5152D">♥</span> {e(d["rodape"])}</span><span style="font:400 22px Inter;color:#888">{e(d["quando"])}</span></div>
 </div></div>'''
    return _m(c)

# =====================================================================================
# 3) PRINT
# =====================================================================================
CSS_P = """
.pr{background:#fff;color:#0f1419;font-family:Inter}
.pr .box{position:absolute;left:84px;right:84px;top:50%;transform:translateY(-52%)}
.pr .cab{display:flex;align-items:center;gap:26px}
.pr .cab img{width:118px;height:118px;border-radius:50%}
.pr .nm{font:700 46px Inter;letter-spacing:-.01em}
.pr .us{font:400 38px Inter;color:#536471;margin-top:4px}
.pr .corpo{margin-top:44px;max-height:900px;font-size:58px}
.pr .corpo p{font:400 1em/1.3 Inter;letter-spacing:-.012em}
.pr .corpo p+p{margin-top:.68em}
.pr .rod{margin-top:50px;font:400 36px Inter;color:#536471;padding-bottom:36px;border-bottom:2px solid #eff3f4}
"""
def print_post(d):
    ps = "".join(f"<p>{e(p)}</p>" for p in d["texto"])
    n = sum(len(p) for p in d["texto"])
    tam = 76 if n < 90 else 70 if n < 140 else 64 if n < 190 else 58
    corpo = f'''<div class="a pr"><div class="box">
 <div class="cab"><img src="{AVATAR}"><div><div class="nm">Arche Agência</div><div class="us">@archeagencia</div></div></div>
 <div class="corpo fit" data-min="38" style="font-size:{tam}px">{ps}</div>
 <div class="rod">{e(d["hora"])} · {e(d["data_txt"])}</div></div></div>'''
    return pagina(corpo, CSS_P)

MODELOS = {"hoje": dia_hoje, "poster": dia_poster, "plantao": dia_plantao, "ranking": dia_ranking,
           "drake": m_drake, "expec": m_expec, "pov": m_pov, "botoes": m_botoes, "kit": m_kit, "tier": m_tier,
           "aura": m_aura, "flags": m_flags, "isso": m_isso, "pizza": m_pizza, "niveis": m_niveis,
           "ninguem": m_ninguem, "celular": m_celular, "print": print_post}
