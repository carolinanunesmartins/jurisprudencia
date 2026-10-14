# Jurisprudência

Protótipo que agrega acórdãos do Supremo Tribunal de Justiça (STJ), publicados em [dgsi.pt](https://www.dgsi.pt), por **questão jurídica** e mostra **onde e quando a jurisprudência divergiu ou mudou**. Cada sinal apresentado traz uma citação literal do acórdão e a ligação ao original.

> **Aviso:** sinal para revisão, não é parecer jurídico.

Estado: em construção (marco M0, ver [ROADMAP.md](ROADMAP.md)). O site em produção estará em `https://carolinanunesmartins.github.io/jurisprudencia/` depois de ativar o GitHub Pages.

## O que faz

1. Seleciona um subconjunto de acórdãos do STJ (tema inicial: *contrato-promessa*, 2000–2025).
2. Classifica cada acórdão, com um modelo de linguagem, segundo uma taxonomia de questões e posições curada por humanos.
3. Deteta divisões, mudanças de entendimento e uniformizações com regras determinísticas e configuráveis.
4. Só mostra uma citação se for uma subcadeia literal do texto guardado (*quote grounding*). Citações inventadas aceites: 0.

Detalhes, requisitos e decisões: [SPEC.md](SPEC.md). Plano: [ROADMAP.md](ROADMAP.md).

## Requisitos

| Ferramenta | Versão | Nota |
|---|---|---|
| Python | 3.12 | gerido pelo `uv` (`.python-version`) |
| [uv](https://docs.astral.sh/uv/) | recente | dependências Python |
| Node.js | 22 | site em `web/` |
| GNU Make | 4+ | em Windows, instalar GNU Make (ex.: `winget install GnuWin32.Make` ou `scoop install make`). **Não** o pacote npm `make`. |

## Começar (sem fazer crawl)

```bash
make setup     # uv sync + npm ci
make verify    # ruff + testes unitários e de regressão + typecheck/lint/test/build do site
make web-dev   # servidor de desenvolvimento do site
```

Sem `make`, os comandos equivalentes estão no [Makefile](Makefile).

## Comandos

| Comando | Quem corre | O que faz |
|---|---|---|
| `make setup` / `make verify` | qualquer | instalar / validar tudo (offline) |
| `make test-unit` / `make test-regression` | qualquer | testes isolados / ficheiros de referência (*golden*) |
| `make detect` / `make export` / `make data-check` | qualquer | deteção, exportação e validação dos dados do site |
| `make classify-replay` | qualquer | classificação offline com respostas gravadas |
| `make index` / `make fetch` | **humano** | crawl do dgsi.pt (ver política abaixo) |
| `make classify` | **humano** | chamadas reais ao LLM (precisa de `LLM_API_KEY`) |

`make index` está implementado (M1); `make fetch` e `make classify` ainda não (M2 e M4).

### Correr `make index` (humano, à noite)

```powershell
$env:JURIS_CONTACT = "o.teu@email"      # vai no User-Agent
make index                              # ≈ 740 pedidos, ≈ 40 min
make index ARGS="--max-pages 3"         # teste curto primeiro (recomendado)
```

Cria `data/juris.db` e a cache `data/raw/` (ambos ignorados pelo git). Se parar (limite de pedidos, 429/503, 3 erros seguidos), basta voltar a correr: as páginas já guardadas não geram pedidos.

## Estrutura

```
pipeline/juris/      crawl, parse, db, llm, taxonomy, classify, detect, export, evaluate
pipeline/tests/      unit/, regression/ (golden/), fixtures/
web/                 Vite + React + TypeScript + Tailwind; lê web/public/data/*.json
data/                taxonomy.json, eval/ (comprometidos); raw/ e *.db (ignorados)
docs/                adr/ (decisões), method.md
```

## Testes e CI

- **Unitários**: lógica isolada (`pipeline/tests/unit`, `web/src/__tests__`).
- **Regressão**: comportamento já verificado, fixado em ficheiros de referência (`pipeline/tests/regression/golden`, `web/tests/regression`). Cada bug corrigido acrescenta um caso.
- **CI** (`.github/workflows/ci.yml`): corre em cada *pull request*, na *merge queue* e em `main`. O *check* `ci-ok` é o que deve ser obrigatório na proteção do ramo.
- **Deploy** (`deploy.yml`): publica o site no GitHub Pages após *merge* em `main`. Passo único: *Settings → Pages → Source = GitHub Actions*.

## Política de crawl (resumo)

Uma ligação, um pedido de cada vez, pausa ≥ 2,5 s, cache em disco, paragem no primeiro 429/503. O crawl é sempre feito por uma pessoa; os agentes trabalham só com *fixtures* HTML. Regras completas em [SPEC.md §3](SPEC.md).

## Dados e privacidade

Os acórdãos são públicos e parcialmente anonimizados. Nunca se comitam textos integrais nem a cache HTML; só metadados, etiquetas do modelo e citações ≤ 400 caracteres com ligação. Sem cookies nem *analytics*.

## Uso de IA

Registado em [AI_LOG.md](AI_LOG.md), que alimenta o `IA.md` final. Todas as alterações assistidas por IA acrescentam uma entrada.

## Contribuir

Ramo `m<N>-<slug>`, *Conventional Commits*, um PR por marco. Regras para agentes e pessoas em [AGENTS.md](AGENTS.md).

## Licença

Código: MIT ([LICENSE](LICENSE)). Licença dos dados derivados: a confirmar após verificar o aviso de reutilização do dgsi.pt.
