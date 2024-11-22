# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""This module provides the function or operations related to FileSystem in AdminConsole
FSHelper : This class provides methods for file system related operations

FSHelper
===========

__init__(driver obj, csdb obj)  --      initialize object of ArrayHelper class associated

create_fs_subclient()           --      Creates filesystem subclient

fsbackup_now()                  --      starts backup operation for a subclient

fs_restore()                    --      starts a restore operation for a subclient

delete_subclient()              --      deletes a subclient from admin console

"""

from AutomationUtils import logger
from AutomationUtils import constants
from Web.AdminConsole.Components.panel import Backup

from Web.AdminConsole.AdminConsolePages.Servers import Servers
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs

from Web.AdminConsole.AdminConsolePages.server_details import ServerDetails
from Web.AdminConsole.FSPages.fs_agent import FsAgent
from Web.AdminConsole.FSPages.fs_backupset import FsBackupset
from Web.AdminConsole.FSPages.fs_subclient import FsSubclient
from Web.AdminConsole.FSPages.Restores import Restores


from Web.Common.exceptions import CVWebAutomationException


class FSHelper:
    """ Admin console helper for FSHelper class """

    def __init__(self, adminconsole):
        """
        Helper for file system related files
        :param driver:  (obj)   --  browser object
        """
        self._admin_console = adminconsole
        self.driver = adminconsole.driver
        self.log = logger.get_log()

        self.servers_obj = Servers(self._admin_console)

        self.fs_server_details_obj = ServerDetails(self._admin_console)

        self.fs_agent_obj = FsAgent(self._admin_console)

        self.fs_backupset_obj = FsBackupset(self._admin_console)

        self.fs_subclient_obj = FsSubclient(self._admin_console)

        self.restores_obj = Restores(self._admin_console)

        self.job_obj = Jobs(adminconsole)

        self._client_name = None
        self._backupset_name = 'defaultBackupSet'
        self._subclient_name = None
        self._subclient_content = None
        self._snap_jobid = None
        self._restore_path = 'C:\\ACRestore'
        self._plan_name = None
        self._snap_engine = None

    @property
    def client_name(self):
        """Returns the client name
                :return:    _client_name    (str)   --  client name

        """
        return self._client_name

    @client_name.setter
    def client_name(self, value):
        """Sets the client name
                :param value    (str)   --  client name

        """
        self._client_name = value

    @property
    def backupset_name(self):
        """Returns the backupset name
                :return:    backupset_name    (str)   --  backup set

        """
        return self._backupset_name

    @backupset_name.setter
    def backupset_name(self, value):
        """Sets the backupset name
                :param value    (str)   --  backupset

        """
        self._backupset_name = value

    @property
    def subclient_name(self):
        """Returns the subclient_name
                :return:    subclient_name    (str)   --  subclient_name

        """
        return self._subclient_name

    @subclient_name.setter
    def subclient_name(self, value):
        """Sets the subclient_name
                :param value    (str)   --  subclient_name

        """
        self._subclient_name = value

    @property
    def subclient_content(self):
        """Returns the subclient_content
                :return:    subclient_content    (str)   --  subclient_content

        """
        return self._subclient_content

    @subclient_content.setter
    def subclient_content(self, value):
        """Sets subclient_content
                :param value    (str)   --  subclient_content

        """
        if isinstance(value, str):
            self._subclient_content = [value]
        elif isinstance(value, list):
            self._subclient_content = value
        else:
            raise Exception("Please pass the correct instance of subclient content")

    @property
    def snap_jobid(self):
        """Returns the snap job id
                :return:    snap_jobid    (str)   --  Snap Job id

        """
        return self._snap_jobid

    @snap_jobid.setter
    def snap_jobid(self, value):
        """Sets the Snap job id
                :param value    (str)   --  Snap job id

        """
        self._snap_jobid = value

    @property
    def restore_path(self):
        """Returns the restore path
                :return:    restore_path    (str)   --  restore path

        """
        return self._restore_path

    @restore_path.setter
    def restore_path(self, value):
        """Sets the restore path
                :param value    (str)   --  restore path

        """
        self._restore_path = value

    @property
    def plan_name(self):
        """Returns the plan name
                :return:    plan_name    (str)   --  plan name

        """
        return self._plan_name

    @plan_name.setter
    def plan_name(self, value):
        """Sets the plan_name
                :param value    (str)   --  plan_name

        """
        self._plan_name = value

    @property
    def snap_engine(self):
        """
        Returns the snap engine name
        Returns:
            snap_engine_name    (str):  name of the snap engine
        """
        return self._snap_engine

    @snap_engine.setter
    def snap_engine(self, value):
        """
        Sets the snap engine to be associated with the subclient
        Args:
            value   (str):  name of the snap engine

        """
        self._snap_engine = value

    def navigate_to_filesystem(self):
        """Navigate to backupset"""
        self._admin_console.navigate_to_servers()
        self.servers_obj.select_client(self.client_name)
        self.fs_server_details_obj.open_agent("File System")

    def create_fs_subclient(self):
        """Create FS Subclient"""
        self.navigate_to_filesystem()
        self.fs_agent_obj.action_add_fs_subclient(self.backupset_name,
                                                  self.subclient_name,
                                                  self.plan_name,
                                                  self.subclient_content)

    def enable_snap(self):
        """
        Enables snap backup for the subclient

        Raises:
            Exception:
                if snap could not be enabled on the subclient

        """
        self.navigate_to_filesystem()
        self.fs_agent_obj.open_backupset_instance(self.backupset_name)
        self.fs_backupset_obj.open_subclient(self.subclient_name)
        self.fs_subclient_obj.enable_snapshot_engine(True, self.snap_engine)

    def fsbackup_now(self, bkp_level=Backup.BackupType.FULL):
        """Run Snap Backup"""
        self.navigate_to_filesystem()
        self.fs_agent_obj.open_backupset_instance(self.backupset_name)
        self.fs_backupset_obj.open_subclient(self.subclient_name)
        if bkp_level not in Backup.BackupType:
            raise CVWebAutomationException(f"backup type : {bkp_level}, isn't "
                                           f"among the types in BackupType enum")
        self.snap_jobid = self.fs_subclient_obj.backup_now(bkp_level)
        job_details = self.job_obj.job_completion(self.snap_jobid)
        if job_details['Status'] not in [
                "Completed", "Completed w/ one or more errors"]:
            raise Exception("Backup job failed. Please check the logs")

    def fs_restore_all_inplace(self):
        """
        Restore all the subclient content to the original folder
        Returns:

        """
        self.navigate_to_filesystem()
        self.fs_agent_obj.open_backupset_instance(self.backupset_name)
        self.fs_backupset_obj.open_subclient(self.subclient_name)
        self.fs_subclient_obj.restore()

        job_id = self.restores_obj.submit_restore(self.client_name, self.subclient_content,
                                                  True, overwrite=True, select_all=True)
        job_status = self.job_obj.job_completion(job_id)
        if job_status['Status'] not in [
                "Completed", "Completed w/ one or more errors"]:
            raise Exception("Restore job failed. Please check the logs")

    def delete_subclient(self):
        """"Delete FS Subclient"""
        self.navigate_to_filesystem()
        self.fs_agent_obj.open_backupset_instance(self.backupset_name)
        self.fs_backupset_obj.delete_fs_subclient(self.subclient_name)
        # Validation
        if self._admin_console.check_if_entity_exists("link", self.subclient_name):
            raise Exception(
                "Validation : Subclient deletion failed, still exists in Admin Console Page")
        else:
            self.log.info("Validation : Subclient deletion successful from Admin Console Page")
