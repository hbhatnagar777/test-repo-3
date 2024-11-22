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

    erverName              --      Name of the NAS server

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
        self.name = "Command Center: NAS NDMP Streaming Acceptance Test"
        self.browser = None
        self.admin_console = None
        self.nas_template = None
        self.enable_snap = False
        self.agent_name1 = "CIFS"
        self.agent_name2 = "NFS"
        self.agent_name3 = "NDMP"
        self.tcinputs = {
            "ServerName": None,
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
            self.nas_template = NASTemplate(self, self.admin_console)
            self.nas_template.cleanup()
            self.log.info("Adding a new plan: %s", self.nas_template.plan_name)
            self.__navigator = self.admin_console.navigator
            self.__navigator.navigate_to_plan()
            self.nas_template.plan_obj.create_server_plan(plan_name=self.nas_template.plan_name,
                                                          storage=self.nas_template.storagepool_name)
            self.log.info("successfully created plan: %s", self.nas_template.plan_name)
            ndmpuser = self.tcinputs['ndmpUser']
            ndmppass = self.tcinputs['ndmpPassword']
            ndmpk = {'impersonate_user': {'username': ndmpuser, 'password': ndmppass},
                     'access_nodes': self.tcinputs.get('NDMPAccessNode', None),
                     'credential_manager': self.tcinputs.get('CredentialManager', False),
                     'credential_manager_name': self.tcinputs.get('CredentialManagerName', None),
                     'client_level_content': self.tcinputs.get('ClientLevelContent', None)}
            cifsuser = self.tcinputs['CIFSShareUser']
            cifspass = self.tcinputs['CIFSSharePassword']
            cifsk = {'impersonate_user': {'username': cifsuser, 'password': cifspass},
                     'access_nodes': self.tcinputs['CIFSAccessNode'].split(',') if self.tcinputs['CIFSAccessNode'] else None,
                     'client_level_content': self.tcinputs.get('ClientLevelContent', None)}
            nfsk = {'access_nodes': self.tcinputs['NFSAccessNode'].split(',') if self.tcinputs['NFSAccessNode'] else None,
                    'client_level_content': self.tcinputs.get('ClientLevelContent', None)}
            self.__navigator.navigate_to_file_servers()
            self.admin_console.access_tab("File servers")
            self.nas_template.rfs_servers.add_nas_client(name=self.nas_template.server_name,
                                                         host_name=self.nas_template.server_name,
                                                         plan=self.nas_template.plan_name,
                                                         vendor=self.nas_template.vendor,
                                                         cifs=cifsk,
                                                         nfs=nfsk,
                                                         ndmp=ndmpk
                                                         )
            self.__navigator.navigate_to_file_servers()
            self.admin_console.access_tab("File servers")
            self.nas_template.rfs_servers.access_server(self.nas_template.server_name)
            self.nas_template.rfs_servers.access_agent(self.agent_name1)
            self.nas_template.rfs_adv.retire_agent()
            self.__navigator.navigate_to_file_servers()
            self.admin_console.access_tab("File servers")
            self.nas_template.rfs_servers.access_server(self.nas_template.server_name)
            self.nas_template.rfs_servers.access_agent(self.agent_name2)
            self.nas_template.rfs_adv.retire_agent()
            self.__navigator.navigate_to_file_servers()
            self.admin_console.access_tab("File servers")
            self.nas_template.rfs_servers.access_server(self.nas_template.server_name)
            self.nas_template.rfs_servers.access_agent(self.agent_name3)
            self.nas_template.rfs_adv.retire_agent()
            self.__navigator.navigate_to_file_servers()
            self.admin_console.access_tab("File servers")
            self.nas_template.rtable.reload_data()
            if self.nas_template.rfs_servers.is_client_exists(self.nas_template.server_name):
                raise Exception("Last iDA retire, didn't retire the client, please check")
            self.nas_template.cleanup()
        except Exception as err:
            handle_testcase_exception(self, err)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
