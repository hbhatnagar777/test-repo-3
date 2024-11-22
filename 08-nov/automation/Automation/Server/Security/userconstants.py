# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file to maintain all the constants used by User related operations."""

class USERGROUP(object):
    """Constants maintaining the user group details"""

    VIEW_ALL = 'View All'
    MASTER = 'master'
    LAPTOP_USERS = 'Laptop Users'

class WebConstants(object):
    """Web related constants"""

    def __init__(self, host_name):
        """initialize the web constants
        Args:
            host_name   (str)   --  host name of CommCell

        """
        self._host_name = host_name

    @property
    def webconsole_url(self):
        """Returns the webconsole url"""
        return 'http://{0}/webconsole'.format(self._host_name)

    @property
    def adminconsole_url(self):
        """Returns the admin console url."""
        return 'http://{0}/adminconsole'.format(self._host_name)
