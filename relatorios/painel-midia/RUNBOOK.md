# Painel de Mídia — Runbook

**O que é**: painel diário do portfólio Meta [VENDA] — recomendações por campanha (recomendador v1 validado, gate monotônico), posição na curva de saturação (spend vs ótimo de margem vs teto de receita) e status da calibração do MMM. Página: `index.html` (portal), dados: `data.json`.

## Atualização

```bash
cd ~/meu_projeto/relatorios-abe-bp/relatorios/painel-midia
python3 update_painel.py          # ~2 min: bqq → recomendador → data.json + decisoes.csv
```

Automática: LaunchAgent `com.bp.painel-midia` roda todo dia às 08h40 (plist em `~/Library/LaunchAgents/`; logs em `logs/`). **Publicar no portal continua manual** (`git push`) — para publicar automático, definir `PAINEL_PUSH=1` no plist (decisão consciente: push = página pública atualiza sozinha).

Se a página mostrar o banner vermelho de "desatualizado há >48h": rodar o comando acima e checar `launchctl list | grep painel`.

## Decision log (o shadow mode)

Toda recomendação REDUZIR/AUMENTAR/ALERTA entra em `decisoes.csv` com `acao_tomada` e `resultado` vazios — **preencher é o trabalho do gestor**: o que fez (seguiu/ignorou/parcial) e o que aconteceu. 2–4 semanas de log preenchido decidem se o recomendador vira regra operacional. Sem log, não há promoção.

## Parâmetros (revisados 10/09/2026 — ver ../midia-paga/ANALISE.md e MARGEM.md)

- Curvatura `b=0,70`; β estratégico EWMA meia-vida 7d; margem cenário `0,75` (digital — pendente financeiro: impostos/gateway e custo de livro)
- Janela de dados D-2 (mart amadurece em 2 dias); step-limit ±20%/dia; teto por campanha = margem × ticket 30d × índice de demanda
- Recalibração mensal do MMM: `V32_LOG=1 python3 ~/meu_projeto/mmm_project/scripts/03_modelagem/60_modelo_mmm_v32.py` (~4 min) — o painel lê o resultado sozinho

## Limitações honestas

Tudo sobre receita **atribuída** (pixel) — o teto real é calibrado por experimento (GeoLift). O lado AUMENTAR é menos validado que o REDUZIR (tratar como sugestão). O ótimo é faixa que se move com o β — nunca constante.
