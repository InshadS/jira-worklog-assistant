---
name: jira-worklog
description: Analyse what someone actually worked on (from their Slack messages, Jira activity and Google Calendar meetings) and turn it into accurate Jira worklogs, then sanity-check their timesheet. Use this whenever the user wants to fill, backfill, review or fix Jira worklogs or a Clockwork/Tempo-style timesheet: "analyse my work for nov 17", "log my hours for yesterday", "fill my timesheet gaps this week", "sanity check last week's logs", "which tickets can I log against", "move these logs to another ticket", or anything about hitting a daily hours target in Jira. Use it even when the user doesn't say "worklog" but is clearly talking about logging time on Jira tickets.
---

# Jira Worklog Assistant

Turns a person's real day (Slack messages, Jira activity, calendar meetings) into
Jira worklogs that hold up to review: each entry is on a ticket whose dates cover
it, the day adds up to the target, and nothing is written until the person says so.

Work only with the current user's own data — their messages, their meetings, their
worklogs. Never read or summarise a teammate's private conversations beyond the
threads the user took part in, and never post anything to Slack.

## Modes

Pick the mode from the request. Several can chain in one conversation.

| Mode | Typical request | Writes? |
|---|---|---|
| **Analyse day** | "analyse my work for nov 17" | No: proposes |
| **Backfill range** | "fill my gaps this week" | No: proposes |
| **Log** | "log", "add these", "log but make X 1.5h" | Yes, after explicit OK |
| **Sanity check** | "check last week's log", "sanity check" | No: reports |
| **Fix fields** | "set the missing story points" | Yes, after explicit OK |
| **Move/adjust** | "move these logs to ABC-123", "make it 2h" | Edits yes; deletes manual |

## Step 0: Detect context (every run, nothing saved)

Read `references/detect-context.md` and resolve: Atlassian cloudId, Jira accountId,
**Jira profile timezone** (worklog `started` times use it), the user's **local
timezone** (Slack and Calendar show times in it), Slack user ID, the site's
Story Points / Start date custom-field IDs, and the catch-all ticket for each date.

Settings come from the prompt when given, otherwise defaults:
- daily target **7h** ("I do 8h days" overrides)
- catch-all ticket pattern: summary contains **"Operations"**, assigned to the user,
  dates covering the day ("use ABC-900 for misc" overrides)
- leave / holidays: none assumed; ask when a weekday has no activity at all

## Step 1: Gather evidence for a day

Read `references/evidence-sources.md`. In short, collect in parallel:
1. **Existing worklogs** by the user that day (so you only fill the gap).
2. **Slack**: every message the user sent that day, all pages. Read threads when a
   message only makes sense with context ("I'm looking into the above issue").
3. **Jira**: tickets the user is assigned/reporter on that were updated that day, and
   any ticket keys mentioned in Slack.
4. **Calendar** (if the Google Calendar connector is present): events that day.
   Treat an event as attended when the user organised or accepted it, or when its
   Meet code appears in their Slack messages; RSVP "needsAction" alone is not proof
   either way. Skip declined events.

If a source is unavailable, say which and continue with the rest.

## Step 2: Build themes and match tickets

Group evidence into 3–7 work themes with time ranges in the user's local time.
Then read `references/ticket-matching.md` and assign each theme a ticket. The rules
that matter most:
- A worklog's date must fall inside the ticket's Start date–Due date window. If the
  natural ticket's window has closed (or it belongs to someone else), put the work on
  the catch-all ticket for that period and say why.
- Prefer the specific ticket the work was about; the catch-all is the fallback.
- On the catch-all, write one entry per theme rather than one big block — reviewers
  read the comments to see what the time was.
- Respect estimates: flag when a proposal would push the user's own time past the
  ticket's original estimate.

## Step 3: Propose (never write in this step)

Fill the day to the target with whole 30-minute blocks, sized by evidence weight
(meeting durations from Calendar are exact; Slack bursts are estimates). Show:

```
**Proposed <Day> <Mon DD> logs (<N>h, Jira time <±HH:MM>)**

| Start | Issue | Time | Note |
|---|---|---|---|
| 07:00 | ABC-1 | 1h | *(already logged, 12345)* |
| 08:00 | ABC-2 | 1h 30m | <what was done, concrete nouns: PR numbers, services, people> |

After: ABC-2 at 3h of 6h estimate; all inside ticket dates.
```

Before the table, give a short evidence summary per theme (times in local tz) so the
user can see why. Then ask: say **"log"** to add them, or tell me what to change.

Start times are in the **Jira profile timezone**, laid out back-to-back from the
user's working-day start, roughly following the real order of work. Notes are one
line, factual, no secrets, no customer data.

## Step 4: Log (only after explicit confirmation)

"log", "add these", "yes" to a shown proposal count as confirmation. Apply any edits
the user gave first ("ABC-105 1.5h only", "split this one", "total 3h") — the
user's numbers always beat yours; re-balance only where they asked. If an edit
changes the plan meaningfully, show the revised table before writing.

Write with the operations in `references/jira-api.md`, in parallel, then reply with
a table of created worklog IDs, the day total, and each touched ticket's
logged-vs-estimate.

## Sanity check mode

Read `references/sanity-check.md`. Pull the user's worklogs for the range, the
fields of every touched ticket, run `scripts/sanity.py`, and report per-day totals
and violations with concrete fixes. Ask about leave/holidays for empty weekdays
rather than flagging them as gaps.

## Things the API can't do

Worklogs cannot be deleted through these tools. When an entry must go, give the
exact worklog ID, ticket and time, ask the user to delete it in Jira, and offer to
re-check afterwards. To "move" a worklog: create the new one, then have the user
delete the old one.

## Watch for

- **Secrets in evidence**: if a Slack message the user sent contains credentials
  (API keys, `secret-key`, tokens, passwords), tell them once, plainly, and suggest
  removing the message and rotating the secret. Never copy secrets into worklogs.
- **Logs on leave days** or after a ticket's due date: flag them in any mode.
- **Timezone slips**: Slack shows local time; Jira `started` needs the Jira profile
  offset. `scripts/timebounds.py` converts and gives epoch-ms bounds for queries.
