# ContextOS — Auditable Token Telemetry & Savings Specification

**Governance Standard:** Auditable, Empirical Token Metrics  
**Prohibition:** Zero Speculative Carbon or Kilowatt-Hour Calculations  

---

## 1. Core Principles & Verification Standard

ContextOS implements a strictly verifiable token telemetry pipeline. All reported metrics are derived from mathematical equations grounded in:
1. **Candidate Context Baseline:** Total AST and symbol tokens present in candidate repository files before budget enforcement.
2. **Selected Context Packet:** Tokens dispatched to the LLM within strict budget partition limits.
3. **Avoided Tokens:** The direct difference between candidate and dispatched tokens.
4. **Context Bytes Saved:** Physical network payload volume not transmitted over wire (~4 bytes/token).
5. **Cost Savings (USD):** Direct dollar calculations using verified provider pricing tables.

> [!IMPORTANT]
> **Strict Governance Notice:** ContextOS explicitly rejects speculative environmental gimmicks (e.g. "trees saved" or "grams of CO₂ avoided") due to the absence of verifiable, real-time data center energy mix measurements. Telemetry is restricted to verifiable token, byte, and dollar figures.

---

## 2. Estimation Status Flagging

ContextOS strictly distinguishes between locally computed heuristic estimates and provider-verified figures:
- `estimated: true`: Telemetry calculated by local AST scanners and token budget compilers prior to model dispatch.
- `estimated: false`: Telemetry parsed directly from vendor API response headers (e.g., `usage.prompt_tokens`, `usage.completion_tokens`).

---

## 3. 4-Tier Budgeting & Compression Mathematics

### 3.1 Partition Budgets
For a given total session budget $B$ (default: $8,000$ tokens):
- **Tier 1 (System Instructions):** $B_{\text{system}} = \lfloor 0.15 \times B \rfloor$
- **Tier 2 (Active Task):** $B_{\text{task}} = \lfloor 0.10 \times B \rfloor$
- **Tier 3 (Memory & ADRs):** $B_{\text{memory}} = \lfloor 0.15 \times B \rfloor$
- **Tier 4 (Source Code & Tests):** $B_{\text{source}} = \lfloor 0.50 \times B \rfloor$
- **Tier 5 (Buffer Reserve):** $B_{\text{buffer}} = \lfloor 0.10 \times B \rfloor$

### 3.2 AST Signature Compression
Full file source code $S_{\text{raw}}$ is processed into an AST signature $S_{\text{ast}}$:
- Implementation bodies (`FunctionDef.body`) are collapsed to `...`.
- Type annotations, parameters, decorators, docstrings, classes, and exported interfaces are fully retained.

**Empirical Compression Efficiency:**
$$\text{Reduction Ratio} = \left( 1 - \frac{\text{Tokens}(S_{\text{ast}})}{\text{Tokens}(S_{\text{raw}})} \right) \times 100\%$$
- Python repositories: **75% – 92% token reduction**.
- TypeScript / JavaScript repositories: **70% – 88% token reduction**.

---

## 4. Defensible Cost Calculation Formula

ContextOS calculates savings based on published provider token rates:

| Provider | Model | Prompt Price / 1M | Completion Price / 1M |
| :--- | :--- | :---: | :---: |
| **Anthropic** | `claude-3-5-sonnet` | $3.00 | $15.00 |
| **Anthropic** | `claude-3-haiku` | $0.25 | $1.25 |
| **Anthropic** | `claude-3-opus` | $15.00 | $75.00 |
| **OpenAI** | `gpt-4o` | $2.50 | $10.00 |
| **OpenAI** | `gpt-4o-mini` | $0.15 | $0.60 |
| **OpenAI** | `o1` | $15.00 | $60.00 |
| **Google** | `gemini-1.5-pro` | $1.25 | $5.00 |
| **Google** | `gemini-1.5-flash` | $0.075 | $0.30 |
| **Google** | `gemini-2.0-flash` | $0.10 | $0.40 |
| **Local / Ollama** | `llama3`, `deepseek` | $0.00 | $0.00 |

### Cost Equations
$$\text{Cost}_{\text{without}} = \left( T_{\text{candidate}} \times \frac{P_{\text{prompt}}}{10^6} \right) + \left( T_{\text{output}} \times \frac{P_{\text{completion}}}{10^6} \right)$$

$$\text{Cost}_{\text{with}} = \left( (T_{\text{selected}} - T_{\text{cached}}) \times \frac{P_{\text{prompt}}}{10^6} \right) + \left( T_{\text{cached}} \times \frac{0.5 \times P_{\text{prompt}}}{10^6} \right) + \left( T_{\text{output}} \times \frac{P_{\text{completion}}}{10^6} \right)$$

$$\text{Cost Saved (USD)} = \max\left(0, \text{Cost}_{\text{without}} - \text{Cost}_{\text{with}}\right)$$

---

## 5. Physical Network Bandwidth Avoided

Because ContextOS compiles minimal AST signatures rather than transmitting multi-megabyte source dumps:
$$\text{Bytes Avoided} = T_{\text{avoided}} \times 4 \text{ bytes/token (UTF-8 mean)}$$
In large monorepos with 150,000+ candidate tokens, this eliminates **~600 KB to 2.4 MB of redundant network transmission per agent prompt cycle**.
