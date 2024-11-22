# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
basic operations on identity servers page for domains and domain details page.

CredentialManagerHelper : This class provides methods for Credential Manager related operations

add_credential()                : Adds a credential and verifies if the
                                  credential is added with the set parameters

edit_credential()               : Edits a credential and verifies if the credential is
                                  updated with the set parameters

update_security()               : Adds security association for the credential and
                                  verifies if the association is updated with the set parameters

return_security_association_dict() : Returns a dictionary of the setter values

verify_security_associations()  : Fetches security association details from the security panel and
                                  verifies it against the expected security dictionary

delete_credential()             : Deletes a credential and verifies if the
                                  credential has been deleted

return_cred_props_dict()        : Returns a dict of the setter values

verify_credential_details()     : Fetches credential details from the edit credential pane and
                                  verifies it against the dict returned by return_cred_props_dict()

verify_cred_visibility()        : Method to verify if the admin created credential is visible

attempt_edit_delete_non_owner() : Method to attempt edit and delete and
                                  verify that it was unsuccessful


create_subclient()    :          create a subclient and associate
                                  it with a credential

run_backup_with_invalid_cred()  : Trigger a backup job while the credential is incorrect

resume_job_with_valid_cred()    : Resume job after correcting credential
"""

import time
from AutomationUtils import logger
from Web.AdminConsole.AdminConsolePages.credential_manager import CredentialManager
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.AdminConsolePages.job_details import JobDetails
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import Backup, RSecurityPanel
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.FSPages.RFsPages.RFile_servers import FileServers
from Web.AdminConsole.FSPages.RFsPages.RFs_agent_details import Subclient
from Web.Common.exceptions import CVWebAutomationException


class CredentialManagerHelper:

    def __init__(self, admin_console):

        self.__admin_console = admin_console
        self.__navigator = admin_console.navigator
        self.__driver = admin_console.driver
        self.log = logger.get_log()
        self._account_type = None
        self._credential_name = None
        self._new_credential_name = None
        self._credential_username = None
        self._credential_password = None
        self._user_or_group = None
        self._role = None
        self._description = None
        self._client_name = None
        self._backupset_name = None
        self._subclient_name = None
        self._sc_content = None
        self._storage_policy_name = None
        self._client = None
        self._notification = ""
        self._plan_name = None
        self.__credential_manager = CredentialManager(self.__admin_console)
        self.__file_server = FileServers(self.__admin_console)
        self.__subclient = Subclient(self.__admin_console)
        self.__rtable = Rtable(self.__admin_console)
        self.__security_panel = RSecurityPanel(self.__admin_console)
        self.__rmodaldialog = RModalDialog(self.__admin_console)
        self.__backup = Backup(self.__admin_console)
        self.__jobs = Jobs(self.__admin_console)
        self.__jobdetails = JobDetails(self.__admin_console)
        self._job_id = None

    @property
    def account_type(self):
        """Get account type value"""
        return self._account_type

    @account_type.setter
    def account_type(self, value):
        """Set the account type of the credential"""
        self._account_type = value

    @property
    def credential_name(self):
        """Get credential name"""
        return self._credential_name

    @credential_name.setter
    def credential_name(self, value):
        """Set the name for the credential"""
        self._credential_name = value

    @property
    def new_credential_name(self):
        """Get new credential name, this is the value which will
        replace the credential name while editing"""
        return self._new_credential_name

    @new_credential_name.setter
    def new_credential_name(self, value):
        """Set the new credential name, this will be used while editing the credential"""
        self._new_credential_name = value

    @property
    def credential_username(self):
        """Get the credential username"""
        return self._credential_username

    @credential_username.setter
    def credential_username(self, value):
        """Sets the credential username"""
        self._credential_username = value

    @property
    def credential_password(self):
        """Get the credential's password"""
        return self._credential_password

    @credential_password.setter
    def credential_password(self, value):
        """Sets the credential password"""
        self._credential_password = value

    @property
    def user_or_group(self):
        """Get the associated user/group"""
        return self._user_or_group

    @user_or_group.setter
    def user_or_group(self, value):
        """Sets the associated user/group"""
        self._user_or_group = value

    @property
    def role(self):
        """Get the associated roles"""
        return self._role

    @role.setter
    def role(self, value):
        """Sets the associated roles"""
        self._role = value

    @property
    def description(self):
        """Get the description of the credential """
        return self._description

    @description.setter
    def description(self, value):
        """Sets the description of the credential"""
        self._description = value

    @property
    def backupset_name(self):
        """Get the backupset name for backupset to be created """
        return self._backupset_name

    @backupset_name.setter
    def backupset_name(self, value):
        """Sets the backupset name for backupset to be created """
        self._backupset_name = value

    @property
    def subclient_name(self):
        """Get the subclient name for subclient to be created """
        return self._subclient_name

    @subclient_name.setter
    def subclient_name(self, value):
        """Sets the subclient name for subclient to be created """
        self._subclient_name = value

    @property
    def storage_policy(self):
        """Get the plan name for subclient to be created """
        return self._storage_policy_name

    @storage_policy.setter
    def storage_policy(self, value):
        """Sets the subclient name for subclient to be created """
        self._storage_policy_name = value

    @property
    def plan(self):
        """Get the plan name for subclient to be created """
        return self._plan_name

    @plan.setter
    def plan(self, value):
        """Plan"""
        self._plan_name = value

    @property
    def sc_content(self):
        """Get the content for subclient"""
        return self._sc_content

    @sc_content.setter
    def sc_content(self, value):
        """Sets the content for subclient"""
        self._sc_content = value

    @property
    def client(self):
        """Get the content for subclient"""
        return self._client

    @client.setter
    def client(self, value):
        """Sets the content for subclient"""
        self._client = value

    def add_credential(self, verify=True):
        """
        Adds a credential and verifies if the credential is added with the set parameters

        Args:
            verify(boolean) : Validate credential against inputs after adding

        Returns:
            None
        """

        self.__navigator.navigate_to_credential_manager()
        self.__admin_console.wait_for_completion()
        self.__credential_manager.add_credential(self.account_type, self.credential_name,
                                                 self.credential_username, self._credential_password,
                                                 self.description)
        self.__admin_console.wait_for_completion()
        if verify:
            self.verify_credential_details(self.return_cred_props_dict())

    def edit_credential(self, verify=True):
        """
        Edits a credential and verifies if the credential is updated with the set parameters

        Args:
            verify(boolean) : Validate credential against inputs after adding

        Returns:
            None
        """

        self.__navigator.navigate_to_credential_manager()
        self.__admin_console.wait_for_completion()
        self.__credential_manager.edit_credential(self.credential_name,
                                                  self.new_credential_name,
                                                  self.credential_username,
                                                  self.credential_password,
                                                  self.description)
        self.__admin_console.wait_for_completion()
        self._credential_name = self.new_credential_name

        if verify:
            self.verify_credential_details(self.return_cred_props_dict())

    def update_security(self, verify=True):
        """
        Adds security association for the credential and
        verifies if the credential is updated with the set parameters
        """
        self.__navigator.navigate_to_credential_manager()
        self.__admin_console.wait_for_completion()
        self.__credential_manager.update_security(self.credential_name, self.user_or_group, self.role)
        self.__admin_console.wait_for_completion()

        if verify:
            self.verify_security_associations(self.return_security_association_dict())

    def return_security_association_dict(self):
        """
        Returns a dictionary of the setter values
        """
        cred_security_dict = dict()

        for user_or_group in self.user_or_group:
            if user_or_group not in cred_security_dict:
                cred_security_dict[user_or_group] = [self.role]
            else:
                cred_security_dict[user_or_group].append(self.role)

        return cred_security_dict

    def verify_security_associations(self, expected_security_dict):
        """
        Fetches security association details from the security panel and verifies it against the
        expected security dictionary

        Args:
            expected_security_dict(dict)  : Dict of expected values

        Returns:
            None
        """
        self.__navigator.navigate_to_credential_manager()

        self.__rtable.access_action_item(self.credential_name, "Update security")
        displayed_security_dict = self.__security_panel.get_details()

        self.log.info("Expected security dict: {0}".format(expected_security_dict))
        self.log.info("Displayed security dict: {0}".format(displayed_security_dict))

        if expected_security_dict == displayed_security_dict:
            self.log.info("Security association details match the displayed details.")
        else:
            raise Exception("Provided security associations are not valid")

        self.__rmodaldialog.click_cancel()
        self.__admin_console.wait_for_completion()

    def delete_credential(self, credential_name=None):
        """
        Deletes a credential and verifies if the credential has been deleted
        """
        if not credential_name:
            credential_name = self.credential_name
        self.__navigator.navigate_to_credential_manager()
        if self.verify_cred_visibility(credential_name):
            self.__credential_manager.action_remove_credential(credential_name)
        else:
            return
        if self.verify_cred_visibility(credential_name):
            raise Exception("Credential {0} was not deleted".format(credential_name))
        else:
            self.log.info("Credential {0} was successfully deleted".format(credential_name))

    def return_cred_props_dict(self):
        """
        Returns a dictionary of the setter values
        """

        cred_details_dict = dict()

        cred_details_dict["Account type"] = self.account_type
        cred_details_dict["Credential name"] = self.credential_name
        cred_details_dict["User name"] = self.credential_username

        if self.description is None:
            cred_details_dict["description"] = ""
        else:
            cred_details_dict["description"] = self.description

        return cred_details_dict

    def verify_credential_details(self, expected_values_dict):
        """
        Fetches credential details from the edit credential pane and verifies it against the
        expected values dictionary

        Args:
            expected_values_dict(dict)  : Dict of expected values

        Returns:
            None
        """

        self.__navigator.navigate_to_credential_manager()

        displayed_details_dict = self.__credential_manager.extract_edit_pane_displayed_details(
            self.credential_name)

        self.log.info("cred det dict: {0}".format(expected_values_dict))
        self.log.info("displayed det dict: {0}".format(displayed_details_dict))

        for key, value in expected_values_dict.items():

            if expected_values_dict[key] == displayed_details_dict[key]:
                self.log.info("Input Value {0} matches with displayed value {1} for {2}".format(
                    expected_values_dict[key], displayed_details_dict[key], key))
            else:
                raise Exception("Provided credentials are not valid %s", key)
        self.__admin_console.wait_for_completion()

    def verify_cred_visibility(self, credential_name=None):
        """
        Method to verify if the credential is visible
        """
        if not credential_name:
            credential_name = self.credential_name
        self.__navigator.navigate_to_credential_manager()
        if self.__rtable.is_entity_present_in_column('Credential name', credential_name):
            return True
        else:
            return False

    def attempt_edit_delete_non_owner(self):
        """
        Method to attempt edit and delete and verify that it was unsuccessful
        """

        self.__navigator.navigate_to_credential_manager()
        self.log.info("Getting edit pane details before edit attempt")
        pre_edit_displayed_dict = self.__credential_manager.extract_edit_pane_displayed_details(self.credential_name)

        try:
            self.edit_credential(verify=False)
        except Exception as exp:
            if "User does not have ownership to update the credentials" in exp.args[0]:
                self.__rmodaldialog.click_cancel()
            else:
                raise CVWebAutomationException(exp)

        self._credential_name = pre_edit_displayed_dict['Credential name']
        self.__navigator.navigate_to_credential_manager()
        self.log.info("Getting edit pane details after edit attempt")
        self.log.info("Comparing pre and post edit attempt details")

        try:
            self.verify_credential_details(pre_edit_displayed_dict)
        except Exception as exp:
            self.log.info("Values were edited while logged in as non owner")

        try:
            self.delete_credential()
        except Exception as exp:
            pass

        self.__admin_console.wait_for_completion()
        credential_visible = self.__rtable.is_entity_present_in_column('Credential name', self.credential_name)
        if ("User does not have ownership to delete the credentials." in self._notification) \
                or credential_visible:
            self.log.info(self._notification)
            self.log.info("Unable to delete through non-owner account")
        else:
            raise Exception("Credential may have been deleted by non-owner account")
        self.__admin_console.wait_for_completion()

    def create_subclient(self):
        """
        Method to create a backupset and subclient and assign credentials to impersonate user.
        Deletes the backupset and creates it again if a backupset with the given name
        already exists.
        """

        self.__navigator.navigate_to_file_servers()
        self.__admin_console.select_file_servers_tab()
        self.__file_server.access_server(self.client)
        self.__admin_console.access_tab("Subclients")
        self.__subclient.add_subclient(subclient_name=self.subclient_name, backupset_name=self.backupset_name,
                                       plan_name=self.plan, define_own_content=True, contentpaths=[self.sc_content],
                                       saved_credentials=self.credential_name, remove_plan_content=True)

    def run_backup_with_invalid_cred(self):
        """
        Method for running backup when an invalid credential is provided, for verifying that backup
        will not run without valid credentials
        """

        # navigate to filesystem page of client
        self.__navigator.navigate_to_file_servers()
        self.__admin_console.select_file_servers_tab()
        self.__file_server.access_server(self.client)
        self.__admin_console.access_tab("Subclients")

        # backup subclient
        self._job_id = self.__subclient.backup_subclient(subclient_name=self.subclient_name,
                                                         backupset_name=self.backupset_name,
                                                         backup_type=self.__backup.BackupType.FULL)

        # navigate to url retrieved from notification
        self.__navigator.navigate_to_jobs()
        self.log.info(f"Job id: {self._job_id}")
        time.sleep(10)

        job_details = None
        job_status_retry = 10

        while job_status_retry > 0:
            self.__jobs.access_job_by_id(self._job_id)
            time.sleep(5)
            job_details = self.__jobdetails.get_all_details()

            if job_details["Status"] == "Running":
                self.log.info("Job is running, waiting for it to go into pending state. "
                              "Wait for 10s.")
                time.sleep(10)
                job_status_retry -= 1

            else:
                break

        if job_details["Status"] == "Pending":
            self.log.info("Verified backup will not run without correct credentials")

        else:
            raise Exception(f"Job id {self._job_id} status: {job_details['Status']}")

    def resume_job_with_valid_cred(self):
        """
        Method for resuming the job pending due to invalid credential. Verifies that the backup job
        resumes after providing correct credentials.
        """

        self.__navigator.navigate_to_jobs()
        self.__admin_console.wait_for_completion()
        self.__jobs.add_filter("Status", "Pending")
        self.__jobs.resume_job(self._job_id)
        self.__admin_console.wait_for_completion()
        job_details_post_edit = None
        job_status_retry = 5
        while job_status_retry > 0:
            self.__jobs.access_job_by_id(self._job_id)
            time.sleep(180)
            job_details_post_edit = self.__jobdetails.get_all_details()

            if job_details_post_edit["Status"] == "Waiting":
                self.log.info("Job is Waiting, waiting for it to go into Running state. "
                              "Wait for 10s.")
                time.sleep(10)
                job_status_retry -= 1

            else:
                break
        if job_details_post_edit["Status"] in ("Completed", "Running"):
            self.log.info("Job id {0} completed after correcting credentials".format(self._job_id))

        else:
            raise Exception(
                f"Job id {self._job_id}. JPR: {job_details_post_edit['Job pending reason']}")
