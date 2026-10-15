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
