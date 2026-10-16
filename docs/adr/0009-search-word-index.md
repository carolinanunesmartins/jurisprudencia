# ADR 0009 — Pesquisa: índice de palavras dos sumários, sem publicar o texto

Estado: aceite (2026-10-16, decisão do responsável).

## Contexto
A pesquisa no sítio deve encontrar palavras nas perguntas, nas citações e nos sumários. As perguntas e as citações (até 400 caracteres) já são públicas. Os sumários não: a regra 3 do AGENTS.md e o SPEC §12 proíbem publicar textos integrais e sumários completos. O sítio é estático (ADR 0001), por isso a pesquisa corre no navegador e só pode usar o que for publicado.

## Decisão
- A exportação publica `web/public/data/search.json`: para cada palavra normalizada, os acórdãos cujo sumário a contém e quantas vezes. **Nenhuma frase nem excerto do sumário é publicado.**
- Normalização v2, igual em Python e no sítio: `º` e `ª` separam palavras (442º = 442.º = 442), sem acentos nem outros sinais combinados, minúsculas, só letras e algarismos, sem palavras vazias (`pipeline/juris/search/stopwords.txt`), entre 2 e 30 caracteres (números de 1 algarismo contam). Casos de referência partilhados pelos dois lados: `pipeline/tests/regression/golden/search_normalise.json`.
- Só entram acórdãos já publicados (com posição numa pergunta). Os poucos classificados pelo texto integral não têm palavras no índice.
- O instantâneo comitado guarda, por acórdão, as contagens de palavras (`sumario_terms`), nunca o texto, para que um clone novo reproduza `search.json` byte a byte.
- `make data-check` rejeita qualquer termo que não seja `[a-z0-9]{1,30}`, o que impede que texto corrido entre no índice por engano.
- O resultado de uma pesquisa mostra sempre a citação verificada e a ligação ao dgsi.pt; quando a palavra só está no sumário, o sítio di-lo.
- Relevância calculada no navegador (BM25 por campo, mais peso à pergunta do que à citação, e à citação do que ao sumário). Sem biblioteca nova.

## Alternativas consideradas
- Publicar os sumários: melhores resultados e excertos com a palavra realçada, mas muda a política de dados e aumenta muito os ficheiros.
- Pesquisar só o que já é público (perguntas e citações): sem mudança de política, mas perde as palavras que só aparecem no sumário.
- Um servidor de pesquisa: contraria o ADR 0001.

## Consequências
- Um conjunto de palavras sem ordem não permite ler o sumário, mas revela que palavras ele contém. É uma alteração consciente à política de dados, registada no SPEC §10 e na regra 3 do AGENTS.md.
- `search.json` é o maior ficheiro do sítio, por isso só é descarregado quando se abre a pesquisa.
- Se a normalização mudar, muda a versão (`version`) e os casos de referência.
