import { useEffect, useState } from "react";
import { Link, Route, Routes } from "react-router-dom";
import { type Data, loadData } from "./data";
import { messages } from "./messages.pt";
import { AujPage, DivergencePage, Home, QuestionPage, Questions } from "./pages";

type State = { status: "loading" } | { status: "error" } | { status: "ready"; data: Data };

export function App({ load = loadData }: { load?: () => Promise<Data> }) {
  const [state, setState] = useState<State>({ status: "loading" });
  useEffect(() => {
    let alive = true;
    load().then(
      (data) => alive && setState({ status: "ready", data }),
      () => alive && setState({ status: "error" }),
    );
    return () => {
      alive = false;
    };
  }, [load]);

  return (
    <main className="mx-auto max-w-3xl p-4 space-y-4">
      <header className="space-y-1">
        <h1 className="text-2xl font-semibold">
          <Link to="/">{messages.appTitle}</Link>
        </h1>
        <p className="text-[color:var(--color-muted)]">{messages.tagline}</p>
        <p role="note" className="text-sm">
          {messages.disclaimer}
        </p>
      </header>
      {state.status === "loading" && <p>{messages.loading}</p>}
      {state.status === "error" && <p role="alert">{messages.loadError}</p>}
      {state.status === "ready" && (
        <Routes>
          <Route path="/" element={<Home data={state.data} />} />
          <Route path="/perguntas" element={<Questions data={state.data} />} />
          <Route path="/perguntas/:id" element={<QuestionPage data={state.data} />} />
          <Route path="/uniformizacoes" element={<AujPage data={state.data} />} />
          <Route path="/divergencias/:id" element={<DivergencePage data={state.data} />} />
          <Route path="*" element={<Home data={state.data} />} />
        </Routes>
      )}
    </main>
  );
}
