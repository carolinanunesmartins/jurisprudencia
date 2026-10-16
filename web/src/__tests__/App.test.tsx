import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { App } from "../App";
import type { Data } from "../data";
import { messages } from "../messages.pt";
import { empty, fixture } from "./fixture";

function at(path: string, data: Data = fixture) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <App load={() => Promise.resolve(data)} />
    </MemoryRouter>,
  );
}

/** Text split across <strong> and coloured spans: match on an element's whole text. */
const whole = (text: string) => (_: string, el: Element | null) =>
  el?.textContent === text && [...el.children].every((c) => c.textContent !== text);

describe("App (unit)", () => {
  it("renders the title and the summary, key numbers in bold", async () => {
    at("/");
    expect(screen.getByRole("heading", { name: messages.appTitle })).toBeInTheDocument();
    const count = await screen.findByText(messages.home.leadCount(813));
    expect(count.tagName).toBe("STRONG");
    expect(screen.getByText(messages.home.leadQuestions(1)).tagName).toBe("STRONG");
  });

  it("opens with the strongest confirmed divergence as two facing quotes", async () => {
    at("/");
    expect(await screen.findByText(messages.home.heroCaption)).toBeInTheDocument();
    expect(screen.getAllByRole("article")).toHaveLength(2);
    expect(screen.getAllByRole("link", { name: messages.divergence.detail })[0]).toHaveAttribute(
      "href",
      "/divergencias/q6-split-2009-2012",
    );
  });

  it("lists the questions with counts per position", async () => {
    at("/perguntas");
    expect(await screen.findByRole("link", { name: "Prazo do contrato prometido" })).toBeInTheDocument();
    expect(screen.getAllByText(whole("Relativo 1"))[0]).toBeInTheDocument();
  });

  // regression: a visitor could not tell splits from changes; the list said only "1 divergência"
  it("names each divergence by kind and years in the question list", async () => {
    at("/perguntas");
    expect(await screen.findByRole("link", { name: "Divisão 2009–2012" })).toHaveAttribute(
      "href",
      "/divergencias/q6-split-2009-2012",
    );
    expect(screen.getByRole("link", { name: "Mudança 2004–2009" })).toHaveAttribute(
      "href",
      "/divergencias/q6-shift-2004-2009",
    );
  });

  it("indexes every confirmed divergence on the home page, with its direction", async () => {
    at("/");
    expect(await screen.findByRole("heading", { name: /Divergências confirmadas/ })).toBeInTheDocument();
    expect(screen.getAllByText(whole("De Relativo para Absoluto")).length).toBeGreaterThan(0);
    expect(screen.getAllByText(whole("Relativo e Absoluto nos mesmos anos")).length).toBeGreaterThan(0);
  });

  // regression: a first-time reader could not tell a question from a divergence
  it("explains the four terms on the home page, in the order they nest", async () => {
    at("/");
    const guide = await screen.findByRole("region", { name: messages.home.guide.label });
    const g = messages.home.guide;
    const terms = [...guide.querySelectorAll("li > div > p:first-child > strong")].map((el) => el.textContent);
    expect(terms).toEqual([g.question.term, g.positions.term, g.divergence.term, g.auj.term]);
    // the examples come from the example question shown below
    expect(guide).toHaveTextContent(fixture.questions[0]!.description);
  });

  it("says when a question has no confirmed divergence", async () => {
    at("/perguntas/q6", { ...fixture, divergences: [] });
    expect(await screen.findByText(messages.eyebrow.question)).toBeInTheDocument();
    expect(screen.getByText(messages.noDivergenceShort)).toBeInTheDocument();
  });

  it("shows position names in bold, in their colour", async () => {
    at("/");
    const [name] = await screen.findAllByText("Relativo", { selector: "strong" });
    expect(name).toHaveStyle({ color: "var(--pos-0)" });
  });

  it("reads a shift as before and after, with the counts of each period", async () => {
    at("/divergencias/q6-shift-2004-2009");
    expect(await screen.findByRole("heading", { name: "De Relativo para Absoluto" })).toBeInTheDocument();
    const [before, after] = screen.getAllByRole("article");
    expect(before).toHaveTextContent(messages.before);
    expect(before).toHaveTextContent("Antes relativo");
    expect(after).toHaveTextContent(messages.after);
    expect(after).toHaveTextContent("Depois absoluto");
    // the evidence: Relativo 2, Absoluto 0 in 2004-2006; Relativo 0, Absoluto 2 in 2007-2009
    expect(screen.getByText("2004–2006")).toBeInTheDocument();
    expect(screen.getByText("2007–2009")).toBeInTheDocument();
    // regression: the judge's confidence and the detection's read as one contradicting number
    expect(screen.getByText(messages.divergence.judgeConfidence).nextElementSibling).toHaveTextContent("baixa");
    expect(screen.getByText(messages.divergence.ruleConfidence).nextElementSibling).toHaveTextContent("alta");
  });

  // regression: q8 has two uniformizações inside its split and the note named only the first
  it("names every uniformização that falls inside a split's years", async () => {
    const auj = fixture.aujs[0]!;
    at("/perguntas/q6", {
      ...fixture,
      aujs: [
        { ...auj, id: "u2", date: "2011-05-02" },
        { ...auj, id: "u1", date: "2010-01-15" },
      ],
    });
    expect(
      await screen.findByText(`${messages.aujShort(["15 jan. 2010", "2 mai. 2011"])} ${messages.aujWhy}`),
    ).toBeInTheDocument();
    // a shift is scoped to its own years, so a later reversal is not hidden
    expect(screen.getByText(messages.shiftScope)).toBeInTheDocument();
  });

  it("names each page in the document title", async () => {
    at("/perguntas/q6");
    await screen.findByRole("heading", { name: "Prazo do contrato prometido" });
    expect(document.title).toBe(messages.pageTitle("Prazo do contrato prometido"));
  });

  it("shows the timeline, the divergence and the judgments of a question", async () => {
    at("/perguntas/q6");
    expect(await screen.findByRole("img", { name: messages.timelineLabel("Prazo do contrato prometido") })).toBeInTheDocument();
    // a split is headed as a split, not as a change over time
    expect(screen.getByRole("heading", { name: `${messages.kind.split} 2009–2012` })).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "1/10" })[0]).toHaveAttribute(
      "href",
      "https://www.dgsi.pt/jstj.nsf/x/a?OpenDocument",
    );
  });

  it("keeps the definitions and the full table one click away", async () => {
    const { container } = at("/perguntas/q6");
    await screen.findByText(messages.definitions);
    const closed = [...container.querySelectorAll("details")].filter((d) => !d.open);
    expect(closed.map((d) => d.querySelector("summary")?.textContent)).toEqual(
      expect.arrayContaining([
        expect.stringContaining(messages.definitions),
        expect.stringContaining(messages.tableHeading),
      ]),
    );
    // collapsed, not removed
    expect(screen.getByText("Def relativo.")).toBeInTheDocument();
  });

  it("renders quotes as text, never as HTML", async () => {
    const { container } = at("/perguntas/q6");
    expect(await screen.findByText(/<b>O prazo é relativo<\/b>/)).toBeInTheDocument();
    expect(container.querySelector("td b")).toBeNull();
  });

  it("lists the STJ's own uniformização cards with the ruling first and both sides behind a click", async () => {
    const { container } = at("/uniformizacoes");
    expect(await screen.findByRole("heading", { name: /Uniformizações/ })).toBeInTheDocument();
    expect(screen.getByText("«Uniformiza-se assim»")).toBeInTheDocument();
    expect(screen.getByText(/Os acórdãos decidiram em sentido oposto/)).toBeInTheDocument();
    expect(screen.getByRole("region", { name: messages.auj.side(1) })).toHaveTextContent("1/10");
    expect(screen.getByRole("region", { name: messages.auj.side(2) })).toHaveTextContent(messages.auj.noneNamed);
    expect(screen.getByText(/<i>Só o uso privado<\/i>/)).toBeInTheDocument();
    expect(container.querySelector("li i")).toBeNull();
    // each card says which question it is about
    expect(screen.getByRole("link", { name: "Prazo do contrato prometido" })).toHaveAttribute("href", "/perguntas/q6");
    expect(screen.getByRole("link", { name: messages.auj.open })).toHaveAttribute(
      "href",
      "https://www.dgsi.pt/jstj.nsf/x/u?OpenDocument",
    );
  });

  // security regression: only dgsi.pt links are rendered as links, never a javascript: URL
  it("renders a non-dgsi.pt URL as plain text, not as a link", async () => {
    const [a, b] = fixture.judgments;
    at("/perguntas/q6", {
      ...fixture,
      judgments: [{ ...a!, url: "javascript:alert(1)" }, b!, ...fixture.judgments.slice(2)],
    });
    expect(await screen.findAllByText("1/10")).not.toHaveLength(0);
    const hrefs = [...document.querySelectorAll("a")].map((x) => x.getAttribute("href") ?? "");
    expect(hrefs.some((h) => h.startsWith("javascript:"))).toBe(false);
  });

  it("shows related uniformização cards on the question page", async () => {
    at("/perguntas/q6");
    expect(await screen.findByRole("heading", { name: messages.auj.related })).toBeInTheDocument();
  });

  it("opens a divergence side by side with how it was detected", async () => {
    at("/divergencias/q6-split-2009-2012");
    expect(await screen.findByText(messages.divergence.how)).toBeInTheDocument();
    expect(screen.getAllByRole("article")).toHaveLength(2);
    expect(screen.getByText(messages.divergence.rule.split)).toBeInTheDocument();
    // the model's rationale keeps its caveat
    expect(screen.getByText(messages.divergence.rationale)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Prazo do contrato prometido/ })).toHaveAttribute(
      "href",
      "/perguntas/q6",
    );
  });

  it("links each divergence card to its detail page", async () => {
    at("/perguntas/q6");
    const links = await screen.findAllByRole("link", { name: messages.divergence.detail });
    expect(links.map((l) => l.getAttribute("href"))).toEqual([
      "/divergencias/q6-split-2009-2012",
      "/divergencias/q6-shift-2004-2009",
    ]);
  });

  it("says when a divergence does not exist", async () => {
    at("/divergencias/nope");
    expect(await screen.findByText(messages.divergence.notFound)).toBeInTheDocument();
  });

  it("explains the method and shows the measured numbers", async () => {
    at("/metodo");
    expect(await screen.findByRole("heading", { name: messages.method_page.heading })).toBeInTheDocument();
    expect(screen.getByText(messages.method_page.stats.quotesSub(1))).toBeInTheDocument();
    expect(screen.getByText("3/4 (75 %)")).toBeInTheDocument();
    // regression: /metodo said '2 de 4' while the report said 2/3 (unclear is not decided)
    expect(screen.getByText(messages.method_page.stats.labels(2, 3))).toBeInTheDocument();
    // the breakdown adds up to the shown total (4), so "2 de 3" does not read as a contradiction
    expect(screen.getByText(messages.method_page.stats.labelsSub(4, 2, 1, 1, "Modelo X"))).toBeInTheDocument();
    expect(screen.getByRole("link", { name: messages.method_page.report })).toHaveAttribute(
      "href",
      messages.method_page.reportUrl,
    );
  });

  it("still explains the method when the evaluation is not published", async () => {
    at("/metodo", empty);
    expect(await screen.findByText(messages.method_page.unavailable)).toBeInTheDocument();
  });

  it("says when there is no data yet", async () => {
    at("/perguntas", empty);
    expect(await screen.findByText(messages.noData)).toBeInTheDocument();
  });

  it("reports a load error", async () => {
    render(
      <MemoryRouter>
        <App load={() => Promise.reject(new Error("x"))} />
      </MemoryRouter>,
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(messages.loadError);
  });
});
