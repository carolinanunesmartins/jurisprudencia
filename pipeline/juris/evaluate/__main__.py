"""`make evaluate`: write `data/eval/report.md` (SPEC §9, ROADMAP T7.2).

Needs the local database (baseline texts) and `data/replay/` (the recorded judge verdicts, to
re-derive pair rule v1 without API calls). Everything else comes from committed files. The
report is pt-PT because `/metodo` is built from it. Counts are given next to every percentage;
no confidence intervals at this sample size (SPEC §9).
"""

import argparse
import contextlib
import csv
import io
import json
import shutil
import sqlite3
import sys
import tempfile
from collections import Counter
from pathlib import Path

from juris.classify.run import build_input
from juris.db.schema import connect
from juris.db.subset import fold
from juris.detect.__main__ import DEV
from juris.detect.__main__ import run as detect_run
from juris.detect.judge import JUDGE, Verdict, display
from juris.detect.judge import run as judge_run
from juris.evaluate.baseline import predict
from juris.evaluate.pools import POOLS
from juris.llm.prompt import PROMPTS
from juris.llm.provider import ReplayProvider
from juris.taxonomy.model import load_taxonomy

EVAL = Path("data/eval")
SNAP = Path("data/classifications")


def score(pairs: list[tuple[str, str]]) -> dict[str, tuple[int, int]]:
    """(label, prediction) pairs without `unclear` → the three counts the report shows."""
    exact = sum(lab == pred for lab, pred in pairs)
    lab_pos = [(lab, pred) for lab, pred in pairs if lab != "nao_decide"]
    pred_pos = [(lab, pred) for lab, pred in pairs if pred != "nao_decide"]
    return {
        "exact": (exact, len(pairs)),
        "recall": (sum(lab == pred for lab, pred in lab_pos), len(lab_pos)),
        "precision": (sum(lab == pred for lab, pred in pred_pos), len(pred_pos)),
    }


def _n(x: float, decimals: int = 0) -> str:
    """pt-PT number: space for thousands, comma for decimals."""
    return f"{x:,.{decimals}f}".replace(",", " ").replace(".", ",")


def _pct(n: int, d: int) -> str:
    return f"{n}/{d} ({100 * n / d:.0f} %)" if d else "0/0"


def _model_predictions() -> dict[tuple[str, str], str]:
    out = {}
    for line in (SNAP / "classification.jsonl").read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        ok = r["relevant"] and r["quote_ok"]
        out[(r["doc_id"], r["question_id"])] = r["position_id"] if ok else "nao_decide"
    return out


def _labels() -> list[dict[str, str]]:
    with (EVAL / "labels.csv").open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def _baseline(conn: sqlite3.Connection, doc_id: str, qid: str) -> str:
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM acordao WHERE doc_id = ?", (doc_id,)).fetchone()
    _, _, text = build_input(row)
    return predict(qid, text, POOLS[qid](fold(text)))


def _verdicts(db: Path, rule: str, tax_path: Path, replay: Path) -> list[dict]:
    """Detect with the given pair rule on a copy of the database, judge from recorded verdicts."""
    cfg_text = Path("detect.toml").read_text(encoding="utf-8")
    lines = [ln for ln in cfg_text.splitlines() if not ln.startswith("pair_rule")]
    with tempfile.TemporaryDirectory() as tmp:
        copy, cfg = Path(tmp) / "db.sqlite", Path(tmp) / "detect.toml"
        shutil.copy(db, copy)
        cfg.write_text("\n".join([*lines, f'pair_rule = "{rule}"']) + "\n", encoding="utf-8")
        conn = connect(copy)
        system = (PROMPTS / f"{JUDGE}.md").read_text(encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            detect_run(conn, tax_path, cfg)
            judge_run(conn, ReplayProvider(replay), load_taxonomy(tax_path), system)
        rows = conn.execute(
            "SELECT question_id, type, window_start, window_end, judge_json, rule_confidence"
            " FROM divergence WHERE type IN ('split', 'shift')"
            " ORDER BY question_id, type, window_start"
        ).fetchall()
        conn.close()
    out = []
    for q, t, s, e, j, rc in rows:
        v = Verdict.model_validate_json(j) if j else None
        out.append(
            {
                "key": (q, t, s, e),
                "shown": display(v) is not None,
                "rule": rc,
                "judge": v.confidence if v else None,
            }
        )
    return out


def precision_section(labelled: list[dict[str, str]]) -> list[str]:
    """Section 6 from the filled rows of the divergence sheet (SPEC §9.2)."""
    out = ["## 6. Precisão das divergências", ""]
    if not labelled:
        out += [
            "Pendente: requer etiquetagem humana das divergências (SPEC §9.2). Sem ela, a "
            "única verificação das divergências mostradas é o juiz (outro modelo).",
            "",
        ]
    else:
        out += [
            "Etiquetas de uma pessoa sem formação jurídica (o responsável do projeto), "
            "a partir dos dois excertos e das ligações ao dgsi.pt; só as divergências "
            "etiquetadas entram na contagem.",
            "",
            "| Conjunto | correct | incorrect | legislative_change | unclear | Precisão |",
            "|---|---|---|---|---|---|",
        ]
        for name, want in (("mostradas no sítio", "yes"), ("ocultadas pelo juiz", "no")):
            rs = [r for r in labelled if r["shown"] == want]
            if not rs:
                continue
            c = Counter(r["label"].strip() for r in rs)
            decided = c["correct"] + c["incorrect"] + c["legislative_change"]
            out.append(
                f"| {name} ({len(rs)}) | {c['correct']} | {c['incorrect']} | "
                f"{c['legislative_change']} | {c['unclear']} | "
                f"{_pct(c['correct'], decided)} |"
            )
        notes = [
            f"- {r['question']} {r['type']} {r['window']}: {r['notes'].strip()}"
            for r in labelled
            if (r["notes"] or "").strip()
        ]
        out += [
            "",
            "Precisão = correct / (correct + incorrect + legislative_change); `unclear` excluído.",
            *(["", "Notas:", *notes] if notes else []),
            "",
        ]
    return out


def report(db: Path, tax_path: Path, replay: Path) -> str:
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    model = _model_predictions()
    rows = _labels()
    out = [
        "# Avaliação",
        "",
        "Gerado por `make evaluate` a partir dos dados publicados no repositório. "
        "Contagens ao lado de cada percentagem; com amostras deste tamanho não se indicam "
        "intervalos de confiança. Afinação só nas perguntas de desenvolvimento (q2, q3); "
        "os resultados de teste são q6–q10.",
        "",
    ]

    # 1. data and cost
    runs = json.loads((EVAL / "runs.json").read_text(encoding="utf-8"))
    cls = runs["classify"]
    tin = sum(r["input_tokens"] for r in cls)
    tout = sum(r["output_tokens"] for r in cls)
    price = runs["price_usd_per_mtok_assumed"]
    usd = tin / 1e6 * price["classify_in"] + tout / 1e6 * price["classify_out"]
    judged = ", ".join(f"{j['run']}: {j['calls']} chamadas" for j in runs["judge"])
    out += [
        "## 1. Dados e custo",
        "",
        f"- Subconjunto: 813 acórdãos do STJ sobre contrato-promessa (2000–2025), "
        f"todos classificados ({cls[0]['judgments']} no piloto e {cls[1]['judgments']} na "
        "execução completa).",
        f"- Classificador `{runs['classify_model']}`: {_n(tin)} tokens de entrada e "
        f"{_n(tout)} de saída (≈ {_n((tin + tout) / 813)} por acórdão). Custo estimado "
        f"≈ {_n(usd, 2)} USD a preços de tabela assumidos "
        f"({_n(price['classify_in'])} / {_n(price['classify_out'])} USD por milhão; "
        "confirmar na consola).",
        f"- Juiz `{runs['judge_model']}`: {judged}. Tokens do juiz não registados.",
        "- Tempo por etapa: não registado.",
        "",
    ]

    # 2. grounding
    snap = [
        json.loads(ln)
        for ln in (SNAP / "classification.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    accepted = [r for r in snap if r["relevant"] and r["quote_ok"]]
    rejected = [r for r in snap if not r["quote_ok"] and r["quote"] is None]
    how = Counter(t for r in accepted for t in (r.get("quote_match") or "").split("+") if t)
    out += [
        "## 2. Citações (regra de verificação)",
        "",
        f"- Respostas com posição propostas pelo modelo: {len(accepted) + len(rejected)}; "
        f"aceites {len(accepted)}, rejeitadas {len(rejected)}. **Citações inventadas "
        "aceites: 0** (cada citação publicada é texto do próprio sumário, verificado).",
        "- Como foram localizadas as aceites (uma citação pode ter mais de uma): "
        + ", ".join(f"{k} {v}" for k, v in sorted(how.items()))
        + ".",
        "- `ellipsis` e `trimmed` mostram só parte do que o modelo citou.",
        "",
    ]

    # 3. position accuracy
    out += [
        "## 3. Exatidão da posição (60 etiquetas)",
        "",
        "Etiquetas feitas por um modelo de IA (Claude Opus 5.5) a pedido do responsável, "
        "sem revisão humana, da mesma família do classificador: a concordância pode estar "
        "inflacionada (ver `data/eval/labeller.md`). Linhas `unclear` excluídas.",
        "",
        "| Conjunto | Sistema | Concordância exata | Etiqueta com posição → mesma posição "
        "| Posição dada → etiqueta concorda |",
        "|---|---|---|---|---|",
    ]
    confusion: dict[str, Counter] = {}
    for name, keep in (
        ("teste (q6–q10)", lambda q: q not in DEV),
        ("dev (q2, q3)", lambda q: q in DEV),
    ):
        sub = [r for r in rows if keep(r["question"]) and r["label"] != "unclear"]
        unclear = sum(1 for r in rows if keep(r["question"]) and r["label"] == "unclear")
        for system, pred in (
            ("modelo", lambda r: model[(r["doc_id"], r["question"])]),
            ("base de palavras-chave", lambda r: _baseline(conn, r["doc_id"], r["question"])),
        ):
            pairs = [(r["label"], pred(r)) for r in sub]
            s = score(pairs)
            out.append(
                f"| {name} ({len(sub)}; {unclear} unclear) | {system} | "
                f"{_pct(*s['exact'])} | {_pct(*s['recall'])} | {_pct(*s['precision'])} |"
            )
            if system == "modelo":
                confusion[name] = Counter((lab, p) for lab, p in pairs if lab != p)
    out += ["", "Erros do modelo (etiqueta → modelo):", ""]
    for name, c in confusion.items():
        items = "; ".join(f"{a} → {b} ×{n}" for (a, b), n in sorted(c.items())) or "nenhum"
        out.append(f"- {name}: {items}")
    out.append("")

    # 4. divergences, v1 vs v2
    v1 = {d["key"]: d for d in _verdicts(db, "v1", tax_path, replay)}
    v2 = {d["key"]: d for d in _verdicts(db, "v2", tax_path, replay)}
    out += [
        "## 4. Divergências detetadas e confirmadas pelo juiz",
        "",
        "Regra de pares v1 (vizinhos no tempo) e v2 (pré-registada: sem citações parciais, "
        "par mais próximo). O sítio usa v2; a Gate G3 foi decidida em v1.",
        "",
        "| Pergunta | Tipo | Janela | v1 | v2 | Confiança da regra (v2) |",
        "|---|---|---|---|---|---|",
    ]
    for key in sorted(set(v1) | set(v2), key=lambda k: (int(k[0][1:]), k[1], k[2])):
        q, t, s, e = key
        tag = " (dev)" if q in DEV else ""
        a, b = v1.get(key), v2.get(key)
        cell = lambda d: "—" if d is None else ("**mostrada**" if d["shown"] else "oculta")  # noqa: E731
        out.append(
            f"| {q}{tag} | {t} | {s}–{e} | {cell(a)} | {cell(b)} | {(b or {}).get('rule') or '—'} |"
        )
    for name, vs in (("v1", v1), ("v2", v2)):
        shown = [k for k, d in vs.items() if d["shown"]]
        test = [k for k in shown if k[0] not in DEV]
        out.append(
            f"\n{name}: {len(shown)} de {len(vs)} mostradas, {len(test)} em perguntas de teste."
        )
    out += [
        "",
        "Gate G3 (≥ 1 divergência confirmada numa pergunta de teste): **ficar** no "
        "contrato-promessa (v1: 2).",
        "",
    ]

    # 5. AUJ
    aujs = json.loads(Path("data/auj/auj.json").read_text(encoding="utf-8"))
    out += [
        "## 5. Divergências reconhecidas pelo STJ",
        "",
        f"{len(aujs)} acórdãos de uniformização no subconjunto, apresentados com citações "
        "literais verificadas (`/uniformizacoes`). Não dependem do classificador nem do "
        "juiz; a escolha dos excertos foi feita por um agente de IA, sem revisão jurídica.",
        "",
    ]

    # 6. divergence precision
    sheet = EVAL / "divergence_labels.csv"
    labelled = []
    if sheet.exists():
        with sheet.open(encoding="utf-8-sig", newline="") as f:
            labelled = [r for r in csv.DictReader(f) if (r["label"] or "").strip()]
    out += precision_section(labelled)

    # 7. survey recovery
    survey = json.loads((EVAL / "survey.json").read_text(encoding="utf-8"))
    out += [
        "## 7. Recuperação do inquérito (5 perguntas-semente)",
        "",
        "| # | Tema | Pergunta | Resultado | Evidência |",
        "|---|---|---|---|---|",
    ]
    out += [
        f"| {s['seed']} | {s['topic']} | {s['question'] or '—'} | {s['result']} | {s['evidence']} |"
        for s in survey
    ]
    out += [
        "",
        "## 8. Limitações",
        "",
        "- Etiquetas de avaliação feitas por IA, da mesma família do classificador.",
        "- Uma só fonte de verificação das divergências (o juiz, um modelo); sem jurista.",
        "- Classificação a partir do sumário (ADR 0007): o que o sumário omite não é visto.",
        "- O classificador atribui posição a acórdãos que só tocam a pergunta "
        "(ver erros na secção 3); o juiz filtra, ocultando também divergências reais.",
        "- Subconjunto por descritor (ADR 0005); só 2000–2025.",
        "",
    ]
    return "\n".join(out)


SHEET_FIELDS = [
    "n",
    "question",
    "type",
    "window",
    "shown",
    "date_a",
    "processo_a",
    "url_a",
    "quote_a",
    "date_b",
    "processo_b",
    "url_b",
    "quote_b",
    "label",
    "notes",
]


def divergence_sheet(db: Path, path: Path) -> int:
    """T7.1: the judged split/shift divergences (site's pair rule) for human labelling, SPEC §9.2.

    Label: correct | incorrect | legislative_change | unclear. Never overwrites a sheet.
    """
    if path.exists():
        raise FileExistsError(f"{path} exists; labels may be filled in it")
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)

    def processo(doc_id: str) -> str:
        return conn.execute("SELECT processo FROM acordao WHERE doc_id = ?", (doc_id,)).fetchone()[
            0
        ]

    rows = conn.execute(
        "SELECT question_id, type, window_start, window_end, evidence_json, judge_json"
        " FROM divergence WHERE type IN ('split', 'shift')"
        " ORDER BY question_id, type, window_start"
    ).fetchall()
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(SHEET_FIELDS)
        for n, (q, t, s, e, ev, j) in enumerate(rows, 1):
            a, b = json.loads(ev)["pair"]
            shown = bool(j) and display(Verdict.model_validate_json(j)) is not None
            w.writerow(
                [
                    n,
                    q,
                    t,
                    f"{s}-{e}",
                    "yes" if shown else "no",
                    a["date"],
                    processo(a["doc_id"]),
                    a["url"],
                    a["quote"],
                    b["date"],
                    processo(b["doc_id"]),
                    b["url"],
                    b["quote"],
                    "",
                    "",
                ]
            )
    return len(rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--db", type=Path, default=Path("data/juris.db"))
    ap.add_argument("--taxonomy", type=Path, default=Path("data/taxonomy.json"))
    ap.add_argument("--replay-dir", type=Path, default=Path("data/replay"))
    ap.add_argument(
        "--divergence-sheet",
        action="store_true",
        help="write data/eval/divergence_labels.csv for human labelling (T7.1)",
    )
    a = ap.parse_args()
    if a.divergence_sheet:
        print(f"{divergence_sheet(a.db, EVAL / 'divergence_labels.csv')} divergences to label")
        return 0
    if not a.db.exists():
        print(f"{a.db} not found: the baseline needs the local texts", file=sys.stderr)
        return 2
    text = report(a.db, a.taxonomy, a.replay_dir)
    (EVAL / "report.md").write_text(text, encoding="utf-8", newline="\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
