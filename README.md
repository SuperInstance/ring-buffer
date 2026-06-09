# ring-buffer

[![PyPI](https://img.shields.io/pypi/v/ring-buffer)](https://pypi.org/project/ring-buffer/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

**Audio pipeline NaN guard.** A fixed-length ring buffer for real-time audio
streams that silently replaces NaN / ±Inf with `0.0` on push.

Extracted from the [OpenSMILE](https://github.com/audeering/opensmile) bridge
NaN fix — the exact guard that prevents silent corruption when downstream
feature extractors (MFCC, prosody, etc.) encounter non-finite samples.

## Why?

Real-world audio pipelines have no shortage of NaN sources:

- **Silence trimming** → `0 / 0` → NaN
- **Normalisation drift** → division by near-zero → ±Inf
- **Hardware glitches** → corrupted ADC reads
- **Network jitter buffers** → uninitialised slots

A single NaN propagates through FFT → MFCC → classifier and poisons
everything downstream. This buffer stops that at the edge.

## Install

```bash
pip install ring-buffer
```

With NumPy support (automatic dispatch, no extra API change):

```bash
pip install "ring-buffer[numpy]"
```

## Usage

```python
from ring_buffer import RingBuffer

# 200 ms at 16 kHz
buf = RingBuffer(maxlen=3200)

# Push samples — NaN/Inf are silently replaced with 0.0
buf.push([0.1, float("nan"), -0.3, float("inf")])
buf.push(0.5)

# Check if buffer is full
buf.ready()  # False — only 5 samples pushed so far

# Read chronological samples
samples = buf.read()  # -> [0.1, 0.0, -0.3, 0.0, 0.5]

# Full pipeline integration
FEATURE_WINDOW = 3200  # 200 ms
buf = RingBuffer(maxlen=FEATURE_WINDOW)

for chunk in audio_stream():
    buf.push(chunk)
    if buf.ready():
        frame = buf.read()  # exactly 3200 clean samples
        features = extract_features(frame)  # safe
```

## API

| Method       | Description                                     |
|--------------|-------------------------------------------------|
| `push(s)`    | Push sample or sequence; sanitises NaN/Inf → 0  |
| `read()`     | Return buffer in chronological order            |
| `ready()`    | `True` once `≥ maxlen` samples have been pushed |
| `clear()`    | Reset to zeros                                  |
| `filled`     | Number of valid samples currently held           |
| `empty`      | `True` if no samples pushed yet                  |
| `maxlen`     | Capacity (fixed at construction)                 |

### `dtype` parameter

```python
RingBuffer(maxlen=3200, dtype="float")   # list[float]     (default)
RingBuffer(maxlen=3200, dtype="array")   # array.array('d')
RingBuffer(maxlen=3200, dtype="numpy")   # np.ndarray
```

## Tests

```bash
pip install "ring-buffer[test]"
pytest tests/
```

## License

MIT
