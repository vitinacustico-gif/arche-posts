# -*- coding: utf-8 -*-
"""Mascote da Arche: o "A" vermelho com cara. Gera SVG paramétrico (expressão, braços, acessórios).
viewBox 0 0 600 660. Use mascote(exp, bracos, prop, ...) -> string <svg>."""
import json, os, math
AQUI = os.path.dirname(os.path.abspath(__file__))
EMO = json.load(open(os.path.join(AQUI, "..", "emoji_index.json")))
K = "#141414"
APEX, PL, PR = (300, 175), (100, 520), (500, 520)
SL, SR = (176, 318), (424, 318)          # ombros

def emoji(nome):
    return "file://" + EMO[nome]

def _corpo(cor, cor2):
    pts = f"{PL[0]},{PL[1]} {APEX[0]},{APEX[1]} {PR[0]},{PR[1]}"
    return f'''
 <polyline points="{pts}" fill="none" stroke="{K}" stroke-width="204" stroke-linejoin="round" stroke-linecap="round"/>
 <polyline points="{pts}" fill="none" stroke="url(#g)" stroke-width="180" stroke-linejoin="round" stroke-linecap="round"/>
 <path d="M212 300 L272 196" stroke="#ffffff" stroke-opacity=".28" stroke-width="20" stroke-linecap="round"/>
 <ellipse cx="92" cy="602" rx="84" ry="32" fill="{K}"/><ellipse cx="508" cy="602" rx="84" ry="32" fill="{K}"/>
 <ellipse cx="70" cy="592" rx="26" ry="7" fill="#fff" opacity=".18"/><ellipse cx="486" cy="592" rx="26" ry="7" fill="#fff" opacity=".18"/>'''

# ---------- olhos ----------
def _olho(cx, cy, tipo, px=0, py=0, lado=1):
    if tipo == "normal":
        return f'<ellipse cx="{cx}" cy="{cy}" rx="34" ry="41" fill="#fff" stroke="{K}" stroke-width="7"/><circle cx="{cx+px}" cy="{cy+py}" r="14" fill="{K}"/><circle cx="{cx+px+4}" cy="{cy+py-5}" r="4.5" fill="#fff"/>'
    if tipo == "grande":
        return f'<ellipse cx="{cx}" cy="{cy}" rx="40" ry="48" fill="#fff" stroke="{K}" stroke-width="7"/><circle cx="{cx+px}" cy="{cy+py}" r="8" fill="{K}"/>'
    if tipo == "feliz":   # ^
        return f'<path d="M{cx-28} {cy+8} Q{cx} {cy-26} {cx+28} {cy+8}" fill="none" stroke="{K}" stroke-width="10" stroke-linecap="round"/>'
    if tipo == "fechado":  # ∩ para baixo (chorando/dormindo)
        return f'<path d="M{cx-28} {cy-4} Q{cx} {cy+22} {cx+28} {cy-4}" fill="none" stroke="{K}" stroke-width="10" stroke-linecap="round"/>'
    if tipo == "aperto":   # > <
        s = 1 if lado > 0 else -1
        return f'<path d="M{cx-22*s} {cy-20} L{cx+20*s} {cy} L{cx-22*s} {cy+20}" fill="none" stroke="{K}" stroke-width="10" stroke-linecap="round" stroke-linejoin="round"/>'
    if tipo == "meio":     # pálpebra caída (desconfiado / blasé)
        cid = f"cl{cx}"
        return (f'<clipPath id="{cid}"><ellipse cx="{cx}" cy="{cy}" rx="34" ry="41"/></clipPath>'
                f'<ellipse cx="{cx}" cy="{cy}" rx="34" ry="41" fill="#fff"/>'
                f'<circle cx="{cx+px}" cy="{cy+py+12}" r="14" fill="{K}"/>'
                f'<rect x="{cx-40}" y="{cy-50}" width="80" height="50" fill="#d8142c" clip-path="url(#{cid})"/>'
                f'<path d="M{cx-34} {cy} L{cx+34} {cy}" stroke="{K}" stroke-width="8" stroke-linecap="round"/>'
                f'<ellipse cx="{cx}" cy="{cy}" rx="34" ry="41" fill="none" stroke="{K}" stroke-width="7"/>')
    if tipo == "x":
        return f'<path d="M{cx-20} {cy-20} L{cx+20} {cy+20} M{cx+20} {cy-20} L{cx-20} {cy+20}" stroke="{K}" stroke-width="11" stroke-linecap="round"/>'
    if tipo == "coracao":
        return f'<path transform="translate({cx-30} {cy-28}) scale(1.25)" d="M24 44 C10 34 0 26 0 14 C0 6 6 0 13 0 C18 0 22 3 24 7 C26 3 30 0 35 0 C42 0 48 6 48 14 C48 26 38 34 24 44Z" fill="#ff8fb1" stroke="{K}" stroke-width="5"/>'
    if tipo == "estrela":
        p = []
        for i in range(10):
            r = 34 if i % 2 == 0 else 15
            a = -math.pi / 2 + i * math.pi / 5
            p.append(f"{cx + r*math.cos(a):.1f},{cy + r*math.sin(a):.1f}")
        return f'<polygon points="{" ".join(p)}" fill="#FFD43B" stroke="{K}" stroke-width="5" stroke-linejoin="round"/>'
    if tipo == "espiral":
        return f'<ellipse cx="{cx}" cy="{cy}" rx="34" ry="41" fill="#fff" stroke="{K}" stroke-width="7"/><path d="M{cx} {cy} m-4 0 a4 4 0 1 1 8 0 a8 8 0 1 1 -16 0 a13 13 0 1 1 26 0 a18 18 0 1 1 -36 0" fill="none" stroke="{K}" stroke-width="4"/>'
    if tipo == "risco":   # — dormindo
        return f'<path d="M{cx-26} {cy+4} L{cx+26} {cy+4}" stroke="{K}" stroke-width="10" stroke-linecap="round"/>'
    return ""

OLHOS = {  # tipo, pupila dx, dy
    "feliz": ("normal", 0, 4), "nervoso": ("normal", 12, 10), "choque": ("grande", 0, 0), "chorando": ("fechado", 0, 0),
    "triste": ("normal", 0, 14), "bravo": ("normal", 0, 6), "cool": ("normal", 0, 0), "apaixonado": ("coracao", 0, 0),
    "rindo": ("feliz", 0, 0), "pensando": ("normal", -10, -14), "desconfiado": ("meio", 10, 0), "dormindo": ("risco", 0, 0),
    "morto": ("x", 0, 0), "estrela": ("estrela", 0, 0), "nojo": ("aperto", 0, 0), "metido": ("meio", 0, 0),
    "confuso": ("espiral", 0, 0), "orgulho": ("feliz", 0, 0), "olhando": ("normal", 14, 0), "sorriso": ("feliz", 0, 0),
}
SOBRANCELHA = {  # (esq), (dir) como linhas
    "feliz": "M232 142 L282 134|M318 134 L368 142", "nervoso": "M236 150 L284 132|M316 132 L364 150",
    "choque": "M228 118 L280 108|M320 108 L372 118", "chorando": "M236 150 L284 128|M316 128 L364 150",
    "triste": "M236 150 L284 130|M316 130 L364 150", "bravo": "M232 126 L286 154|M314 154 L368 126",
    "cool": "", "apaixonado": "M234 130 L282 124|M318 124 L366 130", "rindo": "M232 134 L282 126|M318 126 L368 134",
    "pensando": "M232 128 L282 118|M318 140 L368 140", "desconfiado": "M232 146 L284 146|M316 136 L368 128",
    "dormindo": "M236 150 L284 148|M316 148 L364 150", "morto": "", "estrela": "M232 124 L282 116|M318 116 L368 124",
    "nojo": "M232 132 L286 152|M314 152 L368 132", "metido": "M232 136 L284 128|M316 128 L368 136",
    "confuso": "M232 126 L282 142|M318 118 L368 130", "orgulho": "M232 132 L282 124|M318 124 L368 132",
    "olhando": "M232 140 L282 132|M318 132 L368 140", "sorriso": "M232 136 L282 128|M318 128 L368 136",
}
BOCA = {
    "feliz": f'<path d="M262 262 Q300 304 338 262 Q300 284 262 262Z" fill="#5a0a14" stroke="{K}" stroke-width="7" stroke-linejoin="round"/>',
    "sorriso": f'<path d="M258 258 Q300 300 342 258" fill="none" stroke="{K}" stroke-width="9" stroke-linecap="round"/>',
    "nervoso": f'<path d="M256 262 Q300 282 344 258 L340 280 Q300 306 260 284 Z" fill="#fff" stroke="{K}" stroke-width="7" stroke-linejoin="round"/><path d="M285 268 L284 292 M308 268 L309 292" stroke="{K}" stroke-width="4"/>',
    "choque": f'<ellipse cx="300" cy="282" rx="24" ry="30" fill="#5a0a14" stroke="{K}" stroke-width="7"/>',
    "chorando": f'<path d="M262 292 Q280 262 300 276 Q320 262 338 292 Q300 280 262 292Z" fill="#5a0a14" stroke="{K}" stroke-width="7" stroke-linejoin="round"/>',
    "triste": f'<path d="M266 290 Q300 262 334 290" fill="none" stroke="{K}" stroke-width="9" stroke-linecap="round"/>',
    "bravo": f'<rect x="262" y="266" width="76" height="26" rx="8" fill="#fff" stroke="{K}" stroke-width="7"/><path d="M262 279 L338 279 M281 266 L281 292 M300 266 L300 292 M319 266 L319 292" stroke="{K}" stroke-width="4"/>',
    "cool": f'<path d="M270 274 Q306 290 336 262" fill="none" stroke="{K}" stroke-width="9" stroke-linecap="round"/>',
    "apaixonado": f'<path d="M262 262 Q300 304 338 262 Q300 284 262 262Z" fill="#5a0a14" stroke="{K}" stroke-width="7" stroke-linejoin="round"/>',
    "rindo": f'<path d="M252 254 Q300 330 348 254 Z" fill="#5a0a14" stroke="{K}" stroke-width="7" stroke-linejoin="round"/><path d="M272 288 Q300 306 328 288 Q300 318 272 288Z" fill="#ff6f86"/>',
    "pensando": f'<path d="M280 280 L326 274" stroke="{K}" stroke-width="9" stroke-linecap="round"/>',
    "desconfiado": f'<path d="M276 282 L324 278" stroke="{K}" stroke-width="9" stroke-linecap="round"/>',
    "dormindo": f'<ellipse cx="300" cy="282" rx="12" ry="14" fill="#5a0a14" stroke="{K}" stroke-width="6"/>',
    "morto": f'<path d="M262 270 Q300 290 338 270" fill="none" stroke="{K}" stroke-width="9" stroke-linecap="round"/><path d="M296 276 Q300 312 318 306 Q326 290 316 272" fill="#ff6f86" stroke="{K}" stroke-width="6"/>',
    "estrela": f'<path d="M256 256 Q300 318 344 256 Z" fill="#5a0a14" stroke="{K}" stroke-width="7" stroke-linejoin="round"/>',
    "nojo": f'<path d="M262 284 Q276 268 290 282 Q304 296 318 280 Q330 268 340 284" fill="none" stroke="{K}" stroke-width="9" stroke-linecap="round"/>',
    "metido": f'<path d="M268 276 Q300 290 336 264" fill="none" stroke="{K}" stroke-width="9" stroke-linecap="round"/>',
    "confuso": f'<path d="M266 282 Q282 268 300 282 Q318 296 334 280" fill="none" stroke="{K}" stroke-width="9" stroke-linecap="round"/>',
    "orgulho": f'<path d="M258 258 Q300 304 342 258 Q300 280 258 258Z" fill="#5a0a14" stroke="{K}" stroke-width="7" stroke-linejoin="round"/>',
    "olhando": f'<path d="M272 278 L330 278" stroke="{K}" stroke-width="9" stroke-linecap="round"/>',
}

def _rosto(exp):
    t, px, py = OLHOS[exp]
    s = []
    s.append(_olho(262, 205, t, px, py, 1))
    s.append(_olho(338, 205, t, px, py, -1))
    sb = SOBRANCELHA.get(exp, "")
    for d in [x for x in sb.split("|") if x]:
        s.append(f'<path d="{d}" stroke="{K}" stroke-width="11" stroke-linecap="round"/>')
    s.append(BOCA[exp])
    if exp in ("nervoso",):
        s.append(f'<path d="M398 118 Q414 148 409 164 Q401 180 386 172 Q375 162 383 144 Z" fill="#9fd3ff" stroke="{K}" stroke-width="5"/>')
        s.append(f'<path d="M196 160 Q206 178 203 188 Q198 198 189 194 Q182 188 187 176 Z" fill="#9fd3ff" stroke="{K}" stroke-width="4"/>')
    if exp == "chorando":
        s.append('<path d="M244 222 Q236 300 250 360" fill="none" stroke="#7cc4ff" stroke-width="16" stroke-linecap="round" opacity=".95"/>')
        s.append('<path d="M356 222 Q364 300 350 360" fill="none" stroke="#7cc4ff" stroke-width="16" stroke-linecap="round" opacity=".95"/>')
    if exp == "rindo":
        s.append('<path d="M226 214 Q214 240 222 252 Q232 260 238 246 Q240 232 226 214Z" fill="#7cc4ff" stroke="#141414" stroke-width="4"/>')
        s.append('<path d="M374 214 Q386 240 378 252 Q368 260 362 246 Q360 232 374 214Z" fill="#7cc4ff" stroke="#141414" stroke-width="4"/>')
    if exp == "cool":
        s.append(f'<path d="M218 186 L382 186 L378 200 Q370 244 334 240 Q306 236 304 204 L296 204 Q294 236 266 240 Q230 244 222 200 Z" fill="{K}"/><path d="M236 196 L262 196" stroke="#fff" stroke-width="5" opacity=".5"/>')
    if exp in ("bravo",):
        s.append('<path d="M210 120 Q200 96 222 92 M386 92 Q404 96 392 120" stroke="#141414" stroke-width="6" fill="none"/>')
    if exp == "dormindo":
        s.append('<text x="392" y="120" font-family="Inter" font-weight="800" font-size="46" fill="#141414">z</text><text x="430" y="82" font-family="Inter" font-weight="800" font-size="34" fill="#141414">z</text>')
    if exp in ("apaixonado", "feliz", "rindo", "orgulho", "estrela"):
        s.append('<ellipse cx="226" cy="256" rx="20" ry="11" fill="#ff7a90" opacity=".75"/><ellipse cx="374" cy="256" rx="20" ry="11" fill="#ff7a90" opacity=".75"/>')
    return "\n ".join(s)

# ---------- braços ----------
MAOS = {  # nome: (ponto da mão, controle) ; frente=True desenha na frente do corpo
    "baixo": ((96, 440), (130, 400)), "baixo_d": ((504, 440), (470, 400)),
    "cima": ((88, 92), (110, 230)), "cima_d": ((512, 92), (490, 230)),
    "cabeca": ((196, 92), (110, 210)), "cabeca_d": ((404, 92), (490, 210)),
    "aponta": ((14, 226), (70, 300)), "aponta_d": ((586, 226), (530, 300)),
    "segura": ((70, 330), (120, 370)), "segura_d": ((530, 330), (480, 370)),
    "queixo_d": ((326, 330), (410, 392)), "rosto_d": ((338, 206), (452, 300)),
    "pare_d": ((420, 180), (520, 300)), "pare": ((180, 180), (80, 300)),
    "cintura": ((150, 430), (60, 360)), "cintura_d": ((450, 430), (540, 360)),
}
FRENTE = {"queixo_d", "rosto_d"}

def _braco(nome, lado):
    key = nome if lado == "e" else (nome + "_d" if not nome.endswith("_d") else nome)
    if key not in MAOS:
        key = "baixo" if lado == "e" else "baixo_d"
    (hx, hy), (cx, cy) = MAOS[key]
    sx, sy = SL if lado == "e" else SR
    linha = f'<path d="M{sx} {sy} Q{cx} {cy} {hx} {hy}" fill="none" stroke="{K}" stroke-width="15" stroke-linecap="round"/>'
    if nome.startswith("aponta"):
        dx = -1 if lado == "e" else 1
        mao = f'<circle cx="{hx}" cy="{hy}" r="20" fill="{K}"/><path d="M{hx} {hy-6} L{hx+dx*40} {hy-14}" stroke="{K}" stroke-width="12" stroke-linecap="round"/>'
    elif nome.startswith("pare"):
        mao = f'<rect x="{hx-26}" y="{hy-40}" width="52" height="64" rx="24" fill="{K}"/>' + "".join(
            f'<rect x="{hx-26+i*13}" y="{hy-62}" width="11" height="34" rx="5.5" fill="{K}"/>' for i in range(4))
    elif key == "rosto_d":
        mao = f'<ellipse cx="{hx}" cy="{hy}" rx="40" ry="46" fill="{K}"/>'
    else:
        mao = f'<circle cx="{hx}" cy="{hy}" r="21" fill="{K}"/>'
    return key, linha + mao, (hx, hy)

def mascote(exp="feliz", be="baixo", bd="baixo", prop=None, prop_tam=150, cor="#E5152D", cor2="#B80F24",
            balao=None, extra=""):
    ke, se, he = _braco(be, "e")
    kd, sd, hd = _braco(bd, "d")
    tras = "".join(s for k, s in ((ke, se), (kd, sd)) if k not in FRENTE)
    frente = "".join(s for k, s in ((ke, se), (kd, sd)) if k in FRENTE)
    p = ""
    if prop:
        nomes = prop if isinstance(prop, (list, tuple)) else [prop]
        for i, nm in enumerate(nomes):
            hx, hy = hd if i == 0 else he
            t = prop_tam
            p += f'<image href="{emoji(nm)}" x="{hx - t/2}" y="{hy - t*0.62}" width="{t}" height="{t}"/>'
    return f'''<svg class="masc" viewBox="-40 30 680 620" xmlns="http://www.w3.org/2000/svg">
 <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{cor}"/><stop offset="1" stop-color="{cor2}"/></linearGradient></defs>
 {tras}
 {_corpo(cor, cor2)}
 {_rosto(exp)}
 {frente}
 {p}
 {extra}
</svg>'''

if __name__ == "__main__":
    exps = list(OLHOS)
    poses = [("baixo", "baixo"), ("cima", "cima"), ("cabeca", "baixo"), ("baixo", "aponta"), ("pare", "baixo"),
             ("baixo", "segura"), ("cintura", "cintura"), ("baixo", "queixo"), ("baixo", "rosto"), ("aponta", "baixo")]
    cards = []
    for i, e in enumerate(exps):
        be, bd = poses[i % len(poses)]
        cards.append(f'<div class="c"><div class="st">{mascote(e, be, bd, prop="mobile_phone" if bd=="segura" else None)}</div><b>{e} · {be}/{bd}</b></div>')
    html = f'''<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Inter;font-weight:800;src:url(../ex/fonts/inter-latin-800-normal.woff2)}}
body{{margin:0;background:#f3e6dc;display:flex;flex-wrap:wrap;gap:10px;padding:10px;width:1580px;font:14px sans-serif}}
.c{{width:300px;text-align:center}} .st svg{{width:300px;height:280px;filter:drop-shadow(5px 0 0 #fff) drop-shadow(-5px 0 0 #fff) drop-shadow(0 5px 0 #fff) drop-shadow(0 -5px 0 #fff) drop-shadow(0 10px 14px rgba(0,0,0,.25))}}
</style></head><body>{"".join(cards)}</body></html>'''
    open(os.path.join(AQUI, "teste_mascote.html"), "w").write(html)
