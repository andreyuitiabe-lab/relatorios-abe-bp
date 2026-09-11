# Mecenas — Bolsas: vendidas × distribuídas

## Pergunta original

Pedido ao André (11/09/2026): o programa Mecenas (filantropia — doadores compram bolsas de
assinatura Premium ou de certificação para alunos de instituições parceiras) é antigo e não teve
a atenção operacional devida. Quantas bolsas já vendemos, quantas já distribuímos e qual a
situação atual?

## Decisões de abordagem

- **Vendas na `fct_transactions`** com o filtro canônico BOLSA da wiki (`mecenas.md`): exclui
  Mecenas Solidário/Patrono/Apoiador (população separada por decisão de negócio de ago/2026),
  order bumps e pagamentos < R$ 1.000. Unidade = **bolsa-ano** (renovação conta de novo).
- **Quantidade de bolsas extraída do nome da oferta.** O regex da wiki foi corrigido nesta análise:
  precisa de `-?` para pegar o padrão antigo "Mecenas 1 - Bolsas" (~700 tx de 2021–23 que sumiam
  da soma). Ofertas de preço unitário sem contagem (`Mecenas - R$ 1188/1668`) = 1 bolsa.
- **Certificação × padrão pelo plano**: `mecenas_ciencia-politica`, `mecenas_travessia`,
  `mecenas_metodo-bp`, `mecenas_travessia-familia` = certificação; resto = padrão (Premium).
- **Distribuição na `dim_subscriptions`**: união de `nm_create_reason_type = 'mecenas'` (upload
  via Caverna, "Aluno de instituição parceira" — o grosso), `nm_type = 'donator'` (legado
  2020–ago/2022) e planos `bolsa-mecenas-*` (sistema novo, mar/2026). Campo descoberto nesta
  análise — não estava documentado em lugar nenhum.
- **Instituição extraída do `nm_reason`** só no padrão "Uploaded from Caverna ..." (nos outros
  formatos o texto restante é o nome do operador BP, não da instituição). Limpeza remove
  boilerplate, e-mails e ids hex de 24 chars.
- **Planilha do CS** (controle antigo, ref. 04/03/2026) entra como constante no `refresh.py` —
  é a única fonte do vínculo beneficiário→instituição completo.
- Validada contra a query antiga do André (base = assinantes mecenas → e-mail → transações):
  91.295 bolsas; com o regex corrigido, 92.352 — 0,25% da contagem canônica. Ressalva da query
  antiga: `receita_acumulada` soma TODAS as compras da pessoa (R$ 88M), não só Mecenas (R$ 52,7M).

## Achados principais (11/09/2026)

- **92.588 bolsas-ano vendidas** (89.286 padrão + 3.302 certificação), R$ 52,7M, 9.406 contas
  doadoras, 2020–2026. Mais 82 vendas sem número na oferta (R$ 967k ≈ 530–765 bolsas — a maior:
  Mecenas Funding BP TV, R$ 500k).
- **49.097 assinaturas-bolsa ativadas** para **30.143 contas beneficiárias** distintas.
- **Só 1.749 contas vigentes hoje** (2.022 assinaturas). A planilha registrava 3.378 ativos em
  mar/2026 — metade expirou em 6 meses sem renovação.
- **O gap venda × distribuição explodiu**: 2025 vendeu 28,7k bolsas (recorde) e ativou 4,0k
  contas (14%); 2026: 9,8k vendidas, 708 ativadas (7%). Agregado histórico: ~53%.
- **Certificação foi campanha pontual**: Travessia 2023–24, Ciência Política jul–out/2024; hoje
  praticamente todas canceladas.
- **O DW não sabe a instituição**: só 1.107 contas (3,7%) têm instituição registrada no
  `nm_reason`. Top: IFL BH (226), UJL (148), Sanchez Del Rio (111), RECEBS (88), Atlantos (76).
- **Por produto, a certificação distribui ainda menos que a assinatura**: Ciência Política vendeu
  1.935 bolsas e distribuiu 396 assinaturas (20%); Travessia 1.267 → 145 (11%). Premium: 89,3k →
  48,5k (54%). Exceção: Travessia da Família distribuiu mais do que vendeu (12 → 23, provisionada
  à parte).

## Pendências / próximos passos

- Engajamento dos bolsistas vigentes (`obt_kafka__view_sessions` por e-mail) — a planilha tem
  colunas de horas/mês, dá para reproduzir e automatizar.
- Cruzar doador → instituição → bolsas paradas (vendidas e nunca ativadas) por cohort.
- Conferir com o time do Mecenas se o sistema novo (`bolsa-mecenas-*`) vai substituir o upload
  via Caverna — se sim, o relatório passa a acompanhar a migração.

## Queries

| Arquivo | O que faz |
|---|---|
| [01_vendas_bolsas.sql](queries/01_vendas_bolsas.sql) | Bolsas vendidas por ano × tipo (filtro canônico) |
| [02_vendas_sem_numero.sql](queries/02_vendas_sem_numero.sql) | Vendas sem número de bolsas na oferta + estimativa |
| [03_distribuicao.sql](queries/03_distribuicao.sql) | Contas ativadas por ano × sistema de provisionamento |
| [04_instituicoes.sql](queries/04_instituicoes.sql) | Instituições extraídas do nm_reason (Caverna) |
| [05_totais.sql](queries/05_totais.sql) | KPIs distintos (doadores, beneficiários, vigentes, cobertura de instituição) |
| [06_por_produto.sql](queries/06_por_produto.sql) | Vendido × distribuído por produto entregue (Premium / cada certificação) |

## Wiki atualizada

- `wiki-bp/pages/mecenas.md`: regex de bolsas corrigido (`-?`), seção "Bolsas doadas — números de
  referência" e seção "Lado beneficiário — bolsas DISTRIBUÍDAS" (o `nm_create_reason_type` não
  estava documentado).
