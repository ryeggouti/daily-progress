"""Deterministic activity log; GitHub API only, no paid AI service."""
import html
import json
import os
import re
import urllib.parse
import urllib.request
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

OWNER = 'ryeggouti'
SELF = f'{OWNER}/daily-progress'
TZ = ZoneInfo('Africa/Casablanca')
LOG = Path('DEVLOG.md')


def request(url, token):
    headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/vnd.github+json',
               'Content-Type': 'application/json', 'User-Agent': 'daily-progress-devlog'}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=90) as response:
        return json.load(response)


def gh(path, **params):
    url = 'https://api.github.com/' + path
    if params:
        url += '?' + urllib.parse.urlencode(params)
    return request(url, os.environ['GH_TOKEN'])


def pages(path, **params):
    result = []
    for page in range(1, 101):
        batch = gh(path, per_page=100, page=page, **params)
        result.extend(batch)
        if len(batch) < 100:
            return result
    raise RuntimeError('Pagination limit reached; refusing a partial summary')


def bounds(day):
    # Construct each local midnight separately: Casablanca changes offset in Ramadan.
    start = datetime.combine(day, time.min, TZ).astimezone(timezone.utc)
    end = datetime.combine(day + timedelta(days=1), time.min, TZ).astimezone(timezone.utc)
    return start, end


def exists(text, day):
    human = f'{day:%B} {day.day}, {day.year}'
    return (f'<!-- devlog:{day} -->' in text or
            bool(re.search(r'^#{2,3}\s+(?:' + re.escape(str(day)) + '|' +
                           re.escape(human) + r')\s*$', text, re.M)))


def collect(repos, day):
    start, end = bounds(day)
    found = {}
    for repo in repos:
        name = repo['full_name']
        if name.lower() == SELF or repo['private'] or not repo['size']:
            continue
        # All extant branches, not just the default branch. Deduplicate shared SHAs.
        for branch in pages(f'repos/{name}/branches'):
            commits = pages(f'repos/{name}/commits', sha=branch['name'], author=OWNER,
                            since=start.isoformat(), until=end.isoformat())
            for commit in commits:
                author = commit.get('author') or {}
                stamp = datetime.fromisoformat(commit['commit']['committer']['date'].replace('Z', '+00:00'))
                if author.get('login', '').lower() != OWNER or not start <= stamp < end:
                    continue
                key = commit['sha'] # Same commit in multiple forks is one change.
                if key in found:
                    continue
                detail = gh(f'repos/{name}/commits/{key}')
                if len(detail['parents']) > 1:
                    continue # Merge diffs duplicate the underlying work.
                files = detail.get('files', [])
                if not files:
                    continue
                found[key] = {'repo': name, 'sha': key,
                              'title': commit['commit']['message'].splitlines()[0],
                              'files': len(files), 'partial': len(files) >= 300,
                              'additions': detail['stats']['additions'],
                              'deletions': detail['stats']['deletions']}
    return sorted(found.values(), key=lambda c: (c['repo'], c['sha']))


def summarize(commits):
    lines = []
    for commit in commits:
        # Escape untrusted commit messages as literal Markdown text.
        title = html.escape(' '.join(commit['title'].split())[:240], quote=False)
        title = re.sub(r'([\\`*_{}\[\]()#+.!|~-])', r'\\\1', title)
        url = f"https://github.com/{commit['repo']}/commit/{commit['sha']}"
        count = str(commit['files']) + ('+' if commit['partial'] else '')
        lines.append(f"- [{commit['repo']}@{commit['sha'][:7]}]({url}): {title} "
                     f"({count} files; +{commit['additions']}/-{commit['deletions']} lines)")
    return '\n'.join(lines)


def main():
    today = datetime.now(TZ).date()
    text = LOG.read_text(encoding='utf-8') if LOG.exists() else '# Development Log\n'
    days = [today - timedelta(days=n) for n in (3, 2, 1)]
    days = [day for day in days if not exists(text, day)]
    if not days:
        print('All recent dates already logged.')
        return
    repos = pages(f'users/{OWNER}/repos', type='owner', sort='full_name')
    entries = []
    for day in days:
        commits = collect(repos, day)
        if not commits:
            print(f'{day}: no eligible changes; skipped.')
            continue
        summary = summarize(commits)
        note = '\n\n_Automatically recorded from GitHub commits; titles are original commit messages._'
        entries.insert(0, f'<!-- devlog:{day} -->\n### {day}\n\n{summary}{note}\n\n')
    if entries:
        # Preserve the manual log verbatim beneath the generated entries.
        LOG.write_text(''.join(entries) + text, encoding='utf-8')
        print(f'Prepared {len(entries)} entries.')


if __name__ == '__main__':
    main()
