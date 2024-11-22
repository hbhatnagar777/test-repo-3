# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""All the webconsole operations which needs to adapt to Admin Console goes here """
from Web.Common.cvbrowser import Browser


class WebConsoleAdapter:

    def __init__(self, admin_console, browser: Browser):
        """
        Args:
            admin_console: adminconsole object
            browser      : browser object
        """
        self.admin_console = admin_console
        self.browser = browser

    def wait_till_load_complete(self):
        """Checks for the notification bar at the top of the browser."""
        self.admin_console.wait_for_completion()

    def get_all_unread_notifications(self):
        """Gets the notification text
        Returns:

            notification_text (str): the notification string

        """
        return [self.admin_console.get_notification()]
