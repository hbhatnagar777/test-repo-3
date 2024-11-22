# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

     run()                                      --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Database.auto_discover_helper import AutoDiscoverApp


class TestCase(CVTestCase):
    """Class for executing autodiscover application feature test case
    at server group level"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Verify autodiscover application feature at \
        server group level"
        self.tcinputs = {
            "ClientHostName": None,
            "ClientUserName": None,
            "ClientPassword": None,
            "ClientGroupName": None,
            "ostype": None,
            "Client": None
        }
        self.auto_discover_object = None

    def run(self):
        """Main function for test case execution"""

        try:
            if 'oracle_' in self.tsName.lower():
                agent_name = 'Oracle'
            self.log.info("initializing autodiscover app object...")
            self.auto_discover_object = AutoDiscoverApp(self.commcell)
            self.log.info("autodiscover object is {0}".format(self.auto_discover_object))

            self.log.info("client group operations...")
            self.auto_discover_object.client_group_with_auto_discover(
                self.tcinputs['ClientGroupName'])
            self.log.info("install operations...")
            self.auto_discover_object.install_client(self.tcinputs["Client"],
                                                     self.tcinputs["ClientUserName"], self.tcinputs["ClientPassword"],
                                                     ostype=self.tcinputs["ostype"])
            self.log.info("client association operations...")
            self.auto_discover_object.add_client_to_client_group(self.tcinputs["Client"])
            if self.tcinputs["ostype"].lower() != "windows":
                readpattern1 = "AutoDetectApp::Discover() - Application [Oracle], Package Id [1204] WAS discovered"
                readpattern2 = "AutoDetectApp::PullInstall() - Application [Oracle], package Id [1204] will be installed"
            else:
                readpattern1 = "AutoDetectApp::Discover() - Application [Oracle], Package Id [352] WAS discovered"
                readpattern2 = "AutoDetectApp::PullInstall() - Application [Oracle], package Id [352] will be installed"
            readpattern = "AutoDetectApp::AutoDetectRegCallBack()- Auto detect application is enabled"
            self.log.info("agent and autodiscover validations...")
            self.auto_discover_object.validate_auto_discover(agent_name,
                                                             readpattern, readpattern1, readpattern2)
            self.log.info("disable autodiscover option at client group level...")
            self.auto_discover_object.client_group_obj.disable_auto_discover()
            self.log.info("Uninstall operations...")
            self.auto_discover_object.uninstall_client(self.tcinputs["Client"])

        except Exception as exp:
            self.log.error('Failed with error: {0} exp '.format(str(exp)))
            self.result_string = str(exp)
            self.status = constants.FAILED
