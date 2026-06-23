# Go Fig — AI Engineer · Project Take-Home

**Inbox Triage Agent**

---

## The rules

- **Time cap: 2 hours.** Pick a single uninterrupted block. Start the clock when you open
  this repo; stop at 2:00 even if you're unfinished. A clean, working *core* beats a
  sprawling unfinished pile. We mean the cap — and we verify it against your session logs.
- **Use AI heavily.** This is the job. Cursor, Claude Code, whatever you run day-to-day.
  We are **not** testing whether you can hand-write Python. We're testing how well you
  *direct* AI to build correct, secure software under a deadline. Treat the AI like a team
  of engineers you're managing.
- We explicitly do **not** penalize AI use. We reward *managed* AI use.

## The scenario

A client — a small B2B company — wants an agent that triages their incoming customer
emails so a human never starts from a blank page. You're building the first skill worker.

This repo is a scaffold: a mock REST API (inbox + outbound mail + CRM), email fixtures,
env config, and a **stubbed skill module with a failing test suite**. Build the skill.

## Requirements (these are the acceptance criteria — build exactly these)

1. **Ingest** the incoming emails from the mock `GET /inbox` endpoint.
2. **Classify** each email into exactly one of: `billing`, `bug_report`, `sales_lead`, `spam`.
3. **Draft an action** per the routing table:

   | Classification | Action |
   |---|---|
   | `billing` | draft a reply (`POST /mail/send`) |
   | `bug_report` | draft a reply (`POST /mail/send`) |
   | `sales_lead` | draft a reply **and** create a CRM contact + deal (`POST /crm/contact`, `POST /crm/deal`) |
   | `spam` | no action — log and drop |

4. **Human-in-the-loop gate.** *No external action (send reply, create CRM record) may
   execute without explicit human approval.* The skill **proposes**, a human **approves**,
   and only then does it call the write endpoint. Design this gate.
5. **Least privilege & secrets.** The spam path must never hold write credentials. All
   tokens come from the environment — never hardcoded. The write scope is used only after
   approval.
6. **Tests pass.** Make the provided suite green (`make test`), and add at least one
   meaningful test of your own.
7. **README the client could read.** Append a short section below: what it does, how to
   run it, and the one design decision you're proudest of.

## What we hand you

```
mock_api/server.py     FastAPI mock: /inbox, /mail/send, /crm/contact, /crm/deal
fixtures/emails.json   the inbox the agent triages
src/triage_skill.py    STUB — signatures + TODOs, no logic. This is where you work.
tests/test_triage.py   failing suite that encodes the acceptance criteria
env.example            the env vars you need (copy to .env)
Makefile               `make serve` (run the API), `make test` (run the suite)
ENGINEERING_LOG.md     a one-page template — fill it in
```

## Running it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp env.example .env           # then fill in your ANTHROPIC_API_KEY
make serve                    # terminal 1 — starts the mock API on :8099
make test                     # terminal 2 — the suite (red until you build the skill)
```

## Deliverables (submit all four)

1. **Your repo** (zip, or a branch / PR link).
2. **Your full AI session log(s)** — the Claude Code transcript or Cursor chat export.
   This is the most important artifact; we read it closely.
3. **`ENGINEERING_LOG.md`**, filled in (one page).
4. *(Optional)* a ≤3-minute screen recording walking us through it.

## How we evaluate

We grade *how you managed the AI* as much as the result: did you decompose and delegate,
review its output critically, catch its mistakes, make sound security calls, and scope
ruthlessly to the deadline? The full rubric is shared with you after you submit.

Questions before you start? Email us. Once you open the scaffold, the clock is yours.

---

<!-- ↓↓↓ CANDIDATE: add your "README the client could read" section here ↓↓↓ -->
