# Automated daily devlog

## Activate

1. Create a dedicated OpenAI project API key at https://platform.openai.com/api-keys.
   Enable API billing as needed; a ChatGPT subscription does not supply API credit.
   Restrict the key to response creation where available, set a small project budget
   alert, and disable automatic credit recharge if you want tighter spending control.
   Budget alerts are not a guaranteed hard spending cap.
2. Open https://github.com/ryeggouti/daily-progress/settings/secrets/actions and add
   a **repository secret** named `OPENAI_API_KEY`. Paste the key only into GitHub's
   secret value field. Never send it in chat or commit it. Rotate it if exposed.
3. In Actions, select **Daily devlog**, then **Run workflow** on `main`.
   The run summarizes completed days only. No eligible changes means a successful
   no-op, and no AI request. A date already present in the manual log is preserved.
4. Confirm the run succeeds and inspect the resulting DEVLOG.md diff and source links.
   If branch rules reject the bot push, explicitly allow this workflow to update main
   or adapt it to open pull requests. No personal access token is needed.

## Behavior and scope

- Runs at 02:23 UTC (02:23 or 03:23 Casablanca, depending on the seasonal offset).
  Date windows use `Africa/Casablanca`, including Ramadan offset changes.
- Checks the preceding three completed local days. Older missed days need an explicit
  code change/backfill. Schedules can be delayed or dropped; GitHub may disable public
  repo schedules after 60 days without repository activity. Check Actions occasionally.
- Lists public repositories owned by `ryeggouti`, including forks; excludes daily-progress.
  Reads all currently existing branches, filters commits attributed to `ryeggouti`,
  and assigns dates by commit committer timestamp. Deduplicates SHAs across branches
  and forks. Organization-owned repos, deleted branches, unpushed work, unmatched
  author identities, merge-only changes and binary-only changes are outside this scope.
- Reads actual patches, not commit-message claims. Sends only public diff data to OpenAI.
  Source links are constructed by code from GitHub results, never invented by the model.
  AI summaries can still be mistaken; follow their links to verify them.
- Keeps manual entries, skips existing date headings, adds a persistent date marker,
  serializes runs, and commits only DEVLOG.md as github-actions[bot]. No push trigger,
  no execution of fetched repository code, no personal token, and pinned checkout action.
- Uses gpt-4o-mini, at most one AI request per active unlogged date (three per run),
  a 48,000-character patch budget and 1,100 output-token cap. Each file patch is bounded.
  Large/binary files may be omitted and are disclosed in each entry. More than 40
  eligible commits fails for review rather than silently generating a partial day.
  Failures leave the log unchanged; a push conflict fails safely and a rerun recollects.

## Contribution squares

The devlog bot is credited as `github-actions[bot]`, so these commits should not be
expected to add squares to your personal graph. Your actual source-code commits
are what matter: use an email connected to your account and get eligible commits
onto the default branch (or gh-pages). Fork and other GitHub contribution rules apply.
This workflow does not impersonate your identity or manufacture inactive-day commits.

## Verification

Run `python3 -m unittest discover -s scripts -p 'test_*.py'`.
This checks local-day windows, preservation of manual dates, self-exclusion,
pagination and no-activity behavior without any API key or paid API calls.

References: [OpenAI model](https://developers.openai.com/api/docs/models/gpt-4o-mini),
[structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs),
[GitHub scheduling](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule),
[contributions](https://docs.github.com/en/account-and-profile/how-tos/contribution-settings/troubleshooting-missing-contributions).
