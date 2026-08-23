#!/usr/bin/env python3
"""
github_issue.py — create a Hardonia support issue from a bot escalation handoff.
Used by au_bot_server.py (GH_ISSUE=1) to auto-file S2+ escalations.

Usage:
  python3 github_issue.py --title "..." --body "..." --label "auth"
  echo '{"title":"...","body":"...","label":"auth"}' | python3 github_issue.py -

Outputs the new issue URL on stdout. Fails loud (nonzero) if gh is missing/unauthed.
Requires: gh CLI authed to Hardonian org (verified 2026-07).
"""
import sys, json, argparse, subprocess

REPO = "Hardonian/hardonia-compute-api"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--title", default="[auth] escalation")
    ap.add_argument("--body", default="")
    ap.add_argument("--label", default="auth")
    ap.add_argument("pipe", nargs="?", help="'-' to read JSON {title,body,label} from stdin")
    args = ap.parse_args()

    if args.pipe == "-":
        d = json.load(sys.stdin)
        title = d.get("title", args.title)
        body = d.get("body", args.body)
        label = d.get("label", args.label)
    else:
        title, body, label = args.title, args.body, args.label

    if not title or not body:
        print("ERROR: title and body required", file=sys.stderr); sys.exit(2)

    # gh is the source of truth for issue creation; never invent an issue ID.
    cmd = ["gh", "issue", "create", "--repo", REPO, "--title", title,
           "--body", body, "--label", label]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    except FileNotFoundError:
        print("ERROR: gh CLI not found", file=sys.stderr); sys.exit(3)
    except subprocess.TimeoutExpired:
        print("ERROR: gh timed out", file=sys.stderr); sys.exit(4)

    if out.returncode != 0:
        msg = f"ERROR: gh failed ({out.returncode}): {out.stderr.strip()[:200]}"
        print(msg, file=sys.stderr)
        sys.exit(1)
    # gh prints the issue URL on stdout
    print(out.stdout.strip())

if __name__ == "__main__":
    main()
