# Win-back — Ex-membros engajados (Maio → 15/jun 2026)

## Pergunta original
Lista para o Comercial: ex-membros que perderam acesso entre 01/mai e 15/jun/2026, **não abordados nos últimos 30 dias**, que tinham **alto engajamento** quando eram membros ativos. Excluir high-ticket: Mecenas, CEC-BP, Retiro BP, Vitalícios, Clube do Livro.

## Decisões de abordagem
- **Ex-membro**: `dim_subscriptions` com `bl_is_last_user_subscription = TRUE`, `nm_type = 'paid'`, `nm_status IN ('canceled','expired')` e `DATE(dt_expires_in)` na janela. Usa a assinatura mais recente para garantir que não há plano ativo hoje.
- **Alto engajamento** (escolha do solicitante): **horas totais assistidas** durante a assinatura (`obt_kafka__view_sessions`, sessões entre `dt_started_at` e `dt_expires_in`). Corte no **quartil superior (P75) = 10,9h**, calculado dinamicamente sobre a própria coorte.
- **Não abordados em 30 dias**: exclusões padrão Zenvia + Pipedrive (janela 30d, followUp, deals abertos) + blacklist CRM.
- **High-ticket**: CTE customizada com exatamente os 5 produtos pedidos (Mecenas, Vitalício, CEC/Conselho Editorial, Retiro, Clube do Livro), triple-check email+telefone+CPF. **Não** exclui Black recorrente nem certificações — fora da lista do pedido e bons alvos de win-back.
- **Dedupe**: multi-identificador (email/telefone/CPF), mantém o registro de maior engajamento.

## Achados principais
- Coorte de ex-membros na janela: **51.557**; com algum engajamento: **45.798**.
- Distribuição de horas (engajados): mediana 4,7h · P75 10,9h · P90 22,9h · máx 1.076h.
- **Lista final: 10.102 contatos** após corte P75 + todas as exclusões + dedupe.
- Composição por plano: good 5.154 · supporter 3.841 · best 567 · better 361 · funil-bitcoin 85 · bitcoin 56 · teller 27 · black 7 · outros 4.

## Pendências / próximos passos
- Nenhuma. Se o Comercial quiser priorizar, ordenar por `horas_assistidas` (já é o sort do CSV) ou cruzar com decil de renda.

## Queries
| Arquivo | Status |
|---------|--------|
| [queries/ex_membros_engajados.sql](queries/ex_membros_engajados.sql) | ✅ rodou → `lista_ex_membros_engajados.csv` |

## Wiki atualizada
- (nenhuma — padrão de win-back ainda não documentado; candidato a entrar em `listas-comercial.md` se virar recorrente)
