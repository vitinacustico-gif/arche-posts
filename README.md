# Arche Agência · posts semanais

Artes e calendário dos 50 posts da Arche Agência (@archeagencia).

- `feed/NN.jpg`: post do feed em 3:4 (1080×1440).
- `story/NN.jpg`: versão para stories em 9:16 (1080×1920).
- `calendario.json`: data de publicação (post 1 em 10/10/2026 às 11h; depois toda quarta às 11h, horário de Brasília), número do post e legenda.

O agendamento semanal lê este calendário e publica o post do dia no feed e nos stories.
Para trocar uma legenda ou uma data, basta editar o `calendario.json`.

## Carrosséis: "O manual que não veio com o CNPJ"

- `carrosseis/NN/MM.jpg`: 20 carrosséis educativos (3:4, 1080×1440), sem fotos, de 7 a 9 slides cada.
- `carrosseis.json`: data de publicação (toda terça às 11h, horário de Brasília, de 13/10/2026 a 23/02/2027), lista de slides e legenda.

Uma tarefa agendada separada lê esse calendário e publica o carrossel do dia no feed.
