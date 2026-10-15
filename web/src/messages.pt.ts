// All user-facing strings live here (AGENTS.md rule 10).
export const messages = {
  appTitle: "Jurisprudência",
  tagline: "Onde e quando a jurisprudência do STJ divergiu.",
  disclaimer: "Sinal para revisão, não é parecer jurídico.",
  nav: { home: "Início", questions: "Perguntas", aujs: "Divergências reconhecidas pelo STJ" },
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
