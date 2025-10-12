# /ai/memory_buffer.py
from collections import deque
import random


class ReplayMemory:
    """Stores past episodes for experience replay."""

    def __init__(self, capacity=1000):
        self.buffer = deque(maxlen=capacity)

    def push(self, experience):
        self.buffer.append(experience)

    def sample(self, batch_size=32):
        return random.sample(self.buffer, min(batch_size, len(self.buffer)))

    def __len__(self):
        return len(self.buffer)
