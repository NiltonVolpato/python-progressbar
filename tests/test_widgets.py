import unittest
import time
import io

from progressbar import ProgressBar, widgets

class TestWidgets(unittest.TestCase):
    def test_timer_widget(self):
        pbar = ProgressBar(widgets=[widgets.Timer()])
        pbar.start()
        time.sleep(0.01)
        pbar.update(1)
        # We can't know the exact time, so we just check if it's a string
        self.assertIsInstance(pbar._format_line(), str)
        pbar.finish()

    def test_eta_widget(self):
        pbar = ProgressBar(widgets=[widgets.ETA()], maxval=2)
        pbar.start()
        pbar.update(1)
        # We can't know the exact time, so we just check if it's a string
        self.assertIsInstance(pbar._format_line(), str)
        pbar.finish()

    def test_adaptive_eta_widget(self):
        pbar = ProgressBar(widgets=[widgets.AdaptiveETA()], maxval=2)
        pbar.start()
        pbar.update(1)
        # We can't know the exact time, so we just check if it's a string
        self.assertIsInstance(pbar._format_line(), str)
        pbar.finish()

    def test_file_transfer_speed_widget(self):
        pbar = ProgressBar(widgets=[widgets.FileTransferSpeed()], maxval=2)
        pbar.start()
        pbar.update(1)
        self.assertIn('B/s', pbar._format_line())
        pbar.finish()

    def test_animated_marker_widget(self):
        fd = io.StringIO()
        pbar = ProgressBar(widgets=[widgets.AnimatedMarker()], maxval=2, fd=fd)
        pbar.start()
        self.assertIn('|', fd.getvalue().split('\r')[-2])
        pbar.update(1)
        self.assertIn('/', fd.getvalue().split('\r')[-2])
        pbar.finish()
        self.assertIn('|', fd.getvalue().split('\r')[-2])

    def test_counter_widget(self):
        pbar = ProgressBar(widgets=[widgets.Counter()], maxval=2)
        pbar.start()
        pbar.update(1)
        self.assertIn('1', pbar._format_line())
        pbar.finish()

    def test_percentage_widget(self):
        pbar = ProgressBar(widgets=[widgets.Percentage()], maxval=2)
        pbar.start()
        pbar.update(1)
        self.assertIn('50%', pbar._format_line())
        pbar.finish()

    def test_format_label_widget(self):
        pbar = ProgressBar(widgets=[widgets.FormatLabel('Value: %(value)d')], maxval=2)
        pbar.start()
        pbar.update(1)
        self.assertIn('Value: 1', pbar._format_line())
        pbar.finish()

    def test_simple_progress_widget(self):
        pbar = ProgressBar(widgets=[widgets.SimpleProgress()], maxval=2)
        pbar.start()
        pbar.update(1)
        self.assertIn('1 of 2', pbar._format_line())
        pbar.finish()

    def test_bar_widget(self):
        pbar = ProgressBar(widgets=[widgets.Bar()], maxval=2)
        pbar.start()
        pbar.update(1)
        self.assertIn('#', pbar._format_line())
        pbar.finish()

    def test_reverse_bar_widget(self):
        pbar = ProgressBar(widgets=[widgets.ReverseBar()], maxval=2)
        pbar.start()
        pbar.update(1)
        self.assertIn('#', pbar._format_line())
        pbar.finish()

    def test_bouncing_bar_widget(self):
        pbar = ProgressBar(widgets=[widgets.BouncingBar()], maxval=2)
        pbar.start()
        pbar.update(1)
        self.assertIn('#', pbar._format_line())
        pbar.finish()

if __name__ == '__main__':
    unittest.main()
