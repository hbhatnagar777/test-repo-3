# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
    Dynamics365CSDBHelper is the only class in this file

Dynamics365CSDBHelper:

    Class for performing operations on CommServ DB pertaining to Dynamics 365 CRM Agent


Dynamics365CSDBHelper
=======

    __init__(d365_object)               --      initialize object of Dynamics365CSDBHelper class
    number_of_items_in_backup_job       --      Method to get the number of items in the backup job
    check_licensing_thread_processed    --      Method to Check Licensing Thread Status
    get_licensing_info                  --      Method to verify d365 licensing

"""

from __future__ import unicode_literals
from typing import Set, Any, List
from AutomationUtils.options_selector import OptionsSelector
import xml.etree.ElementTree as ET
import time


class Dynamics365CSDBHelper:
    """
        Class for performing all operations on CommServ DB pertaining to Dynamics 365 Agent
    """

    def __init__(self, d365_object):
        """Initializes the input variables,logging and creates object from other modules.

                Args:
                    d365_object   --  instance of the CVDynamics365 object

                Returns:
                    object  --  instance of Dynamics365CSDBHelper class"""
        self.tc_object = d365_object.tc_object
        if "all_licensed_users" in d365_object.tc_inputs:
            self.licensed_users = d365_object.tc_inputs.get("all_licensed_users")
        self._utility = OptionsSelector(self.tc_object.commcell)
        self.log = self.tc_object.log
        self.log.info('logger initialized for Dynamics 365 DB Helper')
        self.csdb = self.tc_object.csdb

    def number_of_items_in_backup_job(self, job_id: int):
        """
            Method to get the number of items in the backup job
            Arguments:
                job_id(int)        -- Job id for which number of items is required

            Returns:
                Number of items in the provided job id
        """
        try:
            self.log.info(
                "Getting number of items in job %s from CS- DB" %
                job_id)
            query_string = "select totalNumOfFiles from JMBkpStats Where jobId=%s" % job_id
            self.csdb.execute(query_string)
            result = self.csdb.fetch_one_row()
            self.log.info(
                "Number of items in job %s is: %s" %
                (job_id, result[0]))
            return int(result[0])
        except Exception as exception:
            self.log.exception(
                "Error in getting job details from database. %s" %
                str(exception))
            raise exception

    def get_phases_for_job(self, job_id: int) -> list[Any]:
        """
            Method to get the phases for a job
            Arguments:
                job_id(int)        -- Job id for which number of items is required

            Returns:
                Get the phases for a backup job.
        """
        _query: str = "select phase from JMBkpAtmptStats where jobId={}".format(job_id)
        phases_ran = list(map(int, list(self._utility.exec_commserv_query(_query)[0])))
        return phases_ran

    def check_licensing_thread_processed(self, instance_id: int, count=10):
        """"
            Method to Check Licensing Thread Status
            Arguments:
                instance_id(int)        --  Instance ID for which licensing thread ran
                count(int)              --  No. of times query to be run to check licensing status updated or not
                    Default:10

            Returns:
                  Bool: True if licensing status updated within time

            Raises:
                 Exception: If Status doesn't get updated within time
        """

        if count < 0:
            raise Exception("Licensing Tread Time Limit Exceeded. Couldn't verify")

        self.log.info(f"Checking if licensing thread completed. Attempts left {count}")
        try:
            query_string = f"select attrVal from APP_InstanceProp where attrName like '%license%' " \
                           f"and componentnameid = {instance_id}"
            self.csdb.execute(query_string)
            result = self.csdb.fetch_one_row()
            xml = ET.fromstring(result[0])
            status = int(xml.attrib['licensingStatus'])
            if status == 2:
                return True
            time.sleep(60)
            return self.check_licensing_thread_processed(instance_id, count-1)
        except Exception as exception:
            self.log.exception(
                f"Error in getting Licensing Status from the database. {str(exception)}"
            )

    def get_licensing_info(self, instance_id: int, lic_added_user=None, lic_removed_user=None):
        """
            Method to verify d365 licensing
            Arguments:
                instance_id(int)       --  Subclient ID for which licensing check is to be done
                lic_added_user      (str)   --      Username of the user to which license is added
                lic_removed_user    (str)   --      Username of the user from which license is removed

            Returns:
                Bool: True if check is successful

            Raises:
                Exception: If database values don't match
        """
        if lic_added_user and lic_added_user not in self.licensed_users:
            self.licensed_users.append(lic_added_user)
        if lic_removed_user and lic_removed_user in self.licensed_users:
            self.licensed_users.remove(lic_removed_user)
        self.licensed_users.sort()

        if self.check_licensing_thread_processed(instance_id):

            try:
                lic_users_from_db = []
                self.log.info("Getting Licensing Users Info")
                query_string = f"select name from CloudAppsLicensingInfo where instanceId = {instance_id} and isActive=1"
                self.csdb.execute(query_string)
                result = self.csdb.fetch_all_rows()
                for users in result:
                    lic_users_from_db.append(users[0])
                lic_users_from_db.sort()
                if self.licensed_users == lic_users_from_db:
                    self.log.info(f"Licensed Users are {self.licensed_users}")
                    return True
                raise Exception(f"Verification failed, Actual Licensed Users are {self.licensed_users} "
                                f"Licensing Stats shows {lic_users_from_db}")

            except Exception as exception:
                self.log.exception(
                    f"Error in getting Licensing Stats from the database. {str(exception)}"
                )
        else:
            raise Exception("Licensing Tread didn't succeed")
