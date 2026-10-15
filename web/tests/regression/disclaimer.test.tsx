// Regression: AGENTS.md rule 7 — the "not legal advice" disclaimer must always be visible.
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { App } from "../../src/App";
import { fixture } from "../../src/__tests__/fixture";

describe("disclaimer (regression)", () => {
  it.each(["/", "/perguntas", "/perguntas/q6", "/perguntas/nao-existe"])(
    "is rendered on %s",
    async (path) => {
      render(
        <MemoryRouter initialEntries={[path]}>
          <App load={() => Promise.resolve(fixture)} />
        </MemoryRouter>,
      );
      expect(await screen.findByRole("note")).toHaveTextContent("não é parecer jurídico");
    },
  );
});
