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

describe("App (unit)", () => {
  it("renders the title and the summary", async () => {
    at("/");
    expect(screen.getByRole("heading", { name: messages.appTitle })).toBeInTheDocument();
    expect(await screen.findByText(messages.summary(813, 2))).toBeInTheDocument();
  });

  it("lists the questions with counts", async () => {
    at("/perguntas");
    expect(await screen.findByRole("link", { name: "Prazo do contrato prometido" })).toBeInTheDocument();
    expect(screen.getByText(/2 acórdãos com posição/)).toBeInTheDocument();
  });

  it("shows the timeline, the divergence and the judgments of a question", async () => {
    at("/perguntas/q6");
    expect(await screen.findByRole("img", { name: /Linha do tempo/ })).toBeInTheDocument();
    expect(screen.getByText(/Mudança de entendimento/)).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "1/10" })[0]).toHaveAttribute(
      "href",
      "https://www.dgsi.pt/jstj.nsf/x/a?OpenDocument",
    );
  });

  it("renders quotes as text, never as HTML", async () => {
    const { container } = at("/perguntas/q6");
    expect(await screen.findByText(/<b>O prazo é relativo<\/b>/)).toBeInTheDocument();
    expect(container.querySelector("td b")).toBeNull();
  });

  it("lists the STJ's own uniformização cards with both sides, quotes as text", async () => {
    const { container } = at("/uniformizacoes");
    expect(await screen.findByRole("heading", { name: messages.auj.heading })).toBeInTheDocument();
    expect(screen.getByText(/Os acórdãos decidiram em sentido oposto/)).toBeInTheDocument();
    expect(screen.getByRole("region", { name: messages.auj.side(1) })).toHaveTextContent("1/10");
    expect(screen.getByRole("region", { name: messages.auj.side(2) })).toHaveTextContent(
      messages.auj.noneNamed,
    );
    expect(screen.getByText(/<i>Só o uso privado<\/i>/)).toBeInTheDocument();
    expect(container.querySelector("li i")).toBeNull();
    expect(screen.getByRole("link", { name: messages.auj.open })).toHaveAttribute(
      "href",
      "https://www.dgsi.pt/jstj.nsf/x/u?OpenDocument",
    );
  });

  it("shows related uniformização cards on the question page", async () => {
    at("/perguntas/q6");
    expect(await screen.findByRole("heading", { name: messages.auj.related })).toBeInTheDocument();
  });

  it("opens a divergence side by side with how it was detected", async () => {
    at("/divergencias/q6-split-2009-2012");
    expect(await screen.findByRole("heading", { name: messages.divergence.how })).toBeInTheDocument();
    expect(screen.getAllByRole("article")).toHaveLength(2);
    expect(screen.getByText(messages.divergence.rule.split)).toBeInTheDocument();
    expect(screen.getByText(messages.divergence.rationale)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Prazo do contrato prometido/ })).toHaveAttribute(
      "href",
      "/perguntas/q6",
    );
  });

  it("links each divergence card to its detail page", async () => {
    at("/perguntas/q6");
    expect(await screen.findByRole("link", { name: messages.divergence.detail })).toHaveAttribute(
      "href",
      "/divergencias/q6-split-2009-2012",
    );
  });

  it("says when a divergence does not exist", async () => {
    at("/divergencias/nope");
    expect(await screen.findByText(messages.divergence.notFound)).toBeInTheDocument();
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
