# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be performed on the
Events page on the AdminConsole

Class:

    Events() -> AdminConsole() -> AdminConsoleBase() -> object()

Functions:

open_event()          -- select and open an event of the specified event_id
list_of_events_for_job() -- display the events for job with the id as job_id

"""
from Web.AdminConsole.Components.table import Rtable
from Web.Common.page_object import PageService


class Events:
    """
    This class provides the function or operations that can be performed on the Events page
    """

    def __init__(self, admin_console):
        self.__admin_console = admin_console
        self.__table = Rtable(self.__admin_console)

    @PageService()
    def open_event(self, event_id):
        """Opens an event with a given ID

            event_id - id of the event to be selected and opened
        """
        self.__table.access_link(event_id)

    @PageService()
    def show_critical_events(self, day=False):
        """Shows all the critical events
        """
        if day:
            self.__table.view_by_title("Critical (last 24 hours)")
        else:
            self.__table.view_by_title("Critical")

    @PageService()
    def show_major_events(self):
        """Shows all the major events
        """
        self.__table.view_by_title("Major")

    @PageService()
    def show_minor_events(self):
        """Shows all the minor events
        """
        self.__table.view_by_title("Minor")

    @PageService()
    def show_info_events(self):
        """Shows all the info events
        """
        self.__table.view_by_title("Info")

    @PageService()
    def show_focused_events(self):
        """Shows all the default events
        """
        self.__table.view_by_title("Focused (last 24 hours)")

    @PageService()
    def show_all_events(self):
        """Shows all the default events
        """
        self.__table.view_by_title("All")

    @PageService()
    def list_of_events_for_job(self, job_id):
        """Lists all the events for a job
            job_id - id of the job to list the events for
        """
        self.__admin_console.log.info("List of events for the job {0} will be displayed as a dictionary"
                      .format(job_id))
        self.__table.search_for(job_id)
        return self.__table.get_table_data()
