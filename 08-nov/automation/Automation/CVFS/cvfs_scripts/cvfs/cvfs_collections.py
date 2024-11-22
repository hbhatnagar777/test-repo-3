"""This module contains the collection of thread safe python data types used by cvfs auto package."""

import threading
from collections import OrderedDict
from threading import Lock

from .cvfs_constants import CVFSConstants


class ThreadSafeDict(dict):
    """This class is used to create a thread-safe dictionary."""

    def __init__(self, *args, **kwargs):
        """Initialize the ThreadSafeDict object with the provided parameters."""
        super().__init__(*args, **kwargs)
        self.__lock = Lock()

    def __getitem__(self, key):
        """Get the item from the dictionary."""
        with self.__lock:
            return super().__getitem__(key)

    def __setitem__(self, key, value):
        """Set the item in the dictionary."""
        with self.__lock:
            super().__setitem__(key, value)

    def __delitem__(self, key):
        """Delete the item from the dictionary."""
        with self.__lock:
            super().__delitem__(key)

    def __len__(self):
        """Get the length of the dictionary."""
        with self.__lock:
            return super().__len__()

    def __contains__(self, key):
        """Check if the key is present in the dictionary."""
        with self.__lock:
            return super().__contains__(key)

    def items(self):
        """Get the items in the dictionary."""
        with self.__lock:
            return super().items()


class FileWriter:
    """
    This class is used to write data to a file in a thread safe manner.
    """

    def __init__(self, file_path, mode="w", encoding=CVFSConstants.DEFAULT_ENCODING):
        """Initialize the FileWriter object with the provided parameters.

        Args:
            file_path (str): The path of the file to write the data.
            mode (str): The mode to open the file.
                default: "w"
            encoding (str): The encoding to use for the file.
        """
        self._file_path = file_path
        self._file = open(file_path, mode=mode, encoding=encoding)
        self._lock = threading.RLock()

    def write(self, data):
        """Write the data to the file.

        Args:
            data (str): The data to be written to the file.
        """
        with self._lock:
            self._file.write(data)
            self._file.flush()

    def write_line(self, line):
        """Write the line to the file.

        Args:
            line (str): The line to be written to the file.
        """
        with self._lock:
            self.write(f"{line}\n")

    def write_lines(self, lines):
        """Write the lines to the file.

        Args:
            lines (list): The list of lines to be written to the file.
        """
        with self._lock:
            for line in lines:
                self.write_line(line)

    def close(self):
        """Close the file."""
        with self._lock:
            self._file.close()

    def __del__(self):
        """Close the file when the object is deleted."""
        self.close()


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


class ThreadSafeSet(set):
    """This class is used to create a thread-safe set."""

    def __init__(self, *args, **kwargs):
        """Initialize the ThreadSafeSet object with the provided parameters."""
        super().__init__(*args, **kwargs)
        self.__lock = Lock()

    def add(self, value):
        """Add the value to the set."""
        with self.__lock:
            super().add(value)

    def remove(self, value):
        """Remove the value from the set."""
        with self.__lock:
            super().remove(value)

    def __contains__(self, value):
        """Check if the value is present in the set."""
        with self.__lock:
            return super().__contains__(value)

    def __len__(self):
        """Get the length of the set."""
        with self.__lock:
            return super().__len__()

    def __str__(self):
        """Get the string representation of the set."""
        with self.__lock:
            return str(super().__str__())

    def __repr__(self):
        """Get the string representation of the set."""
        with self.__lock:
            return repr(super().__repr__())
