# Eventos USA — Listas para eventos presenciais

> Entrega tipo **lista/export** (sem relatório HTML). ANALISE.md criado retroativamente (jul/2026).

## Pergunta original
Gerar listas de convidados para eventos presenciais nos EUA: (1) lista geral (membros ativos e ex-membros, dedup por email, com classificação) e (2) Membros Fundadores Big Picture (com tier e país/estado).

## Decisões de abordagem
- Dedup por email; prioridade quando a pessoa cai em mais de um grupo: Membro ativo > Ex-membro
- Big Picture tratado em lista separada; leads ficaram fora do escopo

## Queries
| Query | O que faz |
|---|---|
| [lista_eventos_usa.sql](queries/lista_eventos_usa.sql) | Lista única dedup com `classificacao` |
| [fundadores_big_picture.sql](queries/fundadores_big_picture.sql) | Membros Fundadores Big Picture |

## Privacidade
Os CSVs de output (nome/email/telefone/CPF/endereço) estavam commitados num repo público — **removidos e purgados do histórico em jul/2026**. Backup local em `~/meu_projeto/BigQuery/listas-locais/`. Outputs de lista nunca entram neste repo (`.gitignore` raiz bloqueia `*.csv`).
