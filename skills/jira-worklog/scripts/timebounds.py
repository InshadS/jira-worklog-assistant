#!/usr/bin/env python3
"""Time helpers for Jira worklog work.

  bounds START [END] --tz ZONE
      Epoch-ms bounds for listJiraIssueWorklogs (startedAfter / startedBefore).
      END is inclusive; defaults to START.
      e.g. bounds 2026-11-16 2026-11-20 --tz Asia/Dubai

  convert "YYYY-MM-DD HH:MM" --from ZONE --to ZONE
      Convert a local time (e.g. a Slack timestamp) to the Jira profile zone and
      print it in Jira's `started` format.
      e.g. convert "2026-11-17 10:35" --from Asia/Kolkata --to Asia/Dubai

  started "YYYY-MM-DD HH:MM" --tz ZONE
      Format a time already in the Jira zone as a `started` value.
"""
import argparse
import sys
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


def started_fmt(dt: datetime) -> str:
    # Jira wants e.g. 2026-11-17T08:00:00.000+0400 (no colon in the offset)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.000%z")


def cmd_bounds(a):
    tz = ZoneInfo(a.tz)
    start = date.fromisoformat(a.start)
    end = date.fromisoformat(a.end) if a.end else start
    if end < start:
        sys.exit("END is before START")
    lo = datetime.combine(start, time.min, tz)
    hi = datetime.combine(end + timedelta(days=1), time.min, tz)
    print(f"startedAfter={int(lo.timestamp() * 1000)}")
    print(f"startedBefore={int(hi.timestamp() * 1000)}")
    print(f"# {lo.isoformat()} .. {hi.isoformat()} (exclusive)")


def cmd_convert(a):
    src = datetime.strptime(a.when, "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo(a.from_))
    dst = src.astimezone(ZoneInfo(a.to))
    print(f"{dst.strftime('%Y-%m-%d %H:%M')} {a.to}")
    print(f"started={started_fmt(dst)}")


def cmd_started(a):
    dt = datetime.strptime(a.when, "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo(a.tz))
    print(started_fmt(dt))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("bounds")
    b.add_argument("start")
    b.add_argument("end", nargs="?")
    b.add_argument("--tz", required=True)
    b.set_defaults(fn=cmd_bounds)

    c = sub.add_parser("convert")
    c.add_argument("when")
    c.add_argument("--from", dest="from_", required=True)
    c.add_argument("--to", required=True)
    c.set_defaults(fn=cmd_convert)

    s = sub.add_parser("started")
    s.add_argument("when")
    s.add_argument("--tz", required=True)
    s.set_defaults(fn=cmd_started)

    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
