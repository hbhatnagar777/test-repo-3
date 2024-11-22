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




Two sets of Inputs:

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


class TestCase(CVTestCase):
    """ TestCase class used to execute the test case from here"""

    def __init__(self):
        """Initializing the Test case file"""

        super(TestCase, self).__init__()
        self.name = "Command Center: Multi-Site NAS NDMP Intellisnap Acceptance Test "
        self.browser = None
        self.admin_console = None
        self.nas_template = None
        self.enable_snap = False
        self.tcinputs = {
            "ServerName": None,
            "ArrayVendor": None,
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
            "domainPassword": None,
            "ServerName_2": None,
            "ArrayVendor_2": None,
            "Agent_2": None,
            "StoragePoolName_2": None,
            "SubclientContent_2": None,
            "CIFSShareUser_2": None,
            "CIFSSharePassword_2": None,
            "DestinationFiler_2": None,
            "FilerRestoreLocation_2": None,
            "WindowsDestinationClient_2": None,
            "UnixDestinationClient_2": None,
            "domainUsername_2": None,
            "domainPassword_2": None
        }

    def run(self):
        """Main function for test case execution"""

        try:

            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])
            self.nas_template = NASTemplate(self, self.admin_console)
            self.nas_template.NasTemplate()

            self.nas_template.server_name = self.tcinputs['ServerName_2']
            self.nas_template.array_vendor = self.tcinputs['ArrayVendor_2']
            self.nas_template.agent_name= self.tcinputs['Agent_2']
            self.nas_template.storagepool_name = self.tcinputs['StoragePoolName_2']
            self.nas_template.subclient_content = self.tcinputs['SubclientContent_2']
            self.nas_template.cifs_share_user = self.tcinputs['CIFSShareUser_2']
            self.nas_template.cifs_share_password = self.tcinputs['CIFSSharePassword_2']
            self.nas_template.destination_filer = self.tcinputs['DestinationFiler_2']
            self.nas_template.filer_restore_location = self.tcinputs['FilerRestoreLocation_2']
            self.nas_template.windows_destination_client = self.tcinputs['WindowsDestinationClient_2']
            self.nas_template.unix_destination_client = self.tcinputs['UnixDestinationClient_2']
            self.nas_template.domain_username = self.tcinputs['domainUsername_2']
            self.nas_template.domain_password = self.tcinputs['domainPassword_2']
            self.nas_template.NasTemplate()



        except Exception as err:
            handle_testcase_exception(self, err)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
