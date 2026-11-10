#!/usr/bin/env python3
"""Capas e stories dos destaques do perfil (funil: entender → confiar → entrar no grupo → comprar).
uso: python3 gta6/fabrica/destaques.py  → gta6/destaques/capa_<id>.jpg e story_<id>.jpg"""
import pathlib, sys
sys.argv = sys.argv[:1]
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import gerar as g
from PIL import Image, ImageDraw

SAIDA = g.RAIZ / "destaques"
SAIDA.mkdir(exist_ok=True)
W, H = 1080, 1920

DESTAQUES = [
    {"id": "1-vip", "icone": "VIP", "nome": "GRUPO VIP", "titulo": ["GRUPO VIP", "NO WHATSAPP"],
     "itens": ["Ofertas de PS5, Xbox e acessórios todo dia", "Alerta de golpe antes de você comprar",
               "Dicas do GTA 6 antes de todo mundo", "Grátis. Sai quando quiser"],
     "cta": "ENTRA PELO LINK DA BIO"},
    {"id": "2-guia", "icone": "GUIA", "nome": "GUIA", "titulo": ["O GUIA DO", "GTA 6 EM PT-BR"],
     "itens": ["Primeiras horas sem se perder", "Como fazer dinheiro rápido",
               "Veículos e lugares escondidos de Leonida", "Lista de espera com preço de lançamento"],
     "cta": "LISTA DE ESPERA NO LINK DA BIO"},
    {"id": "3-dia19", "icone": "19", "nome": "DIA 19", "titulo": ["19/11", "À MEIA-NOITE"],
     "itens": ["Libera à 0h no horário local. No Brasil, 0h de 19/11",
               "Só PS5 e Xbox Series X|S. PC sem data",
               "Standard R$ 449,90 · Ultimate R$ 549,90",
               "Pré-venda até 20/11: Pacote Vintage Vice City + 1 mês de GTA+"],
     "cta": "ATIVA AS NOTIFICAÇÕES"},
    {"id": "4-ofertas", "icone": "$", "nome": "OFERTAS", "titulo": ["MONTE SEU", "SETUP"],
     "itens": ["Console, controle extra e headset", "Armazenamento extra pro jogo",
               "Cartão presente PSN e Xbox", "As melhores ofertas saem primeiro no grupo VIP"],
     "cta": "OFERTAS NO LINK DA BIO"},
    {"id": "5-faq", "icone": "?", "nome": "DÚVIDAS", "titulo": ["PERGUNTAS", "FREQUENTES"],
     "itens": ["Vai ter no PC? Ainda sem data anunciada",
               "Roda no PS4? Não. Só PS5 e Xbox Series X|S",
               "Onde comprar seguro? PlayStation Store e Loja Xbox",
               "Chave muito barata? Desconfie: é golpe"],
     "cta": "MANDA SUA DÚVIDA NO DIRECT"},
    {"id": "6-sobre", "icone": "@", "nome": "SOBRE", "titulo": ["NERD", "GTA"],
     "itens": ["Tudo do GTA 6 em português", "Notícias com fonte, dicas e humor todo dia",
               "Comunidade de quem vai jogar no Brasil",
               "Página de fã, sem vínculo com a Rockstar Games"],
     "cta": "SEGUE E ATIVA O SININHO"},
]


def capa(d):
    img = Image.fromarray(g.Cena(W, H, horizonte=0.74, sol=0.30, escurecer=0.6, grao=2).render(0.5)).convert("RGBA")
    camada = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(camada)
    r = 300
    cx, cy = W // 2, H // 2
    for i in range(r, 0, -2):  # disco em degradê magenta → laranja
        k = i / r
        cor = tuple(int(a * k + b * (1 - k)) for a, b in zip(g.C["magenta"], g.C["laranja"]))
        dr.ellipse([cx - i, cy - i, cx + i, cy + i], fill=cor + (255,))
    dr.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(255, 255, 255, 255), width=10)
    img.alpha_composite(camada)
    t = g.bloco_titulo([d["icone"]], int(r * 1.45), tam=260, tam_min=90, altura_max=int(r * 1.2))
    g.colar(img, t, cx - t.width / 2, cy - t.height / 2 + 6)
    img.convert("RGB").save(SAIDA / f"capa_{d['id']}.jpg", quality=92)


def story(d):
    img = Image.fromarray(g.Cena(W, H, horizonte=0.80, sol=0.24, escurecer=0.7, grao=2).render(0.2)).convert("RGBA")
    y = 250
    p = g.pilula(d["nome"], 34)
    g.colar(img, p, (W - p.width) / 2, y); y += p.height + 40
    t = g.bloco_titulo(d["titulo"], W - 140, tam=170, destaque=[1])
    g.colar(img, t, (W - t.width) / 2, y); y += t.height + 50
    for it in d["itens"]:
        b = g.bloco_texto("✓  " + it if False else it, W - 240, 44, "700", alinhar="left")
        dr = ImageDraw.Draw(img)
        dr.ellipse([70, y + 34, 106, y + 70], fill=g.C["magenta"] + (255,))
        g.colar(img, b, 120, y); y += b.height + 18
    c = g.pilula(d["cta"], 36, fundo=(255, 255, 255), cor=(12, 4, 20), pad=(36, 22))
    g.colar(img, c, (W - c.width) / 2, max(y + 40, 1480))
    dr = ImageDraw.Draw(img)
    f = g.ft(g.INTER["900"], 36)
    dr.text(((W - f.getlength(g.CFG["handle"])) / 2, 140), g.CFG["handle"], font=f, fill=(255, 255, 255, 230))
    img.convert("RGB").save(SAIDA / f"story_{d['id']}.jpg", quality=92)


for d in DESTAQUES:
    capa(d)
    story(d)
    print("ok", d["id"])
