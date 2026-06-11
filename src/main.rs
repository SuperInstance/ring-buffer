const CAPACITY: usize = 8;

struct RingBuffer<T> {
    data: [Option<T>; CAPACITY],
    head: usize,
    tail: usize,
    len: usize,
}

impl<T: Clone + Default + std::fmt::Debug> RingBuffer<T> {
    fn new() -> Self {
        Self {
            data: Default::default(),
            head: 0,
            tail: 0,
            len: 0,
        }
    }

    fn push_back(&mut self, item: T) -> Result<(), T> {
        if self.len == CAPACITY {
            return Err(item);
        }
        self.data[self.tail] = Some(item);
        self.tail = (self.tail + 1) % CAPACITY;
        self.len += 1;
        Ok(())
    }

    fn pop_front(&mut self) -> Option<T> {
        if self.len == 0 {
            return None;
        }
        let item = self.data[self.head].take();
        self.head = (self.head + 1) % CAPACITY;
        self.len -= 1;
        item
    }

    fn is_empty(&self) -> bool {
        self.len == 0
    }

    fn len(&self) -> usize {
        self.len
    }
}

fn main() {
    let mut buf: RingBuffer<i32> = RingBuffer::new();
    for i in 1..=5 {
        buf.push_back(i).unwrap();
    }
    println!("Ring buffer len: {}", buf.len());
    while let Some(v) = buf.pop_front() {
        print!("{} ", v);
    }
    println!("\nEmpty: {}", buf.is_empty());
}
