# ADR 0003 — Verificação das citações como condição obrigatória

Estado: aceite (2026-10-12; regras de localização acrescentadas em 2026-10-15). Registado retroativamente em 2026-10-15; a decisão está no SPEC §6.1 e na regra 4 do AGENTS.md.

## Contexto
Cada afirmação do sítio tem de poder ser confirmada no acórdão. Um modelo pode parafrasear ou inventar uma passagem com ar de citação.

## Decisão
- O modelo tem de devolver a passagem que sustenta a posição, com 400 caracteres no máximo.
- A passagem é procurada no texto guardado (`juris.classify.grounding.ground`). O que se guarda e mostra é **o excerto do próprio texto**, nunca a cadeia escrita pelo modelo.
- Para a encontrar só se aceitam reparações nomeadas, cada uma contada no relatório: tipografia, número de parágrafo omitido, espaços ou hifenização partidos no original, ponto final em falta, e junções com "..." em que cada parte aparece pela ordem (guarda-se só a parte mais longa).
- O que não for encontrado é rejeitado, guardado com `quote_ok=false` e contado. Citações inventadas aceites: tem de ser 0.
- `make data-check` verifica as citações publicadas. A CI verifica-as só nas *fixtures*, porque os textos integrais nunca são comitados.

## Consequências
- Na corrida real, 11 de 695 respostas foram rejeitadas e nenhuma foi publicada; essas posições ficam fora da deteção.
- As regras de localização foram acrescentadas depois da primeira corrida. Não alteram nenhum limiar nem o prompt e são reaplicadas sem custo a partir das respostas gravadas (`--reground`).
