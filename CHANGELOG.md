# Histórico de alterações

Alterações relevantes, das mais recentes para as mais antigas. As mensagens de commit seguem o formato Conventional Commits; o pormenor de cada passo está no [AI_LOG.md](AI_LOG.md) (em inglês) e o resumo em [IA.md](IA.md).

## Por publicar
- feat(web): "Como ler" na página inicial explica pergunta, posições, divergência e uniformização, com exemplos; as perguntas sem divergência dizem-no; cada página diz se é uma pergunta ou uma divergência
- docs: `docs/guiao-video.md`, guião do vídeo de demonstração
- feat(web): os pontos do gráfico "Ano a ano" abrem uma caixa com a data, a posição e a ligação ao acórdão no dgsi.pt
- feat(web): botão para alternar entre modo claro e escuro; segue o sistema até o leitor escolher e guarda a escolha
- feat(search): pesquisa por relevância (BM25) nas perguntas, nas citações e num índice de palavras dos sumários, sem publicar o texto (ADR 0009); caixa grande na página inicial com exemplos, entrada no cabeçalho e em `/pesquisa`
- docs: documentos para leitura em português (ADRs, guia dos passos com o modelo, este histórico)
- docs: `docs/arquitetura.md`, a arquitetura do MVP e da sua continuação (diagramas Mermaid, quatro fases), em destaque no README
- chore: arrumação do repositório; ADRs 0001–0004 (exigidos pelo SPEC §11, registados retroativamente); README e AI_LOG mais curtos; `DgsiLink` só cria ligações para o dgsi.pt (reforço de segurança)
- feat(web): leitura mínima (destaque pela cor de cada posição, etiquetas, pormenores a um clique); objetivo verificável em 0–1 cliques; carregamento mais rápido e SEO (M9)
- feat(web): identidade visual "duas vozes", gráfico anual espelhado, tipos de letra próprios (ADR 0008) (M9)
- fix(web): `/metodo` usa a aritmética do relatório na revisão das divergências
- docs: README, NOTA.md e IA.md para a entrega (M8)
- feat(web): `/divergencias/:id`, `/metodo` a partir de `evaluation.json`, favicon, revisão de acessibilidade (M6)
- feat(evaluate): relatório `make evaluate` com base de palavras-chave pré-registada, divergências v1/v2 e comparação com o levantamento; etiquetas das divergências feitas por IA, divulgado (M7)
- feat(auj): divergências reconhecidas pelo próprio STJ (`/uniformizacoes`), todos os textos citações verificadas
- feat(detect): regra de escolha dos excertos v2 (pré-registada); a marca de uniformização resiste à gralha do dgsi.pt; os veredictos mantêm-se ao repetir a deteção
- feat(data): instantâneo comitado em `data/classifications/`; um clone novo reproduz os dados do sítio (T5.3)
- feat(classify): a verificação localiza as citações com reparações nomeadas e guarda o excerto do próprio texto; `--reground`; proteções de custo
- feat: classificação dos 813 acórdãos, deteção, juiz, Gate G3 = manter o contrato-promessa (M4, M5)
- feat: taxonomia v1 (7 perguntas), folha de etiquetas às cegas, kits de descoberta e de *spike* (M1.5, M3)
- feat(crawl): crawler educado do índice e dos documentos, leitores HTML, subconjunto de 813 (M1, M2)
- chore: estrutura inicial (pipeline, sítio, testes, CI, publicação no Pages) (M0)
