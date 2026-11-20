---
name: jira-worklog
description: Turn what someone actually worked on (their Slack messages and Jira activity, optionally Google Calendar) into accurate Jira worklogs, and sanity-check their timesheet. Use whenever the user wants to fill, backfill, review, move or fix Jira worklogs or a Clockwork/Tempo-style timesheet — "analyse my work for nov 17", "log my hours for yesterday", "fill my gaps this week", "sanity check last week's logs", "which tickets can I log against" — or talks about hitting a daily hours target in Jira, even without saying "worklog".
---

# Jira Worklog Assistant

Turns a person's real day into Jira worklogs that survive review: every entry sits
on a ticket whose dates cover it, the day adds up to the target, and nothing is
written until the person says so.

Use only the current user's own data: their messages, the threads they replied in,
their worklogs, and their calendar only if they opt in. Never post to Slack.

## Modes and what to read

Pick the mode from the request; several can chain in one conversation. Read only
the references a mode needs — they're written to be loaded on demand.

| Mode | Request | Writes? | Read |
|---|---|---|---|
| Analyse day | "analyse my work for nov 17" | No — proposes | detect-context, evidence-sources, ticket-matching |
| Backfill range | "fill my gaps this week" | No — proposes | same as Analyse |
| Log | "log", "log but make X 1.5h" | After explicit OK | jira-api |
| Sanity check | "check last week's log" | No — reports | detect-context, sanity-check |
| Fix fields | "set the missing story points" | After explicit OK | jira-api |
| Move/adjust | "move these to ABC-200", "make it 2h" | Edits; deletes are manual | jira-api |

Run the scripts in `scripts/` rather than reading their source; `--help` (or the
schema in the reference that calls them) is all you need.

## Settings

Defaults, overridable in the prompt:
- daily target **7h** ("I do 8h days")
- catch-all ticket: assigned to the user, summary contains **"Operations"**, dates
  cover the day ("use ABC-900 for misc")
- leave/holidays: none assumed; ask when a weekday has no activity
- calendar: **off**. On only when the user asks in this conversation ("include my
  calendar", "use my meetings"); then it stays on until they turn it off. While off,
  don't call any Calendar tool even if the connector exists.

## Keep it lean

Tool output is most of the cost, so:
- **Detect once per conversation.** Site, account, timezones, field IDs and
  catch-all tickets don't change between requests — reuse them. Reuse worklogs and
  ticket fields already fetched when the next request covers the same days.
- **Ask Jira for exactly the fields you need** (lists in the references). Don't use
  `view: "evidence"` except the single field-ID lookup, and filter by assignee in
  JQL instead of fetching the assignee object.
- **Slack**: concise format, `include_context: false`; read a thread only when a
  message can't be understood alone, at most ~3 per day.
- **Large results saved to a file**: extract with `scripts/compact.py`, never read
  the whole file.
- **Load tool schemas in one ToolSearch call** with every tool you'll need.

## Analyse / backfill workflow

1. **Context** (`detect-context.md`) — skip what's already known in this conversation.
2. **Evidence** (`evidence-sources.md`), in parallel: existing worklogs for the day
   (only fill the gap), every Slack message the user sent that day (all pages),
   Jira tickets they touched plus keys mentioned in Slack, calendar if on. If a
   source is unavailable, say so and continue. For a range, find the short days
   first and gather only for those.
3. **Themes and tickets** (`ticket-matching.md`): 3–7 themes with local times. The
   rules that matter most: an entry's date must sit inside the ticket's Start–Due
   window; use the specific ticket when the user did the work and it's open,
   otherwise the catch-all, and say why in one line; split catch-all time into one
   entry per theme; flag a proposal that pushes the user's time past an estimate.
4. **Propose — never write here.** Whole 30-minute blocks filling exactly the gap,
   sized by evidence (Slack bursts are estimates; calendar meetings, when on, are
   exact). Start times in the **Jira profile timezone**, back-to-back from the
   working-day start in roughly real order.

Reply format — compact; output tokens cost more than input:

```
<Day Mon DD>: <N>h logged, <gap> to fill.

Evidence (local time): one line per theme — time range, what, key nouns.

**Proposed <Day> <Mon DD> logs (<N>h, Jira time <±HH:MM>)**
| Start | Issue | Time | Note |
|---|---|---|---|
| 07:00 | ABC-1 | 1h | *(already logged, 12345)* |
| 08:00 | ABC-2 | 1h 30m | factual one-liner: PRs, services, issue keys, people |

After: ABC-2 at 3h of 6h estimate; all inside ticket dates.
Say **"log"** to add these, or tell me what to change.
```

Notes are one factual line: no secrets, no customer data. Ask questions (e.g.
uncertain attendance) in one line at the end, not as a separate section.

## Log

"log", "add these" or "yes" to a shown proposal is confirmation. Apply the user's
edits first ("ABC-105 1.5h only", "split this", "total 3h"): their numbers beat
yours; re-balance only where asked, and re-show the table if the plan changed
meaningfully. Write in parallel (`jira-api.md`), then reply with one table of new
worklog IDs, the day total, and each touched ticket's logged-vs-estimate.

## Sanity check

Follow `sanity-check.md`: worklogs for the range, fields of every touched ticket,
run `scripts/sanity.py`, report totals and violations with concrete fixes. Needs no
Slack — ask about leave for empty weekdays instead of searching.

## API limits and safety

- Worklogs can't be deleted with these tools. Give the exact ID, ticket, date and
  time for the user to delete in Jira, then offer to re-check. To move: create the
  new entry, then have them delete the old one.
- If a message the user sent contains credentials (keys, tokens, `secret-key`,
  passwords), say so once and suggest removing it and rotating the secret. Never
  copy secrets into worklogs.
- Flag entries on leave days or outside a ticket's dates in any mode.
- Slack shows local time; `started` needs the Jira offset — use
  `scripts/timebounds.py convert`.
