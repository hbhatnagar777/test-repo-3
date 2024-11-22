# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This file provides helper methods for operations on tags entity

Class:
    EntityTagsHelper -> EntityTags

Methods:
    add_tags    : Method to create tags

Properties:
    tags_name   : name of tag
"""
import time

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Tags import EntityTags


class EntityTagsHelper:
    """
        This class provides helpers methods for performing operations on Entity Tags
    """

    def __init__(self, admin_console: AdminConsole):
        """Initializes EntityTagsHelper object"""
        self.admin_console = admin_console
        random_string = str(time.time()).split(".")[0]
        self._tag_name = f"EntityTag{random_string}"
        self.tags_obj = EntityTags(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.service_commcells = None

    @property
    def tag_name(self):
        """Returns tag name"""
        return self._tag_name

    @tag_name.setter
    def tag_name(self, value):
        """Sets tag name"""
        self._tag_name = value

    def add_tag(self):
        """Helper method to create entity Tag"""
        self.navigator.navigate_to_tags(True)
        self.tags_obj.add(self.tag_name)

    def create_gcm(self, service_commcells=None):
        """Helper method to create entity tag in GCM"""
        self.tag_name = "GCM" + self.tag_name
        self.add_tag()
        return self.tag_name
