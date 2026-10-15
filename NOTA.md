# Nota

**Objetivo.** Agrupar acórdãos do STJ por questão jurídica e mostrar onde e quando a jurisprudência divergiu, com cada afirmação apoiada numa citação literal e numa ligação ao dgsi.pt. Sítio: https://carolinanunesmartins.github.io/jurisprudencia/

**Subconjunto e critério.** Do índice completo do STJ no dgsi.pt (71 760 acórdãos), os que têm um descritor de contrato-promessa (descritor inteiro, não substring), de 2000 a 2025: **813 acórdãos** (ADR 0005). Contrato-promessa foi escolhido por existir um levantamento prévio de divergências conhecidas; mais tarde, a pesquisa no índice confirmou que é dos temas substantivos com mais atividade de uniformização no STJ. 736 têm sumário e texto integral; os restantes têm só um deles no próprio dgsi.pt (ADR 0006). O crawl é feito por uma pessoa, com uma ligação, pausa ≥ 2,5 s e cache.

**Agrupamento.** Taxonomia supervisionada em vez de *clustering*: 5 perguntas-semente do levantamento e uma passagem de descoberta com um modelo sobre 150 acórdãos propuseram questões; o responsável aprovou 7, cada uma com 2 posições escritas antes de classificar (taxonomia `v1` congelada). Um modelo pequeno (Claude Haiku) lê o **sumário** de cada acórdão (texto integral só quando não há sumário, ADR 0007) e indica, por pergunta, a posição e o excerto que a sustenta. O excerto mostrado é sempre o texto do próprio sumário, localizado e verificado; se não for encontrado, a resposta é descartada (11 de 695).

**Deteção de divergências.** Regras determinísticas em janelas de 3 anos (`detect.toml`): **divisão** quando as duas posições têm ≥ 2 acórdãos na mesma janela; **mudança** quando a posição dominante (≥ 60 %) passa a ser outra numa janela posterior. Um segundo modelo (Claude Sonnet), o **juiz**, vê só a pergunta e os dois excertos, sem a posição atribuída, e diz se há oposição real; só as confirmadas aparecem. À parte, os **acórdãos de uniformização** do subconjunto mostram divergências reconhecidas pelo próprio STJ, só com citações literais. Limiares e regras foram fixados antes de ver resultados; a regra de escolha dos excertos v2 foi pré-registada antes de ser corrida.

**Resultados.** 23 divergências detetadas, 4 confirmadas (todas em perguntas de teste), mais 3 reconhecidas pelo STJ. Na amostra de 60 acórdãos, o classificador acerta a posição em 20 de 21 casos em que o acórdão decide (base de palavras-chave: 4 de 21), mas atribui posição a acórdãos que só tocam a pergunta (20 de 28 posições corretas). Custo da classificação ≈ 4 USD (≈ 2,1 milhões de tokens). Relatório: `data/eval/report.md`.

**Limitações principais.**
- **Sem verificação humana especializada:** as 60 etiquetas de posição e as etiquetas das divergências foram feitas por modelos de IA (divulgado); o juiz é também um modelo. Nenhum jurista reviu os resultados.
- **O juiz é conservador e falível:** esconde divergências reais (pelo menos uma, segundo as etiquetas) e confirmou uma que parece assentar em fundamentos diferentes (q9).
- **Só o sumário** é lido: o que o sumário omite não é visto.
- **Cobertura:** um tema, só o STJ, só 2000–2025; poucos acórdãos por posição minoritária.
- Os excertos dos acórdãos de uniformização foram escolhidos por um agente de IA (verificáveis pelas ligações).
