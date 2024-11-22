# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Custom reports: Security roles for data sources"""
from selenium.common.exceptions import NoSuchElementException

from AutomationUtils import config
from AutomationUtils.cvtestcase import CVTestCase

from Reports.Custom.utils import CustomReportUtils

from Web.Common.cvbrowser import (
    BrowserFactory,
    Browser
)
from Web.Common.exceptions import (
    CVTestCaseInitFailure,
    CVTestStepFailure,
    CVWebAutomationException)
from Web.Common.page_object import TestStep

from Web.AdminConsole.Reports.manage_datasources import (
    CommcellDataSource,
    SQLServerDataSource
)
from Web.AdminConsole.adminconsole import AdminConsole


class TestCase(CVTestCase):
    """TestCase class used to execute the test case from here."""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Custom reports: Security roles for data sources"
        self.browser = None
        self.adminconsole = None
        self.utils = None
        self.navigator = None
        self.automation_username = "tc49534"
        self.commcell_datasource = None
        self.datasource = None
        self.sql_server_db_username = None
        self.sql_server_db_password = None
        self.automation_password = None


    def cleanup(self):
        """Cleans up the roles and users"""
        ds_roles = [["Add Datasource"], ["Edit Datasource"], ["Delete Datasource"], ["Query Datasource"]]

        # Deletes roles
        if self.commcell.roles.has_role("Report Management"):
            self.log.info("Deleting role 'Report Management'")
            self.commcell.roles.delete("Report Management")

        if self.commcell.roles.has_role(ds_roles[0][0]):
            self.log.info(f"Deleting role '{ds_roles[0][0]}'")
            self.commcell.roles.delete(ds_roles[0][0])

        if self.commcell.roles.has_role(ds_roles[1][0]):
            self.log.info(f"Deleting role '{ds_roles[1][0]}'")
            self.commcell.roles.delete(ds_roles[1][0])

        if self.commcell.roles.has_role(ds_roles[2][0]):
            self.log.info(f"Deleting role '{ds_roles[2][0]}'")
            self.commcell.roles.delete(ds_roles[2][0])

        if self.commcell.roles.has_role(ds_roles[3][0]):
            self.log.info(f"Deleting role '{ds_roles[3][0]}'")
            self.commcell.roles.delete(ds_roles[3][0])

        # Deleting User
        if self.commcell.users.has_user(self.automation_username):
            self.log.info("Deleting existing user %s" % self.automation_username)
            self.commcell.users.delete(self.automation_username, "admin")

    def create_roles_and_user(self):
        """Creates User"""
        ds_roles = [["Add Datasource"], ["Edit Datasource"], ["Delete Datasource"], ["Query Datasource"]]

        # Creates roles
        self.commcell.roles.add("Report Management", ["Report Management"])
        self.commcell.roles.add(ds_roles[0][0], ds_roles[0])
        self.commcell.roles.add(ds_roles[1][0], ds_roles[1])
        self.commcell.roles.add(ds_roles[2][0], ds_roles[2])
        self.commcell.roles.add(ds_roles[3][0], ds_roles[3])

        # Adding User
        self.commcell.users.add(self.automation_username, self.automation_username,
                                "reports@testing.com", None, self.automation_password)

        dict_ = {"assoc1":
                 {
                     'clientName': [self.commcell.commserv_name],
                     'role': ["Report Management"]
                 }
                 }
        self.commcell.users.get(self.automation_username).update_security_associations(dict_, "UPDATE")

    def init_user_browser(self):
        """Initializes user browser"""
        self.browser = BrowserFactory().create_browser_object(name="User Browser")
        self.browser.open()
        self.adminconsole = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.adminconsole.login(self.automation_username, self.automation_password)
        self.utils.webconsole = self.adminconsole
        self.navigator = self.adminconsole.navigator

    def init_tc(self):
        """Initializes the Testcase"""
        try:
            self.utils = CustomReportUtils(self, username=self.inputJSONnode['commcell']['commcellUsername'],
                                           password=self.inputJSONnode['commcell']['commcellPassword'])
            self.automation_password = self.tcinputs["auto_create_user_pwd"]
            self.sql_server_db_username = self.tcinputs["sql_server_db_username"]
            self.sql_server_db_password = self.tcinputs["sql_server_db_password"]
            self.cleanup()
            self.create_roles_and_user()
            self.init_user_browser()
        except Exception as exception:
            raise CVTestCaseInitFailure(exception) from exception

    def relogin(self):
        """Re logins to the adminconsole"""
        self.adminconsole.logout()
        self.adminconsole = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.adminconsole.login(self.automation_username, self.automation_password)

        try:
            self.navigator.navigate_to_manage_datasources()
        except NoSuchElementException:
            raise CVTestStepFailure("User is not able to access datasources configuration after 'Add Datasource' role")

    @test_step
    def verify_invisibility_of_data_sources_under_navigation(self):
        """Verifies the user is unable to add datasources without 'Add datasource role'"""
        try:
            self.navigator.navigate_to_manage_datasources()
            raise CVTestStepFailure("User is able to access datasources configuration without 'Add Datasource'  role")
        except NoSuchElementException:
            pass

    @test_step
    def addition_of_cs_and_db_ds_edition_and_deletion(self):
        """Verifies the user is able to add datasources with 'Add datasource role' as well as edit and delete
        the one created by him"""
        dict_ = {"assoc":
                 {
                     'commCellName': [self.commcell.commserv_name],
                     'role': ["Add Datasource"]
                 }
                 }

        self.commcell.users.get(self.automation_username).update_security_associations(dict_, "UPDATE")
        self.relogin()

        self.commcell_datasource = CommcellDataSource(self.adminconsole)
        self.datasource = SQLServerDataSource(self.adminconsole)

        # Cleanup
        if self.tcinputs['commserv_name'] in self.commcell_datasource.get_data_source_names():
            self.commcell_datasource.delete_data_source(self.tcinputs['commserv_name'])

        if 'Automation SQL Server DS' in self.datasource.get_data_source_names():
            self.datasource.delete_data_source("Automation SQL Server DS")

        # Adds Datasources
        _CONSTANTS = config.get_config()
        self.commcell_datasource.add_data_source(self.tcinputs['remote_commcell'],
                                                 self.tcinputs['remote_commcell_name'],
                                                 self.tcinputs['remote_commcell_pwd'])
        self.datasource.add_data_source("Automation SQL Server DS", self._tcinputs["hostname"],
                                        "commvault", self.sql_server_db_username,
                                        self.sql_server_db_password)

        data_source = self.commcell_datasource.get_data_source_names()
        if data_source:
            raise CVTestStepFailure(
                f"User able to see commcell datasource: {data_source} without 'Query Datasource Permission'")

        self.datasource.edit_data_source("Automation SQL Server DS", "Automation SQL Server DS Edited",
                                         self._tcinputs["hostname"], "commvault",
                                         self.sql_server_db_username, self.sql_server_db_password)
        self.datasource.delete_data_source("Automation SQL Server DS Edited")

    @test_step
    def addition_of_db_ds_by_admin_user(self):
        """Admin user adds a new Remote data source"""
        with BrowserFactory().create_browser_object() as browser:
            with AdminConsole(browser, self.commcell.webconsole_hostname,
                              username=self.inputJSONnode['commcell']['commcellUsername'],
                              password=self.inputJSONnode['commcell']['commcellPassword']) as adminconsole:
                adminconsole.navigator.navigate_to_manage_datasources()
                datasource_2 = SQLServerDataSource(adminconsole)
                if 'SQL Server DS by admin user' in datasource_2.get_data_source_names():
                    datasource_2.delete_data_source("SQL Server DS by admin user")
                datasource_2.add_data_source("SQL Server DS by admin user", self._tcinputs["hostname"],
                                             "commvault", self.sql_server_db_username,
                                             self.sql_server_db_password)

        self.browser.driver.refresh()
        data_source = self.datasource.get_data_source_names()
        if data_source:
            raise CVTestStepFailure(
                f"User able to see Remote datasource: {data_source} without 'Query Datasource Permission'")

    @test_step
    def validate_visibility_and_immutability_of_ds_created_by_others(self):
        """Verifies the user is able to view commcell datasources with 'Query datasource role'
        and unable to edit or delete datasources created by others"""
        dict_ = {"assoc":
                 {
                     'commCellName': [self.commcell.commserv_name],
                     'role': ["Query Datasource"]
                 }
                 }
        self.commcell.users.get(self.automation_username).update_security_associations(dict_, "UPDATE")
        self.relogin()

        data_source = self.commcell_datasource.get_data_source_names()
        if self.tcinputs['commserv_name'] not in data_source:
            raise CVTestStepFailure(f"User unable to get commcell with 'Query Datasource Permission'.\n"
                                    f"Found commcell datasources :{data_source}")

        # User tries to manipulate on datasource created by admin user
        try:
            self.datasource.edit_data_source("SQL Server DS by admin user", "Modify by user having no permission",
                                             self._tcinputs["hostname"],
                                             "commvault", self.sql_server_db_username,
                                             self.sql_server_db_password)
            raise CVTestStepFailure("User is able to edit database datasources of other users without edit permission")
        except CVWebAutomationException as excp:
            if "user does not have required capability to edit data sources" not in str(excp):
                raise CVTestStepFailure(
                    f"Expected exception string 'user does not have required capability to edit data sources'.\n"
                    f" Got {excp}")
        try:
            self.datasource.delete_data_source("SQL Server DS by admin user")
            raise CVTestStepFailure(
                "User is able to delete database datasources of other users without delete permission")
        except CVWebAutomationException as excp:
            if "user does not have required delete capability on datasource" not in str(excp):
                raise CVTestStepFailure(
                    f"Expected Notification 'user does not have required delete capability on datasource'. Got {excp}")

    @test_step
    def validate_edition_of_db_ds(self):
        """Verifies the user is able to edit datasources with 'Edit datasource role' but not delete them"""
        dict_ = {"assoc":
                 {
                     'commCellName': [self.commcell.commserv_name],
                     'role': ["Edit Datasource"]
                 }
                 }

        self.commcell.users.get(self.automation_username).update_security_associations(dict_, "UPDATE")
        self.relogin()
        try:
            self.datasource.edit_data_source(
                "SQL Server DS by admin user",
                "Modify by user having edit permission",
                self._tcinputs["hostname"],
                "commvault",
                self.sql_server_db_username,
                self.sql_server_db_password)
        except CVWebAutomationException:
            raise CVTestStepFailure("User is unable to edit datasource created by other users after edit permissions")

        try:
            self.datasource.delete_data_source("Modify by user having edit permission")
            raise CVTestStepFailure(
                "User is able to delete datasources created by other users only with edit permissions")
        except CVWebAutomationException as excp:
            if "user does not have required delete capability on datasource" not in str(excp):
                raise CVTestStepFailure(
                    f"Expected Notification 'user does not have required delete capability on datasource'. Got {excp}")

    @test_step
    def validate_deletion_of_ds_db(self):
        """Verifies the user is able to delete datasources with 'Delete datasource role'"""
        dict_ = {"assoc":
                 {
                     'commCellName': [self.commcell.commserv_name],
                     'role': ["Delete Datasource"]
                 }
                 }
        self.commcell.users.get(self.automation_username).update_security_associations(dict_, "UPDATE")
        self.relogin()

        try:
            self.datasource.delete_data_source("Modify by user having edit permission")
        except CVWebAutomationException:
            raise CVTestStepFailure("User is unable to delete datasource after delete permission")

    def run(self):
        try:
            self.init_tc()
            self.verify_invisibility_of_data_sources_under_navigation()
            self.addition_of_cs_and_db_ds_edition_and_deletion()
            self.addition_of_db_ds_by_admin_user()
            self.validate_visibility_and_immutability_of_ds_created_by_others()
            self.validate_edition_of_db_ds()
            self.validate_deletion_of_ds_db()

        except Exception as err:
            self.utils.handle_testcase_exception(err)
        finally:
            AdminConsole.logout_silently(self.adminconsole)
            Browser.close_silently(self.browser)
