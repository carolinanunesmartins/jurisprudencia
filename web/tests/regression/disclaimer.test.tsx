// Regression: AGENTS.md rule 7 — the "not legal advice" disclaimer must always be visible.
import { render, screen } from "@testing-library/react";
import { App } from "../../src/App";

describe("disclaimer (regression)", () => {
  it("is always rendered", () => {
    render(<App />);
    expect(screen.getByRole("note")).toHaveTextContent("não é parecer jurídico");
  });
});
