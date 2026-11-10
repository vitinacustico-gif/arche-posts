# Fábrica GTA 6 — regras da pauta diária

Projeto do Victor (Arche Agência): perfil de fã de GTA 6 no Instagram, 10 peças por dia, levando o público para o link da bio (grupo VIP de ofertas no WhatsApp, vitrine de afiliados e guia em PT-BR).

## Arquivo de pauta: `gta6/pautas/AAAA-MM-DD.json`

```json
{"data": "AAAA-MM-DD", "fontes": ["url aberta e lida", "..."], "itens": [ ...10 itens... ]}
```

Ordem dos 10 itens = ordem dos horários do `config.json` (08:07, 10:07, 11:07, 12:07, 13:07, 15:07, 17:07, 19:07, 20:07, 21:07).
Mistura do dia: 4 `reel` (posições 1, 4, 7, 10), 3 `carrossel` (2, 6, 9) e 3 `post` (3, 5, 8).

### reel
`{"id":"01","formato":"reel","linhas":["FALTAM","5 DIAS"],"destaque":[1],"sub":"frase curta","cta":["ATIVA","O SININHO"],"cta_sub":"frase curta","tag":"CONTAGEM","legenda":"..."}`
- `linhas`: 2 ou 3 linhas, no máximo ~14 caracteres cada (a fonte é larga). `destaque`: índices da linha em amarelo.
- A 1ª linha aparece já no quadro 0: ela é o gancho.

### carrossel
`{"id":"02","formato":"carrossel","capa":["LINHA 1","LINHA 2"],"destaque":[1],"sub":"...","slides":[{"titulo":"até ~28 caracteres","texto":"1 ou 2 frases"}],"legenda":"..."}`
- 4 a 8 slides (máximo 10 imagens no total; com 9 ou mais slides o fecho sai sozinho).

### post
`{"id":"03","formato":"post","tipo":"noticia|enquete|contagem|frase","linhas":[...],"destaque":[...],"texto":"(noticia)","fonte":"(noticia)","opcoes":["A","B"] (enquete),"sub":"...","legenda":"..."}`

### legenda
Só o corpo: gancho de 1 linha + 1 linha com pergunta ou pedido (comenta, salva, marca). O gerador acrescenta sozinho o CTA do link na bio, o aviso de página de fã e as hashtags.

## Regras de conteúdo (obrigatórias)
1. **Nada de material de terceiros.** Nunca baixar nem repostar vídeo, print ou arte de outro criador ou da Rockstar. Toda arte é gerada pelo `gerar.py`.
2. **Fato só com fonte.** Toda informação factual vem de página aberta e lida no dia (WebSearch + WebFetch) e entra em `fontes`. Sem fonte, vira opinião, enquete ou humor. Nunca inventar números, datas, preços, conteúdos de edição ou recursos do jogo.
3. **Sem vazamento, pirataria, hack, mod de dinheiro, venda de conta.**
4. **Sem spoiler da história** depois do lançamento sem avisar na 1ª linha ("ALERTA DE SPOILER").
5. **Não repetir** tema ou gancho dos últimos 7 dias (o `status.py` lista os títulos recentes).
6. Pelo menos 1 peça por dia chama para o grupo VIP e 1 para o guia (lista de espera ou venda).
7. Português do Brasil, tom de fã, frases curtas, humor leve. Sem palavrão. Público pode ter menores: nada de conteúdo adulto.

## Fases
- Até 18/11: contagem regressiva diária (reel das 08:07), notícias oficiais, enquetes, checklists, humor da espera.
- 19/11 a 26/11: lançamento. Notícias de recepção (com fonte), dicas gerais seguras, enquetes, humor. Dicas de gameplay só se houver fonte confiável publicada.
- 27/11 a 01/12: Black Friday. Peças de setup e ofertas levando ao grupo VIP (sem preço inventado).
- Depois: dicas, segredos e curiosidades com fonte, enquetes e chamadas para o guia.

## Mensagens do grupo VIP
Junto com a pauta, escreva `gta6/whatsapp/AAAA-MM-DD.md` com 3 mensagens prontas (9h oferta, 13h notícia ou dica, 19h enquete ou oferta relâmpago). Oferta sem link de afiliado conhecido vira "[COLE AQUI O LINK DE AFILIADO]".
