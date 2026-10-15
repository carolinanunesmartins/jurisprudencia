// All user-facing strings live here (AGENTS.md rule 10).
export const messages = {
  appTitle: "Jurisprudência",
  tagline: "Onde e quando a jurisprudência do STJ divergiu.",
  disclaimer: "Sinal para revisão, não é parecer jurídico.",
  nav: { home: "Início", questions: "Perguntas" },
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
  splitTag: { dev: "conjunto de afinação", test: "conjunto de teste" },
} as const;
