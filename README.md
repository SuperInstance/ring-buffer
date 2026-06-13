# ring-buffer

A **fixed-capacity circular buffer** (ring buffer) in Rust, implementing FIFO semantics with $O(1)$ push and pop using a contiguous array with modular arithmetic for wrap-around.

## Why It Matters

Ring buffers are the **workhorse data structure** of systems programming. They power:

- **Producer-consumer queues** — lock-free variants drive Linux's `io_uring`
- **Network packet buffers** — every NIC DMA ring is a ring buffer
- **Audio/video streaming** — bounded-latency jitter buffers
- **Serial I/O** — UART receive buffers in embedded systems
- **Log buffers** — `dmesg` and `syslog` use circular overwrite buffers

The key advantage over a `VecDeque` is **bounded, compile-time-known capacity**: no allocations, no resize, no fragmentation. This makes ring buffers ideal for `no_std` and real-time contexts.

## How It Works

### Circular Indexing

The buffer maintains three pointers: `head` (read), `tail` (write), and `len` (count). Indices wrap using modular arithmetic:

$$\text{next}(i) = (i + 1) \bmod N$$

where $N$ is the capacity. This creates a logical ring from a linear array:

```
Array:  [_][B][C][D][_][_][_][_]
              ↑           ↑
            head        tail
            (read)     (write)

State: len=3, capacity=8
```

After pushing E, F, G, H and popping B, C, D:

```
Array:  [_][_][_][_][E][F][G][H]
                          ↑
                  head = tail (full or empty — disambiguated by len)
```

### Full / Empty Disambiguation

A classic ring buffer ambiguity: when `head == tail`, is the buffer empty or full? This implementation resolves it with an explicit `len` counter:

| Condition | `head == tail` | `len` | State |
|-----------|----------------|-------|-------|
| Empty | possible | $0$ | Read returns `None` |
| Full | possible | $N$ | Write returns `Err(item)` |

Alternative approaches sacrifice one slot (capacity $N-1$ usable) or use a separate full flag.

### Complexity

| Operation | Time | Space |
|-----------|------|-------|
| `push_back` | $O(1)$ | $O(N)$ total, fixed |
| `pop_front` | $O(1)$ | — |
| `len` / `is_empty` | $O(1)$ | — |
| Memory allocation | Zero (static array) | $O(N)$ at construction |

All operations are **deterministic** — no allocation, no resize, no reallocation. This is critical for real-time systems where jitter must be bounded.

### Generic Constraints

The implementation requires `T: Clone + Default + Debug`:
- `Clone`: needed because `Option<T>` array initialization uses `Default::default()`
- `Default`: for array initialization
- `Debug`: for diagnostic output

In production, a `MaybeUninit<T>` approach could remove these bounds for zero-overhead.

## Quick Start

```rust
use ring_buffer::RingBuffer;

fn main() {
    let mut buf: RingBuffer<i32> = RingBuffer::new();

    // Push 5 elements into capacity-8 buffer
    for i in 1..=5 {
        buf.push_back(i).unwrap();
    }
    println!("Length: {}", buf.len());  // 5

    // Pop in FIFO order
    while let Some(v) = buf.pop_front() {
        print!("{} ", v);  // 1 2 3 4 5
    }
    println!("\nEmpty: {}", buf.is_empty());  // true
}
```

```bash
cargo build
cargo run
```

## API

### `RingBuffer<T>`

| Method | Signature | Description |
|--------|-----------|-------------|
| `new` | `fn new() -> Self` | Create empty buffer (capacity = 8) |
| `push_back` | `fn push_back(&mut self, item: T) -> Result<(), T>` | Add to tail; `Err(item)` if full |
| `pop_front` | `fn pop_front(&mut self) -> Option<T>` | Remove from head; `None` if empty |
| `is_empty` | `fn is_empty(&self) -> bool` | True if `len == 0` |
| `len` | `fn len(&self) -> usize` | Current element count |

**Capacity:** Fixed at `const CAPACITY: usize = 8`. Change the constant to adjust.

## Architecture Notes

This crate is part of the **SuperInstance ecosystem**. Ring buffers serve as **bounded channels** between fleet agents: one agent produces bottles (trit vectors $\gamma$) into the buffer, and another consumes them, producing responses ($\eta$). The conservation law $\gamma + \eta = C$ is preserved because the buffer is **lossless** — every bottle pushed is eventually popped. If the buffer overflows (push returns `Err`), the producer must backpressure, preventing conservation violations from dropped messages.

The fixed capacity mirrors the **bounded-memory** principle of the fleet: no unbounded queues, no OOM, predictable latency.

## References

1. Lamport, L. (1977). *"Proving the Correctness of Multiprocess Programs."* IEEE TSE, SE-3(2).
2. Herlihy, M. & Shavit, N. (2012). *The Art of Multiprocessor Programming.* MIT Press. Ch. 3–4.
3. Linux Kernel Documentation. *Circular Buffers.* <https://www.kernel.org/doc/html/latest/core-api/circular-buffers.html>
4. Duffy, J. (2019). *Java Concurrency in Practice.* Addison-Wesley. §5.3 Blocking Queues.

## License

MIT
