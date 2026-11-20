#!/usr/bin/env python3
"""Timesheet sanity check: per-day totals and ticket-field violations.

Usage: python3 sanity.py input.json   (input schema: references/sanity-check.md)

Keys: tz, target_hours, range [start, end], leave [dates], today (date, counts as
in progress), weekend [weekday numbers, default 5,6], worklogs [{id, issue,
started, seconds}] (user's own), issues {key: {estimate_s, timespent_s,
story_points, start, due, mine (bool), others {name: seconds}}}.

Prints a markdown report; exits 0 when clean, 1 when there are problems.
"""
import json
import sys
from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo


def hm(seconds) -> str:
    sign = "-" if seconds < 0 else ""
    h, m = divmod(abs(int(seconds)) // 60, 60)
    return f"{sign}{h}h {m}m" if h and m else f"{sign}{h}h" if h else f"{sign}{m}m"


def parse_started(s: str, tz: ZoneInfo) -> datetime:
    s = s.strip()  # Jira: 2026-11-13T16:16:46.000+0400 ; also accepts +04:00
    if len(s) >= 5 and s[-5] in "+-" and s[-3] != ":":
        s = s[:-2] + ":" + s[-2:]
    return datetime.fromisoformat(s).astimezone(tz)


def main():
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        sys.exit(__doc__)
    cfg = json.load(open(sys.argv[1]))
    tz = ZoneInfo(cfg["tz"])
    target = int(float(cfg.get("target_hours", 7)) * 3600)
    d0, d1 = (date.fromisoformat(x) for x in cfg["range"])
    leave = set(cfg.get("leave", []))
    weekend = set(cfg.get("weekend", [5, 6]))
    today = date.fromisoformat(cfg["today"]) if cfg.get("today") else None
    issues = cfg.get("issues", {})
    problems, notes = [], []

    per_day, mine_by_issue = defaultdict(int), defaultdict(int)
    for w in cfg.get("worklogs", []):
        dt = parse_started(w["started"], tz)
        day, secs = dt.date(), int(w["seconds"])
        per_day[day] += secs
        mine_by_issue[w["issue"]] += secs
        meta = issues.get(w["issue"], {})
        tag = f'{w["id"]} ({w["issue"]}, {hm(secs)}, {day:%b} {day.day} {dt:%H:%M})'
        if day.isoformat() in leave:
            problems.append(f"Logged on a leave day: {tag}")
        if meta.get("start") and day < date.fromisoformat(meta["start"]):
            problems.append(f"Before ticket start {meta['start']}: {tag}")
        if meta.get("due") and day > date.fromisoformat(meta["due"]):
            problems.append(f"After ticket due {meta['due']}: {tag}")
        if secs < 15 * 60:
            problems.append(f"Tiny entry, likely accidental: {tag}")
        if dt.second:
            problems.append(f"Odd start time (timer?): {tag}")

    print("| Day | Logged | vs target |\n|---|---|---|")
    total = work_days = 0
    d = d0
    while d <= d1:
        logged = per_day.get(d, 0)
        label = f"{d:%a %b} {d.day}"
        if d.isoformat() in leave:
            status = "leave" if not logged else f"🔴 leave but {hm(logged)} logged"
        elif d.weekday() in weekend:
            status = "weekend" if not logged else f"weekend, {hm(logged)} logged"
        elif today and d == today:
            work_days += 1
            if logged == target:
                status = "✅"
            elif logged > target:
                status = f"🔴 +{hm(logged - target)} (today)"
                problems.append(f"{label} (today): {hm(logged)} logged, over target {hm(target)}")
            else:
                status = f"in progress ({hm(target - logged)} to go)"
        elif today and d > today:
            status = "future"
        else:
            work_days += 1
            diff = logged - target
            status = "✅" if diff == 0 else f"🔴 {'+' if diff > 0 else ''}{hm(diff)}"
            if diff:
                problems.append(f"{label}: {hm(logged)} logged, target {hm(target)}")
        total += logged
        print(f"| {label} | {hm(logged) if logged else '0h'} | {status} |")
        d += timedelta(days=1)
    print(f"| **Total** | **{hm(total)}** | target {hm(target * work_days)} over {work_days} working days |\n")

    print("| Ticket | Estimate | SP | Start | Due | Yours (range) | All authors |\n|---|---|---|---|---|---|---|")
    for key in sorted(set(mine_by_issue) | set(issues)):
        m = issues.get(key, {})
        est, sp, allp = m.get("estimate_s"), m.get("story_points"), m.get("timespent_s")
        missing = [n for n, v in (("estimate", est), ("story points", sp),
                                  ("start date", m.get("start")), ("due date", m.get("due")))
                   if v in (None, "", 0)]
        if missing:
            problems.append(f"{key} missing: {', '.join(missing)}")
        mine = mine_by_issue.get(key, 0)
        if est and mine > est:
            problems.append(f"{key}: your time {hm(mine)} exceeds estimate {hm(est)}")
        if est and allp and allp > est:
            others = m.get("others") or {}
            split = ", ".join(f"{n} {hm(s)}" for n, s in sorted(others.items(), key=lambda x: -x[1]))
            notes.append(f"{key} is {hm(allp - est)} over its {hm(est)} estimate (all authors {hm(allp)}"
                         + (f"; you {hm(mine)}, {split}" if split else "") + ")")
        if m.get("mine") is False:
            notes.append(f"{key} is assigned to someone else — fine to log on; field changes belong to the assignee")
        print(f"| {key} | {hm(est) if est else '—'} | {sp if sp not in (None, '') else '—'} | "
              f"{m.get('start') or '—'} | {m.get('due') or '—'} | {hm(mine)} | {hm(allp) if allp else '—'} |")
    print()

    if notes:
        print("**FYI**")
        for n in notes:
            print(f"- {n}")
        print()
    if problems:
        print(f"**{len(problems)} issue(s)**")
        for i, p in enumerate(problems, 1):
            print(f"{i}. {p}")
        sys.exit(1)
    print("**Clean** — working days on target, all entries inside ticket windows, all fields present.")


if __name__ == "__main__":
    main()
