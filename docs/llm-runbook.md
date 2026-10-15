# Runbook: live LLM steps (HUMAN-run)

Agents never run these and never see the key (AGENTS.md rule 6). Everything else is offline.

## 1. One-time setup
1. Create an API key at https://console.anthropic.com (Settings → API keys).
2. **Set a spend limit** on the workspace or key (Settings → Limits). The estimate below is a few US dollars, so a limit of about 20 USD leaves room for a rerun.
3. In the PowerShell session you run `make` from, set the variables (they are not read from `.env` automatically and last only for this session):
   ```powershell
   $env:LLM_API_KEY = "sk-ant-..."
   $env:CLASSIFY_MODEL = "claude-haiku-4-5-20251001"   # small model (SPEC §12)
   $env:JUDGE_MODEL = "claude-sonnet-5-5"              # larger model for the judge
   ```
   If the run says "This API key is not scoped to a workspace", either create the key inside a workspace (Settings → Workspaces → the workspace → API keys), or set that workspace's ID (Settings → Workspaces, starts with `wrkspc_`):
   ```powershell
   $env:LLM_WORKSPACE_ID = "wrkspc_..."
   ```

## 2. Order (blindness and gates)
1. Fill the 60 labels in `data/eval/labels.csv`, run `uv run python pipeline/tools/labelsheet.py validate`, then **commit**. `make classify` refuses to start before this.
2. `make classify`: all 813 judgments, one call each. Resumable: if it stops (rate limit, network), run it again and it continues where it left off. At the end it prints the counts and the tokens used. Keep that output for the report (SPEC §9.6).
   Optional first: `make classify ARGS="--pilot 100"` to see the token use on 100 before the rest.
3. `make detect`: offline, prints the positions and divergences per question.
4. `make judge`: one call per split/shift (at most 40), then prints the **Gate G3** verdict (SPEC §2).
5. Tell the agent the printed output. Re-running `make detect` and then `make judge-replay` costs nothing: verdicts are cached in `data/replay/`.

## 3. Cost estimate (before running)
From the database, measured 2026-10-15: 800 judgments classified from the sumário (average 1 460 characters), 13 from the full text (up to 24 000 characters), plus about 4 100 characters of instructions per call.
That is about 1.5 M input tokens and at most about 0.5 M output tokens for the full run. With a Haiku-class model this is a few USD, but check the current prices in the console. The judge is at most 40 short calls.

## 4. Cost guards (built in)
- Each answer is capped at 1 200 tokens (a typical answer is ~400). An answer cut at the cap is not retried, because it would be cut again; it is counted and retried on the next run.
- `make classify` stops at a token budget: by default 3 M input+output tokens, about twice the estimate. It prints progress every 50 judgments. Re-run to continue, or change the budget with `make classify ARGS="--budget-tokens 1000000"`.
- The spend limit on the key is the final backstop.

## 5. If something fails
- The run prints the API's own message (`API error <status>: <type>: <message>`); read it first.
- `400 invalid_request_error`: most often "credit balance is too low" (buy credits in Settings → Billing) or a wrong model name in `CLASSIFY_MODEL` / `JUDGE_MODEL`. `404 not_found_error` with a model name also means a wrong model name.
- `401`: wrong key. `429`/`529`: rate limit or overload; wait a minute and re-run (the run resumes).
- "STOPPED: token budget reached": expected if the estimate was low; check the printed tokens, then re-run (or raise `--budget-tokens`).
- "schema failures" in the summary: the model answered in the wrong shape twice. Those judgments are not stored and are retried on the next run.
- "quotes rejected": the model quoted text that is not in the sumário. Those answers are stored as not relevant and counted (AGENTS.md rule 4).
