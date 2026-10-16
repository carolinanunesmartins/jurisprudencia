# ADR 0001 — Sítio estático no GitHub Pages

Estado: aceite (2026-10-12). Registado retroativamente em 2026-10-15; a decisão está no SPEC §8 e §12.

## Contexto
O resultado é uma vista só de leitura sobre um conjunto de dados fixo e publicado. O SPEC §1 exclui pesquisa livre, chat/RAG e contas, por isso nada precisa de um servidor no momento do pedido.

## Decisão
- Vite + React + TypeScript compilados para ficheiros estáticos. O pipeline escreve `web/public/data/*.json` (`make export`) e o sítio só os lê.
- HashRouter, para que todas as rotas funcionem num alojamento sem reescritas no servidor.
- Alojamento no GitHub Pages, publicado pelo GitHub Actions depois de `make data-check` passar (`.github/workflows/deploy.yml`).
- O Pages não permite definir cabeçalhos de segurança, por isso a CSP é um `<meta http-equiv>` em `web/index.html` (aí, `frame-ancestors` não tem efeito).

## Consequências
- Sem servidor, sem cookies, sem *analytics*, e nenhum pedido sai da origem do sítio.
- As rotas com `#` não são indexadas em separado pelos motores de pesquisa.
- Um sítio de projeto no Pages não pode servir `robots.txt` na raiz do domínio.
