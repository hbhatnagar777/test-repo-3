# -*- coding: utf-8 -*-
# pylint: disable=R0913
# pylint: disable=R0902
# pylint: disable=W0703

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""This module provides the function or operations related to Distributed FS Apps in AdminConsole

DistributedHelper : This class provides methods for Distributed FS related operations

DistributedHelper
============

__init__()                      --  Initialize object for DistributedHelper class

delete_server()                 --  Delete server

add_server()                    --  Create server with given parameters

delete_subclient()              --  Delete subclient

add_subclient()                 --  Create subclient with given parameters

backup_subclient()              --  Backup subclient

restore_server()                --  Restore files based on given parameters

"""

from cvpysdk.job import Job
from AutomationUtils.constants import DistributedClusterPkgName
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.AdminConsole.Bigdata.details import Overview
from Web.AdminConsole.Bigdata.instances import Instances
from Web.AdminConsole.FileServerPages.fsagent import FsSubclient
from Web.AdminConsole.FileServerPages.fssubclientdetails import FsSubclientDetails
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.exceptions import CVTestStepFailure
from Web.Common.page_object import TestStep


class DistributedHelper():
    """ Helper for handling Distributed FS Apps command center operations."""
    test_step = TestStep()

    def __init__(self, testcase, pkg):
        """Initialize object for DistributedHelper class.

            Args:
                testcase       (obj)   -- testcase object

                pkg            (enum)  -- Instance of constants.DistributedClusterPkgName

            Returns:
                object - instance of DistributedHelper class

        """

        self.log = testcase.log
        self.testcase = testcase
        self.pkg = pkg
        self.is_hadoop = (pkg == DistributedClusterPkgName.HADOOP)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, testcase.commcell.webconsole_hostname)
        self.admin_console.login(testcase.inputJSONnode['commcell']['commcellUsername'],
                                 testcase.inputJSONnode['commcell']['commcellPassword'])
        self.file_servers = FileServers(self.admin_console)
        self.instances = Instances(self.admin_console)
        self.overview = Overview(self.admin_console)
        self.jobs = Jobs(self.admin_console)
        self.fs_subclient = FsSubclient(self.admin_console)
        self.fs_subclient_details = FsSubclientDetails(self.admin_console)
        self.navigator = self.admin_console.navigator
        if self.is_hadoop:
            self.navigator.navigate_to_big_data()
            if self.instances.is_instance_exists(testcase.server_name):
                self.delete_server(testcase.server_name)
        else:
            self.navigator.navigate_to_file_servers()
            if self.file_servers.is_client_exists(testcase.server_name):
                self.delete_server(testcase.server_name)

    @test_step
    def delete_server(self, server_name):
        """Delete server.

            Args:
                server_name      (str)   -- Name of the server to be deleted.

        """
        self.log.info("Deleting [%s] server", server_name)
        if self.is_hadoop:
            self.navigator.navigate_to_big_data()
            self.instances.delete_instance_name(server_name)
            if self.instances.is_instance_exists(server_name):
                raise CVTestStepFailure("[%s] Hadoop server is not getting deleted" % server_name)
        else:
            self.navigator.navigate_to_file_servers()
            try:
                self.file_servers.retire_server(server_name)
                self.admin_console.refresh_page()
            except Exception:
                pass
            if self.file_servers.is_client_exists(server_name):
                self.file_servers.delete_client(server_name)
                self.admin_console.refresh_page()
            if self.file_servers.is_client_exists(server_name):
                raise CVTestStepFailure("[%s] File server is not getting deleted" % server_name)
        self.log.info("Deleted [%s] successfully", server_name)

    @test_step
    def add_server(self, server_name, access_nodes, plan_name, hdfs_user='hdfs'):
        """Create server with given parameters.

            Args:
                server_name      (str)   -- Name of the server to be created.

                access_nodes     (list)  -- list of access nodes to select

                plan_name        (str)   -- plan name to select

                hdfs_user        (str)   -- hadoop user (only applicable for Hadoop)
                    default: 'hdfs'

        """
        if self.is_hadoop:
            self.navigator.navigate_to_big_data()
            hadoop_server = self.instances.add_hadoop_server()
            hadoop_server.add_hadoop_parameters(server_name, access_nodes, hdfs_user, plan_name)
            hadoop_server.save()
            self.navigator.navigate_to_big_data()
            if not self.instances.is_instance_exists(server_name):
                raise CVTestStepFailure("[%s] Hadoop server is not getting added" % server_name)
        else:
            self.navigator.navigate_to_file_servers()
            self.file_servers.add_distributed_app(self.pkg, server_name, access_nodes, plan_name)
            self.navigator.navigate_to_file_servers()
            if not self.file_servers.is_client_exists(server_name):
                raise CVTestStepFailure("[%s] File server is not getting added" % server_name)

    @test_step
    def delete_subclient(self, server_name, subclient_name):
        """Delete subclient.

            Args:
                server_name         (str)   -- Name of the server

                subclient_name      (str)   -- Name of the subclient to be deleted.

        """
        if self.is_hadoop:
            self.navigator.navigate_to_big_data()
            self.instances.access_instance(server_name)
            self.overview.access_hdfs()
        else:
            self.navigator.navigate_to_file_servers()
            self.file_servers.access_server(server_name)
        if not self.fs_subclient.is_subclient_exists(subclient_name):
            self.log.error("Subclient [%s] doesn't exist, returning", subclient_name)
            return
        self.log.info("Deleting [%s] subclient", subclient_name)
        self.fs_subclient.delete_subclient('defaultBackupSet', subclient_name)
        if self.fs_subclient.is_subclient_exists(subclient_name):
            raise CVTestStepFailure("[%s] subclient is not getting deleted" % subclient_name)
        self.log.info("Deleted subclient [%s] successfully", subclient_name)

    @test_step
    def add_subclient(self,
                      server_name,
                      subclient_name,
                      plan_name,
                      subclient_content=None,
                      define_own_content=True,
                      browse_and_select_content=True,
                      remove_plan_content=False,
                      exclusions=None,
                      exceptions=None):
        """Create subclient with given parameters.

            Args:
                server_name                  (str)   -- Name of the server

                subclient_name               (str)   -- Name of the subclient to be created

                subclient_content            (list)  -- Subclient content paths
                    Example: ['/test_path1','/test_path2']
                    default: None

                plan_name                    (str)   -- Plan name to select

                define_own_content           (bool)  -- Whether to use own content or plan content
                    default: True

                browse_and_select_content    (bool)  -- Whether to browse and select the content
                    default: False

                remove_plan_content          (bool)  -- Whether to remove the inherited plan content
                    default: False

                exclusions                   (list)  -- Subclient content filter paths
                    Example: ['/test_path1/filter','/test_path2/filter']
                    default: None

                exceptions                   (list)  -- Subclient content filter exception paths
                    Example: ['/test_path1/filter/exception','/test_path2/filter/exception']
                    default: None

        """
        if self.is_hadoop:
            self.navigator.navigate_to_big_data()
            self.instances.access_instance(server_name)
            self.overview.access_hdfs()
        else:
            self.navigator.navigate_to_file_servers()
            self.file_servers.access_server(server_name)
        self.fs_subclient.add_fs_subclient(backup_set='defaultBackupSet',
                                           subclient_name=subclient_name,
                                           plan=plan_name,
                                           define_own_content=define_own_content,
                                           browse_and_select_data=browse_and_select_content,
                                           backup_data=subclient_content,
                                           exclusions=exclusions,
                                           exceptions=exceptions,
                                           file_system='Unix',
                                           remove_plan_content=remove_plan_content,
                                           toggle_own_content=False)

    @test_step
    def backup_subclient(self, server_name, subclient_name, backup_type, notify=False, wait_for_completion=True):
        """Backup subclient.

            Args:
                server_name         (str)   -- Name of the server

                subclient_name      (str)   -- Name of the subclient to be backed up.

                backup_type         (enum)  -- Type of the backup

                notify              (bool)  -- Whether to notify via email about the backup
                    default: False

                wait_for_completion (bool)  -- Whether to wait till job completes.
                    default: True

            Return:
                object - instance of the cvpysdk Job class for this backup job

        """
        if self.is_hadoop:
            self.navigator.navigate_to_big_data()
            self.instances.access_instance(server_name)
            self.overview.access_hdfs()
        else:
            self.navigator.navigate_to_file_servers()
            self.file_servers.access_server(server_name)
        self.fs_subclient.access_subclient('defaultBackupSet', subclient_name)
        job_id = self.fs_subclient_details.backup(backup_type, notify, drop_down=True)
        self.log.info("Backup job [%s] started successfully", str(job_id))
        job_obj = Job(self.testcase.commcell, int(job_id))
        job_type = str(job_obj.backup_level)
        if job_obj.backup_level is None:
            job_type = str(job_obj.job_type)
        if not job_type.lower() == backup_type.value.replace("_", " ").lower():
            raise CVTestStepFailure(" Job ID [%s] was started with incorrect type" % str(job_id))
        if wait_for_completion:
            self.log.info(
                "Waiting for completion of %s backup with Job ID: %s", job_type, str(
                    job_obj.job_id))

            self.jobs.job_completion(str(job_id), skip_job_details=True)

            if not job_obj.status.lower() == "completed":
                raise CVTestStepFailure(
                    "{0} job {1} status is not Completed, job has status: {2}".format(
                        job_type, str(
                            job_obj.job_id), job_obj.status))

            self.log.info("Successfully finished %s job %s", job_type, str(job_id))
            return job_obj
        return job_obj

    @test_step
    def restore_server(self,
                       server_name,
                       source_paths=None,
                       restore_path=None,
                       unconditional_overwrite=True,
                       notify=False,
                       wait_for_completion=True,
                       cleanup=True):
        """Restore files based on given parameters.

            Args:
                server_name                 (str)       -- Name of the server

                source_paths                (str/list)  -- List of source paths to restore

                restore_path                (str)       -- Destination path where the data should be restored

                unconditional_overwrite     (bool)      -- Whether to overwrite unconditionally on destination path
                    default: True

                notify                      (bool)      -- Whether to notify via email about the backup
                    default: False

                wait_for_completion         (bool)      -- Whether to wait till job completes.
                    default: True

                cleanup                     (bool)      -- Whether to clean up the restore path before restore
                    default: True

            Return:
                object - instance of the cvpysdk Job class for this restore job

        """
        selected_files = []
        if isinstance(source_paths, str):
            selected_files.append(source_paths)
        else:
            selected_files = source_paths
        if self.is_hadoop:
            self.navigator.navigate_to_big_data()
            self.instances.access_instance(server_name)
        else:
            self.navigator.navigate_to_file_servers()
            self.file_servers.access_server(server_name)
        if cleanup:
            # clean up destination directory and create newly before starting restore
            self.testcase.client_machine.remove_directory(restore_path)
            self.testcase.client_machine.create_directory(restore_path)
        job_id = self.fs_subclient_details.restore_recovery_points(recovery_time=None,
                                                                   restore_path=restore_path,
                                                                   unconditional_overwrite=unconditional_overwrite,
                                                                   notify=notify,
                                                                   selected_files=selected_files,
                                                                   hadoop_restore=self.is_hadoop)
        self.log.info("Restore job [%s] started successfully", str(job_id))
        job_obj = Job(self.testcase.commcell, int(job_id))
        if wait_for_completion:
            self.log.info(
                "Waiting for completion of Restore with Job ID: %s", str(job_obj.job_id))

            self.jobs.job_completion(str(job_id), skip_job_details=True)

            if not job_obj.status.lower() == "completed":
                raise CVTestStepFailure(
                    "Restore job {1} status is not Completed, job has status: {2}".format(
                        str(job_obj.job_id), job_obj.status))

            self.log.info("Successfully finished restore job %s", str(job_id))
            return job_obj
        return job_obj
