# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

'''
Test case to check the basic acceptance of change permissions for network shares
functions over,
1. launch to adminconsole solutions -> governance apps -> entitlement management page
2. change file permissions

Pre-requisites :
1. Index server should be configured
2. network file server should be created under solutions archivings page
3. collect owner info should be enabled and data analytics job should already run
'''

from AutomationUtils.cvtestcase import CVTestCase
from Reports.utils import TestCaseUtils
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.GovernanceAppsPages.PermissionReport import PermissionReport
from Web.Common.cvbrowser import BrowserFactory, Browser


class TestCase(CVTestCase):

    ''' Basic Acceptance Test for change file/folder permissions on Governance Apps
        -> Entitlement Management page on AdminConsole
    '''

    def __init__(self):
        '''
       Initializing the Test case file
        '''
        super(TestCase, self).__init__()
        self.name = "Change file/folder permissions and owners on Entitlement Management page"
        self.admin_console = None
        self.test_individual_failure_message = ""
        self.utils = TestCaseUtils(self)

        self.tcinputs = {
            'NWShareName': None,
            'src_path': None,
            'file_name': None,
            'new_user': None,
        }

    def run(self):
        try:

            self.log.info("Started executing testcase 54172")
            self.log.info(" Initialize browser objects ")
            factory = BrowserFactory()
            browser = factory.create_browser_object()
            browser.open()
            self.driver = browser.driver
            self.admin_console = AdminConsole(
                browser,
                self.commcell.webconsole_hostname,
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword'])
            self.admin_console.login(
                self.inputJSONnode['commcell']['commcellUsername'],
                self.inputJSONnode['commcell']['commcellPassword'])

            self.admin_console.navigator.navigate_to_governance_apps()

            pr_obj = PermissionReport(self.admin_console)

            pr_obj.select_permission_report()

            # Change file permission for specified client on permission
            # management page
            nwsharename = self.tcinputs['NWShareName']
            src_path = self.tcinputs['src_path']
            file_name = self.tcinputs['file_name']
            new_user = self.tcinputs['new_user']
            uname = pr_obj.change_file_acl_for_client(
                nwsharename, src_path, file_name, new_user)

            # revert all permission changes for selected file
            pr_obj.revert_acls(uname)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(browser)
