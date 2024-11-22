"""Main file for Registry Interface.

TeamRegistry is the only class defined in this file.

TeamRegistry: Class for representing user registry.

TeamRegistry:
========
    __init()__  --  Initialize object
    get(name)  -- get team based on name provided.
    add(name, team)  -- add team object in to the registry with name and team

"""

import zope.interface
from Application.Teams.Registry.registry import Registry
import multiprocessing


@zope.interface.implementer(Registry)
class TeamRegistry:
    """Singleton Class to store Team objects which are already created"""
    team_registry_instance = None
    lock = multiprocessing.Lock()

    def __init__(self):
        self._team_registry = {}

    @staticmethod
    def get_instance(cls):
        """Method to get singleton instance of TeamRegistry"""
        if cls.team_registry_instance is None:
            cls.lock.acquire()
            if cls.team_registry_instance is None:
                cls.team_registry_instance = TeamRegistry()
            cls.lock.release()
        return cls.team_registry_instance

    def get(self, key):
        """Get a Team object by passing display name"""
        value = self._team_registry.get(key, None)
        return value

    def add(self, key, value):
        """Add a Team object to registry by passing key (display name) and value (Team object) """
        self._team_registry[key] = value

