import { render, screen } from "@testing-library/react";
import { App } from "../App";
import { messages } from "../messages.pt";

describe("App (unit)", () => {
  it("renders the title", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: messages.appTitle })).toBeInTheDocument();
  });
});
