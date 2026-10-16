# Uso de IA

Resumo do [AI_LOG.md](AI_LOG.md), onde cada alteração feita com IA tem uma entrada (ferramenta, tarefa, o que falhou, como se corrigiu, o que uma pessoa verificou).

## Ferramentas

| Papel | Ferramenta / modelo |
|---|---|
| Desenvolvimento (código, testes, documentação, análise) | Claude Code (Claude Sonnet 5.5 e, depois, Claude Opus 5.5) |
| Classificação dos 813 acórdãos | Claude Haiku 4.5 (API), corrida pelo responsável |
| Verificador das divergências (*judge* no código) | Claude Sonnet 5.5 (API), corrido pelo responsável |
| Prova de viabilidade e descoberta de perguntas | um modelo numa conversa, com pacotes preparados pelo agente, corrida pelo responsável |
| Etiquetas de 4 divergências ocultas | GitHub Copilot |
| Teste de usabilidade do sítio | um subagente do Claude Code que só usa o navegador, como visitante novo (duas rondas) |
| Revisão de segurança | `/security-review` do Claude Code, sobre o repositório inteiro |
| Pesquisa no sítio | uma equipa de agentes do Claude Code: um para o pipeline, um para o sítio, um de verificação e um revisor de código |
| Vídeos (demonstração e anúncio) | Claude Code a conduzir o sítio local com Playwright (Chromium), narração sintetizada com edge-tts (voz pt-PT "Raquel"), montagem e legendas com ffmpeg |
| Verificação dos entregáveis | dois agentes do Claude Code: um confirmou o sítio publicado e o repositório público, outro leu README, NOTA e IA contra o enunciado |

## Como se trabalhou

- **Regras escritas antes do código:** `AGENTS.md` (regras rígidas), `SPEC.md` (requisitos) e `ROADMAP.md` (marcos com critérios de aceitação). O agente seguiu os marcos por ordem e registou cada passo no AI_LOG.
- **Separação humano / agente:** o agente nunca contactou o dgsi.pt nem viu a chave da API. O crawl, as chamadas ao modelo e as decisões (tema, perguntas, limites, cortes) foram do responsável; o agente preparou os comandos, os limites de custo e o *runbook*, e leu os resultados.
- **Saída do modelo tratada como não fiável:** validação por esquema (pydantic) e, sobretudo, a regra da citação: o excerto publicado tem de ser texto do próprio acórdão, verificado; o modelo nunca escreve o que é mostrado.
- **Nada afinado depois de ver resultados:** limiares, divisão dev/teste, alocação das etiquetas, regra de escolha de excertos v2 e base de palavras-chave foram fixados e comprometidos antes de serem corridos; quando uma regra mudou depois de ver dados, foi registada como tal e os resultados antigos ficaram no relatório.
- **Reprodutibilidade:** respostas gravadas (*replay*) permitem repetir classificação, verificação e avaliação sem custo; um instantâneo comprometido reproduz o sítio byte a byte.

## O que funcionou

- **Verificação das citações:** 0 citações inventadas publicadas. A primeira regra (substring exata) rejeitava 17 % por diferenças triviais; reparações nomeadas (aspas, números de parágrafo, hifenização do texto-fonte, reticências) reduziram para 11 rejeitadas em 695, sempre guardando o texto do acórdão e não o do modelo.
- **Testes como rede:** 201 testes Python e 93 do sítio; vários erros reais foram apanhados por testes (URL canónico que estragava `?OpenDocument`, chave primária repetida no índice, veredictos do verificador perdidos ao reconstruir a partir do instantâneo).
- **Custo controlado:** limite de tokens por resposta, sem repetição de respostas cortadas, orçamento por corrida; ≈ 4 USD para 813 acórdãos.
- **Verificar o objetivo como um visitante:** um agente que só via o sítio confirmou as 5 partes do objetivo (por tema, divergências, quando, onde, mudança na mesma questão); a primeira versão exigia 3 cliques para ver uma mudança e passou a 1. Depois, menos texto no ecrã (por exemplo 792 → 223 palavras visíveis na pergunta q8) sem perder nenhum aviso.
- **Segunda ronda com o visitante:** percebeu os termos sozinho, mas não distinguia perguntas de divergências; daí o guia "Como ler" na página inicial, a explicação de porque uma pergunta não tem divergência confirmada, o sentido de cada uniformização, o período "Mais tarde" nas mudanças e um só termo ("verificador") no sítio.
- **Vídeos a partir do guião:** um script percorre o sítio cena a cena segundo `docs/guiao-video.md`, com a duração de cada cena acertada pela narração; o dgsi.pt fica bloqueado durante a gravação.
- **Encontrar evidência independente do modelo:** os acórdãos de uniformização mostram divergências reconhecidas pelo próprio STJ, com citações literais verificadas.

## O que falhou ou precisou de correção

- **Erros do agente:** afirmou que não havia *workflow* de deploy (tinha procurado só num ficheiro); escreveu uma razão inventada para a rejeição de uma pergunta no quadro do levantamento (corrigida para a razão registada); deu uma instrução ambígua ("linhas 2, 12…") que levou a etiquetas na linha errada; contagens de descritores por substring inflacionadas; várias vezes, comandos gerados com `\n` mal escapado partiram ficheiros (apanhados pelo *lint*).
- **Pressupostos errados no SPEC:** `processo` não é único (mudou para `doc_id`); tamanho de página e paginação do dgsi.pt; o modelo verificador rejeita o parâmetro `temperature`; uma gralha no dgsi.pt ("JURSIPRUDÊNCIA") escondia um acórdão de uniformização.
- **Verificador e escolha dos excertos:** com a primeira regra, 20 de 23 divergências ficavam ocultas, quase sempre porque um dos excertos não tomava posição; a regra v2 (pré-registada) passou a 4 confirmadas, e uma delas parece assentar em fundamentos diferentes.
- **Vídeos:** a captura do navegador ignorava a escala do ecrã (imagens pequenas); os cartões do anúncio usavam classes que o CSS do sítio não tem; a pesquisa juntou o número do processo à palavra anterior; as legendas mostravam duas linhas ao mesmo tempo. Tudo corrigido e revisto imagem a imagem antes de publicar.
- **Rótulos sem pessoa:** o responsável não tinha tempo nem formação jurídica; as 60 etiquetas de posição e as etiquetas das divergências foram feitas por IA (divulgado em `data/eval/labeller.md`, no relatório e no sítio). Classificador, verificador e etiquetador são em parte da mesma família de modelos, pelo que a concordância pode estar inflacionada.

## O que uma pessoa verificou

- Correu o crawl, a classificação e o verificador, e leu os resultados impressos.
- Escolheu o tema, aprovou as 7 perguntas, decidiu os cortes e as exceções (etiquetas por IA).
- Fez o *merge* e confirmou o deploy; o agente verificou o sítio publicado.
- **Não verificado por uma pessoa:** as posições atribuídas, as divergências confirmadas e os excertos dos acórdãos de uniformização. Nenhum jurista reviu o trabalho.
- **Narração dos vídeos:** é uma voz sintetizada, não a do responsável; foi uma decisão do responsável.
