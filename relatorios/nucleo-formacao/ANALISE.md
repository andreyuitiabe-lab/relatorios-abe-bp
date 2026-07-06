# Núcleo de Formação — Top Consumidores

> ANALISE.md criado retroativamente (jul/2026) na padronização do repo — detalhes de decisão não registrados na época.

## Pergunta original
Identificar os maiores consumidores de conteúdo de formação (certificações + cursos) por janela de 30/90/360 dias, com interesses por playlist.

## Estrutura
`index.html` + `data.json`. ⚠️ Sem `refresh.py` — o data.json foi gerado manualmente; se o relatório precisar de atualização, reconstruir o pipeline.

## Privacidade
O `data.json` original continha nome/email/telefone de 500 clientes num repo público — **anonimizado em jul/2026** (nomes → "Usuário NNN", contatos removidos) e versões antigas purgadas do histórico git. Se o Comercial precisar da lista nominal, rodar a query e entregar fora do repo.

## Pendências
- [ ] Criar `refresh.py` + salvar query em `queries/` se o relatório for atualizado
