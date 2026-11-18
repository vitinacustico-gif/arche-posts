# Fábrica de Reels (2 publicações por hora)

Desde 18/11 o feed do @nerd_gta tem 36 horários por dia: 00:00, 00:30 e de 7:00 às 23:30, de meia em meia hora.
A fábrica diária ocupa 11 (posts, carrosséis, comunicado, série); a **fábrica de Reels** preenche o resto com Reels narrados, sempre 45+ min antes do horário.

## Visual variado (pedido do Victor: "parece tudo a mesma coisa")
O motor tem 5 estilos de Reel: neon, manchete, cinema, tweet e impacto. Ele gira sozinho pela meia hora (dois Reels seguidos nunca ficam iguais). Só ponha "estilo" no item para forçar quando combinar muito: "manchete" para notícia, "tweet" para opinião/pergunta, "impacto" para número/lista, "cinema" para personagem/lugar.

## Cada execução
1. `python3 gta6/fabrica/status_reels.py` → `slots` (até 6 horários vazios), `stories_livres` por dia e `recentes` (não repetir tema nem título).
   Sem slots: termine sem mensagem.
2. Pesquisa rápida (WebSearch modo standard, várias no mesmo turno): "GTA 6 notícias hoje", "GTA 6 news", "GTA 6 dicas" e, a partir de 19/11, "GTA 6 review", "GTA 6 easter egg", "GTA 6 how to". Abra com WebFetch o que for virar fato. Guarde as URLs em `fontes` do item.
3. Um Reel por slot, **assuntos variados** no mesmo lote (não repita categoria seguida): notícia do dia, dica prática, curiosidade/easter egg, personagem, região do mapa, veículo, arma, animal, humor da espera ou do lançamento, enquete (A ou B), comparação GTA 5 x GTA 6, oferta (jogo/console/acessório com link na bio, sem preço fixo), pergunta pra comunidade.
   Item na pauta `gta6/pautas/<data>.json` (acrescente, não apague nada):
   `{"id": slot.id, "hora": slot.hora, "formato": "reel", "linhas": [título curto], "tag": "GTA 6", "cta_bio": "grupo|guia|ofertas|comunidade", "postar_story": true/false, "roteiro": [4 cenas {"fala","tela","imagem"}], "legenda": "...", "fontes": [...]}`
   - 1ª fala = gancho em até 7 palavras (pergunta, número ou aviso). Última = pedido de comentário, salvar ou compartilhar.
   - Fala curta e falada (números por extenso quando soa melhor; "PlayStation 5", não "PS5"). Total do Reel: 10 a 20 segundos.
   - `tela` com no máximo ~26 caracteres. Imagens de `gta6/banco/oficial/` (rode `ls`), uma diferente por cena, sem repetir imagem no mesmo lote.
   - `postar_story: true` só em até `stories_livres[data]` itens (os mais fortes); o resto `false`.
   - Fato só com fonte lida hoje. Nada de vazamento. Sem fonte = humor, enquete ou opinião.
4. Voz (GRATUITA, sem ElevenLabs): escreva `gta6/narracao_job.json` (`[{"path": "gta6/narracao/<data>-<id>/NN.mp3", "text": fala}]`), commit + push. No COMPOSIO_REMOTE_WORKBENCH: `pip install -q edge-tts`, baixe o job pelo raw do GitHub, gere cada fala com `edge_tts.Communicate(texto, "pt-BR-AntonioNeural", rate="+10%").save(arquivo)` (até 4 ao mesmo tempo) e suba todos num commit só pela API Git (proxy_execute "github": blobs → tree com base_tree → commit → PATCH refs/heads/gta6). Se falhar, siga sem voz: o motor faz o Reel com legenda animada e música.
5. `git pull --rebase origin gta6`, depois `python3 gta6/fabrica/gerar.py gta6/pautas/<data>.json --so <ids>` (timeout 20 min). Confira 1 quadro de cada vídeo (ffmpeg -ss 3 -frames:v 1) com Read.
6. `python3 gta6/fabrica/midia_branch.py <data>` (sobe a mídia no branch midia-<data>, somando ao que já estava, e grava "base" no calendário). Se o push dele for recusado (outra fábrica subiu junto), rode o mesmo comando de novo.
7. `git add gta6 && git commit -m "GTA 6: Reels <horários>" && git push origin gta6` (se recusar: `git pull --rebase` e tente de novo).
8. Só mande mensagem a Victor se algo falhar (1 linha).
