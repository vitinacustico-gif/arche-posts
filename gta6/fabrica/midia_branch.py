#!/usr/bin/env python3
"""Sobe a mídia de um dia num branch órfão 'midia-AAAA-MM-DD' (sem histórico, para o repositório não inchar)
e grava "base" nas entradas do calendário desse dia. Uso: python3 gta6/fabrica/midia_branch.py AAAA-MM-DD
O branch pode ser apagado 3 dias depois de publicado (git push origin --delete midia-AAAA-MM-DD)."""
import json, os, pathlib, subprocess, sys, tempfile

RAIZ = pathlib.Path(__file__).resolve().parents[2]
data = sys.argv[1]
pasta = RAIZ / "gta6" / "midia" / data
ramo = f"midia-{data}"


def git(*a, env=None, inp=None):
    return subprocess.run(["git", *a], cwd=RAIZ, env=env, input=inp, capture_output=True, text=True, check=True).stdout.strip()


idx = tempfile.mktemp()
env = dict(os.environ, GIT_INDEX_FILE=idx)
pai = None
try:
    git("fetch", "-q", "--depth", "1", "origin", f"refs/heads/{ramo}")
    pai = git("rev-parse", "FETCH_HEAD")
    git("read-tree", pai, env=env)  # mantém o que já subiu antes neste dia
except subprocess.CalledProcessError:
    pass
arquivos = sorted(p for p in pasta.iterdir() if p.is_file())
for p in arquivos:
    sha = git("hash-object", "-w", str(p))
    git("update-index", "--add", "--cacheinfo", f"100644,{sha},{p.relative_to(RAIZ).as_posix()}", env=env)
arvore = git("write-tree", env=env)
commit = git("commit-tree", arvore, *(["-p", pai] if pai else []), "-m", f"mídia de {data}", env=dict(env, GIT_AUTHOR_NAME="Claude", GIT_AUTHOR_EMAIL="noreply@anthropic.com",
             GIT_COMMITTER_NAME="Claude", GIT_COMMITTER_EMAIL="noreply@anthropic.com"))
git("push", "origin", f"{commit}:refs/heads/{ramo}")
cal_p = RAIZ / "gta6" / "calendario.json"
cal = json.loads(cal_p.read_text(encoding="utf-8"))
n = 0
for c in cal:
    if c.get("pauta", c["data"]) == data:
        c["base"] = ramo; n += 1
cal_p.write_text(json.dumps(cal, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({"ramo": ramo, "arquivos": len(arquivos), "entradas": n}))
