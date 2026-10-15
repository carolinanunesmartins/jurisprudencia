// All user-facing strings live here (AGENTS.md rule 10).
export const messages = {
  appTitle: "Jurisprudência",
  tagline: "Onde e quando a jurisprudência do STJ divergiu.",
  disclaimer: "Sinal para revisão, não é parecer jurídico.",
  nav: {
    home: "Início",
    questions: "Perguntas",
    aujs: "Divergências reconhecidas pelo STJ",
    method: "Método e avaliação",
  },
  method_page: {
    heading: "Método e avaliação",
    stepsHeading: "Como funciona",
    steps: [
      "Subconjunto: os acórdãos do STJ sobre contrato-promessa publicados no dgsi.pt, escolhidos pelos descritores, de 2000 a 2025.",
      "Perguntas: sete questões jurídicas, cada uma com duas posições definidas por escrito antes de qualquer classificação.",
      "Classificação: um modelo de linguagem lê o sumário de cada acórdão e indica, para cada pergunta, a posição tomada e o excerto que a sustenta. O excerto mostrado é sempre texto do próprio sumário, verificado palavra a palavra; se não for encontrado, a resposta é descartada.",
      "Deteção: em janelas de 3 anos procuram-se divisões (as duas posições com pelo menos 2 acórdãos) e mudanças (a posição dominante passa a ser outra).",
      "Juiz: um segundo modelo lê só a pergunta e os dois excertos, sem saber o que o classificador decidiu, e diz se há oposição real. Só as divergências confirmadas aparecem no sítio.",
      "Uniformizações: os acórdãos de uniformização são divergências reconhecidas pelo próprio STJ e mostram-se com citações literais, sem depender do modelo.",
    ],
    numbersHeading: "Resultados medidos",
    grounding: (p: number, a: number, r: number) =>
      `Citações: ${p} respostas com posição; ${a} aceites, ${r} rejeitadas por não estarem no texto. Nenhuma citação inventada é mostrada.`,
    accuracyHeading: "Exatidão da posição (amostra de 60 acórdãos)",
    accuracyNote:
      "Comparação com etiquetas feitas por um modelo de IA, sem revisão humana: a concordância pode estar inflacionada. A «base» é uma regra simples de palavras-chave, fixada antes de ser medida.",
    cols: {
      set: "Conjunto",
      system: "Sistema",
      exact: "Concordância",
      recall: "Posição da etiqueta encontrada",
      precision: "Posição dada correta",
    },
    set: { test: "teste", dev: "afinação" },
    system: { model: "modelo", baseline: "base" },
    divergences: (j: number, v1: number, v2: number, t: number) =>
      `Divergências: ${j} detetadas e avaliadas pelo juiz; ${v2} confirmadas e mostradas (${t} em perguntas de teste). Com a primeira regra de escolha dos excertos eram ${v1}.`,
    labels: (correct: number, total: number) =>
      `Revisão humana (sem formação jurídica) das divergências mostradas: ${correct} de ${total} consideradas corretas.`,
    noLabels: "As divergências mostradas ainda não foram revistas por uma pessoa.",
    aujs: (n: number) => `${n} divergências reconhecidas pelo próprio STJ (acórdãos de uniformização).`,
    cost: (tokens: string, usd: string) =>
      `Custo da classificação: ${tokens} tokens, cerca de ${usd} USD (estimativa a preços de tabela).`,
    surveyHeading: "Comparação com um levantamento prévio da jurisprudência",
    limitsHeading: "Limitações",
    limits: [
      "As etiquetas de avaliação foram feitas por IA, da mesma família do classificador.",
      "As divergências são confirmadas por um modelo (o juiz), não por um jurista.",
      "A classificação usa o sumário: o que o sumário omite não é visto.",
      "O classificador por vezes atribui posição a acórdãos que só tocam a pergunta; o juiz filtra esses casos, ocultando também algumas divergências reais.",
      "Só acórdãos de 2000 a 2025 com os descritores escolhidos.",
    ],
    report: "Relatório completo de avaliação (GitHub)",
    reportUrl: "https://github.com/carolinanunesmartins/jurisprudencia/blob/main/data/eval/report.md",
    unavailable: "A avaliação ainda não foi publicada.",
  },
  auj: {
    heading: "Divergências reconhecidas pelo próprio STJ",
    intro:
      "Um acórdão de uniformização de jurisprudência só existe quando o Supremo reconhece que acórdãos seus decidiram a mesma questão de forma oposta. Abaixo, cada um com a questão, os dois lados e a decisão final. Todos os textos são citações literais, com ligação ao original; nada aqui é resumo nosso.",
    title: (date: string, processo: string) => `Acórdão de uniformização de ${date} (proc. ${processo})`,
    question: "Questão, nas palavras do acórdão",
    conflict: "A divergência, nas palavras do acórdão",
    side: (n: number) => `Lado ${n}, nas palavras do acórdão de uniformização`,
    named: "Acórdãos deste lado citados pelo acórdão (excerto do sumário)",
    noneNamed: "Este lado é atribuído a acórdãos das Relações, sem acórdão do STJ citado.",
    ruling: "Jurisprudência uniformizada",
    open: "Abrir o acórdão de uniformização no dgsi.pt",
    related: "Divergências reconhecidas pelo STJ sobre este tema",
    count: (n: number) => `${n} acórdãos de uniformização no subconjunto.`,
  },
  loading: "A carregar…",
  loadError: "Não foi possível carregar os dados.",
  noData: "Sem dados ainda: a classificação dos acórdãos ainda não foi publicada.",
  notFound: "Pergunta não encontrada.",
  summary: (subset: number, classified: number) =>
    `${subset} acórdãos do STJ sobre contrato-promessa (2000–2025); ${classified} classificados.`,
  method:
    "Cada acórdão é lido a partir do sumário por um modelo de linguagem, que indica a posição " +
    "tomada em cada pergunta e cita o excerto que a sustenta. Só se mostram citações verificadas " +
    "palavra a palavra no texto publicado.",
  questionsHeading: "Perguntas",
  judgmentsCount: (n: number) => (n === 1 ? "1 acórdão com posição" : `${n} acórdãos com posição`),
  years: (a: number, b: number) => (a === b ? `${a}` : `${a}–${b}`),
  divergencesCount: (n: number) => (n === 1 ? "1 divergência" : `${n} divergências`),
  back: "← Todas as perguntas",
  positionsHeading: "Posições",
  timelineHeading: "Linha do tempo",
  timelineLabel: (title: string) => `Linha do tempo das posições: ${title}`,
  tableHeading: "Acórdãos",
  table: {
    date: "Data",
    processo: "Processo",
    position: "Posição",
    quote: "Citação",
    link: "Original",
    open: "Abrir no dgsi.pt",
  },
  onlySummary: "a partir do sumário",
  fromText: "a partir do texto integral",
  uniformizacao: "uniformização",
  divergencesHeading: "Divergências",
  display: {
    mudanca: "Mudança de entendimento",
    possivel_alteracao_legislativa: "Possível efeito de alteração legislativa",
    // a fact, not a claim that the divergence ended (SPEC §6.2: an AUJ in or after the period)
    uniformizada: "Acórdão de uniformização no período",
  },
  type: { split: "divisão", shift: "mudança", resolved: "uniformização" },
  confidence: { alta: "confiança da regra: alta", media: "confiança da regra: média", baixa: "confiança da regra: baixa" },
  noDivergences: "Nenhuma divergência confirmada nesta pergunta.",
  divergence: {
    detail: "Ver em detalhe e como foi detetada",
    notFound: "Divergência não encontrada.",
    backTo: (title: string) => `← ${title}`,
    how: "Como foi detetada",
    window: (a: number, b: number) => `Janela de anos analisada: ${a}–${b}.`,
    support: "Acórdãos com posição nesta janela:",
    rule: {
      split:
        "Divisão: numa mesma janela de 3 anos há pelo menos 2 acórdãos de cada posição. Mostram-se os dois acórdãos de posições opostas mais próximos no tempo, com citações completas.",
      shift:
        "Mudança: a posição dominante numa janela de 3 anos (pelo menos 60 % e 2 acórdãos) passa a ser outra numa janela posterior. Mostram-se o último acórdão da posição antiga e o primeiro da nova.",
      resolved:
        "Acórdão de uniformização com posição nesta pergunta, datado dentro ou depois do período da divergência. Não quer dizer que a divergência tenha terminado: ver as datas.",
    },
    judge: (confidence: string) =>
      `Um segundo modelo (o juiz) leu apenas a pergunta, as posições e os dois excertos, sem saber que posição o classificador atribuiu, e concluiu que há oposição real (confiança do juiz: ${confidence}).`,
    rationale: "Justificação do juiz (texto gerado por um modelo, não verificado):",
    ruleConfidence:
      "Confiança da regra: alta quando o juiz confirma e a posição com menos acórdãos tem pelo menos 3; média com pelo menos 2; baixa nos restantes casos.",
    judgeConfidence: { alta: "alta", media: "média", baixa: "baixa" },
  },
  splitTag: { dev: "conjunto de afinação", test: "conjunto de teste" },
} as const;
