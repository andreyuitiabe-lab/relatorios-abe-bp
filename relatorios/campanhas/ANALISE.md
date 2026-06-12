# Análise: Campanhas — Proxy de Qualidade de Criativos

**Data:** mai/2026  
**Status:** metodologia consolidada; aplicar em campanhas futuras  
**Relatório:** [index.html](index.html)  
**Wiki:** `~/.claude/wiki-brasil-paralelo/pages/els-analise.md` | `~/.claude/wiki-bp/pages/meta-insider-ads.md`

---

## Pergunta original

Desenvolver um proxy de qualidade para criativos de Meta Ads durante a fase de aquecimento, antes de ter dados de conversão — para orientar decisões de budget sem esperar o resultado de vendas.

---

## Decisões de abordagem

- Proxy: % de leads com decil7+ de renda (via dim_user) por anúncio, calculado sobre os 15% que matcham
- Usado para ranking relativo entre criativos dentro da mesma campanha — não para previsão absoluta entre campanhas
- Campanhas analisadas: GOD, HID, DOM, ELS (em ordem cronológica)
- Benchmark de referência: receita real por lead após conversão

---

## Achados principais

- Proxy preserva ranking relativo: criativo com maior proxy dentro de uma campanha tende a ter maior receita por lead
- CPL barato ≠ melhor retorno: em HID, "caviezel" (CPL R$2,76) gerou R$9,65/lead vs "tim" (CPL R$5,24) → R$16,96/lead
- DOM: CPL 2,6× maior que VDS, mas CAC 6,4× maior — proxy teria detectado antes da conversão
- ELS confirmou: compradores têm decil 5,61 (igual ao viewer); proxy de leads fica em 4,95 — proxy subestima qualidade real em ~3–4 pp

---

## Limitações documentadas

- Cobertura de 15% para Não Membros torna o proxy instável para campanhas com muitos leads novos
- Não comparar proxy entre campanhas diferentes (produto, funil e timing dominam sobre qualidade de audiência)
- Para campanhas com público majoritariamente novo, o proxy via pesquisa (renda autodeclarada) é mais confiável

---

## Pendências / próximos passos

- [ ] Aplicar proxy em tempo real na próxima campanha de aquecimento (antes de ter conversões)
- [ ] Combinar proxy dim_user + sinal de pesquisa para aumentar cobertura de Não Membros
- [ ] Validar se ranking do proxy se mantém quando campanha tem >50% de leads novos

---

## Queries

| Arquivo | O que faz |
|---------|-----------|
| [queries/proxy_qualidade_por_criativo.sql](queries/proxy_qualidade_por_criativo.sql) | Proxy de qualidade (% decil7+) por criativo — trocar `nm_tag` para outra campanha |

## Wiki atualizada

- `wiki-brasil-paralelo/pages/els-analise.md` — seção de proxy por criativo com contexto histórico GOD/HID/DOM/ELS
- `wiki-bp/pages/meta-insider-ads.md` — schemas e benchmarks por campanha
- `wiki-bp/pages/bq-regras.md` — distinção UTM vs nm_lead_last_tracking
---

## Checklist de revisão

- [ ] Filtros padrão aplicados: `nm_status = 'approved'`, `bl_is_renovation = FALSE`
- [ ] Exclusões obrigatórias para o tipo de análise (ver `regras-negocio.md`)
- [ ] Resultados batem com benchmarks em `metricas-referencia.md` ou desvio explicado
- [ ] Método de atribuição de campanha correto (UTM vs lead_last_tracking — ver `bq-regras.md`)
- [ ] Métrica principal é a correta para o contexto (não CPL quando deveria ser CAC, etc.)
- [ ] Canal separado onde relevante (Comercial vs Digital)
