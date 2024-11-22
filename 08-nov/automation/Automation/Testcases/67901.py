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

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""
import datetime
import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.constants import TEMP_DIR
from AutomationUtils.commonutils import convert_size_string_to_bytes
from Application.Exchange.Parsers import pst_parser
from AutomationUtils.windows_machine import WindowsMachine
from Metallic.hubutils import HubManagement
from Reports.utils import TestCaseUtils
from Web.AdminConsole.Hub.service_catalogue import ServiceCatalogue
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Hub.constants import HubServices, O365AppTypes
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Web.AdminConsole.Office365Pages.constants import ExchangeOnline, O365Region
from Web.Common.exceptions import CVWebAutomationException
import zipfile


class TestCase(CVTestCase):
    """
    Class for executing Basic acceptance Test of
    Metallic_O365_Exchange_Export_Verification:
    Metallic Exchange Online verification for export of user mails to PST and CAB.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Metallic_O365_Exchange_Export_Verification for Service Catalogue"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.navigator = None
        self.service = None
        self.hub_utils = None
        self.tenant_name = None
        self.tenant_user_name = None
        self.app_type = None
        self.users = None
        self.app_name = None
        self.service_catalogue = None
        self.utils = TestCaseUtils(self)
        self.machine = None

    def setup(self):
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()
        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(
            self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['tenantUserName'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.service = HubServices.office365
        self.app_type = O365AppTypes.exchange
        self.service_catalogue = ServiceCatalogue(
            self.admin_console, self.service, self.app_type)
        self.navigator = self.admin_console.navigator
        self.users = self.tcinputs['Users'].split(",")
        self.app_name = self.tcinputs['Name']
        self.log.info("Creating an object for office365 helper")
        self.office365_obj = Office365Apps(
            self.admin_console, self.app_type, is_react=True)
        self.machine = WindowsMachine()

    def run(self):
        """Main function for test case execution"""
        try:
            self.navigator.navigate_to_plan()
            plans = self.office365_obj.get_plans_list()
            server_plan = None
            for plan in plans:
                if O365Region.PLAN_EASTUS2.value in plan.lower():
                    server_plan = plan
                    break

            self.navigator.navigate_to_service_catalogue()
            self.service_catalogue.choose_service_from_service_catalogue(
                service=self.service.value, id=self.app_type.value)
            self.office365_obj.create_office365_app(name=self.app_name,
                                                    global_admin=self.tcinputs['GlobalAdmin'],
                                                    password=self.tcinputs['Password'],
                                                    plan=server_plan)
            self.app_name = self.office365_obj.get_app_name()

            self.office365_obj.add_user(self.users)
            self.office365_obj.run_backup()

            self.verify_export_helper(
                self.tcinputs['ExportUser'],
                ExchangeOnline.PST_TYPE.value,
                "")
            self.verify_export_helper(
                self.tcinputs['ExportUser'],
                ExchangeOnline.CAB_TYPE.value,
                ExchangeOnline.EML_FORMAT.value)
            self.verify_export_helper(
                self.tcinputs['ExportUser2'],
                ExchangeOnline.CAB_TYPE.value,
                ExchangeOnline.MSG_FORMAT.value)

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def verify_export_helper(self, export_user, export_type, file_format):
        export_name = f"{export_type}_{file_format + '_' if file_format != '' else ''}{export_user}_Exchange"
        self.navigator.navigate_to_office365()
        self.office365_obj.access_office365_app(self.app_name)
        self.office365_obj.click_restore_page_action()
        self.office365_obj.access_folder_in_browse(folder_name=export_user)
        export_job_details = self.office365_obj.perform_export_operation(client_name=export_user,
                                                                         export_as=export_type, file_format=file_format)
        num_selected_mails = export_job_details["Number of files transferred"]
        self.navigator.navigate_to_office365()
        self.office365_obj.access_office365_app(self.app_name)
        self.office365_obj.click_restore_page_action()
        self.office365_obj.click_view_exports()
        export_size = self.office365_obj.get_export_size(
            export_name=export_name)

        self.office365_obj.click_download_file(export_name=export_name)
        ext = 'zip' if export_type == ExchangeOnline.CAB_TYPE.value else ExchangeOnline.PST_TYPE.value
        path = TEMP_DIR + "\\" + export_name + "." + ext
        self.utils.wait_for_file_with_path_to_download(
            machine=self.machine, path=path, timeout_period=400, sleep_time=1)
        self.verify_exported_file(
            export_name,
            export_type,
            num_selected_mails,
            path, export_size)

    def verify_exported_file(
            self, export_name, export_type, num_selected_mails, path, export_size):
        if self.machine.check_file_exists(file_path=path):
            file_size = self.machine.get_file_size(
                file_path=path, in_bytes=True)
            if file_size == 0:
                raise CVWebAutomationException('Downloaded file size is 0!')
            else:
                export_size_in_bytes = convert_size_string_to_bytes(
                    export_size)

                # difference of less than 10 KB, needed because of rounded off values
                if abs(file_size - export_size_in_bytes) < 1024 * 10:
                    self.log.info(
                        f"The downloaded file size is equal to export size : export_size")
                else:
                    raise CVWebAutomationException(f'Size of downloaded file ({file_size}) is '
                                                   f'not equal to export size ({export_size})!')
                if export_type == ExchangeOnline.PST_TYPE.value:
                    pst_count = pst_parser.parsepst(path)

                    if pst_count != num_selected_mails:
                        raise CVWebAutomationException(f'Number of mails in PST ({pst_count}) is '
                                                       f'not equal to mails selected for export ({num_selected_mails})!')
                    else:
                        self.log.info(
                            f'Number of mails in PST is equal to mails selected for export : {pst_count}')
                        time.sleep(5)
                        self.machine.delete_file(file_path=path)
                else:
                    # zip file handler
                    zip_count = 0
                    with zipfile.ZipFile(path) as zip_file:
                        for entry in zip_file.infolist():
                            if not entry.is_dir() and (entry.filename.endswith('.eml') or entry.filename.endswith('.msg')):
                                zip_count += 1
                    # list available files in the container
                    zip_file.close()
                    if zip_count != num_selected_mails:
                        raise CVWebAutomationException(f'Number of mails in Zip ({zip_count}) is '
                                                       f'less than mails selected for export ({num_selected_mails})!')
                    else:
                        self.log.info(
                            f'Number of mails in Zip file is equal to mails selected for export : {zip_count}')
                        time.sleep(5)
                        self.machine.delete_file(file_path=path)
        else:
            raise CVWebAutomationException("The file doesn't exist")

    def tear_down(self):
        """Tear Down function of this test case"""
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.app_name)
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)