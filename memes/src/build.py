# -*- coding: utf-8 -*-
"""Monta o calendário dos 270 memes (13/11/2026 a 10/02/2027), renderiza as artes 1080x1440 e gera calendario.json."""
import os, sys, json, shutil, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from layout import MODELOS, foto
from conteudo_dia import DIA
from conteudo_masc import M
from conteudo_print import P
from playwright.sync_api import sync_playwright

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(RAIZ, "saida", "memes")
os.makedirs(OUT, exist_ok=True)
D0 = dt.date(2026, 11, 13)
DIAS = [D0 + dt.timedelta(days=i) for i in range(90)]
SEM = ["SEG", "TER", "QUA", "QUI", "SEX", "SÁB", "DOM"]
MES = ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
mes_min = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
assert len(DIA) == 90 and len(M) == 90 and len(P) == 90

# ---- prints: fixos por data + o resto em ordem ----
FIXO = {"Hoje é o Dia Mundial da Gentileza.": "2026-11-13", "Black Friday é o único dia do ano": "2026-11-25",
        "Black Friday do empreendedor:": "2026-11-26", "Hoje tem gente que acordou às 5h pra comprar.": "2026-11-27",
        "Dezembro do comércio não passa voando.": "2026-12-01", "O verdadeiro amigo secreto é o lucro:": "2026-12-03",
        "Feliz Natal pra quem fez a loja funcionar": "2026-12-25", "O Natal passou.": "2026-12-26",
        "Ninguém fala dos dias entre o Natal": "2026-12-29", "Ano passado eu disse:": "2026-12-31",
        "Réveillon do empreendedor:": "2027-01-01", "2027 vai ser o ano.": "2027-01-02", "Janeiro tem IPVA": "2027-01-05",
        "Primeira semana do ano": "2027-01-07", "Janeiro: todo mundo de férias.": "2027-01-09", "Quem tem loja na praia": "2027-01-10",
        "O cliente perguntou se ainda tinha promoção de Natal.": "2027-01-15", "O verão chegou. O ar-condicionado": "2027-01-27",
        "O Brasil começa depois do Carnaval.": "2027-02-01", "Fevereiro tem 28 dias:": "2027-02-03",
        "Carnaval: o único período do ano": "2027-02-06", "Fantasia mais assustadora do Carnaval:": "2027-02-07",
        "Pula Carnaval, pula boleto": "2027-02-08", "Terça de Carnaval.": "2027-02-09", "Acabou o Carnaval.": "2027-02-10"}
for p in P:
    for k, v in FIXO.items():
        if p["texto"][0].startswith(k):
            p["d"] = v
assert sum(1 for p in P if p.get("d")) == len(FIXO), "frase fixa não encontrada"
fixos = {p["d"]: p for p in P if p.get("d")}
assert len(fixos) == sum(1 for p in P if p.get("d")), "duas frases na mesma data"
livres = [p for p in P if not p.get("d")]
PR = []
for d in DIAS:
    PR.append(fixos.get(d.isoformat()) or livres.pop(0))
assert not livres

CTAS = ["Manda pra aquele amigo que tem loja. 📲", "Marca quem precisa ver isso hoje. 👇", "Envia pro seu sócio e finge que foi sem querer. 😅",
        "Salva e manda pro grupo dos empreendedores. 📌", "Compartilha nos Stories se você se identificou. 🔁", "Manda pra quem vive isso todo dia. 💬",
        "Se você riu, já sabe: manda pra alguém. 😂", "Marca o lojista mais raiz que você conhece. 🏪", "Envia pro amigo que vai responder “sou eu”. 🙋",
        "Comenta “EU” se já passou por isso. 👇", "Manda pra quem trabalha com Instagram. 📱", "Marca alguém que precisa rir hoje. 😆"]
TAGS = {"dia": ["#datacomemorativa #empreendedorismo #marketingdigital #humor #archeagencia", "#hojeédia #empreendedor #pequenonegocio #memes #archeagencia",
                "#datascomemorativas #lojista #marketing #humor #guarapari"],
        "masc": ["#meme #empreendedor #lojista #marketingdigital #archeagencia", "#memes #pequenonegocio #instagramparanegocios #humor #archeagencia",
                 "#memedomarketing #empreendedorismo #vendas #guarapari #archeagencia"],
        "print": ["#empreender #pequenonegocio #memes #marketing #archeagencia", "#vidadeempreendedor #lojista #humor #marketingdigital #archeagencia",
                  "#empreendedorismo #memesbr #vendas #guarapari #archeagencia"]}
SOFT = "Quer que a Arche cuide do marketing da sua loja? Chama no WhatsApp do link da bio."

def legenda(slot, i, linha):
    cta = CTAS[(i * 5 + {"dia": 0, "masc": 4, "print": 8}[slot]) % len(CTAS)]
    extra = f"\n\n{SOFT}" if (i % 9 == 4 and slot == "masc") else ""
    return f"{linha}\n\n{cta}{extra}\n\n{TAGS[slot][i % 3]}"

itens = []
for i, d in enumerate(DIAS):
    barra = f"{SEM[d.weekday()]} · {d.day:02d} {MES[d.month-1]}"
    # ---- slot 1
    x = dict(DIA[i]); m = x.pop("m")
    if m != "arquivo":
        x["foto"] = foto(x.pop("f"))
        if m == "plantao":
            x["foto2"] = foto(x.pop("f2"))
        x.setdefault("barra", barra)
    itens.append(dict(slot="dia", hora="08:10", data=d, modelo=m, dados=x, leg=legenda("dia", i, DIA[i]["leg"]), titulo=DIA[i].get("titulo") or DIA[i].get("manchete") or "Sexta-feira 13: 37 views"))
    # ---- slot 2
    y = dict(M[i]); m2 = y.pop("m")
    y["foto"] = [foto(g) for g in y.pop("f")]
    itens.append(dict(slot="masc", hora="12:40", data=d, modelo=m2, dados=y, leg=legenda("masc", i, M[i]["leg"]),
                      titulo=M[i].get("topo") or M[i].get("titulo") or M[i].get("tema") or M[i].get("texto") or M[i].get("pergunta") or (M[i].get("nao","") + " x " + M[i].get("sim","")) or M[i].get("fala")))
    # ---- slot 3
    z = dict(PR[i]); z.pop("d", None)
    z["hora"] = "20:20"; z["data_txt"] = f"{d.day} {mes_min[d.month-1]} {d.year}"
    itens.append(dict(slot="print", hora="20:20", data=d, modelo="print", dados=z, leg=legenda("print", i, PR[i]["leg"]), titulo=PR[i]["texto"][0]))

# títulos curtos
for it in itens:
    it["titulo"] = (it["titulo"] or "").replace("|", " ").replace("*", "")[:90]

def render(sel=None):
    tmp = os.path.join(RAIZ, "saida", "_html"); os.makedirs(tmp, exist_ok=True)
    estouros = []
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 1080, "height": 1440})
        for n, it in enumerate(itens, 1):
            nome = f"{it['data'].isoformat()}_{it['hora'].replace(':','')}.jpg"
            it["arquivo"] = nome; it["id"] = f"M{n:03d}"
            if sel and it["id"] not in sel:
                continue
            destino = os.path.join(OUT, nome)
            if it["modelo"] == "arquivo":
                from PIL import Image
                Image.open(os.path.join(RAIZ, "ex", it["dados"]["arquivo"])).convert("RGB").save(destino, quality=90, optimize=True, progressive=True)
                continue
            f = os.path.join(tmp, nome.replace(".jpg", ".html"))
            open(f, "w").write(MODELOS[it["modelo"]](it["dados"]))
            pg.goto("file://" + f); pg.wait_for_function("window.__pronto===true", timeout=20000); pg.wait_for_timeout(120)
            est = pg.evaluate("[...document.querySelectorAll('[data-estouro]')].map(e=>e.className)")
            if est:
                estouros.append((it["id"], nome, est))
            pg.screenshot(path=destino, type="jpeg", quality=88)
        b.close()
    return estouros

if __name__ == "__main__":
    sel = set(sys.argv[1:]) or None
    est = render(sel)
    cal = [dict(id=it["id"], slot=it["slot"], formato=it["modelo"], data=it["data"].isoformat(), hora=it["hora"], fuso="America/Sao_Paulo",
                titulo=it["titulo"], imagem=f"memes/img/{it['arquivo']}", legenda=it["leg"]) for it in itens]
    json.dump(cal, open(os.path.join(RAIZ, "saida", "calendario.json"), "w"), ensure_ascii=False, indent=1)
    print("itens:", len(cal), "estouros:", est)
