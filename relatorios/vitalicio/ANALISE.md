# Análise: Vitalício — Base, LTV e Oportunidades

**Data:** mai/2026  
**Status:** concluída (base documentada; oportunidades em aberto para ação Comercial)  
**Relatório:** [index.html](index.html)

---

## Pergunta original

Entender o tamanho e comportamento da base Vitalício: quem são, quanto gastam no total (LTV), qual a receita incremental pós-compra, quais são as oportunidades de upgrade/upsell e como se compara com assinatura.

---

## Decisões de abordagem

- LTV calculado como entrada + todas as transações aprovadas posteriores do mesmo contato (não só receita Vitalício)
- Upgrades identificados por mudança de `nm_gateway_plan` entre compras ordenadas por `dt_ordered_at`
- Comparação com assinatura feita contra decil 9 de assinantes (mais fiéis), não a média — para comparação justa
- CEC/Retiro: identificados por `nm_gateway_plan LIKE '%cec%'` e `LIKE '%retiro%'`

---

## Achados principais

- Base total: 61.818 compradores, R$130M de entrada, R$167M de LTV (+29% incremental)
- Black (lançado out/2024): já lidera receita anual (R$30,8M em 2025), ticket médio R$4.374
- 17,5% dos compradores voltam a comprar — upgrade de tier é o maior driver (R$22,8M)
- Comercial responde por 88,5% da receita incremental pós-vitalício
- Vitalício supera assinante decil 9 em todas as faixas — vantagem estrutural, não de perfil
- CEC: LTV médio R$51.613 (13× a média) | Retiro: LTV médio R$79.506 (20× a média)
- ~6.250 ex-assinantes recuperados via Vitalício sem campanha específica de reativação

---

## Pendências / próximos passos

- [ ] ~21.000 GBB sem upgrade para Black → oportunidade estimada R$10–15M via Comercial
- [ ] 6.563 compradores de certificação nunca viraram Black → leads quentes (gasto médio prévio R$1.932)
- [ ] ~230 leads perfil CEC/Retiro (Black + ex-Mecenas + alto consumo) → ticket R$28–39k
- [ ] ~24.500 Básico sem upsell → upgrade, Mecenas ou Clube do Livro
- [ ] Análise de timing ótimo para abordagem Comercial (quantos dias após a compra?)

---

## Queries

| Arquivo | O que faz |
|---------|-----------|
| [queries/ltv_por_tier.sql](queries/ltv_por_tier.sql) | LTV total por tier (entrada + incremental) |
| [queries/upgrades_entre_tiers.sql](queries/upgrades_entre_tiers.sql) | Volume, tempo e receita dos upgrades |
| [queries/oportunidades_upsell.sql](queries/oportunidades_upsell.sql) | Segmentação da base para ação Comercial |

## Wiki atualizada

- `wiki-brasil-paralelo/pages/vitalicio.md` — página principal com todos os achados e métricas
- `wiki-bp/pages/metricas-referencia.md` — LTV por tier, receita incremental, benchmarks CEC/Retiro
- `wiki-bp/pages/bq-planos.md` — nm_gateway_plan de certificações, comportamento de upgrade
---

## Checklist de revisão

- [ ] Filtros padrão aplicados: `nm_status = 'approved'`, `bl_is_renovation = FALSE`
- [ ] Exclusões obrigatórias para o tipo de análise (ver `regras-negocio.md`)
- [ ] Resultados batem com benchmarks em `metricas-referencia.md` ou desvio explicado
- [ ] Método de atribuição de campanha correto (UTM vs lead_last_tracking — ver `bq-regras.md`)
- [ ] Métrica principal é a correta para o contexto (não CPL quando deveria ser CAC, etc.)
- [ ] Canal separado onde relevante (Comercial vs Digital)
