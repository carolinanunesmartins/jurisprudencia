# ADR 0002 — Taxonomia supervisionada em vez de *clustering*

Estado: aceite (2026-10-12). Registado retroativamente em 2026-10-15; a decisão está no SPEC §5 e §12.

## Contexto
Uma divergência só tem sentido quando dois acórdãos respondem à mesma questão jurídica de formas opostas. Agrupar por semelhança de texto junta temas, não respostas, e os rótulos que daí saem não são estáveis o suficiente para mostrar a quem lê.

## Decisão
- As perguntas são curadas: 5 perguntas-semente de um levantamento prático (SPEC §5.2), mais até 3 propostas por uma passagem de descoberta com um modelo sobre uma amostra de 150 acórdãos (SPEC §5.3).
- O responsável aprova, edita ou rejeita cada uma. Cada pergunta aprovada tem 2 a 4 posições, com definições escritas antes de classificar qualquer acórdão.
- A taxonomia fica congelada como `v1` (`data/taxonomy.json`, etiqueta git `taxonomy-v1`), junto com o prompt `classify_v1`.
- *Embeddings* e *clustering* ficam como objetivo opcional, não obrigatório.

## Consequências
- A cobertura limita-se às perguntas aprovadas (7 na `v1`); o resto do que os acórdãos discutem não é visto.
- Cada classificação é uma posição numa pergunta definida, por isso as posições comparam-se entre anos e podem ser verificadas contra etiquetas.
