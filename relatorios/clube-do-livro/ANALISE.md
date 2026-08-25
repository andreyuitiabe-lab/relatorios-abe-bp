# Análise: Perfil de Compra — Clube do Livro

_Atualizado em 25/08/2026 (janela original era mai–jun/2026; agora cobre a campanha inteira até 24/08)._

## Pergunta original
Quem são os compradores do CDL? Quantos são membros, ex-membros e não-membros. Há quanto tempo são clientes BP. Perfil de consumo.

## Decisões de abordagem
- **Status no momento da compra**, não status atual — classificação histórica via `dim_subscriptions`
- **id_person** como chave de identidade — resolve múltiplas contas via `dim_person_identity` (email/telefone/CPF)
- **Apenas produtos físicos** — filtro por `nm_gateway_product` (8 valores fornecidos pelo Comercial)
- **Vitalício dual-detection** — `nm_subscription_recurrence = 'vitalício'` em `dim_subscriptions` + fallback `bl_lifetime_offer = TRUE` em `fct_transactions` (corrige ~425 vitalícios ausentes de dim_subscriptions)
- **Operador `>`** (não `>=`) na condição Membro Ativo — o checkout CDL vende produto + assinatura no mesmo dia; `>=` inflava Membros Ativos com pessoas genuinamente novas
- **QUALIFY por id_person** — não por id_gateway_customer, para deduplicar corretamente pessoas com múltiplas contas
- **(25/08) Exclusão de assinaturas-fantasma de produtos físicos** — CDL e Odisseia geram registro `paid` em `dim_subscriptions`, e o combo Odisseia+Travessia vem com `bl_lifetime_offer = TRUE` sem ser vitalício. Sem excluir esses planos, comprar um livro contaria como membership. Efeito aqui: 0,2pp (materialíssimo no relatório irmão da Odisseia, onde 54% da base comprou o CDL antes).

## Achados principais

**Base:** 24.753 compradores físicos (05/05–24/08/2026) · R$ 31,5M · ticket médio R$ 1.274

**Status no momento da compra:**
- Membro Ativo: 36,5% (9.028)
- Vitalício: 30,5% (7.539)
- Nunca foi Membro: 17,7% (4.369)
- Ex-Membro: 15,4% (3.817)
→ 82,3% já eram clientes BP no momento da compra

**Antiguidade na BP:**
- Mais de 4 anos: 39,3% (9.735) — base fiel e consolidada
- 2–4 anos: 22,9% (5.673)
- CDL como 1ª compra: 17,7% (4.369)
→ 62,2% compraram com mais de 2 anos de casa

**Canal:**
- Comercial: 51,2% (12.682) · ticket R$ 1.248
- Digital: 48,8% (12.071) · ticket R$ 1.302

**Consumo histórico (antes do CDL):**
- Gasto médio: R$ 3.072 (mediana R$ 1.199)
- Média de planos adquiridos: 2,8
- 20.191 compradores (82%) tinham histórico de compra antes do CDL

**Produtos mais frequentes antes do CDL:**
- Básico: 41,9% · Premium GBB: 32,8% · Patriota: 22,9% · Núcleo: 18,0% · Acesso Total: 16,6%

## Impacto do id_person vs email-only
- "Nunca foi Membro" caiu de 18,4% → 13,1% na medição original (-5,3pp): vínculos via telefone/CPF identificaram membros que o email não capturava
- "Mais de 4 anos" subiu de 35,9% → 41,9% (+6pp): transações antigas de outras contas agora associadas

## Como o perfil mudou com a campanha completa (jun → ago)
A janela cresceu de 16,8k para 24,8k compradores e as **distribuições ficaram estáveis** — a fase digital
tardia não mudou o tipo de comprador. Os deslocamentos são pequenos e todos na mesma direção: mais gente
nova (1ª compra 14,2% → 17,7%) e menos vitalício (34,8% → 30,5%), coerente com a abertura da venda digital
com lotes e order bumps depois do D14.

## Pendências / próximos passos
- Comparar com o perfil do 2º livro: ver [`odisseia-perfil/`](../odisseia-perfil/ANALISE.md) — inclui a interseção das duas bases (1.583 pessoas compraram os dois; recompra de 6,3%).

## Queries
| Query | Arquivo | Status |
|-------|---------|--------|
| Todas as métricas do relatório | `refresh.py` | ✅ |
| Vendas por estado / cidade | `queries/cdl_por_estado.sql`, `queries/cdl_por_cidade.sql` | ✅ |

## Wiki atualizada
- `queries-referencia.md` — padrão de classificação de status do membro + tabela `>=` vs `>` + nota sobre id_person
- `bq-planos.md` (25/08) — gotcha das assinaturas-fantasma de produtos físicos
