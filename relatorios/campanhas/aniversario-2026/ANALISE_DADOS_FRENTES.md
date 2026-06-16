# Análise de Dados — Forecast Campanha de Aniversário 2026 (duas frentes)

**Data:** 16/jun/2026 | **Evento:** 16/jul/2026 | **Meta:** R$ 15M (R$8M jul + R$7M ago, 55% margem)
**Frentes:** (1) Vitalício — upsell base madura | (2) Bundle — aquisição/rebranding de assinatura

---

## Resumo executivo

| Frente | Conversão | Ticket | Receita/lead | Leads necessários | Receita esperada |
|---|---|---|---|---|---|
| **Vitalício** (base 9m+) | 1,1% da base / 38,1% do lead reativado | R$ 2.300 | R$ 240 (lead base) | ~12.100 leads de base madura via CRM | **R$ 10,6M** |
| **Bundle** (aquisição frio) | 1,44% (frio) / 8,8% (base) | R$ 195 | R$ 13,9 (frio) / R$ 101 (base) | ~318k leads frios OU mix | **R$ 4,4M** (gap restante) |
| **Total** | — | — | — | — | **R$ 15,0M** |

**Mensagem central:** a meta de R$15M é viável, mas **assimétrica**. A frente Vitalício, trabalhando apenas a base madura já existente (9m+), entrega ~R$10,6M **sem nenhum lead incremental de mídia** — é receita de reativação da base via CRM. O Bundle precisa fechar o gap de ~R$4,4M, o que exige um volume de leads frios muito alto (~318k) pela baixa receita/lead do produto de entrada. **A campanha se sustenta na base, não na aquisição.**

---

## FRENTE 1 — VITALÍCIO

### Mercado endereçável (base elegível × conversão Jun-Jul/2025)

Cruzamento da composição atual da base (558.337 elegíveis) com as taxas de conversão por faixa de maturidade da campanha Jun-Jul/2025 (referência mais conservadora e comparável — mesma estação/formato). Ticket Vitalício ponderado: **R$ 2.300**.

| Faixa | Base elegível | Conv. Jun-Jul/25 | Compradores | Receita | Status |
|---|---|---|---|---|---|
| 0-3m | 72.637 | 0,16% | 116 | R$ 267k | ❌ excluir (<6-9m) |
| 3-6m | 48.818 | 0,29% | 142 | R$ 326k | ❌ excluir (<6-9m) |
| 6-9m | 52.880 | 0,31% | 164 | R$ 377k | ⚠️ limiar |
| 9-12m | 46.189 | 1,12% | 517 | R$ 1,19M | ✅ trabalhável |
| 12-18m | 96.828 | 1,14% | 1.104 | R$ 2,54M | ✅ foco |
| 18-24m | 59.677 | 0,71% | 424 | R$ 0,97M | ✅ trabalhável |
| 24m+ | 181.308 | 1,41% | 2.556 | R$ 5,88M | ✅ foco |
| **Total (toda base)** | 558.337 | 0,90% | **5.023** | **R$ 11,6M** | — |
| **Trabalhável (9m+)** | **384.002** | — | **4.601** | **R$ 10,6M** | — |

**Regra do Notion aplicada:** membros com <6-9m convertem muito mal (0,16-0,31%) e devem ser excluídos da oferta. O "mercado trabalhável" é a base **9m+ (384k membros)**, com foco em 12-18m e 24m+ que sozinhos respondem por R$8,4M dos R$10,6M (79%).

**Mediana de tempo até o Vitalício: ~382 dias** — confirma que o comprador é membro maduro. Premium GBB é o plano de entrada com maior conversão para Vitalício.

### Economia do funil por perfil (tag VIT 2025, confirmada)

Query `01_vit_economia_perfil.sql`:

| Perfil | Leads | Compradores | Conv. | Receita | Receita/lead |
|---|---|---|---|---|---|
| **BASE** (membro/ex-membro) | 25.828 | 9.845 | **38,12%** | R$ 6,20M | **R$ 240** |
| **FRIO** (Não Membro) | 42.076 | 1.697 | 4,03% | R$ 0,62M | R$ 15 |

A base entrega 91% da receita com 38% dos leads. **Lead frio em Vitalício é desperdício** (R$15/lead vs R$240/lead). A frente Vitalício deve ser 100% CRM sobre a base madura.

### Leads necessários (Vitalício)

Os 4.601 compradores trabalháveis vêm da base reativada. Pela conversão do lead de base no funil (38,12%):

> **~12.100 leads de perfil Vitalício** (= membros maduros 9m+ reativados via CRM) → **4.601 compradores → R$ 10,6M**

Não exige aquisição de mídia. Exige **cobertura de CRM da base 9m+** (e-mail, WhatsApp, Comercial). O gargalo não é gerar leads, é a taxa de ativação/abertura da base existente.

---

## FRENTE 2 — BUNDLE (aquisição)

### Melhor análogo histórico: CDL (Clube do Livro)

O bundle é novo (rebranding de planos de assinatura), sem histórico direto. Melhor análogo disponível com funil de lead estruturado: **tag CDL** (49.510 leads, mai-jun/2026). BPS (BP Select) não tem registros em `dtm_analytics_lead_conversion`.

**Caveat:** o funil CDL tem só ~1 mês de maturação (registros desde 06/mai/2026). As conversões são **piso** — vão subir com o tempo. Use como cenário conservador.

### Perfil de conversão CDL (query `02`)

| Perfil | Leads | Compradores | Conv. | Receita | Receita/lead |
|---|---|---|---|---|---|
| **FRIO / Não Membro** | 45.273 | 651 | 1,44% | R$ 629k | R$ 13,9 |
| **BASE** (membro/ex-membro/vit) | 4.237 | 373 | 8,80% | R$ 429k | R$ 101 |

**Perfil oposto ao Vitalício, como esperado:** 91% dos leads são Não Membros (frio), e a aquisição vem de mídia paga (87% dos leads frios via Anúncios/Ads). Confirma o bundle como **produto de entrada/aquisição**.

Detalhe por status × canal (frio paga, base converte melhor mas é volume baixo):

| Status | Canal | Leads | Compradores |
|---|---|---|---|
| Não Membro | PAGO | 42.956 | 456 |
| Não Membro | ORG/OUTRO | 1.778 | 152 |
| Ex-Membro | PAGO | 2.428 | 109 |
| Membro Ativo | ORG/OUTRO | 348 | 96 |

### Ticket do bundle (núcleo de planos de assinatura)

Query `03` — novas vendas de assinatura de entrada em 2026 (good/supporter/best/better/bp-clube):

| Métrica | Valor |
|---|---|
| Ticket ponderado assinatura | **R$ 195** |
| Volume (jan-jun/26) | 158.446 vendas |
| Receita | R$ 30,9M |

Por plano: Básico (good) R$ 211 · Apoiador (supporter) R$ 126 · Premium GBB (best) R$ 483 · BP Clube R$ 108. O bundle como rebranding desses planos deve ter ticket na faixa **R$ 195-250** (eventual premium de bundle puxa para cima).

> **Nota de método:** o CDL em si tem ticket R$ 1.218 (produto anuidade), bem acima do bundle de assinatura. Por isso uso o **perfil/conversão** do CDL (skew frio, mix de canal pago) mas o **ticket dos planos de assinatura** (R$ 195) para o forecast do bundle — não o ticket do CDL.

---

## MATEMÁTICA — Quantos leads de cada perfil para R$ 15M

### Composição da meta

| Frente | Receita | % da meta | Origem |
|---|---|---|---|
| Vitalício (base 9m+) | R$ 10,6M | 71% | Base existente, sem lead incremental |
| Bundle (gap restante) | R$ 4,4M | 29% | Aquisição + base via aquecimento |
| **Total** | **R$ 15,0M** | 100% | — |

### Leads necessários por frente

**Vitalício:** ~12.100 leads de perfil Vitalício (membros 9m+ reativados via CRM) → 4.601 compradores @ R$2.300 → **R$ 10,6M**. Não é geração de lead — é ativação de base.

**Bundle (fechar R$ 4,4M @ ticket R$ 195):** 22.651 compradores necessários.

| Cenário de aquisição | Conv. | Leads necessários | Receita/lead |
|---|---|---|---|
| 100% frio (mídia paga) | 1,44% | **~318.000 leads frios** | R$ 13,9 |
| 100% base reaquecida | 8,80% | ~44.000 leads de base | R$ 101 |
| Mix realista (70% frio / 30% base) | — | ~150-220k leads | — |

### Leitura estratégica

1. **A base carrega a campanha.** R$10,6M (71%) vêm de reativar a base madura via CRM, sem custo de mídia. O esforço de growth aqui é **cobertura e segmentação da base 9m+**, não compra de tráfego.

2. **O bundle é caro em lead.** Para os R$4,4M restantes só com frio, são ~318k leads — volume alto para 1,5 mês. Recomenda-se **misturar base reaquecida** (8,8% conv, R$101/lead, 7× mais eficiente que frio) para reduzir a dependência de aquisição massiva.

3. **Saturação é o risco da frente Vitalício.** A conversão Jun-Jul/2025 (0,90% geral) já é fração da Nov/2023 (3,06%). Se a saturação continuar, os 4.601 compradores podem ser otimistas — o número é **teto conservador**, não garantido. Excluir <9m da oferta é obrigatório para não queimar base.

4. **Sazonalidade favorável.** Jul/2025 fez R$20,2M (Vitalício R$13,6M). O forecast de R$10,6M na frente Vitalício está **abaixo** do realizado de jul/2025, o que dá margem de segurança — desde que a composição da base ainda comporte.

---

## Queries

| Arquivo | O que faz | Status |
|---|---|---|
| [01_vit_economia_perfil.sql](queries/01_vit_economia_perfil.sql) | Economia funil VIT por perfil (base/frio) | ✅ rodou |
| [02_bundle_analogo_cdl_perfil.sql](queries/02_bundle_analogo_cdl_perfil.sql) | Perfil de conversão CDL (análogo bundle) | ✅ rodou |
| [03_ticket_planos_assinatura.sql](queries/03_ticket_planos_assinatura.sql) | Ticket ponderado planos de assinatura de entrada | ✅ rodou |

## Pendências / próximos passos

- **Maturar o análogo bundle:** rerodar query CDL em jul/2026 (funil terá ~2 meses) para conversão de frio estabilizada — a 1,44% atual é piso.
- **Validar saturação 2026:** rodar conversão por faixa da campanha imediatamente anterior de 2026 (se houver oferta Vitalício pós Jun-Jul/2025) para checar se a base saturou ainda mais.
- **Definir ticket final do bundle** com o time de produto (R$195 é o piso de assinatura atual; bundle pode ter premium).
- **Mensurar capacidade de CRM:** quantos dos 384k membros 9m+ são alcançáveis (e-mail válido + WhatsApp + não-blacklist) define se 12.100 leads de perfil Vitalício são atingíveis.
