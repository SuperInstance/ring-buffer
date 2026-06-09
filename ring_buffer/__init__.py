"""
ring_buffer — Audio Pipeline NaN Guard

A fixed-length ring buffer that guards against NaN/Inf values in
real-time audio streams. Extracted from the OpenSMILE bridge NaN fix.
"""

import math
import array
from collections.abc import Sequence
from typing import Optional, Union

__all__ = ["RingBuffer"]
__version__ = "0.1.0"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NUMPY_AVAILABLE: bool = True
try:
    import numpy as np
except ImportError:
    _NUMPY_AVAILABLE = False


def _sanitise(value: float) -> float:
    """Replace NaN and ±Inf with 0.0."""
    if math.isnan(value) or math.isinf(value):
        return 0.0
    return value


def _sanitise_array(values: Sequence[float]) -> list[float]:
    """Batch-sanitise a sequence; short-circuits when no NaN/Inf present."""
    if _NUMPY_AVAILABLE:
        arr = np.asarray(values, dtype=np.float64)
        bad = ~np.isfinite(arr)
        if bad.any():
            arr[bad] = 0.0
        return arr.tolist()
    # Pure-Python fallback
    out: list[float] = []
    for v in values:
        if math.isnan(v) or math.isinf(v):
            out.append(0.0)
        else:
            out.append(v)
    return out


# ---------------------------------------------------------------------------
# RingBuffer
# ---------------------------------------------------------------------------

class RingBuffer:
    """Fixed-capacity ring buffer for 1-D audio sample streams.

    Automatically replaces NaN / ±Inf with 0.0 on push so downstream
    signal-processing code never chokes on non-finite values.

    Parameters
    ----------
    maxlen : int
        Maximum number of samples the buffer can hold (e.g. 3200 for
        200 ms at 16 kHz).
    dtype : str, optional
        Numeric type returned by ``read()``. One of ``"float"`` (default),
        ``"array"`` (Python ``array.array('d')``), or ``"numpy"`` (requires
        NumPy; falls back to ``"float"``).
    """

    def __init__(self, maxlen: int, dtype: str = "float") -> None:
        if maxlen < 1:
            raise ValueError("maxlen must be >= 1")
        self._maxlen = maxlen
        self._buf: list[float] = [0.0] * maxlen
        self._idx = 0          # next write position
        self._count = 0        # number of samples ever written

        dtype = dtype.lower()
        if dtype not in ("float", "array", "numpy"):
            raise ValueError(f"unsupported dtype '{dtype}'; use float/array/numpy")
        if dtype == "numpy" and not _NUMPY_AVAILABLE:
            dtype = "float"
        self._dtype = dtype

    # -- Properties -------------------------------------------------------

    @property
    def maxlen(self) -> int:
        return self._maxlen

    @property
    def filled(self) -> int:
        """Number of valid samples currently in the buffer (clamped to maxlen)."""
        return min(self._count, self._maxlen)

    @property
    def empty(self) -> bool:
        return self._count == 0

    # -- Public API -------------------------------------------------------

    def ready(self) -> bool:
        """``True`` once at least ``maxlen`` samples have been pushed."""
        return self._count >= self._maxlen

    def push(self, samples: Union[float, Sequence[float]]) -> None:
        """Push one sample or a sequence of samples into the buffer.

        NaN / ±Inf are silently replaced with ``0.0``.
        """
        if isinstance(samples, (int, float)):
            self._buf[self._idx] = _sanitise(float(samples))
            self._idx = (self._idx + 1) % self._maxlen
            self._count += 1
            return

        clean = _sanitise_array(samples)
        n = len(clean)
        if n > self._maxlen:
            # Only keep the most recent maxlen samples
            idx = self._idx
            for v in clean[-self._maxlen :]:
                self._buf[idx] = v
                idx = (idx + 1) % self._maxlen
            self._idx = idx
            self._count = max(self._count, 0) + self._maxlen
            return

        for v in clean:
            self._buf[self._idx] = v
            self._idx = (self._idx + 1) % self._maxlen
        self._count += n

    def read(self) -> Union[list[float], array.array, "np.ndarray"]:
        """Return the buffer contents in chronological order.

        Returns a ``list[float]`` by default, or the configured dtype.
        """
        n = self.filled
        if n == 0:
            return []

        start = (self._idx - n) % self._maxlen
        if start + n <= self._maxlen:
            data = self._buf[start : start + n]
        else:
            data = self._buf[start:] + self._buf[: self._idx]

        if self._dtype == "float":
            return data
        if self._dtype == "array":
            return array.array("d", data)
        # numpy
        return np.array(data, dtype=np.float64)

    def clear(self) -> None:
        """Reset the buffer to zero."""
        self._buf = [0.0] * self._maxlen
        self._idx = 0
        self._count = 0

    def __len__(self) -> int:
        return self.filled

    def __repr__(self) -> str:
        return (
            f"RingBuffer(maxlen={self._maxlen}, filled={self.filled}, "
            f"ready={self.ready()})"
        )
