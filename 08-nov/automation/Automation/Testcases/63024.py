# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ----------------------------------------------------------------------------
"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --   initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Server.License.lic_summary_helper import LicenseHelper
from Web.Common.cvbrowser import BrowserFactory
from Web.WebConsole.webconsole import WebConsole


class TestCase(CVTestCase):
    """ basic acceptance test case for license summary """

    def __init__(self):
        """Initializing the Test case file """
        super(TestCase, self).__init__()
        self.name = """Validate Sub client peak usage page of
         license summary worldwide at group level report """
        self.factory = None
        self.browser = None
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.clientname = None
        self.groupname = None
        self.commcells_to_add = None
        self.webconsole = None
        self.grouphelper = None
        self.tcinputs = {
            'groupname': None,
            'commcells_to_add': None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""

        self.groupname = self.tcinputs['groupname']
        self.commcells_to_add = self.tcinputs['commcells_to_add'].split(",")
        self.factory = BrowserFactory()
        self.browser = self.factory.create_browser_object()
        self.browser.open()
        self.webconsole = WebConsole(self.browser, self.commcell.webconsole_hostname)
        self.webconsole.login(self.inputJSONnode['commcell']['commcellUsername'],
                              self.inputJSONnode['commcell']['commcellPassword'])
        self.grouphelper = LicenseHelper(self.groupname, self.commcells_to_add, self.webconsole, self.log)

    def run(self):
        try:
            self.grouphelper.goto_commcellgroup()
            self.grouphelper.create_commcell_group()
            self.grouphelper.validate_clientgroup()
            self.grouphelper.access_clientgroup()
            self.grouphelper.generate_summary_and_validate(spu = True)
            self.grouphelper.delete_commcell_group()
        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        """To clean-up the test case environment created"""
        self.browser.close()
