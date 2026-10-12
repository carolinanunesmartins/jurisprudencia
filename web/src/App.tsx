import { messages } from "./messages.pt";

export function App() {
  return (
    <main className="mx-auto max-w-3xl p-4">
      <h1 className="text-2xl font-semibold">{messages.appTitle}</h1>
      <p className="text-[color:var(--color-muted)]">{messages.tagline}</p>
      <p role="note" className="mt-4 text-sm">
        {messages.disclaimer}
      </p>
    </main>
  );
}
