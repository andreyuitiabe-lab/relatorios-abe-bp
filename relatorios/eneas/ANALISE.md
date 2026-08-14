# Análise — Quem está comprando o Enéas (ENE)

**Data:** 14/08/2026 · **Pedido por:** Daymon Richard (via Slack)
**Relatório:** `index.html` (+ `data.json` via `refresh.py`)

## Pergunta original

Daymon pediu o perfil de quem está comprando a campanha do Enéas — **faixa etária principalmente** e distribuição por canal ("o Lambda tá vendendo bastante essa campanha"). Hipótese do Koetz: muita gente não está conseguindo comprar no checkout, possivelmente por ser um público mais velho — e a Lambda estaria capturando essas pessoas.

## Decisões de abordagem

- **Atribuição por união** `tracking_name ∪ utm_campaign ∪ utm_content ∪ lead_last_tracking` (método validado na ELS — UTM sozinho subconta). Padrões: `[ENE]`, `eneas`, `lan_ene_*`, `jornada_ene_*`. ⚠️ Não usar `%ene%` solto (casa "reels" etc.).
- **Janela:** desde 28/07/2026 (a ENE roda venda direta junto com a captação — não há fase de aquecimento separada).
- **Canal derivado do `nm_pptc_tracking_name`** (estrutura `[FASE] [CANAL] [ENE]`); Comercial separado em **humano** vs **Lambda (IA)** pela regra canônica `C0113` (ver `fluxo-comercial.md`).
- **Idade:** `dim_user.dt_birthday` — cobertura de só 13,7% (maioria dos compradores é nova, sem cadastro rico). A pesquisa de qualificação da ENE **não pergunta idade** (só streaming, mídia, tempo que conhece BP, motivação, relação, renda). Números de idade são amostra, não censo.
- **Falha de checkout:** todas as transações não-renovação da mesma atribuição (abandoned/canceled/expired), cruzadas pessoa a pessoa (email) com a compra aprovada posterior.
- **Conversas:** compradores Comercial/Lambda casados por telefone com `dim_zenvia_contacts` → `dim_zenvia_approaches` (transcrições).

## Achados principais

- **1.654 compradores / R$ 564k / ticket R$ 341 por comprador** (1.852 tx, 28/07–14/08).
- **Perfil:** 76% masculino, idade mediana 45 (média 47,4), decil de renda médio 5,5 com 40% no decil 7+, SP 28% / RJ 10% / MG 10%. **70% são clientes novos.**
- **Por onde compram:** Meta Ads 63% dos compradores (1.038, ticket R$ 228); **Comercial (humano + Lambda) = 14% dos compradores mas 42% da receita** — humano tem ticket R$ 1.568 (vitalícios/combos), Lambda R$ 266.
- **Lambda:** 104 compradores, crescendo (até 15/dia na 2ª semana de agosto). **Não vende o produto Enéas** — vende combos El Salvador e Apoiador em disparo sobre os leads da campanha.
- **Hipótese do Koetz CONFIRMADA:** 41,3% dos compradores Lambda tinham **falha prévia no checkout digital** (vs 13,8% dos compradores digitais). A Lambda funciona como recuperadora de checkout.
- **Funil de falhas:** 1.007 abandonos + 460 recusas no período; **964 pessoas falharam e nunca compraram** (pool de recuperação). Quem falha e não compra é mais velho (52,2 anos vs 46,9 de quem compra de primeira; amostra pequena).
- **Motivos de recusa** são majoritariamente fricção operacional: "não autorizada", "verifique os dados do cartão", "código de segurança inválido", "utilize função débito", parcelas acima do limite do emissor (18x não passa em Nubank/Santander/Amex — os próprios vendedores orientam 12x).
- **Conversas (Zenvia, Comercial humano):** 15 de 130 mencionam dificuldade explícita — "não estou achando meu cartão", "não consigo abrir a página", "me confundi e não terminei o cadastro", "o plano novo ainda não registrou". Idade média de quem compra via Lambda: 57,6 anos (n=14).

## Pendências / próximos passos

- [ ] **Acesso às conversas da Lambda**: `lambdalabs-gcp.iasmin_analytics.conversation_report_bp` está **vazia desde ~jun/2026** e o dataset nega listagem — pedir ao time da Lambda (Iasmin) onde está o log atual para ler as conversas da IA (só 17 dos 104 compradores Lambda têm conversa no Zenvia).
- [ ] Incluir **pergunta de idade** na pesquisa de qualificação (a ENE não tem — cobertura de idade ficaria completa nas próximas campanhas).
- [ ] Dimensionar a oportunidade: os 964 que falharam e nunca compraram são lista natural de recuperação (Lambda/Comercial) — respeitar exclusões de `listas-comercial.md`.

## Queries

| Query | O quê |
|---|---|
| [queries/base_compradores.sql](queries/base_compradores.sql) | Tx aprovadas ENE + classificação de canal → `tb_ene_compradores_tx` |
| [queries/perfil_compradores.sql](queries/perfil_compradores.sql) | Perfil por comprador (idade, gênero, decil, UF, novo vs base) → `tb_ene_perfil` |
| [queries/checkout_falhas.sql](queries/checkout_falhas.sql) | Todas as tentativas (falhas incluídas) → `tb_ene_tentativas` |
| [queries/conversas_zenvia.sql](queries/conversas_zenvia.sql) | Match compradores Comercial ↔ conversas Zenvia + menções a dificuldade |

Agregações do relatório: `refresh.py` (roda os DDL acima e gera `data.json`).

## Wiki atualizada

- `wiki-brasil-paralelo/pages/eneas.md` — criada (achados da campanha)
- `wiki-bp/log.md` — entrada registrada
