# Matching work to tickets

The goal is a timesheet a manager can audit: every entry sits on a ticket that was
open for that date, says concretely what was done, and the ticket totals look
plausible against their estimates.

## Order of preference for each theme

1. **The specific ticket the work was about**, if all hold:
   - the worklog date is within its Start date … Due date (inclusive)
   - it's assigned to the user, or the user is clearly a contributor on it
     (named in comments/thread, raised the PR, did the RCA)
   - it has an original estimate and story points (if not, still use it but flag
     the missing fields and offer Fix-fields mode)
2. **The catch-all ticket** covering that date (see `detect-context.md`) when:
   - the specific ticket's window has closed (due date passed) or not started yet
   - the ticket belongs to someone else and the user only advised/reviewed/triaged
   - the work was general: stand-ups, triage, unblock-a-teammate, cross-team
     questions, reviews, ops support, analysis without a ticket
3. **Ask** when neither fits — e.g. no catch-all covers the date. Don't stretch a
   ticket past its due date to make it fit.

When you use the catch-all for something that has its own ticket, say so in one
line ("ABC-41 ended Nov 12, so today's follow-up on that issue goes on the Operations ticket ABC-60").

## Splitting

- One entry per theme on the catch-all, 30m–2h each, with a note that names the
  concrete things (PR numbers, services, issue keys, people). Reviewers read these.
- A specific ticket with a long stretch of focused work can take one bigger entry
  (e.g. 5h RCA + fix), plus a separate entry for a distinct phase like release prep.
- If the user asks to split or merge, do exactly that.

## Sizing

- Fill the gap between existing logs and the daily target; never re-log time that's
  already there.
- Calendar meetings: their real duration.
- Slack: estimate from the span of related messages, how deep the work was (an RCA
  write-up or a PR = more; a one-line redirect = little), and the gaps between bursts.
- Round to 30m. The day must sum exactly to the target.
- If a proposal would push the user's own logged time past a ticket's original
  estimate, flag it and offer an alternative (catch-all, or ask to raise the estimate).

## Estimates and windows to report after a proposal or log

For each touched ticket: logged (including the new entries) vs original estimate,
and whether all the user's entries are inside its dates. Mention when *other*
people's logs have pushed a ticket over estimate, but don't treat that as the
user's problem.
