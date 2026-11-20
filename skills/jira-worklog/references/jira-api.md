# Jira operations used

All through the Atlassian MCP connector. Pass `cloudId` as a top-level argument on
`executeRead` / `executeWrite`, never inside `inputs`. If an operation name below is
rejected, run `discover` with a description of the goal and use the name it returns.

## Read worklogs

```
executeRead  name: listJiraIssueWorklogs
inputs: { issueIdOrKey: "ABC-1", startedAfter: <epoch ms>, startedBefore: <epoch ms> }
responseFields: ["worklogs.id","worklogs.author.displayName","worklogs.timeSpent",
                 "worklogs.timeSpentSeconds","worklogs.started","worklogs.comment"]
```

## Add a worklog

```
executeWrite name: addOrEditJiraIssueWorklog
inputs: {
  issueIdOrKey: "ABC-1",
  timeSpent: "1h 30m",
  started: "2026-11-17T08:00:00.000+0400",   # Jira profile tz offset, no colon
  comment: "One factual line about what was done"
}
```

The response returns the new worklog `id` — report it.

## Edit a worklog

Same operation with `worklogId` added. Use it to change time, start, or comment.
It cannot move a worklog to another issue.

## Delete / move

No delete operation is available. To move: add the new worklog, then ask the user
to delete the old one (give ID, ticket, date, time) in Jira, and re-check after.

## Update ticket fields (Fix-fields mode, after confirmation)

Use `editJiraIssue` with the site's field IDs (from `detect-context.md`):
- Story points: `{ "<storyPointsFieldId>": 2 }`
- Start date: `{ "<startDateFieldId>": "2026-11-13" }`
- Due date: `{ "duedate": "2026-11-18" }`
- Original estimate: `{ "timetracking": { "originalEstimate": "6h" } }`

Show the exact changes first and get a yes. Only touch tickets the user is assigned
to, unless they explicitly ask otherwise. Changing someone else's ticket dates or
estimates affects their reporting — mention that if asked to.
