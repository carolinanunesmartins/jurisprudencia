# Jurisprudência

Protótipo que agrega acórdãos do Supremo Tribunal de Justiça (STJ), publicados em [dgsi.pt](https://www.dgsi.pt), por **questão jurídica** e mostra **onde e quando a jurisprudência divergiu ou mudou**. Cada sinal apresentado traz uma citação literal do acórdão e a ligação ao original.

> **Aviso:** sinal para revisão, não é parecer jurídico.

**Sítio:** https://carolinanunesmartins.github.io/jurisprudencia/

Nota de uma página: [NOTA.md](NOTA.md) · Uso de IA: [IA.md](IA.md) · Avaliação: [data/eval/report.md](data/eval/report.md)

## O que mostra

- **813 acórdãos do STJ sobre contrato-promessa (2000–2025)**, classificados em 7 perguntas jurídicas, com linha do tempo das posições por pergunta (`/perguntas`).
- **Divergências confirmadas** (divisões e mudanças de entendimento), cada uma com os dois excertos lado a lado e a explicação de como foi detetada (`/divergencias/...`).
- **Divergências reconhecidas pelo próprio STJ**: os acórdãos de uniformização do subconjunto, só com citações literais (`/uniformizacoes`).
- **Método e resultados medidos**, incluindo limitações (`/metodo`).

Todas as citações publicadas são texto do próprio acórdão, verificado palavra a palavra; nenhuma citação inventada é mostrada.

## Como funciona (resumo)

1. **Subconjunto:** acórdãos do STJ escolhidos pelos descritores de contrato-promessa (ADR 0005).
2. **Perguntas:** taxonomia curada por uma pessoa, com posições definidas antes de classificar (`data/taxonomy.json`).
3. **Classificação:** um modelo pequeno (Claude Haiku) lê o sumário e dá, por pergunta, a posição e o excerto que a sustenta; o excerto só é aceite se estiver no texto.
4. **Deteção:** regras determinísticas em janelas de 3 anos (`detect.toml`).
5. **Juiz:** um segundo modelo (Claude Sonnet) vê só a pergunta e os dois excertos e diz se a oposição é real; só as confirmadas são mostradas.

Detalhes e decisões: [SPEC.md](SPEC.md), [docs/adr/](docs/adr/). Plano e estado: [ROADMAP.md](ROADMAP.md).

## Requisitos

| Ferramenta | Versão | Nota |
|---|---|---|
| Python | 3.12 | gerido pelo `uv` (`.python-version`) |
| [uv](https://docs.astral.sh/uv/) | recente | dependências Python |
| Node.js | 22 | site em `web/` |
| GNU Make | 4+ | em Windows: `winget install GnuWin32.Make` ou `scoop install make`. **Não** o pacote npm `make`. |

## Começar (sem crawl e sem chave de API)

```bash
make setup     # uv sync + npm ci
make verify    # ruff + testes Python + typecheck/lint/testes/build do site
make web-dev   # o site com os dados publicados no repositório
```

### Reproduzir os dados do site a partir do repositório

Os resultados da classificação estão comprometidos em `data/classifications/` (metadados, posições, citações ≤ 400 caracteres e veredictos do juiz; sem textos).

```bash
make snapshot-load   # cria data/juris.db a partir de data/classifications/
make detect          # recalcula as divergências (mantém os veredictos já dados)
make export          # escreve web/public/data/*.json
make data-check      # valida esquemas, ligações e citações
```

O `web/public/data/` resultante é igual, byte a byte, ao publicado.

## Reprodução completa (passos humanos)

Estes passos contactam o dgsi.pt ou a API do modelo e são sempre corridos por uma pessoa (AGENTS.md).

| Passo | Comando | Notas |
|---|---|---|
| Índice do STJ | `make index` | ≈ 740 pedidos, ≈ 40 min; precisa de `JURIS_CONTACT` (o teu email vai no User-Agent) |
| Acórdãos do subconjunto | `make fetch` | `ARGS="--pilot 100"` primeiro; retoma se parar |
| Classificação | `make classify` | precisa de `LLM_API_KEY` e `CLASSIFY_MODEL`; ver [docs/llm-runbook.md](docs/llm-runbook.md) (custo, limites, erros) |
| Deteção e juiz | `make detect` e `make judge` | o juiz precisa de `JUDGE_MODEL`; `make judge-replay` repete sem custo |
| Site | `make export` e `make data-check` | |
| Avaliação | `make evaluate` | escreve `data/eval/report.md` e `web/public/data/evaluation.json` |
| Instantâneo | `make snapshot` | atualiza `data/classifications/` para comprometer |

## Comandos

| Comando | Quem corre | O que faz |
|---|---|---|
| `make setup` / `make verify` | qualquer | instalar / validar tudo (offline) |
| `make test-unit` / `make test-regression` | qualquer | testes isolados / ficheiros de referência (*golden*) |
| `make snapshot-load` / `make snapshot` | qualquer | carregar / gravar o instantâneo dos resultados |
| `make detect` / `make export` / `make data-check` | qualquer | deteção, exportação e validação dos dados do site |
| `make classify-replay` / `make judge-replay` | qualquer | classificação e juiz offline, com respostas gravadas |
| `make evaluate` | qualquer (precisa da base local) | relatório de avaliação |
| `make index` / `make fetch` | **humano** | crawl do dgsi.pt |
| `make classify` / `make judge` | **humano** | chamadas reais ao modelo (com chave de API) |

## Estrutura

```
pipeline/juris/      crawl, parse, db, llm, taxonomy, classify, detect, export, evaluate
pipeline/tests/      unit/, regression/ (golden/), fixtures/
web/                 Vite + React + TypeScript + Tailwind; lê web/public/data/*.json
data/                taxonomy.json, classifications/, auj/, eval/ (comprometidos); raw/ e *.db (ignorados)
docs/                adr/ (decisões), llm-runbook.md
```

## Testes e CI

- **Unitários** e **regressão** (`pipeline/tests`, `web/src/__tests__`, `web/tests/regression`); cada bug corrigido acrescenta um caso.
- **CI** (`.github/workflows/ci.yml`): em cada *pull request* e em `main`; o *check* `ci-ok` é o obrigatório.
- **Deploy** (`deploy.yml`): após *merge* em `main`, valida os dados (`data-check`), constrói e publica no GitHub Pages.

## Política de crawl (resumo)

Uma ligação, um pedido de cada vez, pausa ≥ 2,5 s, cache em disco, paragem no primeiro 429/503. Os agentes de IA nunca contactam o dgsi.pt. Regras completas em [SPEC.md §3](SPEC.md).

## Dados e privacidade

Os acórdãos são públicos e parcialmente anonimizados. Nunca se comitam textos integrais, sumários nem a cache HTML; só metadados, posições, citações ≤ 400 caracteres com ligação e etiquetas de avaliação. Sem cookies nem *analytics*.

## Uso de IA

Resumo em [IA.md](IA.md); registo completo, entrada a entrada, em [AI_LOG.md](AI_LOG.md).

## Licença

Código: MIT ([LICENSE](LICENSE)). Licença dos dados derivados: a confirmar após verificar o aviso de reutilização do dgsi.pt; os acórdãos continuam a ser do dgsi.pt.
