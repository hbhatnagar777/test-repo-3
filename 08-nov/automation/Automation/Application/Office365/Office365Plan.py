# -*- coding: utf-8 -*-
# Author :- Prajjawal Banati
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# --------------------------------------------------------------------------
from cvpysdk.commcell import Commcell
from cvpysdk.plan import Plans, Plan
from cvpysdk.cvpysdk import CVPySDK
from AutomationUtils import logger
from Web.AdminConsole.Hub.constants import O365AppTypes


class Office365Plan(Plan):
    """
        This class governs the control and operations which can be done on Office 365 Plan. This class provides us the
        simplicity to do most of the READ and UPDATE operations on the Office 365 Plan. To check the CREATE operation
        refer the Plans class in Plan.py
    """

    def __new__(cls, commcell_object, plan_name):
        """
            Overriding the __new__ method to check if the plan exists or not
        """
        plans = Plans(commcell_object)
        if plans.has_plan(plan_name):
            plans.delete(plan_name)
        plans.add_office365_plan(plan_name)
        return super(Office365Plan, cls).__new__(cls)

    def __init__(self, commcell_object, plan_name):
        """Initialize an Office 365 Plan object to perform different operations on the same entity"""
        super().__init__(commcell_object=commcell_object, plan_name=plan_name)
        self.log = logger.get_log()
        self.log.info("Fetched the properties of the plan {}".format(plan_name))
        self._initialize_variables()

    def _initialize_variables(self, refresh_required=False):
        """Initialize class level policy variables while fetching the properties or after updating the properties"""
        if refresh_required:
            self.refresh()
        self._o365Exchange_archive_policy = self.properties["office365Info"]["o365Exchange"]["mbArchiving"]["detail"][
            "emailPolicy"]["archivePolicy"]
        self._o365Exchange_retention_policy = self.properties["office365Info"]["o365Exchange"]["mbRetention"]["detail"][
            "emailPolicy"]["retentionPolicy"]
        self._o365Exchange_cleanup_policy = self.properties["office365Info"]["o365Exchange"]["mbCleanup"]["detail"][
            "emailPolicy"]["cleanupPolicy"]
        self._o365CloudApps_backup_policy = self.properties["office365Info"]["o365CloudOffice"]["caBackup"]["detail"][
            "cloudAppPolicy"]["backupPolicy"]
        self._o365CloudApps_retention_policy = \
            self.properties["office365Info"]["o365CloudOffice"]["caRetention"]["detail"][
                "cloudAppPolicy"]["retentionPolicy"]
        self._payload = {
            "ciPolicyInfo": {},
            "eePolicyInfo": {},
            "exchange": self.properties["exchange"],
            "office365Info": self.properties["office365Info"],
            "summary": self.properties["summary"]
        }

    def _read_retention_criteria(self):
        """Reads and returns the retention criteria for the Office 365 Plan"""
        self.log.info("Reading the retention criteria for {}".format(self.plan_name))
        if self._o365Exchange_retention_policy["numOfDaysForMediaPruning"] == self._o365CloudApps_retention_policy[
            "numOfDaysForMediaPruning"]:
            self.log.info("Retention for plan {} is {} days".format(self.plan_name,
                                                                    "Infinite" if self._o365Exchange_retention_policy[
                                                                                      "numOfDaysForMediaPruning"] == -1
                                                                    else self._o365Exchange_retention_policy[
                                                                        "numOfDaysForMediaPruning"]))
        else:
            raise Exception("Retention days can't be different for exchange and cloudApps")

    def _read_include_exclude_filters(self):
        """
            Reads and returns to include and exclude filters for the Office 365 Plan
            :return
                filters(dict) -- Dictionary containing all the information regarding filters
        """
        self.log.info("Fetching the include and exclude filters for Office 365 Plan")
        filters = dict()
        exchange_include_filters = self._o365Exchange_archive_policy["includeFolderFilter"]
        exchange_exclude_filters = self._o365Exchange_archive_policy["excludeFolderFilter"]
        cloudapps_include_folder_filters = self._o365CloudApps_backup_policy["ruleDetails"][0]["filters"][0][
            "includeFilter"]
        cloudapps_exclude_folder_filters = self._o365CloudApps_backup_policy["ruleDetails"][0]["filters"][0][
            "excludeFilter"]
        cloudapps_include_file_filters = self._o365CloudApps_backup_policy["ruleDetails"][0]["filters"][1][
            "includeFilter"]
        cloudapps_exclude_file_filters = self._o365CloudApps_backup_policy["ruleDetails"][0]["filters"][1][
            "excludeFilter"]

        filters["exchange"] = {
            "Folders": {
                "IncludeFilters": exchange_include_filters,
                "ExcludeFilters": exchange_exclude_filters
            }
        }
        filters["onedrive"] = {
            "Folders": {
                "IncludeFilters": cloudapps_include_folder_filters,
                "ExcludeFilters": cloudapps_exclude_folder_filters
            },
            "Files": {
                "IncludeFilters": cloudapps_include_file_filters,
                "ExcludeFilters": cloudapps_exclude_file_filters
            }
        }
        self.log.info(filters)
        return filters

    def _update_retention_criteria(self, numOfDays):
        """
            Updates the retention criteria details for Office 365 Plan
            :argument
                numOfDays (int) -- number of days needed to set the retention
        """
        self._payload["office365Info"]["o365Exchange"]["mbRetention"]["detail"][
            "emailPolicy"]["retentionPolicy"]["numOfDaysForMediaPruning"] = numOfDays

        self._payload["office365Info"]["o365CloudOffice"]["caRetention"]["detail"][
            "cloudAppPolicy"]["retentionPolicy"]["numOfDaysForMediaPruning"] = numOfDays
        self._update_plan_props(props=self._payload)
        self._initialize_variables(refresh_required=True)

    def _enable_archive_mailbox(self):
        """Enables archive on the Office 365 Plan"""
        self._payload["office365Info"]["o365Exchange"]["mbArchiving"]["detail"]["emailPolicy"]["archivePolicy"][
            "archiveMailbox"] = True
        self._update_plan_props(self._payload)
        self._initialize_variables(refresh_required=True)

    def _enable_backup_deleted_item_retention(self):
        """Update include and exclude filters for Office 365 Plan"""
        self._payload["office365Info"]["o365Exchange"]["mbArchiving"]["detail"]["emailPolicy"]["archivePolicy"][
            "backupDeletedItemRetention"] = True
        self._update_plan_props(self._payload)
        self._initialize_variables(refresh_required=True)

    def _enable_self_service(self, app_type):
        """
            Enables the self-service on the Office 365 Plan
            :argument
                app_type (O365AppTypes Enum) :- Type of O365 App passed
        """
        if app_type == O365AppTypes.exchange:
            self._payload["office365Info"]["o365Exchange"]["mbArchiving"]["detail"]["emailPolicy"]["archivePolicy"][
                "selfServiceEnabled"] = 1
        elif app_type == O365AppTypes.onedrive:
            self._payload["office365Info"]["o365CloudOffice"]["caBackup"]["detail"]["cloudAppPolicy"]["backupPolicy"][
                "ruleDetails"][0].update({"selfServiceEnabled": 1})
        self._update_plan_props(self._payload)
        self._initialize_variables(refresh_required=True)

    def _enable_content_indexing(self):
        """Enables the content indexing on the Office 365 Plan"""
        self._payload["office365Info"]["o365Exchange"]["mbArchiving"]["detail"]["emailPolicy"]["archivePolicy"][
            "contentIndexProps"]["enableContentIndex"] = True
        self._payload["office365Info"]["o365CloudOffice"]["caBackup"]["detail"]["cloudAppPolicy"]["backupPolicy"][
            "onedrivebackupPolicy"]["enableContentIndex"] = True
        self._payload["office365Info"]["o365CloudOffice"]["caBackup"]["detail"]["cloudAppPolicy"]["backupPolicy"][
            "spbackupPolicy"]["enableContentIndex"] = True
        try:
            self._payload["office365Info"]["o365CloudOffice"]["caBackup"]["detail"]["cloudAppPolicy"]["backupPolicy"][
                "teamsbackupPolicy"]["enableContentIndex"] = True
        except KeyError as ex:
            self._payload["office365Info"]["o365CloudOffice"]["caBackup"]["detail"]["cloudAppPolicy"][
                "backupPolicy"].update({"teamsbackupPolicy": {"enableContentIndex": True}})
        self._update_plan_props(self._payload)
        self._initialize_variables(refresh_required=True)

    def _enable_microsoft_unknown_errors(self):
        """Enables microsoft unknown errors on the Office 365 Plan"""
        self._payload["office365Info"]["o365CloudOffice"]["caBackup"]["detail"]["cloudAppPolicy"]["backupPolicy"][
            "teamsbackupPolicy"]["skipMicrosoftErrors"] = True
        self._update_plan_props(self._payload)
        self._initialize_variables(refresh_required=True)

    def _update_custom_backup_settings_for_exchange(self, include_messages_older_than=0, include_messages_larger_than=0,
                                                    include_messages_with_attachments=False):
        """
            Enables the custom backup setting for exchange
            :args
                include_messages_older_than (int) -- Change to include messages older than value for Office 365 Plan
                include_messages_larger_than (int) -- Change to include messages larger than value for Office 365 Plan
                include_messages_with_attachments (bool) -- Change to include messages which have attachments
        """
        self._payload["office365Info"]["o365Exchange"]["mbArchiving"]["detail"]["emailPolicy"]["archivePolicy"][
            "includeMsgsOlderThan"] = include_messages_older_than
        self._payload["office365Info"]["o365Exchange"]["mbArchiving"]["detail"]["emailPolicy"]["archivePolicy"][
            "includeMsgsLargerThan"] = include_messages_larger_than
        self._payload["office365Info"]["o365Exchange"]["mbArchiving"]["detail"]["emailPolicy"]["archivePolicy"][
            "includeOnlyMsgsWithAttachemts"] = include_messages_with_attachments
        self._update_plan_props(self._payload)
        self._initialize_variables(refresh_required=True)

    def _enable_deleted_item_retention(self):
        """
        Enable backup deleted item retention
        :return:
        """
        self._payload["office365Info"]["o365Exchange"]["mbArchiving"]["detail"]["emailPolicy"]["archivePolicy"][
            "backupDeletedItemRetention"] = True
        self._update_plan_props(self._payload)
        self._initialize_variables(refresh_required=True)

    @property
    def archive_policy_name(self):
        """Returns the archive policy name for Office 365 plan"""
        return self.properties["office365Info"]["o365Exchange"]["mbArchiving"]["policyEntity"]["policyName"]

    @property
    def retention_policy_name(self):
        """Returns the cleanup policy name for Office 365 plan"""
        return self.properties["office365Info"]["o365Exchange"]["mbRetention"]["policyEntity"]["policyName"]

    @property
    def cleanup_policy_name(self):
        """Returns the archive policy name for Office 365 plan"""
        return self.properties["office365Info"]["o365Exchange"]["mbCleanup"]["policyEntity"]["policyName"]

    def update_retention_days(self, numOfDaysForMediaPruning):
        """Update the retention days for the Office 365 plan"""
        if numOfDaysForMediaPruning < 0 or numOfDaysForMediaPruning is None:
            raise Exception("Number of days for media Pruning can not be none or negative")
        try:
            self._update_retention_criteria(numOfDays=numOfDaysForMediaPruning)
        except Exception as ex:
            self.log.error("Exception generated while changing retention days.")
            raise ex

    def enable_backup_attachments(self):
        """Enable backup attachments in exchange settings for office 365 plan"""
        self._update_custom_backup_settings_for_exchange(include_messages_with_attachments=True)

    def include_messages_older_than(self, days):
        """
            Change exchange settings to include messages which are older than number of days passed
            :argument
                days(int) -- number of days to include messages
        """
        self._update_custom_backup_settings_for_exchange(include_messages_older_than=days)

    def include_messages_larger_than(self, size):
        """
            Change exchange settings to include messages which are larger than passed size for Office 365 Plan
        :param size(int) --  include messages larger than (size)KB
        :return:
        """
        self._update_custom_backup_settings_for_exchange(include_messages_larger_than=size)

    def enable_backup_deleted_item_retention(self):
        """
        Enable backup deleted item retention
        :return:
        """
        self._enable_deleted_item_retention()

    def enable_content_indexing(self):
        """
        Enables content Indexing on Office 365 Plan
        :return:
        """
        self._enable_content_indexing()

