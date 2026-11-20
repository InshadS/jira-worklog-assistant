# Evidence sources

Gather all sources for a day in parallel. Each is optional: if a tool is missing,
say "no <source> connector, skipping" and carry on.

## 1. Existing worklogs (always)

- Which issues: `searchJiraIssuesUsingJql` with
  `worklogAuthor = currentUser() AND worklogDate = "<YYYY-MM-DD>"`
  (or `>=`/`<=` for a range).
- The entries: `executeRead` → `listJiraIssueWorklogs` per issue, with
  `startedAfter` / `startedBefore` as epoch ms in the **Jira timezone**
  (`scripts/timebounds.py bounds <start> <end> --tz <jira tz>`). Filter to the
  user's own entries by author; other people log on shared tickets.
- `responseFields: ["worklogs.id","worklogs.author.displayName",
  "worklogs.timeSpent","worklogs.timeSpentSeconds","worklogs.started","worklogs.comment"]`
  keeps responses small.

## 2. Slack (primary evidence)

- `slack_search_public_and_private` with `filters: "from:<@USERID> on:YYYY-MM-DD"`,
  `sort: "timestamp"`, `sort_dir: "asc"`, `response_format: "concise"`,
  `natural_language_query: ""`. Page with `cursor` until "No more pages". A busy day
  is 3–5 pages; stopping early loses the afternoon.
- Read a thread (`slack_read_thread`, with `oldest` set to the day's start) when the
  user's message is a reply that needs context — e.g. "I'm looking into the above
  issue", "regarding point 7". Thread parents usually name the issue or ticket.
- Signals worth extracting: ticket keys (`ABC-1234`), PR links/numbers, service and
  env names (Stage/UAT/Prod), people involved, Meet links (`meet.google.com/xxx-xxxx-xxx`
  → ad-hoc call), "joining"/"on call" messages (meeting time), root-cause write-ups
  (heavy analysis time), "merged"/"deployed"/"raised a PR" (delivery work).
- Short replies ("ok", "yes", "Joining") still mark time ranges even if they carry
  little content.

## 3. Jira activity

- Tickets touched that day:
  `(assignee = currentUser() OR reporter = currentUser() OR assignee WAS currentUser()
  DURING ("<day>","<next day>")) AND updated >= "<day>" AND updated < "<next day>"`.
  Note: `updatedBy(...)` inside an OR is rejected by some sites — use the form above.
- Ticket keys found in Slack: fetch them with `key in (...)` to get summary, assignee,
  status, estimate, story points, start date, due date.

## 4. Google Calendar (if connected)

- `list_events` with `startTime: "<day>T00:00:00"`, `endTime: "<next day>T00:00:00"`,
  `orderBy: "startTime"` (no offset — the server uses the user's calendar tz).
- Attendance: organiser, `responseStatus: accepted`, or the event's
  `conferenceUrl` Meet code appears in the user's Slack that day → attended.
  `needsAction` alone is common for people who never click RSVP — treat as
  "probably attended" if it's a recurring team meeting, otherwise uncertain and
  mention it. `declined` → skip.
- Meeting durations are the most reliable time numbers you have; use them.
- Recurring stand-ups and team syncs go on the catch-all ticket unless the
  meeting is clearly about one ticket.
- `OUT_OF_OFFICE` events or all-day "Leave"/"Holiday" events mark leave days.
- An attachment titled "Notes by Gemini" (a Google Doc) can be read with the Google
  Drive connector's `read_file_content` for meeting topics. Use it only to write a
  better note; don't quote it.

## What not to use

Don't infer work from other people's messages that the user didn't take part in,
and don't read DMs between other people. The user's own messages, the threads they
replied in, and their calendar are enough.
