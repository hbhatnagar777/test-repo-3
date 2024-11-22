# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case




Inputs:

            ServerName              --      Name of the NAS server

            ArrayVendor             --      Name of the array vendor

            Agent                   --      Name of the agent like CIFS, NFS or NDMP Snap

            StoragePoolName         --      backup location for disk storage

            SubclientContent        --      content to be backed up

            CIFSShareUser           --      CIFS username

            CIFSSharePassword       --      CIFS Password

            DestinationClient       --      Destination client for restore

            FilerRestoreLocation    --     Restore location for filer

            WindowsDestinationClient    -- Destination Windows client for restore

            UnixDestinationClient      --      Destination UNIX client for restore

            DomainUsername          --      Username of the domain

            DomainPassword          --      Password of the domain


"""
from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.NasTemplate import NASTemplate
from Web.Common.page_object import handle_testcase_exception
from Web.AdminConsole.Hub.constants import HubServices
from Web.AdminConsole.Hub.dashboard import Dashboard


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.name = "Command Center: NAS NDMP Intellisnap Acceptance Test "
        self.browser = None
        self.admin_console = None
        self.nas_template = None
        self.enable_snap = True
        self.tcinputs = {
            "ServerName": None,
            "ArrayName": None,
            "Agent": None,
            "StoragePoolName": None,
            "SubclientContent": None,
            "CIFSShareUser": None,
            "CIFSSharePassword": None,
            "DestinationFiler": None,
            "FilerRestoreLocation": None,
            "WindowsDestinationClient": None,
            "UnixDestinationClient": None,
            "domainUsername": None,
            "domainPassword": None
        }

    def run(self):
        """Main function for test case execution"""

        try:

            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            if self.tcinputs.get('Metallic', False):
                hub_dashboard = Dashboard(self.admin_console, HubServices.file_system)
                hub_dashboard.choose_service_from_dashboard()
                hub_dashboard.go_to_admin_console()
            self.nas_template = NASTemplate(self, self.admin_console)
            self.nas_template.NasTemplate()

        except Exception as err:
            handle_testcase_exception(self, err)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
