import unittest
from datetime import date
from unittest.mock import patch
import daily_devlog as d


class DevlogTests(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()
