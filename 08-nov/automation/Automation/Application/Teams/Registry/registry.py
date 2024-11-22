# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for Registry Interface.

Registry is the only Interface defined in this file.

Registry: Interface for representing registry.

Registry:
========
    get(key)  -- get item based on key provided.
    add(key, value)  -- add item in to the registry with key and object

"""

import zope.interface


class Registry(zope.interface.Interface):
    """Interface to implement registry"""
    def get(self, key):
        pass

    def add(self, key, value):
        pass
