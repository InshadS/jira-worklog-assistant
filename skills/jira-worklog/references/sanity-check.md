# Sanity check

Answer "is my timesheet for this range clean?" with numbers, then list exactly what
to fix.

## Steps

1. Resolve the range ("last week" = previous Mon–Fri; "this week" = current Mon–today)
   and the target hours/day.
2. Get the user's worklogs: JQL `worklogAuthor = currentUser() AND worklogDate >= … AND
   worklogDate <= …` for the issue list, then `listJiraIssueWorklogs` per issue with
   epoch bounds; keep only the user's entries.
3. Get fields for every touched issue in one JQL with `view: "evidence"` (or explicit
   field IDs): original estimate, time spent (all authors), story points, start date,
   due date, assignee. Large results may be saved to a file — use `jq`.
4. Ask about leave/holidays for weekdays with no logs before calling them gaps
   (or, if calendar is turned on, use its out-of-office events). The user's answer wins.
5. Write the input JSON and run `scripts/sanity.py` (schema in the script's
   docstring). It prints the report tables and a list of issues.
6. Present the report, then the fixes.

## Checks

| Check | Why it matters |
|---|---|
| Day total vs target (working days only) | Under/over-logging is what reviewers notice first |
| Logs on leave days | Contradicts leave records |
| Entry date outside ticket Start–Due | Fails "work within the planned window" reviews |
| Ticket missing estimate / story points / start / due | Breaks sprint & capacity reports |
| User's own time on a ticket > original estimate | Overrun the user should explain or re-estimate |
| Ticket total (all authors) > estimate | Informational: note whose time drove it |
| Very small entries (< 15m) or odd starts (e.g. 16:16:46) | Usually accidental timer logs; ask |

## Report format

```
**<Range> <is clean | needs N fixes>**

| Day | Logged | vs 7h |
|---|---|---|
| Mon Nov 9 | — | leave |
| Wed Nov 11 | 7h | ✅ |
| Fri Nov 13 | 8h 43m | 🔴 +1h 43m |

| Ticket | Estimate | SP | Start | Due | Your entries in window? |
|---|---|---|---|---|---|

**Fix**
1. Delete worklog 10234 (ABC-77, 3m, Nov 13) in Jira — outside window, and the day is over.
2. ...
```

End by offering what you can do: re-add entries on the right ticket, fill short
days (Analyse/Backfill mode), or set missing fields (Fix-fields mode). After the
user fixes things manually, re-run the check when they say "check now".
