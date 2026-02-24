import unittest
import time
import io
import sys
import os

import progressbar
from progressbar import widgets as progress_widgets

class TestProgressBar(unittest.TestCase):
    def test_initialization(self):
        pbar = progressbar.ProgressBar(maxval=10)
        self.assertEqual(pbar.maxval, 10)

    def test_start(self):
        pbar = progressbar.ProgressBar(maxval=10).start()
        self.assertIsNotNone(pbar.start_time)
        pbar.finish()

    def test_update(self):
        pbar = progressbar.ProgressBar(maxval=10).start()
        pbar.update(5)
        self.assertEqual(pbar.currval, 5)
        pbar.finish()

    def test_finish(self):
        pbar = progressbar.ProgressBar(maxval=10).start()
        pbar.finish()
        self.assertTrue(pbar.finished)

    def test_iterator(self):
        pbar = progressbar.ProgressBar()
        for i in pbar(range(10)):
            pass
        self.assertEqual(i, 9)
        self.assertEqual(pbar.currval, 10)
        self.assertTrue(pbar.finished)

    def test_unknown_length(self):
        fd = io.StringIO()
        pbar = progressbar.ProgressBar(fd=fd)
        for i in pbar((i for i in range(10))):
            pass
        self.assertTrue(pbar.finished)
        output = fd.getvalue()
        self.assertIn('nan%', output)

    def test_error_value_out_of_range(self):
        pbar = progressbar.ProgressBar(maxval=10).start()
        with self.assertRaises(ValueError):
            pbar.update(11)
        pbar.finish()

    def test_error_update_before_start(self):
        pbar = progressbar.ProgressBar(maxval=10)
        with self.assertRaises(RuntimeError):
            pbar.update(1)

    def test_term_width_is_capped(self):
        pbar = progressbar.ProgressBar(maxval=1, term_width=10 ** 6)
        self.assertEqual(pbar.term_width, pbar._MAX_TERMSIZE)

    def test_env_term_width_is_capped(self):
        previous_columns = os.environ.get('COLUMNS')
        os.environ['COLUMNS'] = '1000000'
        try:
            pbar = progressbar.ProgressBar(maxval=1, fd=io.StringIO())
            self.assertEqual(pbar.term_width, pbar._MAX_TERMSIZE)
        finally:
            if previous_columns is None:
                del os.environ['COLUMNS']
            else:
                os.environ['COLUMNS'] = previous_columns

    def test_maxval_too_large_raises(self):
        with self.assertRaises(ValueError):
            progressbar.ProgressBar(maxval=10 ** 100)

    def test_huge_widget_output_is_limited(self):
        class HugeWidget(object):
            def update(self, pbar):
                return 'x' * 100000

        pbar = progressbar.ProgressBar(widgets=[HugeWidget()], maxval=1)
        self.assertEqual(len(pbar._format_widgets()[0]), progress_widgets._MAX_UPDATABLE_LENGTH)

if __name__ == '__main__':
    unittest.main()
