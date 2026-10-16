import { useEffect, useState } from "react";
import { messages } from "./messages.pt";

type Theme = "light" | "dark";

export const THEME_KEY = "theme";
const root = () => document.documentElement;
const systemDark = () =>
  typeof window.matchMedia === "function" && window.matchMedia("(prefers-color-scheme: dark)").matches;

/** The theme on screen: the reader's saved choice (set on <html> by public/theme.js), else the system's. */
function current(): Theme {
  const set = root().dataset.theme;
  if (set === "light" || set === "dark") return set;
  return systemDark() ? "dark" : "light";
}

/**
 * Light / dark switch. Follows the system until the reader chooses; the choice is kept in
 * localStorage (a per-reader convenience; storage can be unavailable, so every access is guarded).
 */
export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(current);

  // while the reader has not chosen, follow the system when it changes
  useEffect(() => {
    if (typeof window.matchMedia !== "function") return;
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const follow = () => {
      if (!root().dataset.theme) setTheme(mq.matches ? "dark" : "light");
    };
    mq.addEventListener("change", follow);
    return () => mq.removeEventListener("change", follow);
  }, []);

  const next: Theme = theme === "dark" ? "light" : "dark";
  const label = next === "light" ? messages.theme.toLight : messages.theme.toDark;
  return (
    <button
      type="button"
      onClick={() => {
        root().dataset.theme = next;
        try {
          localStorage.setItem(THEME_KEY, next);
        } catch {
          // private mode or blocked storage: the switch still works for this visit
        }
        setTheme(next);
      }}
      aria-label={label}
      title={label}
      className="inline-flex size-11 items-center justify-center rounded-full text-graphite hover:text-ink hover:bg-surface"
    >
      {/* the icon shows what a click gives: a sun to go light, a moon to go dark */}
      <svg viewBox="0 0 24 24" aria-hidden="true" className="size-5" fill="none" stroke="currentColor" strokeWidth="1.8">
        {next === "light" ? (
          <>
            <circle cx="12" cy="12" r="4.2" />
            <path
              strokeLinecap="round"
              d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M5.3 18.7l1.6-1.6M17.1 6.9l1.6-1.6"
            />
          </>
        ) : (
          <path strokeLinejoin="round" d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z" />
        )}
      </svg>
    </button>
  );
}
