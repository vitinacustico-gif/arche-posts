# GTA 6 · Leonida Brasil (perfil de fã)

Fábrica automática de conteúdo do perfil de GTA 6 do Victor (Arche Agência).

- `fabrica/gerar.py`: gera as peças de um dia a partir de `pautas/AAAA-MM-DD.json` (arte 100% gerada por código).
- `fabrica/REGRAS.md`: regras da pauta diária (formato, fatos com fonte, nada de material de terceiros).
- `fabrica/config.json`: @ do perfil, horários, hashtags e cores. Mudou o @? Troque aqui e regenere.
- `midia/AAAA-MM-DD/`: Reels (mp4 + capa), carrosséis (`ID_NN.jpg`) e posts.
- `calendario.json`: o que publica em cada horário (lido pelo publicador agendado).
- `whatsapp/AAAA-MM-DD.md`: 3 mensagens prontas por dia para o grupo VIP.

A fonte de títulos (Pricedown, licença Typodermic) está criptografada em `fabrica/fonts/pricedown.enc`
e só abre com a chave privada do Victor: o arquivo da fonte não é distribuído.
