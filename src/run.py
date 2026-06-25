"""Interactive CLI entrypoint for the Inbox Triage skill.

Usage:
    python src/run.py

Requires a running mock API (`make serve`) and a .env with:
    API_BASE_URL, READ_TOKEN, WRITE_TOKEN, ANTHROPIC_API_KEY
"""

from __future__ import annotations

import os

from dotenv import load_dotenv

from triage_skill import TriageClient, triage_inbox

load_dotenv()


def interactive_approver(email: dict, action) -> bool:
    """Print a summary of the proposed action and ask the human to approve."""
    print()
    print("─" * 60)
    print(f"  Email   : [{email['id']}] {email['subject']}")
    print(f"  From    : {email['from']}")
    print(f"  Action  : {action.kind}")
    print(f"  Why     : {action.rationale}")
    print(f"  Payload : {action.payload}")
    print("─" * 60)
    answer = input("  Approve? [y/N] ").strip().lower()
    return answer == "y"


def main() -> None:
    base_url = os.environ["API_BASE_URL"]
    read_token = os.environ["READ_TOKEN"]
    write_token = os.environ["WRITE_TOKEN"]

    # Client holds both tokens; write token is only used post-approval inside execute()
    client = TriageClient(base_url=base_url, read_token=read_token, write_token=write_token)

    print("Fetching inbox and classifying emails...\n")
    results = triage_inbox(client, approver=interactive_approver)

    print()
    print("═" * 60)
    print("  Triage complete")
    print("═" * 60)
    for r in results:
        action_summary = ", ".join(a.kind for a in r.actions) or "no action"
        print(f"  {r.email_id}  {r.label:<12}  {action_summary}")


if __name__ == "__main__":
    main()
