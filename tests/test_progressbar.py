import unittest
import time
import io
import sys

import progressbar

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

if __name__ == '__main__':
    unittest.main()
