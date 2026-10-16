# ADR 0007 — Classificar primeiro pelo sumário; o texto integral é o recurso

Estado: aceite (2026-10-15, decisão do responsável). Altera o ADR 0006 e o SPEC §6.1.

## Contexto
A exatidão das posições (SPEC §9.1) compara o modelo com 60 etiquetas do responsável. O responsável não consegue ler 60 acórdãos completos do STJ nas ≈ 2 h disponíveis, por isso as etiquetas são lidas no sumário. Se o modelo lesse o texto integral, as discordâncias mediriam em parte "sumário contra texto integral" e não o erro do modelo. O *spike* e a passagem de descoberta (M1.5, M3) também correram sobre sumários, com todas as citações verificadas.

## Decisão
- Um acórdão com sumário é classificado pelos campos do cabeçalho e pelo **sumário** (`text_source=sumario`).
- Um acórdão sem sumário mas com texto integral é classificado pelo texto integral, truncado como no SPEC §6.1 (`text_source=texto`). Na recolha do M2 são 13 de 813.
- Um acórdão sem nenhum dos dois é excluído e contado, como antes.
- A citação é verificada contra o texto que foi usado.

## Alternativas consideradas
- Texto integral primeiro (o ADR 0006 como estava escrito): pode encontrar posições que o sumário omite, mas a avaliação deixaria de medir só o modelo, e custa cerca de 10× os tokens de entrada.

## Consequências
- As posições que só aparecem na fundamentação perdem-se; o relatório declara esta limitação.
- A amostra etiquetada não pode incluir os 13 acórdãos só com texto (não há sumário para etiquetar), por isso a sua exatidão não é medida.
- A marca "só sumário" do ADR 0006 é substituída por uma marca nos poucos acórdãos só com texto.
- Rever se as verificações pontuais do responsável mostrarem que os sumários omitem muitas vezes a posição que o acórdão toma.
