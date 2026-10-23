import unittest
from datetime import date
from unittest.mock import patch
import daily_devlog as d
import os
import tempfile
from pathlib import Path


class DevlogTests(unittest.TestCase):
    def test_today_snapshot_preserves_manual_log_and_is_idempotent(self):
        today = d.datetime.now(d.TZ).date()
        manual = f'# Development Log\n\n### {today:%B} {today.day}, {today.year}\nManual notes.\n'
        with tempfile.TemporaryDirectory() as directory:
            log = Path(directory) / 'DEVLOG.md'
            log.write_text(manual)
            with patch.object(d, 'LOG', log), patch.dict(os.environ, {'INCLUDE_TODAY': 'true'}), \
                 patch.object(d, 'pages', return_value=[]), \
                 patch.object(d, 'collect', side_effect=lambda repos, day: [{}] if day == today else []), \
                 patch.object(d, 'summarize', return_value='- A real source commit.'):
                d.main()
                first = log.read_text()
                self.assertIn(f'<!-- devlog-snapshot:{today} -->', first)
                self.assertTrue(first.endswith(manual))
                d.main()
                self.assertEqual(log.read_text(), first)

    def test_casablanca_offset_and_ramadan(self):
        # Use installed IANA rules rather than assuming future government policy.
        for day in (date(2026, 2, 15), date(2026, 3, 22), date(2026, 10, 23)):
            start, end = d.bounds(day)
            self.assertEqual(start.astimezone(d.TZ).date(), day)
            self.assertEqual(start.astimezone(d.TZ).hour, 0)
            self.assertIn((end - start).total_seconds() / 3600, (23, 24, 25))

    def test_preserve_manual_dates_and_markers(self):
        day = date(2026, 10, 23)
        for text in ('### October 23, 2026\n', '### 2026-10-23\n',
                     '<!-- devlog:2026-10-23 -->'):
            self.assertTrue(d.exists(text, day))
        self.assertFalse(d.exists('### 2026-10-22\n', day))

    def test_self_repo_never_queried(self):
        with patch.object(d, 'pages', side_effect=AssertionError('must not query')):
            self.assertEqual(d.collect([{'full_name': d.SELF, 'private': False,
                                         'size': 1}], date(2026, 10, 23)), [])

    def test_pagination(self):
        with patch.object(d, 'gh', side_effect=[[{}] * 100, [{'last': True}]]) as gh:
            self.assertEqual(len(d.pages('test')), 101)
            self.assertEqual(gh.call_args.kwargs['page'], 2)

    def test_no_activity_never_calls_ai(self):
        with patch.object(d, 'exists', return_value=False), \
             patch.object(d, 'pages', return_value=[]), \
             patch.object(d, 'summarize', side_effect=AssertionError('no AI')), \
             patch.object(d.LOG.__class__, 'write_text', side_effect=AssertionError('no write')):
            d.main()

    def test_commit_log_escapes_titles_and_links_sources(self):
        entry = {'repo': 'ryeggouti/example', 'sha': 'a' * 40,
                 'title': '<script> [bad](https://example.org)\nline',
                 'files': 3, 'partial': False, 'additions': 12, 'deletions': 4}
        text = d.summarize([entry])
        self.assertIn('https://github.com/ryeggouti/example/commit/' + 'a' * 40, text)
        self.assertIn('(3 files; +12/-4 lines)', text)
        self.assertNotIn('<script>', text)
        self.assertNotIn('[bad]', text)
        self.assertNotIn('\n', text)

    def test_author_filter_boundaries_and_shared_branches(self):
        day = date(2026, 10, 23)
        start, end = d.bounds(day)
        def commit(sha, login, stamp):
            return {'sha': sha, 'author': {'login': login}, 'commit': {
                'committer': {'date': stamp.isoformat()}, 'message': 'Add feature'}}
        commits = [commit('a' * 40, d.OWNER, start),
                   commit('b' * 40, 'someone-else', start),
                   commit('c' * 40, d.OWNER, end)]
        def fake_pages(path, **kwargs):
            return [{'name': 'main'}, {'name': 'feature'}] if path.endswith('/branches') else commits
        detail = {'parents': [{}], 'files': [{'filename': 'image.png'}],
                  'stats': {'additions': 0, 'deletions': 0}}
        with patch.object(d, 'pages', side_effect=fake_pages), \
             patch.object(d, 'gh', return_value=detail) as gh:
            result = d.collect([{'full_name': 'ryeggouti/example', 'private': False,
                                 'size': 1}], day)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['sha'], 'a' * 40)
        self.assertEqual(gh.call_count, 1)


if __name__ == '__main__':
    unittest.main()
