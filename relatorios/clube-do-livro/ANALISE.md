# Análise: Perfil de Compra — Clube do Livro

## Pergunta original
Quem são os compradores do CDL? Quantos são membros, ex-membros e não-membros. Há quanto tempo são clientes BP. Perfil de consumo.

## Decisões de abordagem
- **Status no momento da compra**, não status atual — classificação histórica via `dim_subscriptions`
- **id_person** como chave de identidade — resolve múltiplas contas via `dim_person_identity` (email/telefone/CPF)
- **Apenas produtos físicos** — filtro por `nm_gateway_product IN (8 valores)` fornecidos pelo Comercial
- **Vitalício dual-detection** — `nm_subscription_recurrence = 'vitalício'` em `dim_subscriptions` + fallback `bl_lifetime_offer = TRUE` em `fct_transactions` (corrige ~425 vitalícios ausentes de dim_subscriptions)
- **Operador `>`** (não `>=`) na condição Membro Ativo — o checkout CDL vende produto + assinatura no mesmo dia; `>=` inflava Membros Ativos com pessoas genuinamente novas
- **QUALIFY por id_person** — não por id_gateway_customer, para deduplicar corretamente pessoas com múltiplas contas

## Achados principais

**Base:** 16.841 compradores físicos (mai–jun 2026) · R$20,7M · ticket médio R$1.231

**Status no momento da compra:**
- Membro Ativo: 38.1% (6.409)
- Vitalício: 34.8% (5.857)
- Ex-Membro: 14.1% (2.370)
- Nunca foi Membro: 13.1% (2.205)
→ 86,9% já eram clientes BP no momento da compra

**Antiguidade na BP:**
- Mais de 4 anos: 41.9% (7.054) — base fiel e consolidada
- 2–4 anos: 24.3% (4.095)
- CDL como 1ª compra: 14.2% (2.392)
→ 66% compraram com mais de 2 anos de casa

**Canal:**
- Comercial: 52.5% (8.847) · ticket R$1.214
- Digital: 47.5% (7.994) · ticket R$1.251

**Consumo histórico (antes do CDL):**
- Gasto médio: R$3.384 (mediana R$1.415)
- Média de planos adquiridos: 2.9
- 14.505 compradores (86%) tinham histórico de compra antes do CDL

**Produtos mais frequentes antes do CDL:**
- Básico: 44.1%
- Premium GBB: 35.4%
- Patriota: 24.6%
- Núcleo: 20.0%
- Acesso Total: 18.6%

## Impacto do id_person vs email-only
- "Nunca foi Membro" caiu de 18.4% → 13.1% (-5.3pp): vínculos via telefone/CPF identificaram membros que o email não capturava
- "Mais de 4 anos" subiu de 35.9% → 41.9% (+6pp): transações antigas de outras contas agora associadas
- Com histórico: 13.582 → 14.505 (+923 pessoas)

## Queries
| Query | Arquivo | Status |
|-------|---------|--------|
| Todas as métricas do relatório | `refresh.py` | ✅ |

## Wiki atualizada
- `queries-referencia.md` — padrão de classificação de status do membro + tabela `>=` vs `>` + nota sobre id_person
