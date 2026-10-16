# ADR 0006 — Acórdãos sem texto integral são classificados pelo sumário e assinalados

Estado: aceite (2026-10-14, decisão do responsável); alterado pelo ADR 0007 (2026-10-15): o sumário passa a ser a fonte principal para todos os acórdãos que o têm.

## Contexto
O primeiro piloto real (100 acórdãos do subconjunto, estratificados por ano) obteve 91/100 com sumário e texto integral, abaixo da meta de 95 % do ROADMAP M2. As 9 falhas estão vazias no próprio dgsi.pt (verificado no HTML em cache): 7 acórdãos têm sumário mas a "Decisão Texto Integral" vazia (cinco de 2000–2001, dois de 2010) e 2 de 2003 têm texto integral mas não têm sumário. A partir de 2004, 81/83 estavam completos. A amostra dos primeiros anos é pequena (6 acórdãos em 2000–2001), por isso a taxa desses anos é um sinal, não uma estimativa.

## Decisão
- Um acórdão com texto integral é classificado pelo texto integral, como no SPEC §6.1.
- Um acórdão com sumário mas **sem texto integral** é classificado só pelo sumário. A verificação da citação não muda: a citação tem de ser uma parte literal (depois de normalizar os espaços) do sumário guardado, e o limite de 400 caracteres aplica-se.
- Um acórdão sem nenhum dos dois é excluído e contado no relatório.
- A fonte usada fica registada em cada classificação (`text_source` = `texto` | `sumario`, acrescentado no M4) e o sítio assinala os que só têm sumário ("só sumário") na lista de acórdãos e no cartão da divergência.
- A deteção (SPEC §6.2) conta-os como qualquer outro acórdão classificado. O relatório diz quantos acórdãos classificados só têm sumário, por pergunta e por janela, e a amostra de avaliação de 60 inclui alguns, para medir a sua exatidão em separado.

## Alternativas consideradas
- Excluí-los: mais simples e mais estrito, mas 2000–2001 ficariam quase vazios e a linha do tempo começaria por volta de 2002 sem o dizer.
- Excluí-los e começar a janela em 2002: honesto, mas perde dados que o tribunal publicou.

## Consequências
- O sumário é escrito pelo tribunal e é mais curto e mais conclusivo do que a fundamentação, por isso uma posição lida nele pode ser menos fiável. Isto é medido, não presumido (ver acima), e está dito em `/metodo`.
- A citação mostrada para um acórdão só com sumário vem do sumário, e o sítio diz isso.
- A regra 4 do AGENTS.md ("texto guardado") lê-se como: `sumario` ou `texto`, o que a classificação tiver usado.
- Rever se a exatidão dos acórdãos só com sumário, na amostra etiquetada, for claramente pior do que a dos textos integrais: nesse caso, excluí-los.
