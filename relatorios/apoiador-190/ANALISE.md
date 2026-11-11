# Apoiador R$ 1,90 — quem compra e o que faz depois

## Pergunta original

O Apoiador a R$ 1,90/mês (12x) é a oferta principal do Black November 2026, usada para ganhar volume de vendas. Pedido do André (11/11/2026): entender quem compra, o que faz depois e de onde veio cada perfil, para melhorar o upsell para os outros planos.

Meta verificável: quantos compradores do R$ 1,90 sobem de plano, por qual canal, em quanto tempo, e o que diferencia quem sobe.

## Decisões de abordagem

- **Coorte:** 1ª compra aprovada **ou reembolsada** de oferta `supporter` com "12x de R$1,90" desde 23/09/2026, sem renovação, uma linha por e-mail. O reembolso entra porque o gateway reembolsa o R$ 1,90 quando a pessoa troca de plano.
- **Perfil:** medido 10 min antes da compra (assinatura paga vigente → membro ativo; já teve → ex-membro; comprou sem assinar; nunca comprou → novo). A janela evita contar a assinatura recém-criada.
- **Origem:** `utm_medium` do PPTC, não o publisher. O publisher desse checkout tem rastreio quebrado (ver `bq-regras.md`, gotcha do R$ 1,90). As lives da apuração (04/10) e do Paraguai (25/10) entram por `utm_content`.
- **Upsell:** compra aprovada posterior, sem renovação e sem outro R$ 1,90. Separado em:
  - **one-click** = digital em até 60 min (oferta pós-compra do checkout);
  - **Lambda** = tracking C0113;
  - **vendedor humano** = canal Comercial sem C0113;
  - **digital depois** = o restante.
- **Consumo:** horas assistidas nos 7 dias após a compra (`obt_kafka__view_sessions`), sessão limitada a 4h. Entra só quem já tem 7 dias de coorte e não subiu no one-click.
- **Checkouts:** comparados só a partir de 02/11, quando o one-click passou a existir.

## Achados principais (11/11/2026)

**Quem compra**
- **49.443 pessoas.** 75% eram novas na base, 23% ex-membros e 2% membros ativos.
- **Origem:** Meta 53%, Live/YouTube orgânico 18%, CRM 12%, Google/YouTube/X 7%, social/influ 5%, Comercial 2%.
- **A taxa de upsell é parecida entre as origens digitais (~5–6%).** Ex-membros sobem menos que novos (4,6% × 5,7%). Origem e perfil explicam pouco.

**O que faz depois**
- **Reembolso do R$ 1,90:** 4,6%.
- **5,5% compram outro plano depois**, gerando R$ 563 mil em compras posteriores.
- 82% das compras posteriores são Essencial.
- **Canal:** a Lambda traz 45% da receita posterior e o digital 38%. O vendedor humano atende ~100 pessoas, mas concentra Black/Vitalício.
- 66% da receita posterior acontece nas primeiras 24h.

**O one-click mudou o upsell**
- Até 26/10, o upsell na primeira hora era de 0,4%. Desde 02/11 é de 5,1%.
- **28.361 pessoas compraram antes de 02/11 e nunca viram o one-click.**
- **Checkout sem one-click em novembro:** `[10R] [A] [NUB] assine` (0,6%, 1.185 pessoas). Os checkouts LOV têm 5% e 7%.
- Na coorte inteira, `[BN26] [190-ANU] …preco-2` e `[B] [LOV] …/vitalicio` também não tinham one-click.

**Lambda**
- O upsell via Lambda foi de 5,3% dos compradores na semana de 28/09 para 2,2% em novembro. Parte da diferença é coorte imatura.
- A tabela de conversas da Lambda (`lambdalabs-gcp.iasmin_analytics.conversation_report_bp`) está parada desde 14/10, então não dá para separar queda de alcance de queda de conversão.
- Na coorte da live (até 14/10), a Lambda falou com 65% dos compradores. O upsell Comercial foi de 5,6% com conversa × 2,2% sem.

**Consumo na 1ª semana**
- 45% não assistem nada na primeira semana.
- **Upsell posterior por faixa de consumo:** nada 2,3% · <1h 3,9% · 1–3h 4,0% · 3h+ 6,0%.
- É correlação, não causa.

**Teste de CRM no WhatsApp (09/11)**
- Os links mantêm as UTMs para navegador real. O 301 sem parâmetros só aparece para robô e prévia de link.
- O painel mostra zero porque o checkout grava o rastreio anterior da pessoa (`source.pptc.*`). A UTM do link fica só no `source.utm_*` do Guru.
- O fluxo via LP `vd./upsell` (10/11) atribui certo.

## Pendências / próximos passos

- [ ] Colocar o one-click no checkout NUB assine e nos checkouts antigos (dono: produto/checkout).
- [ ] Lista dos ~28 mil compradores pré-02/11 para campanha de upgrade (sob demanda; entrega fora do repo).
- [ ] Desenho de teste de CRM com grupo de controle: gatilho por consumo × calendário, links via LP ou checkout exclusivo.
- [ ] Religar o sync da Lambda no BQ para medir cobertura D0.
- [ ] Coortes de novembro ainda imaturas: reavaliar o upsell posterior no fim de novembro (`python3 refresh.py`).

## Queries

O `refresh.py` concatena `base.sql` (CTEs da coorte, uma linha por pessoa) com o SELECT final de cada arquivo.

| Arquivo | O que responde |
|---|---|
| [queries/base.sql](queries/base.sql) | Coorte, perfil, origem, compras posteriores, consumo 7d, flags de upsell |
| [queries/resumo.sql](queries/resumo.sql) | Números do topo |
| [queries/perfil_origem.sql](queries/perfil_origem.sql) | Perfil × origem com upsell |
| [queries/semanal.sql](queries/semanal.sql) | Coorte semanal por canal de upsell e reembolso |
| [queries/depois.sql](queries/depois.sql) | Plano, janela e canal das compras posteriores |
| [queries/consumo.sql](queries/consumo.sql) | Consumo 7d × upsell posterior |
| [queries/checkouts.sql](queries/checkouts.sql) | One-click por checkout desde 02/11 |

A cobertura da Lambda (65%) e o teste de WhatsApp foram medidos à parte, no chat de 11/11, e não estão no refresh. A tabela da Lambda está parada e o teste de WhatsApp usou o Guru e a Insider.

## Wiki atualizada

- `wiki-bp/pages/metricas-referencia.md` — seção "Apoiador R$ 1,90/mês (BNO26)" com as métricas da coorte.
- `wiki-bp/pages/bq-regras.md` — gotchas: rastreio do R$ 1,90 (publisher × utm_medium); link de CRM direto ao checkout perde a UTM no DW; redirect do go.brasilparalelo depende do User-Agent.
- `wiki-bp/pages/fluxo-comercial.md` — tabela da Lambda parada desde 14/10.
