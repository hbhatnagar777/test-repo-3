"""
This module implements a simple thread safe LRU cache using OrderedDict.
"""

import threading
from collections import OrderedDict


class LRUCache:
    """This class implements a simple thread safe LRU cache using OrderedDict."""

    def __init__(self, capacity):
        """Initialize the LRUCache object with the provided parameters.

        Args:
            capacity (int): The maximum capacity of the cache.
        """
        self._capacity = capacity
        self._cache = OrderedDict()
        self._lock = threading.Lock()

    @property
    def capacity(self):
        """Get the capacity of the cache."""
        return self._capacity

    def get(self, key):
        """Get the value associated with the key from the cache.

        Args:
            key (object): The key to retrieve the value.
        Returns:
            object: The value associated with the key.
        """
        with self._lock:
            if key in self._cache:
                # Move the key to the end to mark it as the most recently used
                self._cache.move_to_end(key)
                return self._cache[key]
        return None

    def put(self, key, value):
        """Put the key-value pair into the cache.

        Args:
            key (object): The key to store the value.
            value (object): The value to be stored.
        """
        with self._lock:
            if key in self._cache:
                # Move the key to the end to mark it as the most recently used
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self._capacity:
                    # If the cache is full, remove the least recently used key
                    self._cache.popitem(last=False)
            self._cache[key] = value

    def evict(self, key):
        """Evict the key from the cache.

        Args:
            key (object): The key to be evicted.
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self):
        """Clear the cache."""
        with self._lock:
            self._cache.clear()

    def __len__(self):
        """Get the length of the cache."""
        with self._lock:
            return len(self._cache)

    def __contains__(self, key):
        """Check if the key is present in the cache."""
        with self._lock:
            return key in self._cache

    def __str__(self):
        """Get the string representation of the cache."""
        with self._lock:
            return str(self._cache)

    def __repr__(self):
        """Get the string representation of the cache."""
        with self._lock:
            return repr(self._cache)
