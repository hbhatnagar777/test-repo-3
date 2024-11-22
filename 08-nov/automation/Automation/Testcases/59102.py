# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    filters_validate() -- Function to validate whether the filters were set correctly or not

    validate_contacts() -- Function to validate contacts

    validate_email_settings() -- Function to validate email settings

    validate_file_exceptions() -- Function to validate file exceptions

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
import time

from cvpysdk.backupset import Backupsets
from cvpysdk.commcell import Commcell

from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.mail_box import MailBox
from FileSystem.FSUtils.fshelper import FSHelper
from Web.AdminConsole.AdminConsolePages.Companies import Companies
from Web.AdminConsole.AdminConsolePages.CompanyDetails import CompanyDetails
from Web.AdminConsole.AdminConsolePages.Users import Users
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.Helper.CompanyHelper import MSPHelper
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception, TestStep
from cvpysdk.instance import Instances


class TestCase(CVTestCase):
    """Class for executing this test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "MSP Testcase :Edit Contacts, Email settings, Sites and File Exceptions and validations"
        self.company_name = None
        self.company_alias = None
        self.config = get_config()
        self.MSP_obj = None
        self.tcinputs = {
            "StoragePolicyName": None,
            "company": {
                'name': None,
                'username': None
            }
        }

    def setup(self):
        """Setup function of this test case"""
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])

        commcell = Commcell(self.commcell.webconsole_hostname,
                            commcell_username=self.tcinputs['company']['username'],
                            commcell_password=self.config.MSPCompany.tenant_password,
                            verify_ssl=False)
        self.navigator = self.admin_console.navigator
        self.__table = Table(self.admin_console)
        self.__company_details = CompanyDetails(self.admin_console)
        self.MSP_obj = MSPHelper(self.admin_console, self.commcell)
        self.user = Users(self.admin_console)
        self.__companies = Companies(self.admin_console)

        all_clients = list(commcell.clients.all_clients.keys())
        self.client = None
        for client in all_clients:
            if self.commcell.clients.get(client).is_ready:
                self.client = self.commcell.clients.get(client)
                break

        self.MSP_obj.company_name = self.company_name = self.tcinputs['company']['name']
        self.MSP_obj.company_alias = self.company_alias = self.tcinputs['company']['username'].split('\\')[0]
        self.random = str(time.time()).split(".")[0]

    def filters_validate(self):
        """Function to validate whether the filters were set correctly or not

        Args:
            client        (obj)  --  Client object.

        """

        self.agent = self.client.agents.get('File System')
        self.instance = self.agent.instances.get('DefaultInstanceName')
        self.machine = Machine(machine_name=self.client)
        self.helper = FSHelper(self)
        self.helper.populate_tc_inputs(self, mandatory=False)
        self.log.info("Creating test data")

        if self.machine.os_info == "WINDOWS":
            filter_extensions = str(self.windows_filters) + ",*.bcd"

        elif self.machine.os_info == "UNIX":
            filter_extensions = str(self.unix_filters) + ",*.tar"

        filter_extension = filter_extensions.replace('*', '')
        self.helper.generate_testdata(filter_extension.split(','))
        install_dir = self.client.install_directory
        content_path = self.machine.join_path(install_dir, "Test")
        sub_content = content_path.split('*')
        self.backupset_name = "test_59102"

        self.helper.create_backupset(self.backupset_name, delete=True)
        self.helper.create_subclient("Filter", self.tcinputs['StoragePolicyName'], sub_content)

        win_filters1 = str(self.windows_filters).split(',')
        unix_filters1 = str(self.unix_filters).split(',')
        time.sleep(60)
        self.helper.run_backup("FULL")
        self.helper.validate_filters(win_filters1, unix_filters1)

    @test_step
    def validate_contacts(self):
        """Method to validate contacts on company page"""
        self.__company_details.edit_contacts(contact_names=[f'TestName{self.random}'])
        self.MSP_obj.contact_name = [f'TestName{self.random}']
        self.MSP_obj.validate_contacts(is_edited=True)

    @test_step
    def validate_email_settings(self):
        """Method to validate email settings on company page"""
        self.MSP_obj.sender_email = self.company_name.replace(' ', '') + '@' \
            + self.company_alias.replace(' ', '') + '.com'
        self.MSP_obj.sender_name = self.company_name + self.company_alias
        self.__company_details.edit_sender_email(sender_name=self.MSP_obj.sender_name,
                                                 sender_email=self.MSP_obj.sender_email)
        self.MSP_obj.validate_email_settings(is_edited=True)

    @test_step
    def validate_file_exceptions(self):
        """Method to validate file exceptions on company page"""
        self.windows_filters = "*.doc,*.txt"
        self.unix_filters = "*.dmg,*.pkg"

        file_except_dict = {"windows_path": str(self.windows_filters).split(','),
                            "unix_path": str(self.unix_filters).split(',')
                            }
        self.admin_console.navigator.navigate_to_companies()
        self.__companies.access_company(self.company_name)
        self.__company_details.edit_company_file_exceptions(file_except_dict)
        new_dict = {
            'Windows': file_except_dict["windows_path"],
            'Unix': file_except_dict["unix_path"]
        }
        self.MSP_obj.file_exceptions = new_dict
        self.log.info("The filters have been set")

        self.filters_validate()

    def check_default_setting(self):
        email_settings = self.__company_details.company_info(tile_name=['Email settings'])['Email settings']
        if email_settings:
            raise Exception("Email settings should be Not Configured at this stage")

        file_excep = self.__company_details.company_info(tile_name=['File exceptions'])['File exceptions']
        if file_excep:
            raise Exception("File exceptions should be Not Configured at this stage")

    def run(self):
        """Run function of this test case"""
        try:
            self.navigator.navigate_to_users()
            self.navigator.switch_company_as_operator(self.company_name)
            self.user.add_local_user(name=f'TestName{self.random}', email=f'tempUser{self.random}@xyz.com',
                                     groups=[self.company_alias + "\\Tenant Admin"],
                                     password=self.config.MSPCompany.tenant_password)
            self.navigator.switch_company_as_operator("Reset")
            self.navigator.navigate_to_companies()
            self.__companies.access_company(self.company_name)

            self.validate_contacts()

            self.validate_email_settings()

            self.validate_file_exceptions()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.log.info('Deleting the created user')
        self.navigator.navigate_to_users()
        # self.user.delete_user(self.company_alias + f'\\tempUser{self.random}')
        self.commcell.refresh()
        self.commcell.users.delete((self.company_alias + f'\\tempUser{self.random}').lower())

        self.log.info("Deleting create backupset")
        backupset = Backupsets(self.agent)
        backupset.delete(self.backupset_name)

        self.admin_console.logout_silently(self.admin_console)
        self.browser.close_silently(self.browser)
