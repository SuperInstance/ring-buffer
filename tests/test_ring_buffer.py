"""Tests for ring_buffer.RingBuffer."""

import math
import array
import sys

import pytest

from ring_buffer import RingBuffer


# -- Construction -----------------------------------------------------------

class TestConstruction:
    def test_default_creation(self):
        buf = RingBuffer(maxlen=3200)
        assert buf.maxlen == 3200
        assert buf.filled == 0
        assert buf.empty is True
        assert buf.ready() is False
        assert len(buf) == 0

    def test_min_maxlen(self):
        with pytest.raises(ValueError, match="maxlen"):
            RingBuffer(maxlen=0)
        with pytest.raises(ValueError, match="maxlen"):
            RingBuffer(maxlen=-1)

    def test_invalid_dtype(self):
        with pytest.raises(ValueError, match="dtype"):
            RingBuffer(maxlen=8, dtype="int32")


# -- Push / Read -----------------------------------------------------------

class TestPushRead:
    def test_push_single_value(self):
        buf = RingBuffer(maxlen=8)
        buf.push(1.0)
        buf.push(2.0)
        assert buf.read() == [1.0, 2.0]
        assert buf.filled == 2
        assert buf.empty is False

    def test_push_sequence(self):
        buf = RingBuffer(maxlen=8)
        buf.push([0.1, 0.2, 0.3])
        assert buf.read() == [0.1, 0.2, 0.3]

    def test_push_wraparound(self):
        buf = RingBuffer(maxlen=4)
        buf.push([1.0, 2.0, 3.0])   # fills positions 0,1,2
        buf.read()                   # idx is 3 now
        buf.push([4.0, 5.0, 6.0])   # wraps: 3→4→(0→5,1→6)
        # buffer has: [6.0, 5.0, 3.0, 4.0]  (chronological: [3, 4, 5, 6])
        assert buf.read() == [3.0, 4.0, 5.0, 6.0]

    def test_push_over_maxlen(self):
        buf = RingBuffer(maxlen=4)
        buf.push([1.0, 2.0, 3.0, 4.0, 5.0, 6.0])  # > maxlen
        assert buf.filled == 4
        assert buf.read() == [3.0, 4.0, 5.0, 6.0]
        assert buf.ready() is True

    def test_read_empty(self):
        buf = RingBuffer(maxlen=8)
        assert buf.read() == []

    def test_ready_true(self):
        buf = RingBuffer(maxlen=4)
        assert buf.ready() is False
        buf.push([1, 2, 3, 4])
        assert buf.ready() is True


# -- NaN / Inf sanitisation ------------------------------------------------

class TestSanitisation:
    def test_nan_becomes_zero(self):
        buf = RingBuffer(maxlen=4)
        buf.push([1.0, float("nan"), 3.0])
        assert buf.read() == [1.0, 0.0, 3.0]

    def test_inf_becomes_zero(self):
        buf = RingBuffer(maxlen=4)
        buf.push([1.0, float("inf"), float("-inf")])
        assert buf.read() == [1.0, 0.0, 0.0]

    def test_single_nan(self):
        buf = RingBuffer(maxlen=4)
        buf.push(float("nan"))
        assert buf.read() == [0.0]

    def test_all_bad(self):
        buf = RingBuffer(maxlen=4)
        buf.push([float("nan"), float("inf"), float("-inf")])
        assert buf.read() == [0.0, 0.0, 0.0]

    def test_clean_passthrough(self):
        vals = [0.5, -0.3, 1.0, -1.0, 0.0]
        buf = RingBuffer(maxlen=len(vals))
        buf.push(vals)
        assert buf.read() == vals


# -- dtype variants --------------------------------------------------------

class TestDtype:
    def test_default_float(self):
        buf = RingBuffer(maxlen=4)
        buf.push([1.0, 2.0])
        assert isinstance(buf.read(), list)
        assert all(isinstance(v, float) for v in buf.read())

    def test_array_dtype(self):
        buf = RingBuffer(maxlen=4, dtype="array")
        buf.push([1.0, 2.0])
        result = buf.read()
        assert isinstance(result, array.array)
        assert result.typecode == "d"

    def test_numpy_dtype(self):
        np = pytest.importorskip("numpy")
        buf = RingBuffer(maxlen=4, dtype="numpy")
        buf.push([1.0, 2.0])
        result = buf.read()
        assert isinstance(result, np.ndarray)
        assert result.dtype == np.float64


# -- Clear / reset ---------------------------------------------------------

class TestManagement:
    def test_clear(self):
        buf = RingBuffer(maxlen=4)
        buf.push([1.0, 2.0, 3.0, 4.0])
        assert buf.ready() is True
        buf.clear()
        assert buf.filled == 0
        assert buf.empty is True
        assert buf.ready() is False
        assert buf.read() == []

    def test_clear_then_refill(self):
        buf = RingBuffer(maxlen=4)
        buf.push([1.0, 2.0])
        buf.clear()
        buf.push([9.0])
        assert buf.read() == [9.0]

    def test_repr(self):
        buf = RingBuffer(maxlen=4)
        buf.push([1.0, 2.0])
        r = repr(buf)
        assert "RingBuffer" in r
        assert "maxlen=4" in r
        assert "filled=2" in r


# -- Edge cases ------------------------------------------------------------

class TestEdgeCases:
    def test_maxlen_one(self):
        buf = RingBuffer(maxlen=1)
        buf.push(1.0)
        assert buf.read() == [1.0]
        buf.push(2.0)
        assert buf.read() == [2.0]  # overwritten

    def test_many_sequential_pushes(self):
        buf = RingBuffer(maxlen=4)
        for i in range(100):
            buf.push(float(i))
        assert buf.read() == [96.0, 97.0, 98.0, 99.0]

    def test_push_integer(self):
        buf = RingBuffer(maxlen=4)
        buf.push(42)         # int, not float
        result = buf.read()
        assert result == [42.0]

    def test_push_empty_sequence(self):
        buf = RingBuffer(maxlen=4)
        buf.push([])
        assert buf.read() == []

    def test_mixed_nan_clean_push(self):
        buf = RingBuffer(maxlen=4)
        # Push clean, then nan, then clean — wraparound at play
        buf.push([1.0, 2.0])
        buf.push(float("nan"))
        buf.push([3.0])
        assert buf.read() == [1.0, 2.0, 0.0, 3.0]
