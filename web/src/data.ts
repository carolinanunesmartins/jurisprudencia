// Types of web/public/data/*.json; mirror of pipeline/juris/export/model.py (validated by data-check).

export type Meta = {
  taxonomy_version: string;
  prompt_version: string;
  subset_size: number;
  classified: number;
  by_source: Record<string, number>;
  quotes_rejected: number;
  divergences_shown: number;
  divergences_hidden: number;
  divergences_unjudged: number;
};

export type Position = { id: string; label: string; definition: string };

export type Question = {
  id: string;
  title: string;
  description: string;
  split: "dev" | "test";
  positions: Position[];
  counts: Record<string, number>;
  first_year: number | null;
  last_year: number | null;
};

export type Judgment = {
  doc_id: string;
  processo: string;
  date: string;
  url: string;
  secao: string;
  relator: string;
  question_id: string;
  position: string;
  quote: string;
  text_source: "sumario" | "texto";
  uniformizacao: boolean;
};

export type PairItem = {
  doc_id: string;
  processo: string;
  date: string;
  url: string;
  position: string;
  quote: string;
};

export type Divergence = {
  id: string;
  question_id: string;
  type: "split" | "shift" | "resolved";
  window_start: number;
  window_end: number;
  display: "mudanca" | "possivel_alteracao_legislativa" | "uniformizada";
  rule_confidence: "alta" | "media" | "baixa" | null;
  support: Record<string, number>;
  pair: PairItem[];
  judge: {
    real_opposition: boolean;
    legislative_change_possible: boolean;
    rationale: string;
    confidence: string;
  } | null;
};

export type Data = {
  meta: Meta;
  questions: Question[];
  judgments: Judgment[];
  divergences: Divergence[];
};

async function getJson<T>(name: string): Promise<T> {
  // relative to the page: works with base "./", HashRouter and CSP connect-src 'self'
  const res = await fetch(`./data/${name}`);
  if (!res.ok) throw new Error(`${name}: HTTP ${res.status}`);
  return (await res.json()) as T;
}

export async function loadData(): Promise<Data> {
  const [meta, questions, judgments, divergences] = await Promise.all([
    getJson<Meta>("meta.json"),
    getJson<Question[]>("questions.json"),
    getJson<Judgment[]>("judgments.json"),
    getJson<Divergence[]>("divergences.json"),
  ]);
  return { meta, questions, judgments, divergences };
}
