# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


'''
Test case to check the basic acceptance of create new nerworks share and enable archiving rules for
point solution project

functions,
1. creation network share.
2. edit newly created network share server content
3. run analytics job
2. enable archiving rules

Pre-requisites :
1. Index server should be configured
2. plan should be configured
'''

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Archiving.Archiving import Archiving
from Web.AdminConsole.Helper.LoginHelper import LoginMain
from Web.Common.cvbrowser import BrowserFactory


class TestCase(CVTestCase):

    ''' Basic Acceptance Test for create new network share server, enable archiving, edit file server properties
         and run analytics job from solutions -> archiving page in AdminConsole '''

    def __init__(self):
        '''
       Initializing the Test case file
        '''
        super(TestCase, self).__init__()
        self.name = "Acceptance Test: Create network share, edit file servers, \
                    run analytics job and enable archiving from Adminconsole"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.utils = TestCaseUtils(self)
        self.driver = None
        self.tcinputs = {
            'ImpersonateUser': None,
            'ImpersonatePassword': None,
            'NWShareName': None,
            'indexEngine': None,
            'src_path': None,
            'src_path2': None,
            'accessNode': None,
            'plan': None,
        }

    def run(self):
        try:
            self.log.info("Started executing  testcase 54171")
            self.log.info(" Initialize browser objects ")
            factory = BrowserFactory()
            browser = factory.create_browser_object()
            browser.open()

            self.driver = browser.driver

            self.log.info("Creating the login object")
            login_obj = LoginMain(self.driver, self.csdb)

            login_obj.login(self.inputJSONnode['commcell']['commcellUsername'],
                            self.inputJSONnode['commcell']['commcellPassword'])
            self.log.info(
                "login successful, Creating the Archiving page object")

            archiving_obj = Archiving(self.driver)

            self.log.info(
                "Created Archiving Object. now start launch to Solutions -> Archiving")
            archiving_obj.navigate_to_archiving()

            # Create new File server
            archiving_obj.create_new_server(
                self.tcinputs['indexEngine'],
                self.tcinputs['NWShareName'],
                self.tcinputs['src_path'],
                self.tcinputs['ImpersonateUser'],
                self.tcinputs['ImpersonatePassword'],
                self.tcinputs['accessNode'])

            # click Edit file server action for selected file server
            self.log.info(
                "Click Edit filer server action for selected network share")
            archiving_obj.select_action_item(
                self.tcinputs['NWShareName'], 'Edit file server', 'Actions')

            # Edit file server content
            src_path2 = self.tcinputs['src_path2']
            archiving_obj.edit_file_server_content(src_path2)

            # will enable this check later
            '''
            try:
                # Edit file server collect owner info
                archiving_obj.editfileserverownerprop(self.tcinputs['NWShareName'])
            except Exception as exp:
                self.test_individual_status = False
                self.test_individual_failure_message = str(exp)
                raise exp
            '''

            # launching back to archiving page
            self.log.info("launching back to Archiving page")
            archiving_obj.navigate_to_archiving()

            # run analytics job for selected network share server
            archiving_obj.run_analytic_job(self.tcinputs['NWShareName'])

            # launching back to archiving page
            self.log.info("launching back to Archiving page")
            archiving_obj.navigate_to_archiving()

            # Enable archiving rules for newly create network file server
            archiving_obj.enable_archiving_rules(
                self.tcinputs['NWShareName'],
                self.tcinputs['plan'],
                self.tcinputs['accessNode'])

        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            raise exp
        finally:
            archiving_obj.logout()
            self.driver.quit()
            browser.close()
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
