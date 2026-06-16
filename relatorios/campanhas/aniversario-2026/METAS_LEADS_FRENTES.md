# Metas de Leads por Frente — Campanha Aniversário BP 2026

**Data:** 16/jun/2026 | **Evento:** 16/jul/2026 | **Janela:** ~1,5 mês (aquecimento + venda)
**Meta:** R$ 15M (R$8M jul + R$7M ago) a 55% margem de contribuição (CM)
**Frentes:** (1) Vitalício — upsell base madura | (2) Bundle — aquisição/rebranding de assinatura

> Documento de calibração de growth. Define meta de leads por frente, forecast integrado, divisão de esforço e cenários. **NÃO aceita os números do analista cegamente** — corrige inconsistências sinalizadas e trabalha com faixas onde a premissa é frágil.

---

## TL;DR — o que a gestora precisa saber

1. **Vitalício carrega a campanha; bundle é complemento, não pilar.** ~71% da meta (R$10,6M) vem de reativar a base madura 9m+ via CRM, com custo de mídia ~zero. Essa frente é **ativação de base, não geração de lead**.

2. **A matemática do bundle no relatório de dados está errada e otimista.** O R$13,9/lead reportado pertence ao ticket do CDL (R$1.218), não ao bundle (R$195). Com ticket R$195 e conversão frio 1,44%, o lead frio rende **~R$2,8**, não R$13,9. Fechar R$4,4M só com frio exigiria **~1,5 milhão de leads** — não 318k. **O bundle é estruturalmente incapaz de ser carregado por aquisição fria.**

3. **318k (e muito menos 1,5M) leads frios é operacionalmente impossível.** O BPDay 2025 captou ~69k leads no total. A frente bundle precisa ser **majoritariamente vendida para a base reaquecida** (8,8% conv, R$101/lead — 7× mais eficiente que frio), com cota de frio limitada por teto de CM.

4. **Meta de leads recomendada (cenário realista):**
   - **Vitalício:** ~12.100 leads de perfil base 9m+ reativados via CRM (cobertura ~6,3% da base trabalhável de 384k).
   - **Bundle:** ~50–70k leads no total → **~18–22k de base reaquecida + ~35–45k de frio com teto**. NÃO 318k.

5. **Veredito de viabilidade:** R$15M **fecha com folga**, mas a composição declarada (R$4,4M de bundle via frio massivo) **não fecha como descrita**. O número viável do bundle é **R$2,5–4,0M** se for puxado pela base reaquecida + frio capeado. O gap remanescente é coberto naturalmente pela base Vitalício/renovações, que sozinhas já entregam R$15–17M. **A meta global é sólida; o que precisa ser recalibrado é a expectativa de quanto o bundle entrega via aquisição.**

---

## ⚠️ ATUALIZAÇÃO 16/jun — dois inputs da gestora que corrigem o modelo

Esta seção **supera** os números de CPL e parte do enquadramento de "leads necessários" abaixo. O resto do documento permanece válido.

### Correção 1 — A receita NÃO vem necessariamente dos leads
A maior parte da venda para a base (Vitalício e assinatura) acontece na **abertura da oferta via CRM/direto, SEM a pessoa se cadastrar como lead**. O funil de leads (`dtm_analytics_lead_conversion`) só enxerga venda atribuída a quem virou lead — subconjunto da realidade.

**Consequência:** o framing "precisamos de X leads para fechar R$15M" está errado. Os R$15M vêm majoritariamente da **base comprando na abertura** (não de leads). Lead pago é mecanismo de **aquisição incremental de cliente novo** (frente bundle), avaliado por **CAC vs LTV**, não por receita in-campaign.

- "12.100 leads Vitalício" → leia como **12.100 compradores ativados via CRM**, não meta de geração de lead. O KPI real é **alcance/cobertura de CRM da base 9m+**.
- A meta de leads pagos aplica-se essencialmente ao **frio do bundle**.

### Correção 2 — CPL de assinatura = R$3 (não R$10–15)
Em campanhas de venda de assinatura a BP trabalha com **CPL ~R$3**. Toda a hesitação anterior em torno de R$10–28 e a regra "CPL ≤R$15" estão **revogadas** para a frente bundle. Isso muda a economia do frio:

| Item | Antes (CPL assumido) | Corrigido (CPL R$3) |
|---|---|---|
| Custo de 40k leads frios | R$400k (a R$10) | **R$120k** |
| Custo de 100k leads frios | R$1,0M (a R$10) | **R$300k** |
| Custo dos "318k leads" do analista | inviável | **~R$954k — cabe no orçamento** |
| ROAS direto do frio (1ª compra, ticket R$195, conv 1,44% → R$2,8/lead) | 0,19× (perde) | **~0,94× (quase empata)** |
| Veredito do frio | "queima dinheiro" | **break-even in-campaign, lucra no LTV (assinatura renova)** |

**Reenquadramento da frente bundle:** com CPL R$3, captar frio é **barato** e o cost-objection desaparece. O frio deixa de "perder dinheiro" e vira **investimento em base de assinantes futura (LTV)**, ~empatando na campanha. O limitante deixa de ser custo e passa a ser **(a) conversão/retenção real do bundle e (b) capacidade operacional de volume** (criativo, saturação de audiência). O teto de gasto frio continua existindo — mas por disciplina de CM e qualidade de lead (mix de base ≥35%), não por inviabilidade econômica.

**O que NÃO muda:** os R$15M in-campaign continuam carregados pela base. O CPL barato torna o bundle uma boa aposta de **crescimento de assinantes/LTV**, não um novo pilar de receita do mês.

> Nos cenários da §4, releia os custos de mídia a **CPL R$3** (ex.: realista 40k frios = **R$120k**, não R$400k) e a KPI da §3.3 "CPL ≤R$15" como **"CPL ~R$3, alvo de assinatura"**.

---

## 1. Meta de leads por frente

### 1.1 Frente VITALÍCIO — ativação de base, não aquisição

Não é uma meta de "gerar leads novos" — é uma meta de **cobertura de CRM sobre a base madura existente**.

| Parâmetro | Valor | Origem |
|---|---|---|
| Base trabalhável (9m+) | 384.002 membros | ANALISE_DADOS, excluir <9m |
| Compradores esperados | ~4.601 | conv. por faixa Jun-Jul/25 (saturada) |
| Conv. do lead de base no funil | 38,12% | tag VIT 2025 |
| **Leads de perfil Vitalício necessários** | **~12.100** | 4.601 / 38,12% |
| **Cobertura de CRM necessária** | **~12.100 / 384.002 = 3,2% da base 9m+ entrando no funil** | — |
| Receita esperada | **~R$10,6M** | 4.601 × R$2.300 |
| Custo de mídia | ~R$0 | 100% CRM/Comercial |

**Leitura de cobertura:** 12.100 leads de perfil Vitalício a partir de uma base de 384k significa que **basta 3,2% da base madura entrar no funil** para entregar os R$10,6M. Isso é atingível — mas o gargalo real não é o 3,2%, é a **taxa de alcance do CRM** (e-mail válido + WhatsApp + não-blacklist + abertura). Se o CRM alcança efetivamente ~50–60% da base 9m+ e desses ~5–6% entram no funil, os 12.100 são realistas. **Validar capacidade de CRM é a premissa #1.**

**Regra de governança Vitalício:** **zero lead frio nesta frente.** Frio em Vitalício rende R$15/lead vs R$240 da base — é queima de orçamento. Todo gasto de aquisição vai para o bundle.

### 1.2 Frente BUNDLE — base reaquecida primeiro, frio com teto

Aqui está o coração da recalibração. A premissa de "318k leads frios" está duplamente errada:

**Correção da economia do frio do bundle:**

| Item | Relatório do analista | Realidade calibrada |
|---|---|---|
| Receita/lead frio | R$13,9 | **R$2,8** (1,44% × R$195) |
| Origem do R$13,9 | (atribuído ao bundle) | pertence ao CDL, ticket R$1.218 |
| Leads frios p/ R$4,4M só com frio | 318k | **~1,57M** (R$4,4M / R$2,8) |
| Veredito | "volume alto" | **estruturalmente impossível** |

> **Por que o R$13,9 não vale:** R$629k de receita CDL / 45.273 leads = R$13,9, mas isso embute o ticket do CDL (R$1.218). O bundle de assinatura tem ticket ~R$195. A conversão (1,44% frio) é transferível do análogo; o ticket NÃO é. Receita/lead correto do bundle frio = conv × ticket bundle = **R$2,8**.

**Implicação:** o bundle **não pode** depender de frio. A receita do bundle tem de vir da **base reaquecida** (membros/ex-membros que recebem a oferta do bundle no aquecimento):

| Origem do lead bundle | Conv. | Ticket | Receita/lead | Eficiência vs frio |
|---|---|---|---|---|
| Base reaquecida | 8,80% | R$195 | **R$17,2** | 6,1× |
| Frio (mídia) | 1,44% | R$195 | **R$2,8** | 1× |

> Nota: a conversão de base do bundle (8,8%) vem do análogo CDL com ~1 mês de maturação — é **piso**, deve subir. Mesmo assim já é 6× mais eficiente que o frio.

**Meta de leads do bundle (cenário realista, alvo R$3,0–3,5M da frente):**

| Componente | Leads | Conv. | Compradores | Receita |
|---|---|---|---|---|
| Base reaquecida | ~20.000 | 8,8% | ~1.760 | ~R$343k |
| Frio (com teto) | ~40.000 | 1,44% | ~576 | ~R$112k |
| **Subtotal funil bundle** | **~60.000** | — | **~2.336** | **~R$455k** |

Aqui surge a segunda verdade desconfortável: **mesmo com 60k leads (quase a captação inteira do BPDay), o funil de lead do bundle só entrega ~R$0,45M de receita rastreável**, não R$4,4M. O ticket de R$195 é simplesmente baixo demais para que aquisição feche um gap de milhões em 1,5 mês.

**Conclusão da meta bundle:** o bundle como **funil de lead de aquisição** entrega **R$0,4–1,0M**, não R$4,4M. Os R$4,4M de "gap" só fecham se (a) o ticket do bundle for muito maior que R$195 (premissa a validar — ver §5), ou (b) o gap não precisar ser fechado pelo bundle porque a base Vitalício + renovações já cobrem (é o caso — ver §2).

---

## 2. Forecast integrado das duas frentes rumo a R$15M

A pergunta certa não é "quantos leads frios para o bundle fechar R$4,4M" — é "**a campanha inteira fecha R$15M?**". E fecha, mas a composição é diferente da declarada.

### 2.1 De onde vem a receita (cenário realista)

| Bloco | Receita | Lead incremental? | Observação |
|---|---|---|---|
| **Vitalício upsell (base 9m+, conv. 2025 saturada)** | R$10,6M | Não — ativação CRM | Motor da campanha |
| **Renovações automáticas** | R$4–6M | Não | Baseline ago/25 = R$4,0M só de renovação |
| **Bundle — funil de lead (base reaq. + frio)** | R$0,4–1,0M | Sim — aquecimento | Frente de aquisição |
| **Bundle/assinatura — base ampla via CRM** | R$2–4M | Parcial | Rebranding sobre base jovem + leads, fora do funil de lead estruturado |
| **Mecenas + outros** | R$1–2M | Não | Estimativa |
| **TOTAL** | **~R$18–23,6M** | — | Acima dos R$15M |

**A meta de R$15M fecha com folga — mas NÃO pela via que o relatório de dados descreveu.** O relatório alocou R$4,4M ao bundle-via-aquisição-fria; isso não acontece. O que acontece é:
- **A base (Vitalício + renovações) sozinha já entrega R$14,6–16,6M** sem nenhum lead incremental.
- O bundle adiciona R$2,4–5,0M, majoritariamente via **base ampla recebendo a oferta de assinatura no CRM** (não via funil de lead frio).
- O lead frio incremental contribui com **<R$1M** de receita direta rastreável.

### 2.2 Quanto vem da base sem lead incremental vs do aquecimento

| Fonte | Receita | % da meta R$15M |
|---|---|---|
| **Base sem lead incremental** (Vitalício 9m+ + renovações + Mecenas) | R$15,6–18,6M | 104–124% |
| **Aquecimento/aquisição incremental** (funil bundle base+frio) | R$0,4–1,0M | 3–7% |

**A meta de R$15M é coberta pela base sozinha.** O aquecimento/aquisição é **upside e construção de pipeline futuro (LTV)**, não o que faz a meta fechar. Isso é exatamente o aprendizado do BIT vs DBI: a base é o motor.

### 2.3 Veredito de viabilidade

- **R$15M: VIÁVEL com folga.** É ~43% do baseline jul-ago/2025 (R$35,3M). A base madura cobre sozinha.
- **A composição declarada (bundle = R$4,4M via 318k frios): INVIÁVEL como descrita.** Recalibrar para: bundle entrega R$2,4–5,0M, dos quais <R$1M via frio. O resto via base/CRM.
- **Número viável do bundle como frente de aquisição:** R$0,4–1,0M de receita direta de funil de lead frio. Se o ticket real for >R$400 (a validar), pode chegar a R$1–2M.

---

## 3. Calibração de estratégia: divisão de esforço, prioridade e governança

### 3.1 Divisão de esforço/orçamento

| Frente | Esforço de CRM | Orçamento de mídia | Prioridade |
|---|---|---|---|
| **Vitalício** | **Alto** — segmentação fina por faixa (12-18m, 24m+), Comercial sobre base madura | R$0 | **1ª** |
| **Bundle — base reaquecida** | **Alto** — oferta de bundle para base jovem (<9m) + ex-membros via CRM | R$0 | **2ª** |
| **Bundle — frio** | Baixo | **Capeado em 5–7% da receita-alvo** (~R$0,75–1,0M) | **3ª (último)** |

**O orçamento de mídia inteiro vai para o frio do bundle**, porque Vitalício não usa frio e a base reaquecida do bundle é CRM (custo ~zero). Com teto de R$0,75–1,0M e CPL ≤R$15, isso compra 50–65k leads frios — coerente com a capacidade operacional (~BPDay) e suficiente, dado que o frio não é o motor.

### 3.2 Ordem de prioridade de execução

1. **CRM sobre base Vitalício 9m+** (12-18m e 24m+ primeiro — 79% da receita Vitalício). Custo zero, maior ROI.
2. **CRM com oferta de bundle para base jovem (<9m) e ex-membros** — converte 8,8%, R$17/lead. Aproveita os membros que NÃO devem receber oferta de Vitalício.
3. **Indicação/MGM** desde o dia 1 — amplia base sem CPL.
4. **Frio do bundle com teto** — último, monitorado por mix de base e CM.

> Segmentação crítica: **membro 9m+ → Vitalício; membro <9m + ex-membro + frio → bundle.** Isso resolve o risco de canibalização do rebranding sobre o Vitalício (Risco 3 da ANALISE_GROWTH) e usa cada segmento da base no produto certo.

### 3.3 KPIs de governança

| KPI | Alvo | Por quê |
|---|---|---|
| **Mix de base no funil (blended)** | **≥35%** | Linha que separou BIT (sucesso) de DBI (fracasso). Abaixo de 30% = colapso de ROI |
| **Gasto de mídia frio / receita total** | **≤5–7%** (~R$0,75–1,0M) | Teto que preserva 55% CM |
| **CPL frio** | **≤R$15** | Acima disso o frio não se paga na campanha (ROAS direto <1) |
| **Cobertura CRM da base 9m+** | medir alcance efetivo | Define se 12.100 leads Vitalício são atingíveis |
| **CM blended** | **≥55%** | Restrição-mãe. Furada apenas se frio escalar sem base carregar |
| **Conversão real por faixa (primeiros 3 dias venda)** | vs Jun-Jul/25 | Detecta saturação cedo, recalibra |

---

## 4. Três cenários

Premissas comuns: ticket Vitalício R$2.300; ticket bundle R$195 (a validar — §5); conv. base = Jun-Jul/25 (saturada); CPL frio = input de mídia (assume R$10 no realista); mix base ≥35%; gasto frio capeado.

### Pessimista
- **Leads Vitalício:** ~10.000 (CRM subperforma, alcance baixo) → ~3.800 compradores → **R$8,7M**
- **Leads bundle:** 15k base + 25k frio = 40k. Base 1.320 compr. + frio 360 → **R$0,33M funil** + R$1,5M base ampla CRM = **R$1,8M**
- **Renovações + Mecenas:** R$5M
- **Mídia frio (R$10 × 25k):** R$250k
- **Receita total:** **~R$15,5M** | **CM:** ~57% (frio ~1,6% da receita)
- *Risco materializado:* saturação 24m+ pior que 2025, rebranding confunde a base, alcance de CRM fraco.

### Realista
- **Leads Vitalício:** ~12.100 → ~4.601 compradores → **R$10,6M**
- **Leads bundle:** 20k base + 40k frio = 60k. Base 1.760 + frio 576 → **R$0,46M funil** + R$3M base ampla CRM = **R$3,5M**
- **Renovações + Mecenas:** R$6M
- **Mídia frio (R$10 × 40k):** R$400k
- **Receita total:** **~R$20M** | **CM:** ~56% (mídia ~2% da receita)
- *Premissa:* CRM forte (mix base ≥40%), segmentação Vitalício/bundle limpa.

### Otimista
- **Leads Vitalício:** ~13.000 (uplift de mix Black/Premium) → ~4.800 compradores → **R$12M**
- **Leads bundle:** 22k base + 45k frio = 67k. Base reaquecida converte acima de 8,8% (funil maturado) + ticket bundle >R$250 → **R$1,2M funil** + R$4,5M base ampla = **R$5,7M**
- **Renovações + Mecenas:** R$6M
- **Mídia frio (R$10 × 45k):** R$450k
- **Receita total:** **~R$23,7M** | **CM:** ~55–56% (frio <2%)
- *Premissa:* rebranding cria nova onda de aquisição, ticket bundle confirma premium, CRM reativa ex-membros em escala.

### Resumo dos cenários

| Cenário | Leads VIT | Leads bundle (base/frio) | Receita VIT | Receita bundle | Receita total | CM |
|---|---|---|---|---|---|---|
| Pessimista | 10.000 | 15k / 25k | R$8,7M | R$1,8M | **~R$15,5M** | ~57% |
| Realista | 12.100 | 20k / 40k | R$10,6M | R$3,5M | **~R$20M** | ~56% |
| Otimista | 13.000 | 22k / 45k | R$12M | R$5,7M | **~R$23,7M** | ~55–56% |

> Em todos os cenários a meta de R$15M fecha e a CM fica ≥55%. **A CM só furaria se o frio fosse escalado 5–10× perseguindo volume — o que esta calibração proíbe explicitamente (KPI: frio ≤7% da receita).**

---

## 5. Premissas a validar e riscos

### Premissas a validar (ANTES de comprometer números)

1. **Ticket real do bundle (CRÍTICO — muda tudo).** R$195 é o piso de assinatura mensal atual. Se o bundle for **plano anual ou tiver order bumps**, o ticket pode ser R$400–1.200+, multiplicando a receita/lead e tornando o frio viável. **O forecast do bundle é provisório até produto confirmar o ticket.** Toda a §1.2 e §2 são função desse número.
2. **Conversão real do bundle.** A 1,44% (frio) / 8,8% (base) vem do análogo CDL com ~1 mês de maturação — é piso. Rerodar em jul/26 com funil maturado. A conversão real estabilizada pode ser 30–50% maior.
3. **Capacidade de CRM (CRÍTICO p/ Vitalício).** De quantos dos 384k membros 9m+ conseguimos extrair os 12.100 leads de perfil Vitalício (e-mail válido + WhatsApp + não-blacklist + abertura). Se o alcance for baixo, os R$10,6M desidratam.
4. **CPL de aquecimento** — input obrigatório do time de mídia. Define quantos frios o teto de R$0,75–1,0M compra.
5. **Custo de parcelamento do Vitalício** (até 18x) — vetor variável mais provável de furar a CM, não a mídia. Validar com financeiro.

### Riscos

| # | Risco | Severidade | Mitigação |
|---|---|---|---|
| 1 | **Saturação do 24m+** (caiu 12,93%→6,28%→1,41% em 3 campanhas; é 51% da receita Vitalício) | Alta | Variar o angle; personalizar por comportamento; NÃO projetar acima de 1,41% |
| 2 | **Repetir o DBI** — frio sem ativar base via CRM | Alta, evitável | Mix base ≥35% como KPI de gate; se cair na 1ª semana, pausar escala de frio |
| 3 | **Ticket bundle frágil (R$195)** — premissa não confirmada | Alta | Validar com produto ANTES de comprometer receita do bundle; tratar como faixa, não ponto |
| 4 | **Bundle não consegue ser carregado por frio** (1,5M leads necessários) | Alta, estrutural | Bundle = base reaquecida primeiro; frio é cota limitada, não pilar |
| 5 | **Capacidade de CRM insuficiente** para 12.100 leads Vitalício | Alta | Medir alcance efetivo da base 9m+ antes de comprometer R$10,6M |
| 6 | **Rebranding confunde/canibaliza o Vitalício** | Média | Segmentar: 9m+ → Vitalício; <9m + ex-membro + frio → bundle |
| 7 | **Custo de parcelamento erode CM** | Média, subestimado | Validar custo efetivo por tier com financeiro |
| 8 | **Confundimento de demanda no CPL** (orgânico inflado no aniversário) | Média | Não decidir budget só por CPL; usar % que vira base como proxy de qualidade |

---

*Calibração de growth — 16/jun/2026. Baseada em ANALISE_GROWTH.md e ANALISE_DADOS_FRENTES.md. Correção numérica do bundle (receita/lead frio R$2,8 vs R$13,9 reportado) sinalizada explicitamente. Tickets e conversões do bundle tratados como provisórios. CPL como input de mídia, não assumido.*
