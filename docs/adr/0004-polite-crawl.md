# ADR 0004 — Política de crawl educado

Estado: aceite (2026-10-12). Registado retroativamente em 2026-10-15; as regras estão no SPEC §3 e nas regras 1 e 2 do AGENTS.md.

## Contexto
O dgsi.pt é um serviço público sem robots.txt (verificado pelo responsável em 2026-10-12). Não ter robots.txt não é autorização, e a recolha tem de custar o mínimo possível ao sítio.

## Decisão
- Uma ligação e um pedido de cada vez, com pelo menos 2,5 s (mais 0–1 s aleatórios) entre pedidos e 30 s de limite de espera.
- Um `User-Agent` identificável, com o contacto do responsável (`JURIS_CONTACT`).
- Cada resposta fica em cache no disco (`data/raw/`, ignorado pelo git) pelo URL canónico. Nenhum URL é pedido duas vezes e as corridas retomam a partir da cache.
- Uma corrida para no primeiro HTTP 429/503 ou após 3 erros seguidos. Sem repetições em ciclo e sem contornos. Cada corrida tem um limite de pedidos (`--max-requests`, 800 por omissão) e corre fora das horas de ponta.
- Antes de cada pedido verifica-se uma lista de anfitriões permitidos.
- Só uma pessoa corre `make index` e `make fetch`. Os agentes de IA nunca contactam o dgsi.pt e trabalham sobre páginas guardadas.

## Consequências
- O índice completo leva cerca de 740 pedidos (cerca de 40 min). Com os documentos do subconjunto, a recolha toda leva cerca de 1,3 a 2,5 h.
- Os testes correm sem rede, sobre *fixtures* HTML em `pipeline/tests/fixtures/`.
