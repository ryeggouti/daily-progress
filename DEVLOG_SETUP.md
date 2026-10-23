# Automatic daily activity log

No AI API, API key, paid model, or personal access token is needed. The workflow
uses GitHub's built-in GITHUB_TOKEN and standard-library Python. This public repo
uses the standard Ubuntu GitHub-hosted runner.

## Schedule and content

Runs daily at 02:23 UTC, or manually from Actions > Daily devlog > Run workflow.
Uses Africa/Casablanca calendar dates and checks the previous three completed days.
It lists your public, personally owned repositories and all existing branches,
excluding daily-progress. Only commits attributed to ryeggouti are recorded.
Each entry contains original commit titles, source links, file counts and changed-line
counts from GitHub, including binary-file commits. Titles are quoted data, not AI claims.
Merge commits are skipped to avoid repeating their underlying changes. SHA deduplication
covers shared branches and forks. Organization-owned repos, deleted branches, unpushed
work and unmatched author identities are outside this scope.

No eligible source activity means no log commit. Existing manual dates and generated
date markers are preserved; runs are serialized and only DEVLOG.md is committed.
There is no push trigger and daily-progress excludes itself, preventing recursion.
The original manual log is retained. API failures leave the log unchanged.

## Personal contribution attribution

With your authorization, automatic log commits use the author and committer identity:

- Name: ryeggouti
- Email: 242990324+ryeggouti@users.noreply.github.com

GitHub has already associated this noreply identity with your account on the setup
commit. Updates are pushed to main, the default branch of this standalone public repo.
These commits should be eligible for your personal contribution graph under GitHub's
rules, even though GITHUB_TOKEN performs the push. GitHub makes the final decision;
allow up to 24 hours for the graph to refresh.

The log commit uses its actual current timestamp in Africa/Casablanca. A summary of
yesterday's activity counts on the day the log commit is created, not retroactively.
There is no backdating, empty commit, or inactive-day placeholder. Entries explicitly
say that they are recorded automatically.

## Activation and maintenance

The workflow is ready after it is on main. Run it manually from Actions to check it;
a no-op is expected when all recent dates are already in the manual log.
If branch protection rejects the push, allow the workflow to update main or adapt it
to open pull requests. Schedules can be delayed or dropped and GitHub may disable
public-repo schedules after 60 days without repo activity. Check Actions occasionally.
Missed dates older than three days need an explicit backfill change.

If you created an OpenAI key solely for this workflow, you can revoke it and delete
the unused OPENAI_API_KEY repository secret. This workflow never reads that secret.

## Checks

Run: python3 -m unittest discover -s scripts -p 'test_*.py'

[GitHub contribution rules](https://docs.github.com/en/account-and-profile/how-tos/contribution-settings/troubleshooting-missing-contributions)
