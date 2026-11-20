# Detecting context

Everything here is re-detected each run; nothing is stored. Do the lookups in
parallel where they don't depend on each other, and only ask the user for what
can't be found.

## Atlassian site (cloudId)

Call `getAccessibleAtlassianResources`. One Jira site → use it. Several → pick the
one the user named or the one whose URL appears in their Slack messages
(`<site>.atlassian.net/browse/...`); if still ambiguous, ask once.

## Jira identity and timezone

- `atlassianUserInfo` gives the accountId.
- The **Jira profile timezone** is what worklog `started` offsets must use. Read it
  from any issue assigned to the user: the `assignee.timeZone` field (e.g.
  `Asia/Dubai`). A quick way:
  `searchJiraIssuesUsingJql` with `assignee = currentUser() ORDER BY updated DESC`,
  `maxResults: 1`, `fields: ["assignee"]`.
- If nothing is assigned, use `discover` to find the "get current user / myself"
  operation and read `timeZone` there.

## The user's local timezone

Slack search results print times in the user's local zone (e.g. `10:35:25 IST`).
Map the abbreviation to an IANA name (IST → Asia/Kolkata, GST → Asia/Dubai, etc.).
If calendar is turned on, its `list_events` response also has a top-level
`timeZone` you can use to confirm. If it's ambiguous or missing, ask.

Local and Jira zones often differ (e.g. Asia/Kolkata vs Asia/Dubai, 1h30m apart).
Convert with:

```bash
python3 scripts/timebounds.py convert "2026-11-17 10:35" --from Asia/Kolkata --to Asia/Dubai
```

## Slack user ID

The Slack search tool's own description states the logged-in user's ID
("Current logged in user's user_id is U…"). Use `from:<@U…>` in filters.

## Custom-field IDs (differ per site)

Run one `searchJiraIssuesUsingJql` with `view: "evidence"` on a recent issue of the
user's and read `fields.customFields`: each entry has a human label and an `id`.
Look for labels **Story Points** (sometimes "Story point estimate") and
**Start date**. Original estimate is the standard `timeoriginalestimate` (seconds),
due date is `duedate`.

Evidence-view results can be large. If a result is saved to a file instead of
returned, extract with `jq`, e.g.:

```bash
jq -r '.issues.nodes[] | [.key, .fields.timeoriginalestimate, .fields.duedate,
  (.fields.customFields|to_entries|map(select(.key|test("Start date|Story";"i"))
  |"\(.key)=\(.value.value)")|join(";"))] | @tsv' <file>
```

## Catch-all ("Operations") ticket for a date

Many teams keep a rolling ticket per sprint for support/ops/analysis time
(e.g. "Operations Nov 16 - Nov 27 Tech Analysis"). Find the one covering a date:

```
assignee = currentUser() AND summary ~ "Operations"
AND "Start date" <= "<date>" AND duedate >= "<date>"
```

If the JQL rejects the Start date clause on this site, drop it and filter by
the returned fields instead. If the user named another pattern or ticket, use that.
If none covers the date, say so and ask which ticket to use — don't stretch an old
one past its due date.
