# Detecting context

Do this once per conversation and reuse the results. Run independent lookups in
parallel; ask the user only for what can't be found.

| Need | Call | Keep |
|---|---|---|
| Site | `getAccessibleAtlassianResources` | cloudId (several sites → the one the user named or that appears in their Slack links; else ask) |
| Account + Jira timezone | `executeRead` `getJiraCurrentUser`, `responseFields: ["accountId","timeZone"]` | accountId, Jira tz (e.g. Asia/Dubai) — worklog `started` uses this |
| Slack user ID | none — the Slack search tool's description states it ("user_id is U…") | `from:<@U…>` |
| Local timezone | First Slack result's timestamp suffix (`10:35:25 IST`) → IANA (IST → Asia/Kolkata, GST → Asia/Dubai). With calendar on, `list_events` returns `timeZone` too | local tz; ask if ambiguous |
| Field IDs + catch-all | one call, below | Story Points id, Start date id, catch-all key + dates |

## Field IDs and the catch-all ticket (one call)

Custom-field IDs differ per site. Find them with a single evidence-view search on
the catch-all ticket, which also gives you that ticket:

```
searchJiraIssuesUsingJql
  jql: assignee = currentUser() AND summary ~ "Operations" ORDER BY created DESC
  view: "evidence", maxResults: 1
```

Read `fields.customFields`: labels **Story Points** (or "Story point estimate") and
**Start date**, each with an `id`. From then on, request those IDs explicitly in
`fields` — never use the evidence view again in this conversation.

If the newest Operations ticket doesn't cover the dates you need, find the right
one cheaply:

```
jql: assignee = currentUser() AND summary ~ "Operations" ORDER BY created DESC
fields: ["summary","duedate","<startDateId>"], maxResults: 5
```

and pick the one whose Start–Due covers the date. If the user named another
pattern or ticket, use that. If none covers the date, say so and ask — don't
stretch an old ticket past its due date.

If the result is saved to a file instead of returned, run
`python3 scripts/compact.py <file>`.

## Timezone conversion

```bash
python3 scripts/timebounds.py convert "2026-11-17 10:35" --from Asia/Kolkata --to Asia/Dubai
python3 scripts/timebounds.py bounds 2026-11-16 2026-11-20 --tz Asia/Dubai   # epoch ms for worklog queries
```
