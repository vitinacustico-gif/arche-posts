"""Monta o plano da série: datas (2 por dia, 07:00 e 17:35, a partir de 23/10/2026 17:35) e foto de cada slide,
espalhando as fotos para não repetir dentro do carrossel nem em carrosséis próximos."""
import json, datetime, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import roteiros_a, roteiros_b, roteiros_c
from fotos import GRUPOS, TAG, RESERVA, REPROVADAS

INICIO = datetime.date(2026, 10, 23)  # 1º post em 23/10 às 17:35 (pedido do Victor)
PRIMEIRO_SLOT = 1  # 0 = 07:00, 1 = 17:35
HORAS = ["07:00", "17:35"]
HASHTAGS = "#vidaadulta #empreendedorismo #pequenosnegocios #mentalidade #crescimentopessoal #Guarapari #ArcheAgencia"
EXCLUIR = {19566900, 7792752, 28704057, 8972265, 6694530, 6943430, 7984773, 18045304, 5332520, 31146885}  # já usadas no post de 16/10


def plano(falhas=()):
    C = roteiros_a.C + roteiros_b.C + roteiros_c.C
    falhas = set(falhas) | EXCLUIR | REPROVADAS
    usos, ultimo = {}, {}
    out = []
    for n, car in enumerate(C):
        tags = [car["capa_foto"]] + [s[2] for s in car["slides"]]
        usadas = set()
        fotos = []
        for tag in tags:
            g = TAG[tag]
            cand = [p for p in GRUPOS[g] if p not in falhas and p not in usadas]
            if not cand and g in RESERVA:
                cand = [p for p in GRUPOS[RESERVA[g]] if p not in falhas and p not in usadas]
            # menos usada primeiro; empate: a que foi usada há mais tempo
            cand.sort(key=lambda p: (usos.get(p, 0), ultimo.get(p, -99)))
            p = cand[0]
            usos[p] = usos.get(p, 0) + 1; ultimo[p] = n; usadas.add(p)
            fotos.append(p)
        k = n + PRIMEIRO_SLOT
        dia = INICIO + datetime.timedelta(days=k // 2)
        out.append({
            "id": car["id"], "titulo": car["titulo"], "data": dia.isoformat(), "hora": HORAS[k % 2],
            "fuso": "America/Sao_Paulo", "tipo": "carrossel",
            "capa": car["capa"], "slides_texto": [list(s[:2]) for s in car["slides"]],
            "fotos": fotos,
            "slides": [f"reflexao/{car['id']}/{i:02d}.jpg" for i in range(1, 11)],
            "legenda": car["legenda"].strip() + "\n\n" + HASHTAGS,
        })
    return out, usos


if __name__ == "__main__":
    p, usos = plano()
    json.dump(p, open(os.path.join(os.path.dirname(__file__), "plano.json"), "w"), ensure_ascii=False, indent=1)
    print(len(p), "carrosséis;", len(usos), "fotos distintas; máx. usos:", max(usos.values()))
    print(p[0]["data"], p[0]["hora"], "->", p[-1]["data"], p[-1]["hora"])
