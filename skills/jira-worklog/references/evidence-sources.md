# Evidence sources

Gather in parallel. Each source is optional — if a tool is missing, say so and
continue. Field lists below are deliberately short: extra fields (assignee objects,
avatars, descriptions) are the main source of wasted tokens.

## 1. Existing worklogs (always)

- Which issues: `searchJiraIssuesUsingJql`,
  `worklogAuthor = currentUser() AND worklogDate = "<YYYY-MM-DD>"` (or `>=`/`<=`),
  `fields: ["summary"]`. No issues → nothing logged; skip step 2.
- Entries: `executeRead` `listJiraIssueWorklogs` per issue, with `startedAfter` /
  `startedBefore` from `scripts/timebounds.py bounds … --tz <Jira tz>` and
  `responseFields: ["worklogs.id","worklogs.author.accountId","worklogs.timeSpentSeconds","worklogs.started"]`.
  Keep only entries whose author is the user. Add `worklogs.comment` only when you
  need to show what an existing entry was.

## 2. Slack (primary)

- `slack_search_public_and_private`: `filters: "from:<@USERID> on:YYYY-MM-DD"`,
  `sort: "timestamp"`, `sort_dir: "asc"`, `response_format: "concise"`,
  `include_context: false`, `natural_language_query: ""`. Page with `cursor` until
  "No more pages" — a busy day is 2–5 pages; stopping early loses the afternoon.
- Don't re-run the same search in detailed format. If one message needs context
  ("looking into the above issue", "regarding point 7"), read that thread with
  `slack_read_thread` (`oldest` = day start, `limit: 30`, `response_format:
  "concise"`). Budget about 3 thread reads a day; prefer the ones behind the biggest
  bursts of activity.
- Signals: ticket keys, PR numbers, service/env names, people, Meet links and
  "joining"/"on call" (meeting time), RCA write-ups (deep work), "merged"/"deployed"
  (delivery). Short replies still mark time ranges.

## 3. Jira tickets

- Touched that day:
  `(assignee = currentUser() OR reporter = currentUser()) AND updated >= "<day>" AND updated < "<next day>"`
  (`updatedBy()` inside OR fails on some sites).
- Keys from Slack plus the above, in one call: `key in (...)` with
  `fields: ["summary","status","duedate","timeoriginalestimate","timespent","<storyPointsId>","<startDateId>"]`.
- Whose ticket: one more cheap call, `key in (...) AND assignee = currentUser()`,
  `fields: ["summary"]` — the keys it returns are the user's. Don't request the
  `assignee` field; its avatar URLs are large.

## 4. Google Calendar (opt-in, off by default)

Only when the user asked to include their calendar in this conversation; otherwise
skip entirely and rely on Slack call/meeting signals.

- `list_events`, `startTime: "<day>T00:00:00"`, `endTime: "<next day>T00:00:00"`,
  `orderBy: "startTime"`, `pageSize: 50` (no offset; server uses the calendar tz).
  Use only summary, start, end, organizer/self responseStatus, conferenceUrl,
  eventType, attachments — ignore the rest.
- Attended: organiser, `accepted`, or its Meet code appears in the user's Slack
  that day. `needsAction` alone: recurring team meeting → probably attended (say
  so once); otherwise uncertain. `declined` → skip.
- Meeting durations are exact; recurring stand-ups/syncs go on the catch-all unless
  clearly about one ticket. `OUT_OF_OFFICE` or all-day "Leave"/"Holiday" → leave.
- A "Notes by Gemini" attachment can be read with Google Drive `read_file_content`
  to improve a note; don't quote it.

## Not used

Other people's messages the user didn't take part in, and DMs between others.
