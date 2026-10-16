# Guia: passos com o modelo de linguagem (corridos por uma pessoa)

Os agentes nunca correm estes passos nem veem a chave (AGENTS.md, regra 6). Tudo o resto corre sem rede.

## 1. Preparação (uma vez)
1. Criar uma chave de API em https://console.anthropic.com (Settings → API keys).
2. **Definir um limite de gasto** no espaço de trabalho ou na chave (Settings → Limits). A estimativa abaixo é de poucos dólares, por isso um limite de cerca de 20 USD deixa margem para repetir.
3. Na sessão de PowerShell onde vai correr `make`, definir as variáveis (não são lidas automaticamente do `.env` e só duram esta sessão):
   ```powershell
   $env:LLM_API_KEY = "sk-ant-..."
   $env:CLASSIFY_MODEL = "claude-haiku-4-5-20251001"   # modelo pequeno (SPEC §12)
   $env:JUDGE_MODEL = "claude-sonnet-5-5"              # modelo maior, para o juiz
   ```
   Se a corrida disser "This API key is not scoped to a workspace", crie a chave dentro de um espaço de trabalho (Settings → Workspaces → o espaço → API keys) ou indique o ID desse espaço (Settings → Workspaces, começa por `wrkspc_`):
   ```powershell
   $env:LLM_WORKSPACE_ID = "wrkspc_..."
   ```

## 2. Ordem (etiquetas às cegas e *gates*)
1. Preencher as 60 etiquetas em `data/eval/labels.csv`, correr `uv run python pipeline/tools/labelsheet.py validate` e **comitar**. `make classify` recusa-se a começar antes disso.
2. `make classify`: os 813 acórdãos, uma chamada cada. Pode ser retomado: se parar (limite de pedidos, rede), corra outra vez e continua onde ficou. No fim mostra as contagens e os tokens usados; guarde essa saída para o relatório (SPEC §9.6).
   Opcional, antes: `make classify ARGS="--pilot 100"` para ver os tokens gastos em 100 antes do resto.
3. `make detect`: sem rede; mostra as posições e as divergências por pergunta.
4. `make judge`: uma chamada por divisão ou mudança (no máximo 40) e depois o veredicto do **Gate G3** (SPEC §2).
5. Passar ao agente a saída mostrada. Repetir `make detect` e depois `make judge-replay` não custa nada: os veredictos ficam guardados em `data/replay/`.

## 3. Estimativa de custo (antes de correr)
Medido na base de dados em 2026-10-15: 800 acórdãos classificados pelo sumário (média de 1 460 caracteres), 13 pelo texto integral (até 24 000 caracteres), mais cerca de 4 100 caracteres de instruções por chamada.
São cerca de 1,5 M tokens de entrada e no máximo cerca de 0,5 M de saída para a corrida completa. Com um modelo da classe Haiku são poucos dólares, mas confirme os preços atuais na consola. O juiz são no máximo 40 chamadas curtas.

## 4. Proteções de custo (já incluídas)
- Cada resposta está limitada a 1 200 tokens (uma resposta típica tem ~400). Uma resposta cortada no limite não é repetida, porque seria cortada outra vez; é contada e repetida na corrida seguinte.
- `make classify` para num orçamento de tokens: por omissão 3 M de entrada + saída, cerca do dobro da estimativa. Mostra o progresso a cada 50 acórdãos. Corra outra vez para continuar, ou mude o orçamento com `make classify ARGS="--budget-tokens 1000000"`.
- O limite de gasto da chave é a última proteção.

## 5. Se algo falhar
- A corrida mostra a mensagem da própria API (`API error <estado>: <tipo>: <mensagem>`); leia-a primeiro.
- `400 invalid_request_error`: quase sempre "credit balance is too low" (comprar créditos em Settings → Billing) ou um nome de modelo errado em `CLASSIFY_MODEL` / `JUDGE_MODEL`. `404 not_found_error` com um nome de modelo também quer dizer nome errado.
- `401`: chave errada. `429`/`529`: limite de pedidos ou sobrecarga; espere um minuto e corra outra vez (a corrida retoma).
- "STOPPED: token budget reached": esperado se a estimativa foi baixa; veja os tokens mostrados e corra outra vez (ou suba `--budget-tokens`).
- "schema failures" no resumo: o modelo respondeu duas vezes no formato errado. Esses acórdãos não são guardados e são repetidos na corrida seguinte.
- "quotes rejected": o modelo citou texto que não está no sumário. Essas respostas ficam guardadas como não relevantes e são contadas (AGENTS.md, regra 4).
- Depois de uma alteração à verificação das citações, verifique de novo todas as respostas guardadas, sem rede e sem chamadas à API: `uv run python -m juris.classify --provider replay --reground` (faça antes uma cópia de `data/juris.db`).
