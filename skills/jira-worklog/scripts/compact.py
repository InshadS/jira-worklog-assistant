#!/usr/bin/env python3
"""Compact a large saved tool result (Jira search / worklog list) into short TSV.

Usage: python3 compact.py <saved-result-file> [--fields key,summary,duedate,...]

Handles searchJiraIssuesUsingJql results (issues.nodes[]) and listJiraIssueWorklogs
results (data.worklogs[] or worklogs[]). For Jira issues, custom fields are shown by
label (e.g. "Story Points", "Start date") and the field-ID map is printed once, so
you can request those IDs explicitly afterwards.
"""
import json
import sys

DEFAULT = ["key", "summary", "status", "assignee", "timeoriginalestimate",
           "timespent", "duedate", "Start date", "Story Points"]


def get_issue_value(node, name):
    if name == "key":
        return node.get("key")
    f = node.get("fields", {})
    if name in f:
        v = f[name]
    else:
        cf = f.get("customFields", {}) or {}
        v = (cf.get(name) or {}).get("value")
    if isinstance(v, dict):
        v = v.get("displayName") or v.get("name") or v.get("value") or ""
    return "" if v is None else str(v)


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        sys.exit(__doc__)
    fields = DEFAULT
    if "--fields" in args:
        fields = args[args.index("--fields") + 1].split(",")
    raw = open(args[0]).read()
    data = json.loads(raw)
    if isinstance(data, list) and data and isinstance(data[0], dict) and "text" in data[0]:
        data = json.loads(data[0]["text"])  # MCP content-block wrapper

    nodes = (data.get("issues") or {}).get("nodes") if isinstance(data, dict) else None
    if nodes is not None:
        ids = {}
        for n in nodes:
            for label, v in ((n.get("fields") or {}).get("customFields") or {}).items():
                if isinstance(v, dict) and v.get("id"):
                    ids[label] = v["id"]
        wanted = {k: v for k, v in ids.items() if any(s in k.lower() for s in ("story", "start date"))}
        if wanted:
            print("# field ids: " + ", ".join(f"{k}={v}" for k, v in wanted.items()))
        print("\t".join(fields))
        for n in nodes:
            print("\t".join(get_issue_value(n, f).replace("\t", " ")[:80] for f in fields))
        return

    wl = None
    if isinstance(data, dict):
        wl = (data.get("data") or {}).get("worklogs") or data.get("worklogs")
    if wl is not None:
        print("id\tauthor\tstarted\tseconds")
        for w in wl:
            a = w.get("author") or {}
            print(f"{w.get('id')}\t{a.get('displayName') or a.get('accountId')}\t"
                  f"{w.get('started')}\t{w.get('timeSpentSeconds')}")
        return
    sys.exit("Unrecognised result shape; inspect the top-level keys with: python3 -c "
             "\"import json,sys;print(list(json.load(open(sys.argv[1]))))\" <file>")


if __name__ == "__main__":
    main()
