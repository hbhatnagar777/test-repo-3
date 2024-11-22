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

from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Office365Pages.office365_apps import Office365Apps
from AutomationUtils.commonutils import convert_size_string_to_bytes
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Office365Pages.constants import ExchangeOnline
from AutomationUtils.windows_machine import WindowsMachine
from AutomationUtils.constants import TEMP_DIR
from Application.Exchange.Parsers import pst_parser
import time
import zipfile


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VMware backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "O365 client operations by tenant admin"
        self.browser = None
        self.office365_obj = None
        self.admin_console = None
        self.users=None

        self.app_stats_dict={}
        self.utils = TestCaseUtils(self)

    def setup(self):
        """Setup function for test case execution"""
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname, enable_ssl=True)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.app_name=self.tcinputs["Name"]
        self.users = self.tcinputs['Users'].split(",")
        self.log.info("Creating an object for office365 helper")
        self.tcinputs['office_app_type'] = Office365Apps.AppType.exchange_online
        self.office365_obj = Office365Apps(tcinputs=self.tcinputs,
                                           admin_console=self.admin_console,
                                           is_react=True)
        self.machine = WindowsMachine()

    def run(self):
        """Main function for test case execution"""

        try:
            self.admin_console.close_popup()
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_office365()
            self.office365_obj.create_office365_app()
            self.office365_obj.add_user(users=self.users)
            self.office365_obj.run_backup()

            self.verify_export_helper("filter_1", ExchangeOnline.PST_TYPE.value, "", self.tcinputs["filter_1"])

            self.verify_export_helper("filter_2", ExchangeOnline.CAB_TYPE.value, ExchangeOnline.EML_FORMAT.value,
                                      self.tcinputs["filter_2"])

            self.verify_export_helper("filter_3", ExchangeOnline.CAB_TYPE.value, ExchangeOnline.MSG_FORMAT.value,
                                      self.tcinputs["filter_3"])

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def verify_export_helper(self, export_filter_name, export_type, file_format,filter_value=None):
        """
        Perform export operation on the client
        export_filter_name (str) : Export filter name
        export_type   (str) : Type of Export that needs to be done
                            For Exchange agents only
                            Valid Arguments
                                -- PST  (for PST export)
                                -- CAB  (for CAB export)
        file_format (str)   :   Export file format (EML or MSG)
        filter_vale (dict)  :   filters to apply in browse page
        """
        export_name = f"{export_type}_{file_format + '_' if file_format != '' else ''}{export_filter_name}_Exchange"
        self.navigator.navigate_to_office365()
        self.office365_obj.access_office365_app(self.app_name)
        self.office365_obj.click_restore_page_action()
        export_job_details = self.office365_obj.perform_export(export_name=export_filter_name,
                                                                             export_as=export_type,
                                                                             file_format=file_format,
                                                                             filter_value=filter_value)
        num_selected_mails = int(export_job_details["Number of files transferred"])
        self.navigator.navigate_to_office365()
        self.office365_obj.access_office365_app(self.app_name)
        self.office365_obj.click_restore_page_action()
        self.office365_obj.click_view_exports()
        export_size = self.office365_obj.get_export_size(
                export_name=export_name)

        self.office365_obj.download_export(export_name=export_name)
        ext = 'zip' if export_type == ExchangeOnline.CAB_TYPE.value else ExchangeOnline.PST_TYPE.value
        path = TEMP_DIR + "\\" + export_name + "." + ext
        self.utils.wait_for_file_with_path_to_download(
                machine=self.machine, path=path, timeout_period=400, sleep_time=1)
        self.verify_exported_file(
                export_name,
                export_type,
                num_selected_mails,
                path, export_size)

    def verify_exported_file(self, export_name, export_type, num_selected_mails, path, export_size):
        """
        Verify export file downloaded or not, size of the export file and no of message in the export file
        Args:
            export_name(str)    :   Export file name
            export_type   (str) : Type of Export that needs to be done
                            For Exchange agents only
                            Valid Arguments
                                -- PST  (for PST export)
                                -- CAB  (for CAB export)
            num_selected_mails(int) :   Number of files transferred in export job
            path(str)               :   Path of the export file downloaded in system
            export_size(str)        :   Size of the export file
        """
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
                        time.sleep(30)
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
                        self.log.info(f'Number of mails in Zip file is equal to mails selected for export : {zip_count}')
                        time.sleep(30)
                        self.machine.delete_file(file_path=path)
        else:
            raise CVWebAutomationException("The file doesn't exist")

    def tear_down(self):
        """Tear down function of this testcase"""
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.tcinputs['Name'])
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)