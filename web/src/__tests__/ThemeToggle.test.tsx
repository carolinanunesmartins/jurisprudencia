import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { messages } from "../messages.pt";
import { THEME_KEY, ThemeToggle } from "../ThemeToggle";

// jsdom here has no localStorage: an in-memory one per test (the component guards every access)
let store: Map<string, string>;
beforeEach(() => {
  store = new Map();
  vi.stubGlobal("localStorage", {
    getItem: (k: string) => store.get(k) ?? null,
    setItem: (k: string, v: string) => void store.set(k, v),
  });
});
afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  delete document.documentElement.dataset.theme;
});

describe("ThemeToggle", () => {
  it("switches to dark and back, on <html> and in storage", () => {
    document.documentElement.dataset.theme = "light";
    render(<ThemeToggle />);
    fireEvent.click(screen.getByRole("button", { name: messages.theme.toDark }));
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(store.get(THEME_KEY)).toBe("dark");
    fireEvent.click(screen.getByRole("button", { name: messages.theme.toLight }));
    expect(document.documentElement.dataset.theme).toBe("light");
    expect(store.get(THEME_KEY)).toBe("light");
  });

  it("starts from the saved choice set before paint", () => {
    document.documentElement.dataset.theme = "dark";
    render(<ThemeToggle />);
    expect(screen.getByRole("button", { name: messages.theme.toLight })).toBeInTheDocument();
  });

  it("follows the system when nothing was chosen (light here: jsdom has no dark preference)", () => {
    render(<ThemeToggle />);
    expect(screen.getByRole("button", { name: messages.theme.toDark })).toBeInTheDocument();
  });

  it("still switches when storage is blocked", () => {
    vi.stubGlobal("localStorage", {
      getItem: () => null,
      setItem: () => {
        throw new Error("blocked");
      },
    });
    render(<ThemeToggle />);
    fireEvent.click(screen.getByRole("button", { name: messages.theme.toDark }));
    expect(document.documentElement.dataset.theme).toBe("dark");
  });
});
