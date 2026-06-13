# Ring Buffer — Fixed-Size Circular Queue

A **ring buffer** (circular buffer) is a fixed-size queue where the end wraps around to the beginning, forming a ring. Two pointers — `head` (read position) and `tail` (write position) — track the valid region. When either pointer reaches the array boundary, it wraps to index 0 via modular arithmetic.

## Why It Matters

Ring buffers are the fundamental data structure for bounded producer-consumer scenarios: audio processing (PortAudio's playback buffer), serial I/O (kernel UART receive buffers), network packet queues, and real-time data streaming. They're used in every operating system kernel and audio driver.

The key advantage: O(1) push and pop with **zero allocations** after initialization. The buffer is pre-allocated to a fixed size, making it suitable for real-time systems where allocation jitter is unacceptable. When full, `push_back` returns an error rather than growing — providing natural backpressure.

Compared to `VecDeque` (which also uses a ring internally): ring buffers have a fixed capacity (no reallocation), can be placed in shared memory (for IPC between processes), and can be made lock-free for SPSC (single-producer, single-consumer) scenarios. See `ring-buffer-atomic` for the lock-free variant.

## How It Works

The buffer stores data in a fixed array with three indices:

```
[_][_][A][B][C][D][_][_]
       ↑ head (read)     ↑ tail (write)

After push_back(E): tail advances
[_][_][A][B][C][D][E][_]

After pop_front() → A: head advances
[_][_][_][B][C][D][E][_]
            ↑ head       ↑ tail
```

**push_back(item)**: If `len == CAPACITY`, return Err (full). Otherwise, write at `tail`, advance `tail = (tail + 1) % CAPACITY`, increment `len`. O(1).

**pop_front()**: If `len == 0`, return None (empty). Otherwise, read at `head`, advance `head = (head + 1) % CAPACITY`, decrement `len`. O(1).

The `% CAPACITY` modular arithmetic creates the circular behavior — after writing to the last slot, `tail` wraps to slot 0. The `len` counter tracks the number of valid elements, distinguishing full from empty (both would have `head == tail` without the counter).

## Quick Start

```rust
use ring_buffer::RingBuffer;

let mut buf: RingBuffer<i32> = RingBuffer::new();

// Fill the buffer (capacity = 8)
for i in 0..8 {
    buf.push_back(i).unwrap();
}

// Buffer is full
assert!(buf.push_back(99).is_err());

// Drain it
while let Some(val) = buf.pop_front() {
    print!("{} ", val); // 0 1 2 3 4 5 6 7
}
```

## API

- `RingBuffer::new()` — Create buffer with default capacity (8)
- `push_back(item)` — Enqueue. O(1). Returns Err if full
- `pop_front()` — Dequeue. O(1). Returns None if empty
- `len()` — Current element count
- `is_empty()` / `is_full()` — State queries

## Architecture Notes

Part of the [SuperInstance](https://github.com/SuperInstance) ecosystem. Ring buffers connect fleet agents in producer-consumer pipelines — the bottle protocol uses ring buffers internally for message queuing. The fixed capacity provides natural backpressure: if a consumer agent is slow, its ring buffer fills and the producer gets Err, triggering the conservation law's feedback loop.

See [ARCHITECTURE.md](https://github.com/SuperInstance/SuperInstance/blob/main/ARCHITECTURE.md).

## References

- Lamport, L. (1977). "Proving the Correctness of Multiprocess Programs." — using ring buffers in concurrent systems
- Herlihy, M. & Shavit, N. (2012). *The Art of Multiprocessor Programming*, Ch. 3. — bounded queues
- Linux kernel source: `include/linux/circ_buf.h` — production ring buffer implementation

## License

MIT
