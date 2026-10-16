# ADR 0008 — Tipos de letra alojados no próprio sítio

Estado: aceite (2026-10-15, o responsável pediu uma renovação visual com identidade).

## Contexto
O sítio usava a letra sem serifa por omissão do navegador. A renovação dá-lhe uma voz de leitura para as citações dos acórdãos e uma letra mais discreta para a interface. A CSP é `default-src 'self'` (SPEC §8), por isso os tipos de letra não podem vir de um CDN externo, e a regra 9 do AGENTS.md pede um ADR para cada nova dependência de execução.

## Decisão
- Acrescentar `@fontsource-variable/literata` (serifada, desenhada para leitura longa em ecrã; citações e títulos) e `@fontsource-variable/hanken-grotesk` (sem serifa; texto da interface e números).
- Ambos são incluídos pelo Vite em `web/dist` e servidos a partir da origem do próprio sítio, por isso a CSP não muda.
- Licença: SIL Open Font License 1.1 nos dois (a redistribuição no pacote é permitida).
- As alternativas na pilha de letras (`Iowan Old Style`, `Georgia`, `system-ui`) mantêm o texto legível se um tipo de letra não carregar.

## Alternativas consideradas
- Só letras do sistema: sem dependência, mas sem identidade, e o resultado varia muito entre plataformas.
- Google Fonts em tempo de execução: exigiria uma exceção na CSP e enviaria o IP de cada visitante a terceiros.

## Consequências
- Cerca de 100 a 200 KB de woff2 por visitante, em cache; só se descarregam os subconjuntos de caracteres que o texto da página usa (`unicode-range`).
- Mais dois pacotes para manter atualizados (o Dependabot cobre `web/`).
