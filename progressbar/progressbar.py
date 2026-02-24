# -*- coding: utf-8 -*-
#
# progressbar  - Text progress bar library for Python.
# Copyright (c) 2005 Nilton Volpato
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

"""A text-based progress bar library for Python.

This module provides a `ProgressBar` class that can be used to display the
progress of a long-running operation. It is highly customizable with a variety
of widgets to display different information.
"""

from __future__ import division

import math
import os
import signal
import sys
import time

try:
    from fcntl import ioctl
    from array import array
    import termios
except ImportError:
    pass

from .compat import *  # for: any, next
from . import widgets


class ProgressBar(object):
    """Manages the progress bar display.

    The `ProgressBar` class is the core of the library, responsible for
    managing the state and display of the progress bar.

    Examples:
        A simple progress bar:

        >>> pbar = ProgressBar(maxval=10).start()
        >>> for i in range(10):
        ...     time.sleep(0.1)
        ...     pbar.update(i + 1)
        >>> pbar.finish()

        Using the progress bar as an iterator:

        >>> pbar = ProgressBar()
        >>> for i in pbar(range(10)):
        ...     time.sleep(0.1)

    Attributes:
        currval: The current value of the progress bar.
        maxval: The maximum value of the progress bar.
        finished: A boolean indicating if the progress bar has finished.
        start_time: The `time.time()` when the progress bar was started.
        seconds_elapsed: The number of seconds elapsed since the start.
        widgets: The list of widgets to display.
        term_width: The width of the terminal in characters.
    """

    __slots__ = ('currval', 'fd', 'finished', 'last_update_time',
                 'left_justify', 'maxval', 'next_update', 'num_intervals',
                 'poll', 'seconds_elapsed', 'signal_set', 'start_time',
                 'term_width', 'update_interval', 'widgets', '_time_sensitive',
                 '__iterable')

    _DEFAULT_MAXVAL = 100
    _DEFAULT_TERMSIZE = 80
    _MAX_MAXVAL = 1000000000000
    _MAX_TERMSIZE = 4096
    _DEFAULT_WIDGETS = [widgets.Percentage(), ' ', widgets.Bar()]

    def __init__(self, maxval=None, widgets=None, term_width=None, poll=1,
                 left_justify=True, fd=None):
        """Initializes a new `ProgressBar`.

        Args:
            maxval: The maximum value of the progress bar. If `None`, the
                progress bar will be in "unknown length" mode.
            widgets: A list of widget objects to display.
            term_width: The width of the terminal. If `None`, it will be
                automatically detected.
            poll: The polling interval in seconds for time-sensitive widgets.
            left_justify: If `True`, the progress bar will be left-justified.
            fd: The file descriptor to write the progress bar to. Defaults to
                `sys.stderr`.
        """

        # Don't share a reference with any other progress bars
        if widgets is None:
            widgets = list(self._DEFAULT_WIDGETS)

        self.maxval = self._sanitize_maxval(maxval)
        self.widgets = widgets
        self.fd = fd if fd is not None else sys.stderr
        self.left_justify = left_justify

        self.signal_set = False
        if term_width is not None:
            self.term_width = self._sanitize_term_width(term_width)
        else:
            try:
                self._handle_resize()
                signal.signal(signal.SIGWINCH, self._handle_resize)
                self.signal_set = True
            except (SystemExit, KeyboardInterrupt): raise
            except:
                self.term_width = self._env_size()

        self.__iterable = None
        self._update_widgets()
        self.currval = 0
        self.finished = False
        self.last_update_time = None
        self.poll = poll
        self.seconds_elapsed = 0
        self.start_time = None
        self.update_interval = 1
        self.next_update = 0


    def __call__(self, iterable):
        """Makes the `ProgressBar` usable as an iterator.

        Args:
            iterable: The iterable to iterate over.

        Returns:
            An iterator that updates the progress bar on each iteration.
        """
        try:
            maxval = len(iterable)
        except:
            if self.maxval is None:
                self.maxval = widgets.UnknownLength
        else:
            self.maxval = self._sanitize_maxval(maxval)

        self.__iterable = iter(iterable)
        return self


    def __iter__(self):
        return self


    def __next__(self):
        try:
            value = next(self.__iterable)
            if self.start_time is None:
                self.start()
            else:
                self.update(self.currval + 1)
            return value
        except StopIteration:
            if self.start_time is None:
                self.start()
            self.finish()
            raise


    # Create an alias so that Python 2.x won't complain about not being
    # an iterator.
    next = __next__


    @classmethod
    def _sanitize_maxval(cls, maxval):
        if maxval in (None, widgets.UnknownLength):
            return maxval
        if maxval < 0:
            raise ValueError('Value out of range')
        if maxval > cls._MAX_MAXVAL:
            raise ValueError('Value out of range')
        return maxval


    @classmethod
    def _sanitize_term_width(cls, term_width):
        if term_width < 1:
            return 1
        return min(term_width, cls._MAX_TERMSIZE)


    def _env_size(self):
        """Tries to find the term_width from the environment."""
        try:
            term_width = int(os.environ.get('COLUMNS', self._DEFAULT_TERMSIZE))
        except (TypeError, ValueError):
            term_width = self._DEFAULT_TERMSIZE
        return self._sanitize_term_width(term_width - 1)


    def _handle_resize(self, signum=None, frame=None):
        """Tries to catch resize signals sent from the terminal."""

        h, w = array('h', ioctl(self.fd, termios.TIOCGWINSZ, b'\0' * 8))[:2]
        self.term_width = self._sanitize_term_width(w)


    def percentage(self):
        """Calculates the percentage of progress.

        Returns:
            The percentage of progress as a float, or `NaN` if the length is
            unknown.
        """
        if self.maxval is widgets.UnknownLength:
                return float("NaN")
        if self.currval >= self.maxval:
            return 100.0
        return (self.currval * 100.0 / self.maxval) if self.maxval else 100.00

    percent = property(percentage)


    def _format_widgets(self):
        result = []
        expanding = []
        width = self.term_width

        for index, widget in enumerate(self.widgets):
            if isinstance(widget, widgets.WidgetHFill):
                result.append(widget)
                expanding.insert(0, index)
            else:
                widget = widgets.format_updatable(widget, self)
                result.append(widget)
                width -= len(widget)

        count = len(expanding)
        while count:
            portion = max(int(math.ceil(width * 1. / count)), 0)
            index = expanding.pop()
            count -= 1

            widget = result[index].update(self, portion)
            width -= len(widget)
            result[index] = widget

        return result


    def _format_line(self):
        """Joins the widgets and justifies the line."""

        widgets = ''.join(self._format_widgets())

        if self.left_justify: return widgets.ljust(self.term_width)
        else: return widgets.rjust(self.term_width)


    def _need_update(self):
        """Returns whether the ProgressBar should redraw the line."""
        if self.currval >= self.next_update or self.finished: return True

        delta = time.time() - self.last_update_time
        return self._time_sensitive and delta > self.poll


    def _update_widgets(self):
        """Checks all widgets for the time sensitive bit."""

        self._time_sensitive = any(getattr(w, 'TIME_SENSITIVE', False)
                                    for w in self.widgets)


    def update(self, value=None):
        """Updates the progress bar to a new value.

        Args:
            value: The new value of the progress bar. If `None`, the progress
                bar is not updated, but the display is redrawn.
        """
        if value is not None and value is not widgets.UnknownLength:
            if (self.maxval is not widgets.UnknownLength
                and not 0 <= value <= self.maxval):

                raise ValueError('Value out of range')

            self.currval = value


        if not self._need_update(): return
        if self.start_time is None:
            raise RuntimeError('You must call "start" before calling "update"')

        now = time.time()
        self.seconds_elapsed = now - self.start_time
        self.next_update = self.currval + self.update_interval
        self.fd.write(self._format_line() + '\r')
        self.fd.flush()
        self.last_update_time = now


    def start(self):
        """Starts the progress bar.

        This method should be called before the first call to `update()`.

        Returns:
            The `ProgressBar` instance.
        """
        if self.maxval is None:
            self.maxval = self._DEFAULT_MAXVAL

        self.num_intervals = max(100, self.term_width)
        self.next_update = 0

        if self.maxval is not widgets.UnknownLength:
            if self.maxval < 0: raise ValueError('Value out of range')
            self.update_interval = self.maxval / self.num_intervals


        self.start_time = self.last_update_time = time.time()
        self.update(0)

        return self


    def finish(self):
        """Marks the progress bar as finished.

        This method should be called after the progress is complete. It will
        update the progress bar to 100% and print a newline.
        """
        if self.finished:
            return
        self.finished = True
        self.update(self.maxval)
        self.fd.write('\n')
        if self.signal_set:
            signal.signal(signal.SIGWINCH, signal.SIG_DFL)
