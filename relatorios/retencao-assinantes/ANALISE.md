# Análise: Impacto Financeiro — Downgrade Anual → Mensal (Saldo Insuficiente)

**Data:** jun/2026
**Status:** concluída
**Solicitante:** Thyago Berardinelli / Marinho

---

## Pergunta original

Avaliar se faz sentido fazer downgrade automático (anual → mensal) para clientes com renovação recusada por "Saldo Insuficiente", comparando com o processo atual de recuperação via comercial + CRM.

**Meta verificável:** calcular receita recuperada no cenário atual vs. receita projetada no cenário downgrade.

---

## Decisões de abordagem

- Campo correto: `nm_error_category = 'SALDO/LIMITE INSUFICIENTE'` (não `nm_refuse_reason`)
- Janela de recuperação atual: 90 dias após primeira falha
- Downgrade aplicado **somente aos não recuperados** — é complementar ao processo atual, não substituto
- Preços confirmados: sem desconto anual vs mensal (anual = 12× mensal)
- Clientes únicos como unidade (os 68k da mensagem do Thyago são transações; média de 2.6 tentativas/cliente)

---

## Achados principais

### Clientes únicos impactados (últimos 12 meses)

| Plano | Clientes únicos | Transações | Tentativas/cliente |
|---|---|---|---|
| Básico | 14.735 | 38.648 | 2,6 |
| Apoiador | 5.430 | 14.016 | 2,6 |
| Premium GBB | 3.483 | 8.711 | 2,5 |
| Intermediário | 947 | 2.396 | 2,5 |
| **Total** | **24.595** | **63.771** | |

### Taxa de recuperação atual (processo comercial + CRM, 90 dias)

| Plano | Falhas | Recuperados | Não recuperados | Taxa |
|---|---|---|---|---|
| Básico | 14.735 | 2.338 | 12.397 | **15,9%** |
| Apoiador | 5.430 | 885 | 4.545 | **16,3%** |
| Premium GBB | 3.483 | 393 | 3.090 | **11,3%** |
| Intermediário | 947 | 159 | 788 | **16,8%** |
| **Total** | **24.595** | **3.775** | **20.820** | **15,4%** |

**Importante:** 100% dos recuperados voltaram no mesmo plano anual — nenhum downgrade espontâneo foi observado.

### Impacto financeiro

**Receita atual recuperada (comercial + CRM):**

| Plano | Valor anual | Recuperados | Receita |
|---|---|---|---|
| Básico | R$228 | 2.338 | R$533.064 |
| Apoiador | R$120 | 885 | R$106.200 |
| Premium GBB | R$708 | 393 | R$278.244 |
| Intermediário | R$468 | 159 | R$74.412 |
| **Total** | | | **R$991.920** |

**Receita projetada com downgrade (aplicado aos 20.820 não recuperados):**

| Cenário | Adesão | Meses retidos | Receita adicional | Total com recuperação atual |
|---|---|---|---|---|
| Conservador | 40% | 9 | R$1.778.526 | **R$2.770.446** |
| Moderado | 60% | 9 | R$2.667.789 | **R$3.659.709** |
| Otimista | 80% | 12 | R$4.742.736 | **R$5.734.656** |

**Potencial máximo** (todos renovassem anual): R$6.920.540

| Cenário | % do potencial capturado |
|---|---|
| Hoje (só comercial + CRM) | 14% |
| + Downgrade conservador | 40% |
| + Downgrade moderado | 53% |
| + Downgrade otimista | 83% |

---

## Conclusão

O processo atual recupera apenas **15% dos clientes** com falha por saldo insuficiente, gerando **R$992k** dos R$6,9M potenciais.

O downgrade mensal aplicado ao segmento não recuperado é **complementar ao processo atual** (não o substitui). Mesmo no cenário conservador (40% de adesão, 9 meses de retenção), **quase triplica a receita recuperada** (R$1,78M adicional).

A incerteza está nas taxas de adesão e retenção do plano mensal — não há histórico interno de clientes nesse fluxo específico. Recomendação: testar com uma amostra antes de escalar.

---

## Pendências / próximos passos

- [ ] Validar taxa de adesão e retenção com um piloto (ex: 1.000 clientes Básico não recuperados)
- [ ] Definir janela de espera antes de oferecer downgrade (ex: 30 dias → esperar comercial, depois oferece mensal)
- [ ] Verificar se o gateway suporta troca de periodicidade sem cancelar a assinatura

---

## Queries

| Arquivo | Status | O que faz |
|---|---|---|
| [queries/01_clientes_saldo_insuficiente.sql](queries/01_clientes_saldo_insuficiente.sql) | ✅ validada (via inline) | Clientes únicos com falha por saldo insuficiente |
| [queries/02_taxa_recuperacao_atual.sql](queries/02_taxa_recuperacao_atual.sql) | ✅ validada (via inline) | Taxa de recuperação atual + receita perdida por plano |
| [queries/03_cenarios_downgrade.sql](queries/03_cenarios_downgrade.sql) | ✅ validada (via inline) | Projeção de receita com downgrade |

**Campo correto para filtrar:** `nm_error_category = 'SALDO/LIMITE INSUFICIENTE'`

---

## Wiki atualizada

- `wiki-bp/pages/bq-schema-core.md` — adicionar campos de erro: `nm_error_category`, `nm_error_type`, `nm_error_meaning`, `nm_refuse_reason`, `cd_refuse_reason`
