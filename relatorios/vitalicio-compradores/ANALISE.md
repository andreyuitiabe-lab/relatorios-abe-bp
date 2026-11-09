# Análise: Quem está comprando o vitalício (BNO26)

**Data:** 09/11/2026
**Status:** relatório vivo (refresh diário possível com `python3 refresh.py`)
**Relatório:** [index.html](index.html)

---

## Pergunta original

A Bárbara perguntou no #performance-e-bi (09/11/2026) de onde estavam vindo as vendas de vitalício do Comercial: da campanha VIT atual ou de outras (assinaturas, livros, leads anteriores). A análise foi ampliada para: **quem está comprando o vitalício na Black November 2026, no Comercial e no digital, e o que mudou em relação à BNO25 e ao BP10?** Importa porque a meta da Black é "recuperar o vitalício", e o Comercial vende menos receita de vitalício que no ano passado.

## Decisões de abordagem

- **Universo**: venda aprovada, não renovação, pela regra canônica de vitalício (`bq-planos.md` §Vitalícios).
- **Janelas**:
  - **BNO26**: de 01/11 até ontem.
  - **BNO25**: os mesmos dias do mês em 2025. O mês inteiro distorceria, porque a BNO26 ainda está em curso.
  - **BP10**: de 16/07 a 30/09/2026, a campanha inteira, com o Comercial até 30/09. Serve para comparar o mix, não o volume.
- **Big Picture Membro Fundador ficou fora das comparações.** Ele entra na regra de vitalício, mas foi um lançamento à parte e caiu na 1ª semana da BNO25: 255 vendas, R$ 927 mil. Com ele, a BNO25 parecia ter o dobro de Comercial (422 contra 214) e a leitura se invertia: o Comercial parecia ter caído em volume, quando na verdade subiu.
- **Pessoa = `id_person`** do identity graph, juntando todos os e-mails dela. Histórico de compras, assinaturas, leads e consumo são buscados em qualquer e-mail da pessoa.
- **Relação com a BP**: cada comprador cai numa categoria só, na primeira desta lista que se aplicar:
  1. já tinha vitalício (upgrade);
  2. tinha assinatura de membership paga e ativa (iniciada mais de 1h antes da compra, para não contar a própria);
  3. tinha assinatura encerrada (ex-assinante);
  4. só comprou produto avulso;
  5. nunca comprou.
- **Origem do lead**: último cadastro na `dtm_analytics_lead_conversion` antes da compra.
  - A tag `HUB` fica fora: é criação de conta, não lead.
  - As tags `lp-*` (captura do e-mail na própria página de venda) aparecem separadas do lead de aquisição.
- **UTM da venda do Comercial**: lido como o último anúncio ou disparo de CRM clicado. Não está confirmado que é isso que o Comercial grava (ver pendências).
- **Consumo**: horas de D-90 a D-1, sem sessões acima de 4h, casadas por e-mail.
- **Renda e cartão**:
  - renda = decil de renda do CEP (`dtm_purchasing_power`);
  - cartão = nível máximo já usado pela pessoa (`int_credit_card_level`), que inclui o cartão da própria compra.
- No relatório, linhas com menos de 30 vendas ficam fora dos gráficos de composição. Hoje é o caso da BNO25 · Digital, com 3 vendas.

## Achados principais (01–08/11/2026)

- **633 vitalícios, R$ 1,02 mi**, contra 217 (R$ 647 mil) nos mesmos dias da BNO25, sem o Membro Fundador. Quase toda a diferença vem do digital: 3 vendas na BNO25 e **362** agora, 57% do volume.
- **Comercial: 271 vendas (+27%) e R$ 505 mil (−21%).**
  - O ticket caiu de R$ 2.975 para R$ 1.864.
  - O Black era 67% das vendas do Comercial na BNO25 e agora é 39%. Premium e Essencial cresceram.
- **O Comercial converte menos assinante ativo**: 35% das vendas, contra 57% na BNO25 e 48% no BP10.
  - Entre esses assinantes, o Black caiu de 58% para 45% das compras.
  - A receita vinda de assinante ativo foi de R$ 332 mil para R$ 189 mil.
- **O Comercial vende mais para ex-assinantes e para quem nunca comprou.**
  - Ex-assinantes: de 37 para 88 vendas.
  - Nunca compraram: de 20 para 47.
- **O digital traz gente nova**: 44% nunca compraram nada da BP e 32% são ex-assinantes. É o mesmo perfil do digital no BP10 (53% e 31%).
- **De onde vem o Comercial na BNO26** (último lead antes da compra):
  - 35% nunca foram lead;
  - 25% são lead de mais de 180 dias (BP10-LP, ODI, NTL21, RBP…);
  - 14% são lead de 31 a 180 dias;
  - 14% são lead novo, quase todo da `BNO26-VIT-LP`;
  - 13% vieram de captura na página de venda (`lp-cbr`, `lp-clu`), quase todos já clientes. É upgrade puxado pela campanha da Coleção Brasil com Black Vitalício.
- **UTM das vendas do Comercial**:
  - 75 com BNO26 · Vitalício;
  - 68 com campanhas anteriores (CBR, BP10, CLU, ELS);
  - 55 com outras linhas da BNO26 (CBR, CLU, JOM, BPO);
  - 39 com Google;
  - 34 sem UTM ou só com id de CRM.
- **Lead novo compra rápido**: 148 vendas de quem cadastrou lead nos 30 dias anteriores, a maioria da `BNO26-VIT-LP` (94 no digital, 27 no Comercial). 94% fecharam em até 3 dias do cadastro.
- **Digital por canal de tráfego**: Facebook Ads 175, Message Service 81, site próprio 37, e-mail 25.
- **Pouca gente chega assistindo**: 76% dos compradores não têm sessão na plataforma nos 90 dias antes. Entre os assinantes ativos, são 39%.
- **Perfil geral**:
  - cerca de 2/3 homens;
  - cartão Black, Amex ou Platinum em cerca de metade dos compradores (56% no Comercial, 49% no digital), contra 69% no Comercial da BNO25. Parte da diferença é falta de dado: na BNO26, 19% dos compradores do Comercial não têm cartão registrado, contra 5% na BNO25;
  - SP concentra 1/3 dos compradores.

## Pendências / próximos passos

- [ ] Confirmar com o time de Comercial ou de dados o que é o UTM gravado na venda do Comercial: o último clique do lead, o link do vendedor ou o checkout?
- [ ] A queda do Black no Comercial é de oferta (preço e combos da BNO26 diferentes dos da BNO25) ou de abordagem? Cruzar com o `cenario-comercial.md` quando o log de ofertas da BNO26 for registrado.
- [ ] Assinantes ativos com Black: medir quantos assinantes ativos foram abordados pelo Comercial na BNO26 contra a BNO25 (Zenvia/Pipedrive). É o grupo que mais perdeu receita.
- [ ] O "já tinha vitalício" usa a regra canônica. O identity graph pode unir pessoas indevidamente, então vale uma amostra antes de usar número por pessoa em lista.

## Queries

| Arquivo | O que faz |
|---|---|
| [queries/base_compradores.sql](queries/base_compradores.sql) | Uma linha por venda de vitalício nas 3 janelas, com o perfil do comprador no momento da compra. O `refresh.py` preenche as datas e agrega em Python; o `data.json` só tem agregados. |
| [queries/conversas_zenvia.sql](queries/conversas_zenvia.sql) | 1ªs interações das conversas na Zenvia iniciadas até 30 dias antes da compra; o refresh classifica a origem (botão de disparo, link da LP, hotlead, espontâneo) e só grava contagens. |
| [queries/conversas_abertas.sql](queries/conversas_abertas.sql) | Mensagens em qualquer conversa da pessoa (e-mail e telefone) para separar "conversa já aberta" de "sem conversa". |
| [queries/deals_pipedrive.sql](queries/deals_pipedrive.sql) | Deal da Pipedrive que levou cada venda (`dtm_seller_conversion_rate`) e, no hotlead, a transação de origem. |
| [queries/jornada_eventos.sql](queries/jornada_eventos.sql) | Jornada na `fct_leads_events` dos 30 dias antes da compra (compradores da BNO26), incluindo CRM, Zenvia, Pipedrive, checkout, plataforma e cadastro. Disparos vêm só como contagem. Varre cerca de 35 GB. Ainda não está no relatório (exploração de 09/11). |

### Jornada na `fct_leads_events` (exploração 09/11, 01–08/11)

- **Comercial (271 vendas)**:
  - 48% começaram numa conversa de chat ou WhatsApp. São deals da Pipedrive do tipo "Chat" ou conversa na Zenvia com origem "FLOW", que provavelmente é inbound (a confirmar).
  - 15% vieram de oportunidade aberta pelo vendedor.
  - 9% foram recuperação de checkout (abandono, compra negada, Pix expirado).
  - 23% não têm nenhum contato registrado na Zenvia ou na Pipedrive nos 30 dias anteriores. Pode ser ligação, contato anterior à janela ou e-mail diferente.
- **Velocidade**: dos 179 compradores do Comercial com conversa na Zenvia, 51% compraram em até 1 dia da primeira conversa.
- **Digital (362 vendas)**: 31% falaram com o Comercial nos 30 dias antes. São 44 em conversa de chat, 21 em oportunidade aberta pelo vendedor, 40 em recuperação de checkout e 6 em outro contato. Outros 10% tiveram checkout falho e voltaram sozinhos. É venda que passou pelo Comercial mas não aparece no canal Comercial.
- **Como começam as conversas do Comercial.** Pela 1ª mensagem na Zenvia (`int_zenvia_analytics`), considerando a conversa mais antiga em até 30 dias antes da compra, as 271 vendas se dividem assim:
  - 54 (20%) são resposta a botão de disparo, como "QUERO MEU VITALÍCIO" e "VER COLEÇÃO + BLACK". Em ~77% delas não houve WhatsApp do Insider antes, então o mais provável é o Attraction.
  - 34 (13%) vieram de mensagem pronta de link de WhatsApp de LP ou anúncio.
  - 32 (12%) foram conversas abertas pelo vendedor a partir da Pipedrive.
  - 28 (10%) são FLOW sem histórico do bot, provavelmente botão também.
  - 18 (7%) foram texto livre no bot.
  - 3 vieram do portal.
  - 102 (38%) não iniciaram conversa na janela. Validado buscando por e-mail **e telefone** em qualquer conversa ([queries/conversas_abertas.sql](queries/conversas_abertas.sql)): 56 trocaram mensagens com o vendedor nos 30 dias antes numa conversa aberta havia muito tempo (41 com 1º contato na Zenvia há mais de 1 ano; mediana de 36 mensagens do vendedor e 11 do cliente; 23 só aparecem pelo telefone). Os outros 45 não têm mensagem antes da compra: 23 estão na Zenvia sem mensagem nos 30 dias, 11 só têm mensagem depois da compra e 11 nunca estiveram na Zenvia. Não são clientes mais antigos que a média do Comercial (41% com mais de 3 anos de casa, igual à média); o que eles têm é contato antigo com o vendedor.
  - O "Chat" da Pipedrive e o "FLOW" da Zenvia não são inbound espontâneo: em boa parte são resposta a disparo.
- **Deal da Pipedrive que levou a venda do Comercial** (271): chat 128 (R$ 241 mil), **hotlead 97 (36%, R$ 163 mil)**, lista 25, sem deal 21.
  - Hotlead por tipo: **oportunidade pós-compra 46** (compra aprovada e o vendedor subiu o plano; 29 viraram Black Vitalício; em 27 a compra original foi reembolsada, ou seja, troca; origem mais comum Premium Vitalício e Coleção Brasil), **recuperação de compra nova 28** (abandono 15, compra negada 13), **renovação que falhou 23** (Pix 15, compra negada 5, boleto 3).
  - 35 dos 97 hotleads tiveram o deal aberto mais de 7 dias antes da venda; como a venda fica com o deal mais recente, parte pode ser crédito de chat ou lista.
  - As 32 conversas "vendedor abriu" são quase todas hotlead (29: 18 oportunidade, 5 abandono, 3 compra negada, 3 Pix).
- **Contato espontâneo** (19 vendas): pergunta sobre a oferta 4, só cumprimento 5, veio de outra área da BP (app, Clube do Livro) 3, resposta ao chatbot 4, botão no portal 3. 16 de 19 já eram ou tinham sido assinantes. O texto literal não vai para o repo (público).
- **CRM**: o comprador do Comercial recebeu em mediana 43 disparos em 30 dias, 13 deles de campanha de vitalício ou Black. 37% clicaram em alguma mensagem. 74% visitaram o site.

## Wiki atualizada

- `wiki-brasil-paralelo/pages/vitalicio.md`: seção "Quem compra vitalício na BNO26".
- `wiki-bp/pages/metricas-referencia.md`: vendas de vitalício nas três janelas.
- `wiki-bp/pages/bq-planos.md`: gotcha do Membro Fundador na 1ª semana da BNO25.
- `wiki-bp/log.md`: registro das três atualizações.
