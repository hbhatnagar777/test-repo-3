"""Main file for Registry Interface.

UserRegistry is the only class defined in this file.

UserRegistry: Class for representing user registry.

UserRegistry:
========
    __init()__  --  Initialize object
    get(name)  -- get user based on name provided.
    add(name, user)  -- add user object in to the registry with name and user

"""

import zope.interface
from Application.Teams.Registry.registry import Registry
import multiprocessing


@zope.interface.implementer(Registry)
class UserRegistry:
    """Singleton Class to store User objects which are already created"""
    user_registry_instance = None
    lock = multiprocessing.Lock()

    def __init__(self):
        self._user_registry = {}

    @staticmethod
    def get_instance(cls):
        """Method to get singleton instance of UserRegistry"""
        if cls.user_registry_instance is None:
            cls.lock.acquire()
            if cls.user_registry_instance is None:
                cls.user_registry_instance = UserRegistry()
            cls.lock.release()
        return cls.user_registry_instance

    def get(self, key):
        """Get a User object by passing display name"""
        value = self._user_registry.get(key, None)
        return value

    def add(self, key, value):
        """Add a User object to registry by passing key (display name) and value (User object) """
        self._user_registry[key] = value

