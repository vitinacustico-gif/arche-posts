#!/usr/bin/env python3
"""Diz qual data a fábrica deve gerar agora e lista os títulos recentes (para não repetir).
uso: python3 gta6/fabrica/status.py   → imprime JSON {"hoje", "gerar", "faltam_dias", "recentes"}"""
import datetime, json, pathlib, zoneinfo

RAIZ = pathlib.Path(__file__).resolve().parents[1]
CFG = json.load(open(RAIZ / "fabrica/config.json", encoding="utf-8"))
hoje = datetime.datetime.now(zoneinfo.ZoneInfo("America/Sao_Paulo")).date()
cal_p = RAIZ / "calendario.json"
cal = json.load(open(cal_p, encoding="utf-8")) if cal_p.exists() else []
por_dia = {}
for c in cal:
    d = c.get("pauta", c["data"])
    por_dia[d] = por_dia.get(d, 0) + 1
INT = CFG.get("intensivo") or {}
SER = CFG.get("serie") or {}
def serie(d):
    if not SER: return None
    n = (datetime.date.fromisoformat(d) - datetime.date.fromisoformat(SER["de"])).days
    if 0 <= n < SER["dias"]:
        return {"dia": n + 1, "tema": SER["temas"][n % len(SER["temas"])]}
    return None
def meta(d):
    if INT and INT["de"] <= d <= INT["ate"]:
        return INT.get("por_dia", 10)
    return 10 + (1 if serie(d) else 0)
gerar = None
for k in range(1, 4):  # mantém até 3 dias prontos à frente
    d = (hoje + datetime.timedelta(days=k)).isoformat()
    if por_dia.get(d, 0) < meta(d):
        gerar = d
        break
lanc = datetime.date.fromisoformat(CFG["lancamento"])
alvo = datetime.date.fromisoformat(gerar) if gerar else None
recentes = [f'{c.get("pauta", c["data"])} {c["formato"]}: {c["titulo"]}' for c in cal if c["data"] >= (hoje - datetime.timedelta(days=7)).isoformat()]
print(json.dumps({"hoje": hoje.isoformat(), "gerar": gerar,
                  "faltam_dias_no_dia_gerado": (lanc - alvo).days if alvo else None,
                  "pecas_no_dia_gerado": meta(gerar) if gerar else None,
                  "serie_no_dia_gerado": serie(gerar) if gerar else None,
                  "dias_prontos": {d: n for d, n in sorted(por_dia.items()) if d >= hoje.isoformat()},
                  "recentes": recentes}, ensure_ascii=False, indent=1))
