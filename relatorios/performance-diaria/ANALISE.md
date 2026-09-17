# Performance diária — "de onde veio o dia"

**Data:** 16/09/2026 · **Pedido por:** André (14/09) · **Status:** MVP para revisão (não publicado no portal)
**Desenho:** [DESENHO.md](DESENHO.md) · **Prévia:** artifact privado (link na conversa de 16/09)

## Pergunta original

Medir o impacto de cada dia, mostrar de onde veio a diferença de performance e quais alavancas
estão funcionando — sair do achismo, ou ao menos dar um caminho claro para essas análises.
Nasce da rodada 9a do `relevancia-marca`: discutimos "por que vendeu" sem ter "de onde veio".

## Decisões de abordagem

| Decisão | Por quê |
|---|---|
| Esperado = mediana do mesmo dia da semana nas 4 semanas anteriores | Baseline já validado pelo harness de overspend do MMM (evento 09–10/05); simples de explicar; sem modelo |
| Decomposição exata em volume × ticket e por canal de atribuição (`fct_transactions`) | Fecha no real; a lição do MMM em 2026 é que unidades e receita divergem por mix de ticket |
| Ads por campanha com atribuição da **plataforma** (Meta/Google/PMax) | É onde existe spend por campanha; gasto = Δspend × ROAS esp., eficiência = spend × ΔROAS |
| Contexto fora da soma (YT orgânico/MM28, busca, demanda não-Meta, estreias, abordagens) | São termômetros, não contribuições contábeis — misturar seria fingir causalidade |
| Alavancas com IC bootstrap **e MDE declarado** | Erro central das rodadas anteriores: "nulo" sem potência. Veredito "sinal" exige IC fora de zero e robustez sem dias de abertura |
| Calendário hardcoded da wiki (fase por campanha dominante em spend Meta) | `tb_campaign_period` sem 2026; substituir pela `api-mappings/campaign_dashboards` quando deployada |

## Achados do MVP (janela 01/06–13/09/2026)

- **13/09 (fechamento de fim de semana BP10):** +R$ 276k (+40%) vs esperado, **inteiramente ticket/mix**
  (volume −R$ 36k, ticket +R$ 312k). Ads Meta +R$ 225k, CRM +R$ 68k, Ads Google −R$ 52k. BP10:
  +R$ 121k por gasto e **+R$ 166k por eficiência** (ROAS 2,06 vs 1,41 esperado) — a escalada de
  BP10 converteu melhor que a base, não só gastou mais.
- **Semana 07–13/09:** +R$ 534k (+10,8%) vs esperado, com volume −R$ 216k e ticket +R$ 750k —
  a semana cresceu por mix de produto de ticket alto, não por mais transações.
- **Alavancas (90d):** spend > 1,2× esperado e abordagens Comercial > 1,2× têm sinal (como se
  espera de alavancas de execução); **YouTube orgânico alto e estreias na plataforma saem
  inconclusivas com MDE de ±47 a ±95 pp** — em 90 dias este teste só enxerga efeitos enormes.
  É a régua honesta que faltava no relevancia-marca.
- Fases de abertura/fechamento têm 3 dias cada na janela — calendário incompleto impede ler fase.

## Pendências / próximos passos

1. Validar a decomposição em 09–10/05 (overspend medido pelo MMM) e 14/08 (Renan) além de 13/09.
2. Baseline alternativo (MM28 pareada por spend) como sensibilidade.
3. Calendário via API do marketing-bp → fases completas (aquecimento/abertura/fechamento).
4. Automatizar GA4 (fetch diário) e refresh 9h via launchd; publicar no portal se aprovado.
5. Decisões do André (DESENHO.md): baseline, granularidade de canal, onde publicar, quem consome.

## Queries

| Arquivo | O que faz | Status |
|---|---|---|
| [01_vendas_diarias_canal_campanha.sql](queries/01_vendas_diarias_canal_campanha.sql) | tx/receita por dia × canal × sigla (fct) | ✅ |
| [02_spend_vendas_campanha_fonte.sql](queries/02_spend_vendas_campanha_fonte.sql) | spend/vendas/receita por dia × fonte × sigla (plataforma) | ✅ |
| [03_estreias_plataforma.sql](queries/03_estreias_plataforma.sql) | estreias de mídia com audiência D0 | ✅ |
| [04_abordagens_comercial.sql](queries/04_abordagens_comercial.sql) | abordagens Zenvia/dia | ✅ |
| GA4 `date × sessionDefaultChannelGroup` (MCP) → `data/ga4_sessions_canal.csv` | termômetros orgânicos | ✅ manual |

`refresh.py` roda as 4 queries e monta `data.json`; `preview.html` é o fragmento para o artifact.

## Wiki atualizada

Nada ainda — aguarda validação do André.
