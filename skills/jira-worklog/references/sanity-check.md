# Sanity check

Answer "is my timesheet for this range clean?" with numbers, then the exact fixes.
No Slack needed.

## Steps

1. Range: "last week" = previous Mon–Fri; "this week" = Mon–today. Target from the
   prompt, else 7h.
2. Worklogs: JQL `worklogAuthor = currentUser() AND worklogDate >= … AND worklogDate <= …`,
   `fields: ["summary"]`; then `listJiraIssueWorklogs` per issue with epoch bounds and
   `responseFields: ["worklogs.id","worklogs.author.accountId","worklogs.author.displayName","worklogs.timeSpentSeconds","worklogs.started"]`.
   Keep the user's entries for `worklogs`; sum others' per name for `others`.
3. Ticket fields, one call: `key in (...)`,
   `fields: ["summary","duedate","timeoriginalestimate","timespent","<storyPointsId>","<startDateId>"]`.
   Which are the user's: `key in (...) AND assignee = currentUser()`, `fields: ["summary"]`.
4. Empty weekdays: ask whether they were leave/holidays (or use calendar
   out-of-office if calendar is on). The user's answer wins. Today counts as in
   progress, not a gap.
5. Write the JSON below to a scratch file and run `python3 scripts/sanity.py <file>`.
6. Present its output, then the fixes.

### sanity.py input

```json
{"tz": "Asia/Dubai", "target_hours": 7, "range": ["2026-11-09","2026-11-13"],
 "leave": ["2026-11-09"], "today": "2026-11-13",
 "worklogs": [{"id": "10234", "issue": "ABC-77", "started": "2026-11-13T16:16:46.000+0400", "seconds": 180}],
 "issues": {"ABC-77": {"estimate_s": 288000, "timespent_s": 180, "story_points": null,
            "start": "2026-10-05", "due": "2026-10-16", "mine": true,
            "others": {"Priya": 3600}}}}
```

`worklogs` = the user's entries only; `timespent_s` = all authors, all time.
Optional: `weekend` (weekday numbers, default [5,6]), `today`, `mine`, `others`.

## Checks (done by the script)

| Check | Why |
|---|---|
| Day total vs target (working days) | First thing reviewers see |
| Logs on leave days | Contradicts leave records |
| Entry outside ticket Start–Due | Fails planned-window reviews |
| Missing estimate / story points / start / due | Breaks sprint and capacity reports |
| User's own time > estimate | Overrun to explain or re-estimate |
| Ticket total > estimate | Informational, with per-person split |
| Entry < 15m or odd start (16:16:46) | Usually an accidental timer log |
| Ticket not assigned to the user | Informational; fields belong to the assignee |

## After the report

Numbered fixes with worklog IDs (e.g. "Delete worklog 10234 (ABC-77, 3m, Nov 13) in
Jira — outside window"). Offer: re-add entries on the right ticket, fill short days
(Analyse/Backfill), set missing fields (Fix fields). Re-run when the user says
"check now".
