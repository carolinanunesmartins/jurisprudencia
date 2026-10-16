import { readFileSync } from "node:fs";
import type { Judgment, Question, SearchFile } from "../data";
import { createIndex, highlight, normalise, parseQuery, validSearchFile } from "../search";

// vitest runs from web/
const read = (path: string) => readFileSync(`../${path}`, "utf8");
const golden = JSON.parse(read("pipeline/tests/regression/golden/search_normalise.json")) as {
  cases: { input: string; tokens: string[] }[];
};
const stopwords = new Set(
  read("pipeline/juris/search/stopwords.txt")
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter((l) => l && !l.startsWith("#")),
);

describe("normalise (golden file shared with pytest)", () => {
  it.each(golden.cases.map((c) => [c.input, c.tokens] as const))("%j", (input, tokens) => {
    expect(normalise(input, stopwords)).toEqual(tokens);
  });
});

const q = (id: string, title: string, description: string): Question => ({
  id,
  title,
  description,
  split: "dev",
  positions: [
    { id: "a", label: "Alfa", definition: "def" },
    { id: "b", label: "Beta", definition: "def" },
  ],
  counts: {},
  first_year: null,
  last_year: null,
});

const j = (doc_id: string, question_id: string, quote: string, date = "2010-01-01", processo = doc_id): Judgment => ({
  doc_id,
  processo,
  date,
  url: `https://www.dgsi.pt/${doc_id}`,
  secao: "",
  relator: "",
  question_id,
  position: "a",
  quote,
  text_source: "sumario",
  uniformizacao: false,
});

const questions = [q("qa", "Sinal", "x"), q("qb", "Mora", "Discute o sinal")];
const judgments = [
  j("j1", "qb", "Pagou o sinal", "2010-01-01"),
  j("j2", "qb", "Nada relevante aqui", "2011-01-01"),
  j("j3", "qb", "Outra coisa", "2012-01-01"),
  j("j4", "qa", "Sinal sinal sinal", "2013-01-01"),
  j("j5", "qa", "O possuidor", "2014-01-01", "123/45.6T8LSB.S1"),
  j("j6", "qa", "123 45 coisa", "2014-06-01"),
  j("p1", "qa", "outro", "2009-01-01", "882/14.9TJVNF-G.G1.G1.S1"),
  j("p2", "qa", "G1 e 882 coisa", "2009-06-01"),
  j("t1", "qa", "empate", "2015-01-01"),
  j("t2", "qa", "empate", "2016-01-01"),
  j("t3", "qa", "empate", "2016-01-01"),
];
// the sumário of j2 says "sinal" and "mora"; nothing else is indexed
const summary: SearchFile = {
  version: 2,
  stopwords: ["de", "que", "do"],
  docs: ["j1", "j2", "j3", "j4", "j5", "j6", "p1", "p2", "t1", "t2", "t3"],
  lengths: [3, 4, 3, 3, 3, 3, 1, 3, 1, 1, 1],
  terms: Object.fromEntries([
    ["sinal", [[1, 1]]],
    ["mora", [[1, 1]]],
    ["constructor", [[2, 1]]],
  ] satisfies [string, [number, number][]][]),
};
const index = createIndex({ questions, judgments }, summary);
const ids = (query: string) => index.search(query).judgments.map((h) => h.judgment.doc_id);

describe("search ranking", () => {
  it("ranks the title match above the description match, in questions", () => {
    expect(index.search("sinal").questions.map((h) => h.question.id)).toEqual(["qa", "qb"]);
  });

  it("ranks quote above sumário-only above question-only", () => {
    const order = ids("sinal");
    expect(order.indexOf("j4")).toBeLessThan(order.indexOf("j2"));
    expect(order.indexOf("j1")).toBeLessThan(order.indexOf("j2"));
    expect(order.indexOf("j2")).toBeLessThan(order.indexOf("j3"));
  });

  it("says where each word matched", () => {
    const hits = new Map(index.search("sinal").judgments.map((h) => [h.judgment.doc_id, h.where]));
    expect(hits.get("j1")).toEqual(["quote", "question"]);
    expect(hits.get("j2")).toEqual(["summary", "question"]);
    expect(hits.get("j3")).toEqual(["question"]);
  });

  it("puts rows matching every word above rows matching some, whatever the score", () => {
    const order = ids("sinal mora");
    // j4 matches only "sinal" (strongly); j1 matches both (sinal in the quote, mora in its question)
    expect(order.indexOf("j1")).toBeLessThan(order.indexOf("j4"));
  });

  it("matches the last word as a prefix while typing, not once it is finished", () => {
    expect(ids("possu")).toContain("j5");
    expect(ids("possu ")).not.toContain("j5");
    expect(ids("po")).toEqual([]);
  });

  it("ignores accents, case and stopwords in the query", () => {
    expect(ids("O SÍNAL de")).toEqual(ids("sinal"));
    expect(index.search("de que").judgments).toEqual([]);
  });

  it("puts an exact processo first", () => {
    expect(ids("123/45.6T8LSB.S1")[0]).toBe("j5");
  });

  // regression: the query was deduplicated before the lookup, so a processo with a repeated token never matched
  it("matches a processo that repeats a token", () => {
    const hits = index.search("882/14.9TJVNF-G.G1.G1.S1").judgments;
    expect(hits[0]?.judgment.doc_id).toBe("p1");
    expect(hits[0]?.where).toContain("processo");
  });

  it("breaks ties by date (newest first), then doc_id", () => {
    expect(ids("empate")).toEqual(["t2", "t3", "t1"]);
    expect(ids("empate")).toEqual(ids("empate"));
  });

  it("does not trip over words that are Object properties", () => {
    expect(ids("constructor")).toEqual(["j3"]);
    expect(ids("toString")).toEqual([]);
  });

  it("still searches questions and quotes without search.json", () => {
    const bare = createIndex({ questions, judgments }, null);
    expect(bare.summaryAvailable).toBe(false);
    const order = bare.search("sinal").judgments.map((h) => h.judgment.doc_id);
    expect(order).toContain("j1");
    expect(bare.search("sinal").judgments.find((h) => h.judgment.doc_id === "j2")?.where).toEqual(["question"]);
  });
});

describe("highlight", () => {
  it("marks matching words, accent-blind, keeping the original text", () => {
    const segs = highlight("Execução específica do possuidor", parseQuery("execucao possu"));
    expect(segs.filter((s) => s.hit).map((s) => s.text)).toEqual(["Execução", "possuidor"]);
    expect(segs.map((s) => s.text).join("")).toBe("Execução específica do possuidor");
  });

  // regression: marks after the word were left outside the <mark>
  it("keeps the combining marks of a decomposed word inside the highlight", () => {
    const nfd = "fé publica";
    expect(highlight(nfd, parseQuery("fe publica"))[0]).toEqual({ text: "fé", hit: true });
  });

  it("marks nothing when there is no match", () => {
    expect(highlight("sem nada", parseQuery("xyz"))).toEqual([{ text: "sem nada", hit: false }]);
  });
});

describe("validSearchFile", () => {
  const ok = { version: 2, stopwords: ["de"], docs: ["a"], lengths: [1], terms: { x: [[0, 1]] } };
  it("accepts version 2 and rejects other versions and shapes", () => {
    expect(validSearchFile(ok)).not.toBeNull();
    expect(validSearchFile({ ...ok, version: 1 })).toBeNull();
    expect(validSearchFile({ ...ok, lengths: [] })).toBeNull();
    expect(validSearchFile({ ...ok, terms: { x: [[5, 1]] } })).toBeNull();
    expect(validSearchFile(null)).toBeNull();
  });
});
