# Jurisprudência

Agrupa acórdãos do Supremo Tribunal de Justiça (STJ), publicados no [dgsi.pt](https://www.dgsi.pt), por **questão jurídica** e mostra **onde e quando a jurisprudência divergiu ou mudou**. Cada sinal traz uma citação literal do acórdão e a ligação ao original.

> **Aviso:** sinal para revisão, não é parecer jurídico.

**Sítio:** https://carolinanunesmartins.github.io/jurisprudencia/
**Ler primeiro:** [NOTA.md](NOTA.md) (uma página) · [IA.md](IA.md) (uso de IA) · [relatório de avaliação](data/eval/report.md)

## Vídeos

Clique numa imagem para ver o vídeo no browser (também no telemóvel).

<table>
  <tr>
    <td align="center"><a href="https://carolinanunesmartins.github.io/jurisprudencia/video/anuncio.mp4"><img src="web/public/video/anuncio.jpg" width="260" alt="Anúncio"></a><br><b><a href="https://carolinanunesmartins.github.io/jurisprudencia/video/anuncio.mp4">Anúncio</a></b><br>45 s · a ideia em cinco frases</td>
    <td align="center"><a href="https://carolinanunesmartins.github.io/jurisprudencia/video/demo-60s.mp4"><img src="web/public/video/demo-60s.jpg" width="260" alt="Demonstração curta"></a><br><b><a href="https://carolinanunesmartins.github.io/jurisprudencia/video/demo-60s.mp4">Demonstração curta</a></b><br>41 s · um exemplo, o gráfico e o método</td>
    <td align="center"><a href="https://carolinanunesmartins.github.io/jurisprudencia/video/demo-3min.mp4"><img src="web/public/video/demo-3min.jpg" width="260" alt="Demonstração completa"></a><br><b><a href="https://carolinanunesmartins.github.io/jurisprudencia/video/demo-3min.mp4">Demonstração completa</a></b><br>3 min 33 s · todas as páginas, passo a passo</td>
  </tr>
</table>

Os vídeos são servidos pelo próprio sítio (GitHub Pages); os ficheiros estão em [`web/public/video/`](web/public/video/), com as legendas em `.srt`. O guião está em [`docs/guiao-video.md`](docs/guiao-video.md). A narração é uma voz sintetizada em português de Portugal (edge-tts, voz "Raquel"), não a voz do autor; as legendas estão na imagem. Foram gravados no sítio local, sem abrir o dgsi.pt.

> [!TIP]
> **Arquitetura em duas imagens:** [como o MVP foi construído e como deve continuar](docs/arquitetura.md). Recolha, classificação com a citação como prova, deteção, publicação; e a seguir: vários tribunais, texto integral, atualização automática e um produto para advogados.

## O que mostra

- **813 acórdãos** do STJ sobre contrato-promessa (2000–2025), em **7 perguntas**, com as posições ano a ano.
- **Divergências confirmadas**: *divisões* (as duas posições nos mesmos anos) e *mudanças* (uma posição substitui a outra), com os dois excertos lado a lado.
- **Uniformizações**: divergências reconhecidas pelo próprio STJ, só com citações.
- **Pesquisa** por relevância nas perguntas, nas citações e nas palavras dos sumários (os sumários não são publicados, só um índice de palavras: [ADR 0009](docs/adr/0009-search-word-index.md)).
- **Método e números medidos**, com as limitações.

Nenhuma citação inventada é publicada: cada excerto é texto do próprio acórdão, verificado palavra a palavra.

## O subconjunto escolhido

**Acórdãos do STJ sobre contrato-promessa, de 2000 a 2025: 813 acórdãos**, de um índice de 71 760 acórdãos do STJ no dgsi.pt ([ADR 0005](docs/adr/0005-subset.md)).

**Porquê contrato-promessa**
- **Há divergências conhecidas para confirmar:** existe um levantamento prévio de divergências neste tema, junto de profissionais. Dele saíram as perguntas-semente, o que permite ver se o sistema encontra o que os juristas já conhecem.
- **O próprio STJ uniformizou aqui:** a pesquisa no índice confirmou que é dos temas substantivos com mais acórdãos de uniformização de jurisprudência. É, portanto, um tema onde o Supremo reconheceu que decidia de formas diferentes.
- **O tamanho cabe num protótipo:** o objetivo era 600 a 1 500 acórdãos. 813 chega para ver tendências por ano (cerca de 25 a 30 acórdãos por ano) e custa pouco: cerca de 45 minutos de recolha e cerca de 4 USD de classificação.
- **Ficou sujeito a pontos de decisão, com alternativa:** uma prova inicial com as três perguntas-semente não encontrou posições opostas suficientes, mas a passagem de descoberta encontrou cerca de 5 perguntas com dois lados (*gate* G2). Depois da deteção, a regra era: pelo menos uma divergência confirmada numa pergunta de teste, ou mudar para arrendamento urbano. Houve confirmações, e o tema ficou (*gate* G3, 2026-10-15).

**Como se seleciona**
- **A regra:** um acórdão entra se tiver data entre 2000 e 2025 e pelo menos um **descritor** do dgsi.pt que nomeie um contrato-promessa (`CONTRATO-PROMESSA` e as suas grafias, ou um descritor que comece por `PROMESSA DE COMPRA`, `PROMESSA DE VENDA`, `PROMESSA UNILATERAL` ou `PROMESSA BILATERAL`).
- **Compara-se o descritor inteiro, não pedaços de palavra.** Procurar `PROMESSA` ou `TRADIÇÃO` dentro do texto apanharia `PROMESSA DE CASAMENTO` ou `EXTRADIÇÃO` (267 casos). As duas listas estão fixadas em testes.
- **Onde está:** `pipeline/juris/db/subset.py`. A recolha (`make fetch`) só descarrega estes acórdãos.
- **O que se lê de cada acórdão:** o sumário, ou o texto integral quando não há sumário ([ADR 0007](docs/adr/0007-classify-from-sumario.md)). 736 dos 813 têm os dois; os restantes têm só um deles ([ADR 0006](docs/adr/0006-summary-only-judgments.md)).

**O que fica de fora, e porquê**
- **2000 é uma escolha de âmbito, não dos dados.** Fica de fora o acórdão uniformizador de 1998 sobre a primeira pergunta-semente, e com ele o "antes" dessa mudança. Alargar a 1995–2025 daria 1 144 acórdãos; o responsável rejeitou-o (2026-10-14).
- **Ficam de fora os acórdãos sobre uma promessa que não têm esse descritor**, ou que não têm descritores.
- **Ficam de fora os descritores `SINAL`, `EXECUÇÃO ESPECÍFICA`, `TRADIÇÃO DA COISA` e `CLÁUSULA PENAL` sozinhos,** porque também aparecem fora da promessa. Juntar `SINAL` e `EXECUÇÃO ESPECÍFICA` só acrescentaria 34 acórdãos.
- **Só o STJ**, sem as Relações nem outros tribunais.

## Como funciona

1. **Subconjunto:** acórdãos do STJ com descritores de contrato-promessa ([ADR 0005](docs/adr/0005-subset.md)).
2. **Perguntas:** taxonomia aprovada por uma pessoa, com as posições escritas antes de classificar ([ADR 0002](docs/adr/0002-supervised-taxonomy.md)).
3. **Classificação:** um modelo pequeno lê o sumário e indica a posição e o excerto; o excerto só fica se estiver no texto ([ADR 0003](docs/adr/0003-quote-grounding.md)).
4. **Deteção:** regras fixas em janelas de 3 anos (`detect.toml`).
5. **Verificador** (*judge* no código): um segundo modelo vê só a pergunta e os dois excertos; só se mostram as divergências que confirma.

Requisitos e decisões: [SPEC.md](SPEC.md), [docs/adr/](docs/adr/). Plano: [ROADMAP.md](ROADMAP.md).

## Começar

Precisa de Python 3.12 com [uv](https://docs.astral.sh/uv/), Node.js 22 e GNU Make (em Windows: `winget install GnuWin32.Make`; não o pacote npm `make`).

```bash
make setup     # uv sync + npm ci
make verify    # lint, testes Python e do site, build (offline)
make web-dev   # o site com os dados do repositório
```

Reproduzir os dados do site sem crawl nem chave de API (o resultado é igual, byte a byte, ao publicado):

```bash
make snapshot-load   # base local a partir de data/classifications/
make detect          # divergências (mantém os veredictos do verificador)
make export          # web/public/data/*.json
make data-check      # esquemas, ligações e citações
```

## Comandos

| Comando | Quem | O que faz |
|---|---|---|
| `make setup` / `make verify` | qualquer | instalar / validar tudo |
| `make snapshot-load` / `make snapshot` | qualquer | carregar / gravar `data/classifications/` |
| `make detect` / `make export` / `make data-check` | qualquer | deteção, exportação e validação |
| `make classify-replay` / `make judge-replay` | qualquer | repetir classificação e verificação com respostas gravadas, sem custo |
| `make evaluate` | qualquer, com a base local | `data/eval/report.md` e `evaluation.json` |
| `make index` / `make fetch` | **só uma pessoa** | crawl do dgsi.pt; precisa de `JURIS_CONTACT` ([ADR 0004](docs/adr/0004-polite-crawl.md)) |
| `make classify` / `make judge` | **só uma pessoa** | chamadas reais ao modelo; precisa de `LLM_API_KEY` ([runbook](docs/llm-runbook.md)) |

Os agentes de IA nunca contactam o dgsi.pt nem veem a chave da API ([AGENTS.md](AGENTS.md)).

## Estrutura

```
pipeline/juris/   crawl, parse, db, llm, taxonomy, classify, detect, export, evaluate
pipeline/tests/   unit/, regression/ (golden/), fixtures/ (HTML guardado)
pipeline/tools/   scripts pontuais: spike, descoberta, folha de etiquetas, contagens
web/              site (Vite + React + TypeScript + Tailwind); lê web/public/data/
data/             taxonomy.json, classifications/, auj/, eval/  (raw/ e *.db ficam locais)
docs/             arquitetura.md, adr/ (decisões), llm-runbook.md
```

CI em cada *pull request* (`ci-ok` é o *check* obrigatório). O deploy para o GitHub Pages só publica dados que passam o `data-check` ([ADR 0001](docs/adr/0001-static-site-github-pages.md)).

## Dados e privacidade

Os acórdãos são públicos e parcialmente anonimizados. Nunca se comitam textos integrais, sumários nem a cache HTML: só metadados, posições, citações até 400 caracteres com ligação, e etiquetas de avaliação. Sem cookies nem *analytics*.

## Licença

Código: MIT ([LICENSE](LICENSE)). Dados derivados: licença a confirmar depois de verificar o aviso de reutilização do dgsi.pt; os acórdãos continuam a ser do dgsi.pt.
