# Análise: Qualificação de Leads — Framework CPL×CAC

**Data:** mai/2026  
**Status:** framework concluído; implementação de pesquisa e scoring em andamento  
**Relatório:** [index.html](index.html)  
**Wiki:** `~/.claude/wiki-bp/pages/metricas-referencia.md` | memória: `project_lead_qualification_framework`

---

## Pergunta original

O time de mídia otimizava por CPL. A hipótese era que CPL e qualidade de lead são anticorrelacionados em algumas campanhas — e que falta um sistema de qualificação que funcione no momento do registro, antes da compra.

---

## Decisões de abordagem

- Comparação CPL×CAC entre campanhas (DOM vs VDS) para evidenciar o problema
- Qualificação em 3 camadas: (1) status no momento do registro, (2) dados internos dim_user, (3) pesquisa pós-registro
- Gap de cobertura: Membros/Ex-Membros têm 100% de cobertura em dim_user; Não Membros apenas 13% — para 87% dos Não Membros, o sistema interno é mudo
- Tabelas materializadas em `bp-staging.dbt_abe` para não depender de joins caros em análises futuras

---

## Achados principais

- CPL e CAC anticorrelacionam: DOM tem CPL 2,6× maior que VDS, mas CAC 6,4× maior — decisão por CPL levou a desperdício
- Lift de status: Membro converte 5–11× mais que Não Membro (consistente entre campanhas)
- 87% dos Não Membros sem cobertura em dim_user — o lead score ML atual (`dtm_lead_score_predictions_upsell_current`) foi treinado para upsell de membros, não funciona para qualificar leads de aquecimento
- Pesquisa pós-registro: renda gera lift 4,6×; intencionalidade (responder à pesquisa) já é sinal — +50% de conversão vs quem não responde
- 342k respostas normalizadas de 4 pesquisas (TLR/TPV/RIO/MST) em `tb_lead_surveys`

---

## Tabelas criadas

| Tabela | Conteúdo |
|--------|----------|
| `bp-staging.dbt_abe.tb_leads_qualification_base` | Leads jan/2025+ com status + atribuição last-click |
| `bp-staging.dbt_abe.tb_leads_qualification_enriched` | + dim_user + IBGE + renda decile + lead score ML |
| `bp-staging.dbt_abe.tb_lead_surveys` | 4 pesquisas normalizadas (342k respostas) |

---

## Análise EVG — jun/2026

**Relatório:** [2026-06-11/index.html](2026-06-11/index.html)  
**Período:** 21/mai–08/jun/2026 · 34.249 leads · 390 conversões · R$135.902 receita

### Achados EVG

- Mix: 84% Não Membros, mas Membros+Ex-Membros = 40% da receita
- Membro Ativo converte 3,64% (RPL R$14,23); Ex-Membro 2,79% (RPL R$7,68); Não Membro 0,74% (RPL R$1,85)
- Único ad set positivo: Pack 1 (+R$1,22 de folga). Pack 2 tem CPL mais baixo (R$1,84) mas pior mix de qualificados (11%)
- AD35 "alinhamento político": 30% de leads qualificados com CPL R$1,47 — melhor custo-benefício
- Survey renda: Não Membro com R$10k+ converte 4% (RPL R$9,79) — equivale a Ex-Membro
- Survey relação BP: "nunca ouvi falar" converte 0,24% vs 1% média — excluir ou orçamento mínimo
- Survey streaming: BP informal = 1,64% conv; plataformas educacionais = RPL R$5,13
- Orgânico/Portal: 980 leads, 8% conversão, RPL R$64, custo zero
- Reativação: leads >1 ano convertem 1,35% vs 0,90% de novos (+50%)

### Pendências / próximos passos

- [ ] Parte 1 (RPV): conectar GA4 MCP para comparar pageviews por variante
- [ ] Separar audiências no Meta (retargeting vs prospecting) para lançamento seguinte
- [ ] Integrar sinal de renda (survey) no fluxo de nurturing Insider no dia do cadastro
- [ ] Treinar lead score específico para Não Membros em aquecimento
- [ ] Revisar CPL alvo por segmento com time de mídia (tabela no relatório)

---

## Queries

| Arquivo | O que faz |
|---------|-----------|
| [queries/leads_com_status_e_cobertura.sql](queries/leads_com_status_e_cobertura.sql) | Status + cobertura dim_user por campanha |
| [queries/cpl_vs_cac_por_campanha.sql](queries/cpl_vs_cac_por_campanha.sql) | Leads e compradores por campanha (requer custo externo para calcular CPL/CAC) |
| [queries/06_cpl_por_tipo_lead_evg.sql](queries/06_cpl_por_tipo_lead_evg.sql) ✅ | CPL×RPL por anúncio × tipo de lead — EVG · jun/2026 |

## Wiki atualizada

- `memory/project_lead_qualification_framework.md` — framework e tabelas documentados
- `wiki-bp/pages/metricas-referencia.md` — benchmarks CPL×CAC por campanha
---

## Checklist de revisão

- [ ] Filtros padrão aplicados: `nm_status = 'approved'`, `bl_is_renovation = FALSE`
- [ ] Exclusões obrigatórias para o tipo de análise (ver `regras-negocio.md`)
- [ ] Resultados batem com benchmarks em `metricas-referencia.md` ou desvio explicado
- [ ] Método de atribuição de campanha correto (UTM vs lead_last_tracking — ver `bq-regras.md`)
- [ ] Métrica principal é a correta para o contexto (não CPL quando deveria ser CAC, etc.)
- [ ] Canal separado onde relevante (Comercial vs Digital)
