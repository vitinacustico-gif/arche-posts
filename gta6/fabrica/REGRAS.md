# Fábrica GTA 6 — regras da pauta diária

Projeto do Victor (Arche Agência): perfil de fã de GTA 6 no Instagram, 10 peças por dia, levando o público para o link da bio (grupo VIP de ofertas no WhatsApp, vitrine de afiliados e guia em PT-BR).

## Arquivo de pauta: `gta6/pautas/AAAA-MM-DD.json`

```json
{"data": "AAAA-MM-DD", "fontes": ["url aberta e lida", "..."], "itens": [ ...10 itens... ]}
```

Ordem dos 10 itens = ordem dos horários do `config.json` (08:07, 10:07, 11:07, 12:07, 13:07, 15:07, 17:07, 19:07, 20:07, 21:07).
Mistura do dia: 4 `reel` (posições 1, 4, 7, 10), 3 `carrossel` (2, 6, 9) e 3 `post` (3, 5, 8).
**Modo intensivo** (`config.json` → `intensivo`, de 11 a 13/11): 18 peças por dia, 1 por hora das 7h à 0h, seguindo a `grade` (hora e formato). Cada item leva o campo `"hora"` da grade; a peça `"24:00"` sai às 00:00 do dia seguinte. O `status.py` já sabe quantas peças cada data precisa.
Todo item ganha automaticamente uma versão de story (`<id>_story.jpg`, ou o próprio vídeo no reel): o publicador posta no feed e no story.
**Post "comunicado oficial"** (`"tipo":"documento"`, formato viral de compartilhar): papel sobre a mesa com título formal, texto com **negrito**, campos "Motivo: GTA 6." e um retorno engraçado, carimbo, foto 3x4 oficial e assinatura. Campos: `titulo_doc`, `corpo`, `campos` [[rótulo, valor, destaque_vermelho]], `rodape_doc`, `carimbo`, `assinatura` [2 linhas], `imagem` (fundo, banco/oficial), `foto_3x4` (banco/oficial) e `foco_3x4` [x, y, zoom] centrado no rosto, `tag`. Legenda sempre pedindo pra mandar pra alguém (chefe, família, amor, grupo). Use no máximo 1 por dia, variando o destinatário.
**Carrossel "tela dividida"** (`"estilo": "grade"`): cada slide junta 2 a 6 imagens oficiais, cada painel com um rótulo curto (`rot`) e uma linha de informação (`txt`). Formato: `{"formato":"carrossel","estilo":"grade","capa":{"titulo":[..],"sub":"..","fotos":[4 caminhos]},"puxa_capa":"Arrasta","slides":[{"titulo":"..","puxa":"..","paineis":[{"foto":"gta6/banco/oficial/..","rot":"..","txt":".."}]}],"fecho":{"foto":"..","titulo":[..],"texto":".."},"legenda":"..","cta_bio":".."}`. Use pelo menos 1 por dia, sempre denso de informação com fonte.
Carrossel pode usar imagens oficiais em vez de temas: `"fotos": ["gta6/banco/oficial/arquivo.jpg", ...]` (na ordem).

### reel
`{"id":"01","formato":"reel","linhas":["FALTAM","5 DIAS"],"destaque":[1],"sub":"frase curta","cta":["ATIVA","O SININHO"],"cta_sub":"frase curta","tag":"CONTAGEM","legenda":"..."}`
- `linhas`: 2 ou 3 linhas, no máximo ~14 caracteres cada (a fonte é larga). `destaque`: índices da linha em amarelo.
- A 1ª linha aparece já no quadro 0: ela é o gancho.

### carrossel (SEMPRE infinito e inteligente — pedido do Victor, nada genérico)
`{"id":"02","formato":"carrossel","capa":["LINHA 1","LINHA 2"],"destaque":[1],"sub":"gancho de curiosidade","puxa_capa":"COMEÇA AQUI  >>","fotos":["miami","carro"],"slides":[{"titulo":"até ~28 caracteres","texto":"1 ou 2 frases","puxa":"pergunta curta que puxa o próximo"}],"fecho":{"titulo":["LINHA","LINHA"],"texto":"pedido de ação específico do tema"},"legenda":"..."}`
- O motor monta um panorâmico contínuo com FOTOS REAIS do banco licenciado (gta6/banco/fotos, Pexels), emendadas em diagonal com neon, uma linha que atravessa todos os slides e os números nas emendas. Não use fundo gerado.
- `fotos`: 1 ou 2 temas que combinem com o assunto: miami, policia, carro, jacare, ceu, noite, luxo, gamer.
- `sub` da capa = promessa ou curiosidade concreta ("O nº 9 quase ninguém sabe", "O 3º rouba contas toda semana"). Nunca "confira", "veja", "tudo sobre".
- Cada slide tem `puxa`: uma pergunta ou frase curta que obriga a arrastar ("E o PC?", "Agora o absurdo"). O último slide de conteúdo também pode ter puxa para o fecho.
- `fecho` sempre específico do tema (pergunta para comentar, marcar alguém ou salvar), nunca genérico.
- 4 a 8 slides (máximo 10 imagens no total; com 9 ou mais slides o fecho sai sozinho).

### post
`{"id":"03","formato":"post","tipo":"noticia|enquete|contagem|frase","linhas":[...],"destaque":[...],"texto":"(noticia)","fonte":"(noticia)","opcoes":["A","B"] (enquete),"sub":"...","imagem":"gta6/banco/oficial/<arquivo>.jpg","cta_bio":"grupo|guia|ofertas|comunidade","legenda":"..."}`
- **Todo post leva `imagem`** do `gta6/banco/oficial/` (imagens oficiais que o Victor subiu). Combine o tema: enquete de personagem → `pessoa-*`; notícia, lugar ou contagem → `lugar-*`; humor e frase → `arte-*`. Rode `ls gta6/banco/oficial` e não repita a mesma imagem nos últimos 7 dias (confira em `calendario.json`).
- Formatos que viralizam (modelar o formato, nunca copiar texto de ninguém): enquete A ou B, notícia urgente com fonte, contagem regressiva, "você reparou nisso?" (detalhe visível na imagem oficial), personagem em destaque, frase de humor da espera, "marca o amigo que...".

### legenda
Só o corpo: gancho forte de 1 linha (curiosidade, número ou polêmica leve) + 1 linha com pedido de ação (comenta, salva, marca, compartilha). Toda peça leva `cta_bio` escolhido pelo tema: `grupo` (ofertas e avisos), `guia` (lista de espera do guia), `ofertas` (setup, console, acessório), `comunidade` (enquete, papo, nostalgia). O gerador acrescenta o CTA do link na bio correspondente, o aviso de página de fã e as hashtags. Nos 3 posts do dia, use pelo menos 3 CTAs diferentes.

Antes de escolher os temas do dia, leia `gta6/fabrica/SUGESTOES.md` e use a primeira pauta não riscada (marque [x] depois de usar).

## Série Nerd GTA (30 dias, 11/11 a 10/12)
Se o `status.py` devolver `serie_no_dia_gerado`, o dia tem 1 peça a mais: um carrossel "tela dividida" do tema indicado, seguindo `gta6/fabrica/SERIE.md` (assunto do dia, regras de cheats e de vazamento). Em dias normais, esse item entra com `"hora":"14:07"` e `"serie":"<tema>"`; o total do dia passa a ser 11 (`pecas_no_dia_gerado`). Marque [feito] na tabela do SERIE.md.

## Reels narrados (obrigatório desde 12/11)
Todo reel leva `"roteiro"`: 3 a 5 cenas `{"fala": "...", "tela": "TEXTO CURTO", "imagem": "gta6/banco/oficial/..."}`. A 1ª fala é o gancho (pergunta, aviso ou número) e a última pede comentário ou compartilhamento. Fala curta e falada (números por extenso quando soa melhor, "PlayStation 5" em vez de "PS5"). Cada cena com imagem diferente, sem repetir no mesmo dia.
Como gerar a voz (ElevenLabs via Composio, voz `TX3LPaxmHKxFdv7VOQHJ`, modelo `eleven_multilingual_v2`, stability 0.4, similarity 0.8, style 0.3):
1. Escreva `gta6/narracao_job.json` = lista `[{"path": "gta6/narracao/<data>-<id>/NN.mp3", "text": fala}]`, faça commit e push.
2. No COMPOSIO_REMOTE_WORKBENCH: baixe o job pelo raw do GitHub, chame `ELEVENLABS_TEXT_TO_SPEECH` para cada fala (8 em paralelo), baixe o `data.file.s3url` com requests e suba todos os mp3 num commit só pela API Git do GitHub (`proxy_execute` com toolkit "github": blobs → tree com base_tree → commit → PATCH refs/heads/gta6).
3. `git pull` e rode o gerar.py normalmente: o reel com roteiro sai narrado (narrado.py).
Se a voz falhar (cota do plano grátis: 10 mil caracteres por mês), remova o "roteiro" do item e gere o reel no estilo antigo, e avise Victor na mensagem final.

## Links de afiliado
Os produtos com link de afiliado do Mercado Livre estão em `gta6/afiliados/produtos.json`. Nas mensagens do WhatsApp (gta6/whatsapp/), use esses links de verdade no lugar de "[COLE AQUI O LINK DE AFILIADO]", escolhendo o produto que combina com o tema do dia (o jogo GTA VI para PS5 é o principal até o dia 19). Não escreva preço fixo: muda todo dia.

## Regras de conteúdo (obrigatórias)
1. **Nada de material de outros criadores.** Nunca baixar nem repostar vídeo, print ou arte de outras páginas. Imagens oficiais só as do `gta6/banco/oficial/` (enviadas pelo Victor), sempre dentro da moldura do `gerar.py`; fotos de cenário só do `gta6/banco/fotos/`.
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
