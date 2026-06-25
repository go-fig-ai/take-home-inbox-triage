# Engineering Log

**Name:** Sagar Raval
**Time spent:** ~2 hours

---

## How I broke the work down

Started by walking through the entire scaffold end-to-end before writing a line of code — README, stub signatures, mock API auth model, and all 8 email fixtures. That read identified two things worth designing around upfront: the prompt injection attack in e-007 and the ambiguous billing/sales signal in e-008.

Task order:
1. `TriageClient` — HTTP wrapper with read/write token separation baked in structurally
2. `classify_email()` — LLM call with prompt injection defense
3. `plan_actions()` — pure routing, no side effects
4. `execute()` — HITL gate, single responsibility
5. `triage_inbox()` — orchestrator wiring it all together
6. `src/run.py` — interactive CLI for the live demo
7. `tests/test_triage.py` — 14 tests covering routing, HITL gate, and injection scenario without needing a live LLM or server

Built bottom-up so each piece was independently testable before the next layer depended on it.

## Where I ran things in parallel

- Ran the test suite and the live end-to-end run independently — tests use stub classifiers and mock clients so they never need a running server or LLM key
- Iterated on the classifier prompt in isolation (running `classify_email` on e-008 five times in a loop) while the mock API stayed running — confirmed the tie-break rule was stable before doing a full triage run

## One time the AI was wrong, and how I caught it

The initial tie-break rule in the classifier prompt preferred `billing` over `sales_lead` for mixed-signal emails. Running `classify_email` five times on e-008 returned `billing` consistently — which looked like success. But reviewing the actual routing logic made it clear that was the wrong call: Jordan isn't reporting a problem, he's signalling expansion intent ("growing to 40 people next year"). Billing agents aren't equipped to handle upsell conversations. Caught it by reasoning about which *team* receives the email and what they'd do with it — not just whether the label was consistent.

Flipped the rule to prefer `sales_lead` and re-ran the five-sample check: 5/5 `sales_lead`.

## What I deliberately cut to fit the 2 hours

- **LLM-drafted reply bodies**: replies are currently templated strings. In production the LLM would draft a personalised reply per email using the original body as context. Cut because the routing and HITL logic is the core of the skill — reply quality is a content problem, not an architecture problem.
- **Retry logic**: no retries on Groq API failures. A production skill would retry with backoff on transient errors.
- **Structured logging**: print statements suffice for a demo. A real deployment would emit structured JSON logs per email for observability.

## The design decision I'm proudest of

The least-privilege token model. `TriageClient` is constructed with both tokens upfront, but `_write_headers()` raises `PermissionError` if `write_token` is `None` — meaning a client initialised without the write token structurally cannot perform writes, regardless of what code paths are hit. Combined with `execute()` gating on `approved=True`, there are two independent layers preventing unauthorised writes: one structural (no token → no HTTP call possible) and one behavioural (approved=False → execute returns None immediately). The spam path never touches a write endpoint because `plan_actions("spam", ...)` returns an empty list — so `execute()` is never even called.
