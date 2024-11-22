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
from AutomationUtils import constants
from Web.AdminConsole.Office365Pages.constants import ExchangeOnline
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Office365Pages.office365_apps import Office365Apps
from Reports.utils import TestCaseUtils
from Web.Common.exceptions import CVTestStepFailure
from Web.AdminConsole.Reports.Custom._components.table import TableViewer


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
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname, enable_ssl=True)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        self.app_name=self.tcinputs["Name"]
        self.users = self.tcinputs['Users'].split(",")
        self.remove_users=self.tcinputs['RemoveUser'].split(",")
        self.exclude_users=self.tcinputs['ExcludeUser'].split(",")
        self.log.info("Creating an object for office365 helper")
        self.tcinputs['office_app_type'] = Office365Apps.AppType.exchange_online
        self.office365_obj = Office365Apps(tcinputs=self.tcinputs,
                                           admin_console=self.admin_console,
                                           is_react=True)

    def run(self):
        """Main function for test case execution"""

        try:
            self.admin_console.close_popup()
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_office365()
            self.office365_obj.create_office365_app()
            self.office365_obj.add_user(users=self.users)
            self.office365_obj.run_backup()
            self.office365_obj.run_ci_job(self.app_name)
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            self.office365_obj.run_backup(update_mail_stats=True)
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            self.admin_console.access_tab(ExchangeOnline.CONTENT_TAB.value)
            for user in self.remove_users:
                self.office365_obj.remove_user_from_content(entity=user)
            for user in self.exclude_users:
                self.office365_obj.exclude_from_backup(entity=user)
            self.admin_console.access_tab(ExchangeOnline.ACCOUNT_TAB.value)
            self.app_stats_dict['Mails'] = int(self.office365_obj.get_app_stat(stat_type='Mails'))
            self.app_stats_dict['Mailboxes'] = int(self.office365_obj.get_app_stat(stat_type='Mailboxes'))
            self.app_stats_dict['Indexed emails'] = int(self.office365_obj.get_app_stat(stat_type='Indexed mails'))
            self.app_stats_dict['Backup size'] = self.office365_obj.get_app_stat(stat_type='Backup size')
            backup_stats=self.office365_obj.get_backup_stats()
            backup_stats_table=self.office365_obj.backup_stats_table_data()
            if ((self.app_stats_dict['Mailboxes']!=int(backup_stats["Included in backup"])
                 or int(backup_stats["Excluded from backup"])!=len(self.exclude_users)
                    or int(backup_stats["Deleted from content"])!=len(self.remove_users))
                    or self.app_stats_dict['Backup size']!=backup_stats_table["Total"][0]
                    or self.app_stats_dict['Mails']!=int(backup_stats_table["Total"][1]))\
                    or self.app_stats_dict['Indexed emails']!=int(backup_stats["Total"]):
                raise CVTestStepFailure("Stats from App and Backup stats panel are mismatched")
            self.log.info("Stats from App and Backup stats panel are verified")
            self.admin_console.access_tab(self.admin_console.props['office365dashboard.tabs.overview'])
            self.office365_obj.click_discovery_stats()
            self.office365_obj.get_discovery_stats()
            self.office365_obj.verify_discovery_stats()
            self.admin_console.access_tab(ExchangeOnline.ACCOUNT_TAB.value)
            self.office365_obj.run_restore()
            self.office365_obj.verify_backedup_mails()
            self.navigator.navigate_to_office365()
            self.office365_obj.access_office365_app(self.app_name)
            self.office365_obj.add_azure_app_and_verify()
            self.office365_obj.verify_app_config_values()
            self.office365_obj.verify_modern_authentication()
            if not self.office365_obj.modern_authentication:
                self.status = constants.FAILED

        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

    def tear_down(self):
        self.navigator.navigate_to_office365()
        self.office365_obj.delete_office365_app(self.tcinputs['Name'])
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)