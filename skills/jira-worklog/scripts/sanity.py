#!/usr/bin/env python3
"""Timesheet sanity check: per-day totals and ticket-field violations.

Usage: python3 sanity.py input.json

input.json:
{
  "tz": "Asia/Dubai",                 # Jira profile timezone (worklog dates use it)
  "target_hours": 7,
  "range": ["2026-11-09", "2026-11-13"],
  "leave": ["2026-11-09", "2026-11-10"],   # leave / holidays (optional)
  "weekend": [5, 6],                  # weekday numbers Mon=0 (optional, default Sat/Sun)
  "worklogs": [                       # the USER's own entries only
    {"id": "10234", "issue": "ABC-77", "started": "2026-11-13T16:16:46.000+0400",
     "seconds": 180}
  ],
  "issues": {
    "ABC-77": {"estimate_s": 288000, "timespent_s": 180, "story_points": null,
                 "start": "2026-10-05", "due": "2026-10-16"}
  }
}

Prints a markdown report and exits 0 when clean, 1 when there are problems.
"""
import json
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


def hm(seconds: int) -> str:
    sign = "-" if seconds < 0 else ""
    seconds = abs(int(seconds))
    h, m = divmod(seconds // 60, 60)
    if h and m:
        return f"{sign}{h}h {m}m"
    if h:
        return f"{sign}{h}h"
    return f"{sign}{m}m"


def parse_started(s: str, tz: ZoneInfo) -> datetime:
    # Jira: 2026-11-13T16:16:46.000+0400 ; also accept +04:00
    s = s.strip()
    if len(s) >= 5 and (s[-5] in "+-") and s[-3] != ":":
        s = s[:-2] + ":" + s[-2:]
    return datetime.fromisoformat(s).astimezone(tz)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    cfg = json.load(open(sys.argv[1]))
    tz = ZoneInfo(cfg["tz"])
    target = int(float(cfg.get("target_hours", 7)) * 3600)
    d0, d1 = (date.fromisoformat(x) for x in cfg["range"])
    leave = set(cfg.get("leave", []))
    weekend = set(cfg.get("weekend", [5, 6]))
    issues = cfg.get("issues", {})
    problems = []

    per_day = defaultdict(int)
    per_issue_user = defaultdict(int)
    for w in cfg.get("worklogs", []):
        dt = parse_started(w["started"], tz)
        day = dt.date()
        per_day[day] += int(w["seconds"])
        per_issue_user[w["issue"]] += int(w["seconds"])
        meta = issues.get(w["issue"], {})
        tag = f'{w["id"]} ({w["issue"]}, {hm(w["seconds"])}, {day:%b %d} {dt:%H:%M})'
        if day.isoformat() in leave:
            problems.append(f"Logged on a leave day: {tag}")
        start, due = meta.get("start"), meta.get("due")
        if start and day < date.fromisoformat(start):
            problems.append(f"Before ticket start {start}: {tag}")
        if due and day > date.fromisoformat(due):
            problems.append(f"After ticket due {due}: {tag}")
        if int(w["seconds"]) < 15 * 60:
            problems.append(f"Tiny entry, likely accidental: {tag}")
        if dt.second != 0:
            problems.append(f"Odd start time (timer?): {tag}")

    print("| Day | Logged | vs target |")
    print("|---|---|---|")
    d = d0
    work_total = 0
    work_days = 0
    while d <= d1:
        logged = per_day.get(d, 0)
        label = f"{d:%a %b} {d.day}"
        if d.isoformat() in leave:
            status = "leave" if not logged else f"🔴 leave but {hm(logged)} logged"
        elif d.weekday() in weekend:
            status = "weekend" if not logged else f"weekend, {hm(logged)} logged"
        else:
            work_days += 1
            diff = logged - target
            if diff == 0:
                status = "✅"
            else:
                status = f"🔴 {'+' if diff > 0 else ''}{hm(diff)}"
                problems.append(f"{label}: {hm(logged)} logged, target {hm(target)}")
        work_total += logged
        print(f"| {label} | {hm(logged) if logged else '0h'} | {status} |")
        d += timedelta(days=1)
    print(f"| **Total** | **{hm(work_total)}** | target {hm(target * work_days)} over {work_days} working days |")
    print()

    print("| Ticket | Estimate | SP | Start | Due | Your time (range) | All authors (total) |")
    print("|---|---|---|---|---|---|---|")
    for key in sorted(set(per_issue_user) | set(issues)):
        m = issues.get(key, {})
        est = m.get("estimate_s")
        sp = m.get("story_points")
        missing = [n for n, v in (("estimate", est), ("story points", sp),
                                  ("start date", m.get("start")), ("due date", m.get("due")))
                   if v in (None, "", 0)]
        if missing:
            problems.append(f"{key} missing: {', '.join(missing)}")
        mine = per_issue_user.get(key, 0)
        allp = m.get("timespent_s")
        if est and mine > est:
            problems.append(f"{key}: your time {hm(mine)} exceeds estimate {hm(est)}")
        note = ""
        if est and allp and allp > est and mine <= est:
            note = " (over estimate, mostly others)"
        print(f"| {key} | {hm(est) if est else '—'} | {sp if sp not in (None, '') else '—'} | "
              f"{m.get('start') or '—'} | {m.get('due') or '—'} | {hm(mine)} | "
              f"{hm(allp) if allp else '—'}{note} |")
    print()

    if problems:
        print(f"**{len(problems)} issue(s)**")
        for i, p in enumerate(problems, 1):
            print(f"{i}. {p}")
        sys.exit(1)
    print("**Clean** — every working day on target, all entries inside ticket windows, all fields present.")


if __name__ == "__main__":
    main()
