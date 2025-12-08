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

"""A collection of widgets for the `ProgressBar` class.

Each widget is a class that can be used to display different information in the
progress bar. Widgets can be combined in a list to create a custom progress
bar.
"""

from __future__ import division

import datetime
import math

try:
    from abc import ABCMeta, abstractmethod
except ImportError:
    AbstractWidget = object
    abstractmethod = lambda fn: fn
else:
    AbstractWidget = ABCMeta('AbstractWidget', (object,), {})

class UnknownLength:
  pass

def format_updatable(updatable, pbar):
    if hasattr(updatable, 'update'): return updatable.update(pbar)
    else: return updatable


class Widget(AbstractWidget):
    """The base class for all widgets.

    This class is an abstract base class for all widgets. A widget is an
    object that can be displayed in a `ProgressBar` and updated on a regular
    basis.

    Attributes:
        TIME_SENSITIVE: A boolean indicating if the widget is time-sensitive.
            If `True`, the `ProgressBar` will update the widget more frequently.
    """

    TIME_SENSITIVE = False
    __slots__ = ()

    @abstractmethod
    def update(self, pbar):
        """Updates the widget and returns the string to display.

        Args:
            pbar: The `ProgressBar` instance.

        Returns:
            The string to display for the widget.
        """


class WidgetHFill(Widget):
    """A widget that expands to fill the available horizontal space."""

    @abstractmethod
    def update(self, pbar, width):
        """Updates the widget and returns the string to display.

        Args:
            pbar: The `ProgressBar` instance.
            width: The available width for the widget.

        Returns:
            The string to display for the widget.
        """


class Timer(Widget):
    """Displays the elapsed time since the progress bar was started."""

    __slots__ = ('format_string',)
    TIME_SENSITIVE = True

    def __init__(self, format='Elapsed Time: %s'):
        """Initializes a `Timer` widget.

        Args:
            format: The format string for the timer.
        """
        self.format_string = format

    @staticmethod
    def format_time(seconds):
        """Formats a number of seconds into a `HH:MM:SS` string."""
        return str(datetime.timedelta(seconds=int(seconds)))


    def update(self, pbar):
        """Updates the widget with the elapsed time."""
        return self.format_string % self.format_time(pbar.seconds_elapsed)


class ETA(Timer):
    """Estimates the time of arrival (ETA)."""

    TIME_SENSITIVE = True

    def update(self, pbar):
        """Updates the widget with the ETA."""
        if pbar.maxval is UnknownLength or pbar.currval == 0:
            return 'ETA:  --:--:--'
        elif pbar.finished:
            return 'Time: %s' % self.format_time(pbar.seconds_elapsed)
        else:
            elapsed = pbar.seconds_elapsed
            eta = elapsed * pbar.maxval / pbar.currval - elapsed
            return 'ETA:  %s' % self.format_time(eta)


class AdaptiveETA(Timer):
    """Estimates the time of arrival (ETA) using a moving average."""

    TIME_SENSITIVE = True

    TIME_SENSITIVE = True
    NUM_SAMPLES = 10

    def _update_samples(self, currval, elapsed):
        sample = (currval, elapsed)
        if not hasattr(self, 'samples'):
            self.samples = [sample] * (self.NUM_SAMPLES + 1)
        else:
            self.samples.append(sample)
        return self.samples.pop(0)

    def _eta(self, maxval, currval, elapsed):
        return elapsed * maxval / float(currval) - elapsed

    def update(self, pbar):
        """Updates the widget to show the ETA or total time when finished."""
        if pbar.maxval is UnknownLength or pbar.currval == 0:
            return 'ETA:  --:--:--'
        elif pbar.finished:
            return 'Time: %s' % self.format_time(pbar.seconds_elapsed)
        else:
            elapsed = pbar.seconds_elapsed
            currval1, elapsed1 = self._update_samples(pbar.currval, elapsed)
            eta = self._eta(pbar.maxval, pbar.currval, elapsed)
            if pbar.currval > currval1:
                etasamp = self._eta(pbar.maxval - currval1,
                                    pbar.currval - currval1,
                                    elapsed - elapsed1)
                weight = (pbar.currval / float(pbar.maxval)) ** 0.5
                eta = (1 - weight) * eta + weight * etasamp
            return 'ETA:  %s' % self.format_time(eta)


class FileTransferSpeed(Widget):
    """Displays the file transfer speed."""

    FMT = '%6.2f %s%s/s'
    PREFIXES = ' kMGTPEZY'
    __slots__ = ('unit',)

    def __init__(self, unit='B'):
        """Initializes a `FileTransferSpeed` widget.

        Args:
            unit: The unit to use (e.g., "B" for bytes, "b" for bits).
        """
        self.unit = unit

    def update(self, pbar):
        """Updates the widget with the current transfer speed."""
        if pbar.seconds_elapsed < 2e-6 or pbar.currval < 2e-6: # =~ 0
            scaled = power = 0
        else:
            speed = pbar.currval / pbar.seconds_elapsed
            power = int(math.log(speed, 1000))
            scaled = speed / 1000.**power

        return self.FMT % (scaled, self.PREFIXES[power], self.unit)


class AnimatedMarker(Widget):
    """Displays an animated marker that cycles through a sequence of characters."""

    __slots__ = ('markers', 'curmark')

    def __init__(self, markers='|/-\\'):
        """Initializes an `AnimatedMarker` widget.

        Args:
            markers: A string of characters to cycle through.
        """
        self.markers = markers
        self.curmark = -1

    def update(self, pbar):
        """Updates the widget with the next marker in the sequence."""
        if pbar.finished: return self.markers[0]

        self.curmark = (self.curmark + 1) % len(self.markers)
        return self.markers[self.curmark]

# Alias for backwards compatibility
RotatingMarker = AnimatedMarker


class Counter(Widget):
    """Displays a counter of the current progress."""

    __slots__ = ('format_string',)

    def __init__(self, format='%d'):
        """Initializes a `Counter` widget.

        Args:
            format: The format string for the counter.
        """
        self.format_string = format

    def update(self, pbar):
        """Updates the widget with the current count."""
        return self.format_string % pbar.currval


class Percentage(Widget):
    """Displays the progress as a percentage."""

    def update(self, pbar):
        """Updates the widget with the current percentage."""
        return '%3.0f%%' % pbar.percentage()


class FormatLabel(Timer):
    """Displays a formatted label with progress information."""

    mapping = {
        'elapsed': ('seconds_elapsed', Timer.format_time),
        'finished': ('finished', None),
        'last_update': ('last_update_time', None),
        'max': ('maxval', None),
        'seconds': ('seconds_elapsed', None),
        'start': ('start_time', None),
        'value': ('currval', None)
    }

    __slots__ = ('format_string',)
    def __init__(self, format):
        """Initializes a `FormatLabel` widget.

        Args:
            format: The format string for the label.
        """
        self.format_string = format

    def update(self, pbar):
        """Updates the widget with the formatted label."""
        context = {}
        for name, (key, transform) in self.mapping.items():
            try:
                value = getattr(pbar, key)

                if transform is None:
                   context[name] = value
                else:
                   context[name] = transform(value)
            except: pass

        return self.format_string % context


class SimpleProgress(Widget):
    """Displays the progress as a simple count (e.g., "5 of 47")."""

    __slots__ = ('sep',)

    def __init__(self, sep=' of '):
        """Initializes a `SimpleProgress` widget.

        Args:
            sep: The separator to use between the current and max values.
        """
        self.sep = sep

    def update(self, pbar):
        """Updates the widget with the simple progress count."""
        if pbar.maxval is UnknownLength:
            return '%d%s?' % (pbar.currval, self.sep)
        return '%d%s%s' % (pbar.currval, self.sep, pbar.maxval)


class Bar(WidgetHFill):
    """A progress bar that fills from left to right."""

    __slots__ = ('marker', 'left', 'right', 'fill', 'fill_left')

    def __init__(self, marker='#', left='|', right='|', fill=' ',
                 fill_left=True):
        """Initializes a `Bar` widget.

        Args:
            marker: The character to use for the filled part of the bar.
            left: The character to use for the left-hand side of the bar.
            right: The character to use for the right-hand side of the bar.
            fill: The character to use for the unfilled part of the bar.
            fill_left: If `True`, the bar fills from left to right.
        """
        self.marker = marker
        self.left = left
        self.right = right
        self.fill = fill
        self.fill_left = fill_left


    def update(self, pbar, width):
        """Updates the widget with the current progress bar."""
        left, marked, right = (format_updatable(i, pbar) for i in
                               (self.left, self.marker, self.right))

        width -= len(left) + len(right)
        # Marked must *always* have length of 1
        if pbar.maxval is not UnknownLength and pbar.maxval:
          marked *= int(pbar.currval / pbar.maxval * width)
        else:
          marked = ''

        if self.fill_left:
            return '%s%s%s' % (left, marked.ljust(width, self.fill), right)
        else:
            return '%s%s%s' % (left, marked.rjust(width, self.fill), right)


class ReverseBar(Bar):
    """A progress bar that fills from right to left."""

    def __init__(self, marker='#', left='|', right='|', fill=' ',
                 fill_left=False):
        """Initializes a `ReverseBar` widget.

        Args:
            marker: The character to use for the filled part of the bar.
            left: The character to use for the left-hand side of the bar.
            right: The character to use for the right-hand side of the bar.
            fill: The character to use for the unfilled part of the bar.
            fill_left: If `True`, the bar fills from left to right.
        """
        self.marker = marker
        self.left = left
        self.right = right
        self.fill = fill
        self.fill_left = fill_left


class BouncingBar(Bar):
    """A progress bar with a bouncing marker."""

    def update(self, pbar, width):
        """Updates the widget with the bouncing marker."""
        left, marker, right = (format_updatable(i, pbar) for i in
                               (self.left, self.marker, self.right))

        width -= len(left) + len(right)

        if pbar.finished: return '%s%s%s' % (left, width * marker, right)

        position = int(pbar.currval % (width * 2 - 1))
        if position > width: position = width * 2 - position
        lpad = self.fill * (position - 1)
        rpad = self.fill * (width - len(marker) - len(lpad))

        # Swap if we want to bounce the other way
        if not self.fill_left: rpad, lpad = lpad, rpad

        return '%s%s%s%s%s' % (left, lpad, marker, rpad, right)
