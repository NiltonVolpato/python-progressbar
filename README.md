# Python Progress Bar

A simple, customizable text-based progress bar library for Python.

## Installation

```bash
pip install progressbar
```

## Usage

The `ProgressBar` class is the core of the library. It can be used as follows:

```python
import time
from progressbar import ProgressBar, Percentage, Bar

pbar = ProgressBar(widgets=[Percentage(), Bar()], maxval=10).start()
for i in range(10):
    time.sleep(0.1)
    pbar.update(i + 1)
pbar.finish()
```

You can also use the progress bar as an iterator:

```python
import time
from progressbar import ProgressBar

pbar = ProgressBar()
for i in pbar(range(10)):
    time.sleep(0.1)
```

## Widgets

The progress bar is highly customizable through the use of widgets. The following widgets are available:

*   `AnimatedMarker`: An animated marker that cycles through a sequence of characters.
*   `Bar`: A progress bar that fills from left to right.
*   `BouncingBar`: A progress bar with a bouncing marker.
*   `Counter`: A counter of the current progress.
*   `ETA`: Estimates the time of arrival (ETA).
*   `FileTransferSpeed`: Displays the file transfer speed.
*   `FormatLabel`: Displays a formatted label with progress information.
*   `Percentage`: Displays the progress as a percentage.
*   `ReverseBar`: A progress bar that fills from right to left.
*   `SimpleProgress`: Displays the progress as a simple count (e.g., "5 of 47").
*   `Timer`: Displays the elapsed time since the progress bar was started.

You can create your own widgets by subclassing `progressbar.Widget`.
