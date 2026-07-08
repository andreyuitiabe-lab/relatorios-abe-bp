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
- [x] Treinar lead score específico para Não Membros em aquecimento — **IQL v0.2 implementado e backtestado (jul/2026)**: algoritmo em [ALGORITMO-IQL.md](ALGORITMO-IQL.md), metodologia + plano em [METODOLOGIA-IQL.md](METODOLOGIA-IQL.md), **dashboard em [iql/index.html](iql/index.html)**. Tabelas em `bp-staging.dbt_abe`: config (`tb_iql_de_para`, `tb_iql_pontos`, `tb_iql_cutoffs`, `tb_iql_ddd_regiao`), score (`tb_lead_iql`, 2,77M leads), monitoramento (`tb_iql_iv_perguntas`, `tb_iql_woe_respostas`) e view `vw_lead_conversion_iql`. **Backtest out-of-campaign (EVG→BP10): top decil NM captura 32,4% das vendas (lift 3,24×) vs 20,4% da v0.1**; faixas no teste A 2,36× / C 0,29× a base. Atributos v0.2 incluem identity graph (membro oculto 2,9×), região DDD e tempo_conhece. Artefatos/pesos em `~/meu_projeto/BigQuery/iql_v0/` (fora do repo público — anti-Goodhart). ⚠️ `tb_leads_qualification_base` é snapshot estático de mai/2026 — o IQL lê `dtm_analytics_lead_conversion` direto. Pendente: piloto na próxima campanha (gate: Spearman CPLq×CAC > CPL×CAC) → promoção ao dbt.
- [ ] Revisar CPL alvo por segmento com time de mídia (tabela no relatório)

### Dashboard IQL v2 — campanha-primeiro (08/jul/2026)

`iql/index.html` + `iql/refresh.py` evoluídos in-place para dashboard analítico:

- **Navegação campanha-primeiro**: uma aba por campanha (derivada de `data.json` — campanha nova aparece sozinha) + aba "Comparativo" secundária. Cada aba é o mini-dashboard da campanha: cards (leads, IQL, NM-A, cobertura da pesquisa, investimento, CPL, CPLq, NM-A/R$100), quadrante, tendência, anúncios, faixas, monotonia, IV.
- **Quadrante de decisão CPL×IQL** (SVG puro, sem libs): bolhas = anúncios (tamanho ∝ leads), zonas escalar/otimizar/cortar/matar divididas pelas **medianas da própria campanha** (nunca globais). No comparativo, scatter por cor de campanha sem zonas + aviso de não-comparabilidade.
- **Novos blocos no data.json**: `campanhas` (resumo por tag), `serie` (leads × faixa × dia, últimos 60 dias), `bandas` agora por campanha (agregação client-side no comparativo), `anuncios` ganhou `qualificados` e `investimento`.
- **Fix importante**: extração do id_ad em `utm_content` generalizada para `r'(\d{10,})$'` — o padrão antigo `r'__(\d+)$'` perdia o BP10 inteiro (48 anúncios recuperados; BP10 usa id puro, EVG usa `nome__id`). Documentado em `wiki-bp/pages/bq-leads.md`.
- Leituras dos dados atuais: BP10 IQL 38,0% vs EVG 19,5% (indicativo — coberturas de pesquisa diferentes); CPLq mediano por anúncio visível no quadrante de cada aba.

**Iteração 2 (08/jul/2026) — aba "Perguntas" + conversão/receita em tudo:**

- **Aba "Perguntas"**: ficha por pergunta da pesquisa (ordenada por IV máximo) com (a) estabilidade entre campanhas — cobertura, IV total, IV respondentes, chip de recomendação; (b) tabela de respostas — n, % da base, conversão (absoluta + %), lift vs base da tag, R$/lead. Objetivo: decidir promover/observar/aposentar/reformular cada pergunta.
- **Conversão e RPL em todas as visões**: cards da campanha ganharam "Conversão" e "R$/lead"; tabela de anúncios ganhou Conv. (absoluto + %, porque com poucas conversões o % engana) e R$/lead; monotonia (bandas) ganhou R$/lead. Aviso obrigatório por aba: "conversão/receita last-click, cohort maturando — leitura relativa, não ROI final".
- **Pipeline WOE com receita**: `iql_v0/sql/03_tb_iql_iv_perguntas.sql` agora propaga `vl_receita_atribuida` (inclusive no nível `__sem_resposta__`, derivado por diferença do total da tag) e `tb_iql_woe_respostas` ganhou coluna `rpl`. Tabelas recriadas no BigQuery.
- **Governança**: novo bloco `perguntas` no data.json exporta n/conv/lift/rpl mas **não** `woe`/`iv_contrib` (proxy dos pesos — repo público); verificação automatizada no fluxo de refresh confirma ausência.

**Iteração 3 (08/jul/2026) — reta de iso-CPLq no quadrante:**

- Fronteira de eficiência `IQL = 100·CPL/CPLq_ref` (reta pela origem), com `CPLq_ref` = CPLq **mediano** dos anúncios da campanha; clipada na área do gráfico (nos dados atuais sai pelo topo nas duas campanhas). Rótulo na ponta: "CPLq mediano R$ X — acima da linha = melhor". Só nas abas de campanha — no Comparativo não há referência comum válida.
- Tooltip dos anúncios ganhou posição relativa: "Z% melhor/pior que a mediana" = `(1 − CPLq/CPLq_ref)`. Subtítulo do gráfico explica o trade-off (CPL 2× maior é aceitável se o IQL for 2× maior; distância à reta = vantagem em custo por lead qualificado).
- Referências atuais: CPLq mediano BP10 R$ 11,54 · EVG R$ 22,44.

## Queries

| Arquivo | O que faz |
|---------|-----------|
| [queries/leads_com_status_e_cobertura.sql](queries/leads_com_status_e_cobertura.sql) | Status + cobertura dim_user por campanha |
| [queries/cpl_vs_cac_por_campanha.sql](queries/cpl_vs_cac_por_campanha.sql) | Leads e compradores por campanha (requer custo externo para calcular CPL/CAC) |
| [queries/06_cpl_por_tipo_lead_evg.sql](queries/06_cpl_por_tipo_lead_evg.sql) ✅ | CPL×RPL por anúncio × tipo de lead — EVG · jun/2026 |
| [queries/07_recencia_frequencia_cadastro.sql](queries/07_recencia_frequencia_cadastro.sql) ✅ | Conversão por recência/frequência de cadastro × status — cohort 2025 · jul/2026 (feature IQL) |

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

---

## Organização da pasta (jul/2026)

- `index.html` — relatório do framework CPL×CAC (visão geral do tema)
- `evg-bp10-pesquisa/` — **versão viva** da análise de pesquisa de qualificação (EVG × BP10)
- `2026-06-19-v3/` — snapshot EVG v3 apresentado a stakeholders (URL compartilhada — não mover)
- `archive/` — iterações supersedidas (2026-06-10 a -12-v2), fora do portal
- `modelo_evg_bp10/` — artefatos do modelo ML (dataset, benchmark, scripts)

Regra: versão viva evolui in-place (git é o histórico); snapshots de apresentação vão para `archive/` e não ganham card no portal.
