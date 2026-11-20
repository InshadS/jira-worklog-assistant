# jira-worklog-assistant

A [Claude Code](https://claude.com/claude-code) plugin that turns what you actually
did — your Slack messages and Jira activity (optionally your Google Calendar) — into Jira
worklogs, and checks your timesheet for gaps and mistakes.

Works with native Jira worklogs, so it fits tools that read them (Clockwork, Tempo
reports, Jira's own time tracking).

> **Nothing is written to Jira until you say "log".** Every run starts with a
> proposal you can edit.

## What you can ask

| Ask | What happens |
|---|---|
| `analyse my work for nov 17` | Reads your Slack and Jira activity for the day, groups the work into themes, and proposes worklogs that fill the day to your target |
| `fill my gaps this week` | Finds short days and proposes entries for each |
| `log` · `log but make ABC-123 1.5h` · `split the ops entry` | Writes the proposed worklogs, applying your edits first, and reports the new worklog IDs |
| `sanity check last week` | Per-day totals vs target, entries outside ticket dates, missing estimate / story points / dates, over-estimate tickets, accidental timer entries |
| `set the missing story points` | Updates ticket fields after you confirm |
| `move these logs to ABC-200` | Re-creates the entries on the new ticket and tells you which old ones to delete |

### Example

```
you:    analyse my work for nov 19
claude: You have no worklogs on Thu Nov 19 (0h of 7h).
        Evidence by theme (your local time): meetings, prod support, scoping, PR reviews …

        Proposed Thu Nov 19 logs (7h, Jira time +04:00)
        | Start | Issue  | Time   | Note                                   |
        |-------|--------|--------|----------------------------------------|
        | 08:30 | ABC-60 | 30m    | Team sync                              |
        | 09:00 | ABC-60 | 1h     | Prod support: stuck transactions …     |
        | …     | …      | …      | …                                      |
        After: ABC-60 at 14h of 80h estimate; all inside ticket dates.
        Say "log" to add these, or tell me what to change.
you:    log, but make the prod support 1.5h and the review block 1h
```

## How it decides

- **Fills only the gap.** Existing worklogs for the day count toward the target.
- **Respects ticket dates.** An entry only goes on a ticket whose Start date … Due
  date covers that day. If the natural ticket has closed (or hasn't started), the
  work goes on your catch-all ticket for the period and it tells you why.
- **Catch-all ticket.** Many teams keep a rolling "Operations …" ticket per sprint
  for support, triage and analysis. The skill finds the one assigned to you that
  covers the date, and splits time on it into one entry per theme with concrete
  notes (PR numbers, services, issue keys).
- **Your numbers win.** If you say "1.5h only", it uses 1.5h.
- **Calendar is off by default.** Calls and meetings are picked up from Slack
  ("joining", Meet links, "on call with …"). Say "include my calendar" to also use
  Google Calendar: events then give exact durations and out-of-office days, and a
  meeting counts as attended if you organised or accepted it, or its Meet link
  appears in your Slack that day. It stays on for that conversation.
- **Timezones.** Reads evidence in your local timezone; writes worklog start times
  in your Jira profile timezone.
- **Can't delete.** The Jira connector has no delete-worklog operation, so the skill
  lists exact worklog IDs for you to delete in Jira, then re-checks.
- **Privacy.** Uses only your own messages, the threads you took part in, your
  worklogs, and your calendar only if you turn it on. It never posts to Slack. If it notices credentials in
  a message you sent, it tells you so you can remove it and rotate the secret.

## Prerequisites

Connect these in **claude.ai → Settings → Connectors** (Claude Code picks them up):

| Connector | |
|---|---|
| Atlassian (Jira) | Required |
| Slack | Required — main evidence source |
| Google Calendar | Optional, off by default — say "include my calendar" to use it |
| Google Drive | Optional — with calendar on, reads Gemini meeting notes attached to events |

Also: Python 3.9+ (for the helper scripts).

## Install

In Claude Code:

```
/plugin marketplace add InshadS/jira-worklog-assistant
/plugin install jira-worklog-assistant@jira-worklog-assistant
```

Restart Claude Code, then just ask — e.g. `analyse my work for yesterday`.

To update later: `/plugin marketplace update jira-worklog-assistant`.

## Settings

Detected on every run; nothing to configure. Override in your prompt when needed:

| Setting | Default | Override example |
|---|---|---|
| Daily target | 7h | "I work 8h days" |
| Catch-all ticket | Assigned to you, summary contains "Operations", dates cover the day | "use ABC-900 for misc work" |
| Leave / holidays | Asks when a weekday has no activity |
| Calendar | Off | "include my calendar" / "use my meetings" | "16 and 18 were leave" |
| Jira site | The only one you can access, or asks | "use the acme site" |

## Repository layout

```
.claude-plugin/
  plugin.json              plugin manifest
  marketplace.json         lets this repo be added as a plugin marketplace
skills/jira-worklog/
  SKILL.md                 workflow, modes and rules
  references/
    detect-context.md      site, identity, timezones, field IDs, catch-all ticket
    evidence-sources.md    Slack, Jira (and opt-in Calendar): what to query and how
    ticket-matching.md     theme → ticket rules, splitting, sizing
    jira-api.md            worklog and field operations
    sanity-check.md        checks and report format
  scripts/
    timebounds.py          epoch-ms bounds and timezone conversion
    sanity.py              timesheet check report from worklog + ticket JSON
```

The helper scripts work standalone:

```bash
python3 skills/jira-worklog/scripts/timebounds.py bounds 2026-11-16 2026-11-20 --tz Asia/Dubai
python3 skills/jira-worklog/scripts/timebounds.py convert "2026-11-17 10:35" --from Asia/Kolkata --to Asia/Dubai
python3 skills/jira-worklog/scripts/sanity.py input.json   # schema in the script's docstring
```

## Status and roadmap

v0.2 — calendar is now opt-in (off by default). v0.1 was tested against a real Jira/Slack/Calendar setup: analyse a day, backfill,
weekly sanity check, and the "never write without confirmation" guard.

Planned:
- Per-author breakdown on over-estimate tickets in the sanity report
- Show "today" as in progress instead of short
- GitHub PRs / commits as an evidence source

Issues and pull requests welcome.
