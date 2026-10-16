import { fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { App } from "../App";
import type { SearchFile } from "../data";
import { messages } from "../messages.pt";
import { fixture, searchFixture } from "./fixture";

function Where() {
  const l = useLocation();
  return <div data-testid="where">{l.pathname + l.search}</div>;
}

function at(path: string, search: () => Promise<SearchFile> = () => Promise.resolve(searchFixture)) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App load={() => Promise.resolve(fixture)} search={search} />
      <Where />
    </MemoryRouter>,
  );
}

describe("search page", () => {
  it("has an accessible search box on every page that goes to /pesquisa?q=", async () => {
    at("/metodo");
    const form = await screen.findByRole("search");
    const box = within(form).getByLabelText(messages.search.formLabel);
    fireEvent.change(box, { target: { value: "execução específica" } });
    fireEvent.submit(form);
    expect(screen.getByTestId("where")).toHaveTextContent(
      `/pesquisa?q=${encodeURIComponent("execução específica")}`,
    );
    // let the lazy index finish, so no update lands after the test
    await screen.findByText(messages.search.noResults("execução específica"));
  });

  it("fills the box from the URL, so a shared link shows its query", async () => {
    at("/pesquisa?q=prazo");
    expect(await screen.findByLabelText(messages.search.formLabel)).toHaveValue("prazo");
  });

  it("shows the help and three example links when the query is empty, without loading search.json", async () => {
    const search = vi.fn(() => Promise.resolve(searchFixture));
    at("/pesquisa", search);
    await screen.findByText(messages.search.helpIntro);
    const links = messages.search.examples.map((e) => screen.getByRole("link", { name: e }));
    expect(links).toHaveLength(3);
    expect(links[0]).toHaveAttribute("href", `/pesquisa?q=${encodeURIComponent(messages.search.examples[0])}`);
    expect(search).not.toHaveBeenCalled();
  });

  it("lists judgments with the matched words in <mark>, the question and the position", async () => {
    const { container } = at("/pesquisa?q=relativo");
    expect(await screen.findByRole("heading", { name: new RegExp(messages.search.judgmentsHeading) })).toBeInTheDocument();
    const marks = [...container.querySelectorAll("mark")].map((m) => m.textContent);
    expect(marks).toContain("relativo");
    // the quote stays text: the fixture quote contains literal tags
    expect(screen.getByText("<b>O prazo é", { exact: false })).toBeInTheDocument();
    expect(container.querySelector("blockquote b")).toBeNull();
    expect(screen.getAllByRole("link", { name: "Prazo do contrato prometido" })[0]).toHaveAttribute("href", "/perguntas/q6");
    expect(screen.getAllByRole("link", { name: "1/10" })[0]).toHaveAttribute(
      "href",
      "https://www.dgsi.pt/jstj.nsf/x/a?OpenDocument",
    );
  });

  it("says when a word was found only in the unpublished sumário, and still shows the quote", async () => {
    at("/pesquisa?q=possuidor");
    const w = messages.search.where;
    const note = await screen.findByText(`${w.label} ${w.summaryOnly}`);
    const item = note.closest("li");
    expect(item).toHaveTextContent("Depois absoluto");
    expect(item?.querySelector("mark")).toBeNull();
    expect(screen.getByRole("status")).toHaveTextContent(messages.search.count(1));
  });

  it("finds a question by its title and says the word is in the question", async () => {
    at("/pesquisa?q=prazo");
    expect(await screen.findAllByText(new RegExp(`${messages.search.where.label}.*${messages.search.where.question}`))).not.toHaveLength(0);
    expect(screen.getByRole("heading", { name: messages.search.questionsHeading })).toBeInTheDocument();
  });

  it("finds a judgment by its processo", async () => {
    at("/pesquisa?q=2/11");
    const note = await screen.findByText(new RegExp(messages.search.where.processo));
    expect(note.closest("li")).toHaveTextContent("O prazo é absoluto");
  });

  it("says so when nothing matches", async () => {
    at("/pesquisa?q=zzzz");
    expect(await screen.findByText(messages.search.noResults("zzzz"))).toBeInTheDocument();
  });

  it("shows a loading state while search.json loads", async () => {
    at("/pesquisa?q=prazo", () => new Promise(() => {}));
    expect(await screen.findByText(messages.search.loading)).toBeInTheDocument();
  });

  it("still searches quotes and questions when search.json fails, and says the sumário index is missing", async () => {
    at("/pesquisa?q=relativo", () => Promise.reject(new Error("x")));
    expect(await screen.findByText(messages.search.noSummaryIndex)).toBeInTheDocument();
    expect(document.querySelector("mark")?.textContent).toBe("relativo");
  });

  it("caps the list at 50 and shows more on demand", async () => {
    const many = Array.from({ length: 120 }, (_, i) => ({
      ...fixture.judgments[0]!,
      doc_id: `m${i}`,
      processo: `${i}/20`,
      quote: "tema comum",
    }));
    render(
      <MemoryRouter initialEntries={["/pesquisa?q=tema"]}>
        <App load={() => Promise.resolve({ ...fixture, judgments: many })} search={() => Promise.resolve(searchFixture)} />
      </MemoryRouter>,
    );
    await screen.findByText(messages.search.count(120));
    expect(screen.getAllByRole("blockquote", { hidden: true }).length).toBe(50);
    fireEvent.click(screen.getByRole("button", { name: messages.search.showMore }));
    expect(screen.getAllByRole("blockquote", { hidden: true }).length).toBe(100);
  });

  it("announces loading, then the result count, in one live region", async () => {
    let done: (f: SearchFile) => void = () => {};
    at("/pesquisa?q=relativo", () => new Promise((r) => (done = r)));
    const status = await screen.findByRole("status");
    expect(status).toHaveAttribute("aria-live", "polite");
    expect(status).toHaveTextContent(messages.search.loading);
    done(searchFixture);
    await screen.findByText(messages.search.count(6));
    expect(screen.getByRole("status")).toBe(status);
  });

  it("announces 'no results' in the same live region", async () => {
    at("/pesquisa?q=zzzz");
    expect(await screen.findByText(messages.search.noResults("zzzz"))).toHaveAttribute("role", "status");
  });

  // regression: the count was rows (judgment x question), so one judgment on two questions counted twice
  it("counts distinct judgments, not judgment-question rows", async () => {
    const q = fixture.questions[0]!;
    const twice = {
      ...fixture,
      questions: [q, { ...q, id: "q7", title: "Outra pergunta" }],
      judgments: [...fixture.judgments, { ...fixture.judgments[2]!, question_id: "q7" }],
    };
    render(
      <MemoryRouter initialEntries={["/pesquisa?q=outro"]}>
        <App load={() => Promise.resolve(twice)} search={() => Promise.resolve(searchFixture)} />
      </MemoryRouter>,
    );
    await screen.findByText(messages.search.count(2));
    expect(screen.getAllByRole("blockquote", { hidden: true }).length).toBe(3);
  });

  // regression: a wrong-version or malformed search.json must not hang on "A carregar" or throw
  it.each([
    ["an old version", { ...searchFixture, version: 1 }],
    ["a malformed file", { version: 2, stopwords: [], docs: ["a"], lengths: [1], terms: { x: [null] } }],
    ["not an object", null],
  ])("falls back to questions and quotes on %s", async (_name, file) => {
    at("/pesquisa?q=relativo", () => Promise.resolve(file as unknown as SearchFile));
    expect(await screen.findByText(messages.search.noSummaryIndex)).toBeInTheDocument();
    expect(document.querySelector("mark")?.textContent).toBe("relativo");
  });

  it("explains each hit with one short line, not a sentence per field", async () => {
    at("/pesquisa?q=relativo");
    const lines = await screen.findAllByText(new RegExp(`^${messages.search.where.label}`));
    expect(lines.length).toBeGreaterThan(0);
    for (const l of lines) expect(l.textContent?.length).toBeLessThan(60);
    expect(document.body.textContent).not.toContain("·");
  });

  it("has Pesquisa in the main navigation", async () => {
    at("/");
    const nav = await screen.findByRole("navigation", { name: messages.nav.label });
    expect(within(nav).getByRole("link", { name: messages.nav.search })).toHaveAttribute("href", "/pesquisa");
  });

  it("encodes a question id in the link", async () => {
    const q = { ...fixture.questions[0]!, id: "q 6/é" };
    const data = { ...fixture, questions: [q], judgments: fixture.judgments.map((j) => ({ ...j, question_id: q.id })) };
    render(
      <MemoryRouter initialEntries={["/pesquisa?q=relativo"]}>
        <App load={() => Promise.resolve(data)} search={() => Promise.resolve(searchFixture)} />
      </MemoryRouter>,
    );
    const links = await screen.findAllByRole("link", { name: q.title });
    expect(links[0]).toHaveAttribute("href", `/perguntas/${encodeURIComponent(q.id)}`);
  });
});
