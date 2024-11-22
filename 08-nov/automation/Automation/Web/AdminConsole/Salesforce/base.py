# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides functions and operations that can be performed on the Salesforce Organizations list page

SalesforceApps:

    __get_incremental_job_id()          --  Get id of latest incremental job run on org

    __wait_for_job_completion()         --  Method that waits for completion of job

    __wait_for_incremental()            --  Method that waits for job completion and then waits for automatic
                                            incremental

    backup()                            --  Runs backup on a Salesforce

    __click_on_backup()                 --  Clicks on backup
"""
from abc import ABC, abstractmethod
from time import sleep

from AutomationUtils import logger
from Web.AdminConsole.Components.dialog import RBackup
from Web.Common.page_object import PageService


class SalesforceBase(ABC):
    """Base class for Salesforce pages on Command Center"""

    def __init__(self, admin_console, commcell):
        self.__admin_console = admin_console
        self.__commcell = commcell
        self.__backup = RBackup(self.__admin_console)
        self._log = logger.get_log()

    def __get_incremental_job_id(self, org_name):
        """
        Get id of latest incremental job run on org

        Args:
            org_name (str)  --  name of org

        Returns:
            (str)           --  job id

        Raises:
            Exception       --  if latest job id retrieved from commcell is not incremental
        """
        self.__commcell.clients.refresh()
        client = self.__commcell.clients.get(org_name)
        instance = client.agents.get('Cloud Apps').instances.get(org_name)
        subclient = instance.subclients.get('default')
        return str(subclient.find_latest_job().job_id)

    def _wait_for_job_completion(self, job_id):
        """
        Method that waits for completion of job

        Args:
            job_id (str)    --  Job id

        Raises:
            Exception       --  if job fails
        """
        sleep(10)
        job_obj = self.__commcell.job_controller.get(job_id)
        if not job_obj.wait_for_completion():
            raise Exception("Failed to run job:%s with error: %s" % (job_id, job_obj.delay_reason))
        self._log.info('Job %s finished successfully', job_id)

    def _wait_for_incremental(self, org_name):
        """
        Method that waits for job completion and then waits for automatic incremental job completion

        Args:
            org_name (str)      --  name of org on which full job was run

        Returns:
            (str)               --  job id of automatic incremental job

        Raises:
            Exception           --  if latest job id retrieved from commcell is not incremental
                                    if incremental job fails
        """
        job_id = self.__get_incremental_job_id(org_name)
        self._log.info(f"Automatic incremental job id is {job_id}")
        self._wait_for_job_completion(job_id)
        return job_id

    @PageService()
    def backup(self, org_name, backup_type="Incremental", wait_for_job_completion=True):
        """
        Runs backup on a Salesforce Organization

        Args:
            org_name (str)              --  name of the org to backup
            backup_type (str)           --  "Full" or "Incremental", case insensitive
            wait_for_job_completion (bool) --  if True, waits for current job and any automatic job that launches
                                            if False, just returns job id of full/incremental job run

        Returns:
            (tuple)                     --  (job_id, ) or (full_job_id, incremental_job_id)

        Raises:
            Exception                   --  if wait_for_job_completion is True and waiting for full/automatic
                                            incremental job encounters an error
        """
        sleep(60)
        backup_map = {
            "full": RBackup.BackupType.FULL,
            "incremental": RBackup.BackupType.INCR
        }
        backup_type = backup_map[backup_type.lower()]
        self._click_on_backup(org_name)
        job_id = self.__backup.submit_backup(backup_type=backup_type)
        if wait_for_job_completion:
            self._wait_for_job_completion(job_id)
            if backup_type == RBackup.BackupType.FULL:
                sleep(10)
                incremental_job_id = self._wait_for_incremental(org_name)
                return job_id, incremental_job_id
        return job_id,

    @abstractmethod
    def _click_on_backup(self, org_name):
        """
        Method to click on backup

        Args:
            org_name (str)  --  Name of org to click on backup for
        """
