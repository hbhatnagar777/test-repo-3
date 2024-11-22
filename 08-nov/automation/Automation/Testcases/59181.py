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

    run()           --  run function of this test case

    Input Example FOR TESTCASE:
    FOR CIFS
    "testCases": {
    "59181": {
        "ClientName": "**",
        "AgentName": "File System",
        "StoragePolicyName": "**",
        "HostName": "**",
        "AccessNodes": "**,**",
        "server": "server",
        "share": "share",
        "DefaultStreams": "2",
        "No_of_dirs": 1,
        "No_of_files": 1,
        "File_length": 1024,
        "machine_username": "root",
        "machine_password": "**",
        "impersonate_username": "root",
        "impersonate_password": "**",
        "cifs": "True"
        }
    }

    FOR NFS
    "testCases": {
    "59181": {
        "ClientName": "**",
        "AgentName": "File System",
        "StoragePolicyName": "**",
        "HostName": "**",
        "AccessNodes": "**,**",
        "server": "server",
        "share": "share",
        "DefaultStreams": "2",
        "No_of_dirs": 1,
        "No_of_files": 1,
        "File_length": 1024,
        "machine_username": "root",
        "machine_password": "**",
        "impersonate_username": "root",
        "impersonate_password": "**",
        "cifs": "False"
        }
    }
"""
import time
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.page_object import handle_testcase_exception, TestStep
from functools import partial


class TestCase(CVTestCase):
    """ Command center: Create network share for NFS/CIFS from command center """
    test_step = TestStep()

    def __init__(self):
        """ Initializing the reference variables """
        super(TestCase, self).__init__()
        self.name = "Create network share for NFS/CIFS from command center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.machine = None
        self.slash_format = None
        self.fs_helper = None
        self.file_server = None
        self.access_nodes = []
        self.host_name = None
        self.host_loc = None
        self.testPath = None
        self.incPath = None
        self.fullPath = None
        self.expected_streams = None
        self.machine_username = None
        self.machine_password = None
        self.impersonate_username = None
        self.impersonate_password = None
        self.server = None
        self.share = None
        self.num_dirs = 1
        self.num_files = None
        self.file_size_kb = None
        self.mounted_path_for_sc_content = None
        self.browse_path = None
        self.cifs = None
        self.tcinputs = {
            "StoragePolicyName": None
        }

    def verify_restore(self, source_data, impersonate_user=None):
        """
           Verifies restore for the latest job
           Args:
                source_data (str) -- path to the source data
                impersonate_user (dict) -- impersonate user details
           Returns:
                None - if restore is successful
           Raises:
                Exception: if restore is not successful
        """
        self.navigator.navigate_to_file_servers()
        restore_job_id = self.file_server.restore_subclient(self.host_name, self.access_nodes[0],
                                                            selected_files=[self.fullPath],
                                                            impersonate_user=impersonate_user)
        self.log.info(f"Ran restore with job-id = {restore_job_id}")
        self.commcell.job_controller.get(restore_job_id).wait_for_completion()
        self.log.info("Restore completed")
        result, diff = self.machine.compare_meta_data(
            source_data,
            self.fullPath,
            dirtime=True, skiplink=True)
        if result:
            self.log.info("Metadata comparison was successful.")
        else:
            raise Exception(f"Metadata comparison failed, diff = {diff}")

    def get_base_cvd_from_instance(self, instance_install):
        """
            Get base directory from instance
            Args:
                 instance_install (str) -- install directory of the instance
            Returns:
                 Base directory (str) - cvd path of instance
        """
        return self.machine.join_path(instance_install, "Base", "cvd")

    def setup(self):
        """ Pre-requisites for this testcase """
        self.log.info("Initializing pre-requisites")
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser,
                                          self.commcell.webconsole_hostname)
        self.admin_console.login(username=self._inputJSONnode['commcell']['commcellUsername'],
                                 password=self._inputJSONnode['commcell']['commcellPassword'])
        self.fs_helper = FSHelper(self)
        self.file_server = FileServers(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.access_nodes = self.tcinputs["AccessNodes"].split(',')
        self.host_name = self.tcinputs["HostName"]
        self.machine = Machine(self.access_nodes[0], commcell_object=self.commcell)
        self.expected_streams = int(self.tcinputs["DefaultStreams"]) * len(self.access_nodes)
        self.server = self.tcinputs["server"]
        self.share = self.tcinputs["share"]
        self.cifs = self.tcinputs["cifs"]
        self.num_files = int(self.tcinputs.get('No_of_files', 10))
        self.file_size_kb = int(self.tcinputs.get('File_length', 10240))

        if self.cifs == "True":
            # Mount PATH WILL BE \\server\share..... FOR host_loc SPECIFIED AS \\server\share
            self.testPath = f"\\\\{self.server}\\{self.share}"
            self.host_loc = self.testPath
            self.impersonate_username = self.tcinputs["impersonate_username"]
            self.impersonate_password = self.tcinputs["impersonate_password"]
        else:
            # Mount PATH WILL BE /server/share..... FOR host_loc SPECIFIED AS server:/share
            self.testPath = f"/{self.server}/{self.share}"
            self.host_loc = f"{self.server}:/{self.share}"
        self.machine_username = self.tcinputs["machine_username"]
        self.machine_password = self.tcinputs["machine_password"]

    def run(self):
        """ Main function for test case execution """
        try:
            def verify_streams(expected, job):
                actual = self.fs_helper.get_backup_stream_count(job)
                if expected == actual:
                    self.log.info(f"Streams verified for backup job {job.job_id}")
                else:
                    self.log.info("Streams not verified")

            impersonation_args = None
            if self.cifs == "True":
                impersonation_args = {'username': self.impersonate_username, 'password': self.impersonate_password}
                partial_generate_test_data = partial(self.machine.generate_test_data, dirs=self.num_dirs,
                                                     files=self.num_files, file_size=self.file_size_kb,
                                                     **impersonation_args)
            else:
                partial_generate_test_data = partial(self.machine.generate_test_data, dirs=self.num_dirs,
                                                     files=self.num_files, file_size=self.file_size_kb)
            partial_modify_test_data = partial(self.machine.modify_test_data, modify=True)
            self.fullPath = self.machine.join_path(self.testPath, "FULL")
            self.host_loc = self.machine.join_path(self.host_loc, "FULL")

            # ***************
            # STEP 1 BEGINS
            # ***************
            self.log.info(f"Add Data for full job at location {self.fullPath}")
            partial_generate_test_data(self.fullPath)
            self.log.info("Navigate to File Server page")
            self.navigator.navigate_to_file_servers()
            self.log.info("Create NAS client")
            if self.cifs == "True":
                self.file_server.add_nas_client(name=self.host_name,
                                                host_name=self.host_name,
                                                plan=self.tcinputs["StoragePolicyName"],
                                                cifs={'access_nodes': self.access_nodes, 'content': self.host_loc,
                                                      'impersonate_user': impersonation_args})
            else:
                self.file_server.add_nas_client(name=self.host_name,
                                                host_name=self.host_name,
                                                plan=self.tcinputs["StoragePolicyName"],
                                                nfs={'access_nodes': self.access_nodes, 'content': self.host_loc})
            self.navigator.navigate_to_file_servers()
            job_id = self.file_server.backup_subclient(self.host_name, "Full")
            self.log.info(f"Ran FULL backup with job-id = {job_id}")
            self.commcell.job_controller.get(job_id).wait_for_completion()
            self.log.info("FULL backup completed")
            backup_job = self.commcell.job_controller.get(job_id)
            verify_streams(self.expected_streams, backup_job)
            source = "_".join((self.fullPath, "SOURCE"))
            self.machine.rename_file_or_folder(self.fullPath, source)
            self.verify_restore(source, impersonation_args)

            self.incPath = self.machine.join_path(self.fullPath, "INCREMENTAL")
            self.log.info(f"Add Data for incremental job at location {self.incPath}")
            partial_modify_test_data(self.fullPath)
            partial_generate_test_data(self.incPath)
            self.log.info("Navigate to File Server page")
            self.navigator.navigate_to_file_servers()
            job_id = self.file_server.backup_subclient(self.host_name, "Incremental")
            self.log.info(f"Ran Incremental backup with job-id = {job_id}")
            self.commcell.job_controller.get(job_id).wait_for_completion()
            self.log.info("Incremental backup completed")
            backup_job = self.commcell.job_controller.get(job_id)
            verify_streams(self.expected_streams, backup_job)
            if self.machine.check_directory_exists(source):
                self.machine.remove_directory(source)
            self.machine.rename_file_or_folder(self.fullPath, source)
            self.verify_restore(source, impersonation_args)

            self.log.info("Navigate to File Server page")
            self.navigator.navigate_to_file_servers()
            job_id = self.file_server.backup_subclient(self.host_name, "Synthfull")
            self.log.info(f"Ran SYNTHFULL backup with job-id = {job_id}")
            self.commcell.job_controller.get(job_id).wait_for_completion()
            self.log.info("SYNTHFULL backup completed")
            if self.machine.check_directory_exists(source):
                self.machine.remove_directory(source)
            self.machine.rename_file_or_folder(self.fullPath, source)
            self.verify_restore(source, impersonation_args)

            if self.machine.check_directory_exists(self.incPath):
                self.machine.remove_directory(self.incPath)
            self.incPath = self.machine.join_path(self.fullPath, "INCREMENTAL1")
            self.log.info(f"New Data for incremental job at location {self.incPath}")
            partial_generate_test_data(self.incPath)
            self.log.info("Navigate to File Server page")
            self.navigator.navigate_to_file_servers()
            job_id = self.file_server.backup_subclient(self.host_name, "Incremental")
            self.log.info(f"Ran Incremental backup with job-id = {job_id}")
            self.commcell.job_controller.get(job_id).wait_for_completion()
            self.log.info("Incremental backup completed")
            backup_job = self.commcell.job_controller.get(job_id)
            verify_streams(self.expected_streams, backup_job)
            if self.machine.check_directory_exists(source):
                self.machine.remove_directory(source)
            self.machine.rename_file_or_folder(self.fullPath, source)
            self.verify_restore(source, impersonation_args)

            # ***************
            # STEP 2 BEGINS
            # ***************
            # Validate all nodes are used
            self.navigator.navigate_to_file_servers()
            self.log.info("Run full on nodes")
            job_id = self.file_server.backup_subclient(self.host_name, "Full")
            self.commcell.job_controller.get(job_id).wait_for_completion()
            self.log.info("FULL backup completed")
            backup_job = self.commcell.job_controller.get(job_id)
            self.fs_helper.check_if_all_node_participated_in_backup(backup_job, self.access_nodes)
            if self.machine.check_directory_exists(source):
                self.machine.remove_directory(source)
            self.machine.rename_file_or_folder(self.fullPath, source)
            self.verify_restore(source, impersonation_args)

            # Bring 1 node down and validate backup/restore
            partial_modify_test_data(self.fullPath)
            self.log.info("Shutting down 1st node services")
            node_1 = self.access_nodes[0]
            node_1_client = self.commcell.clients.get(node_1)
            node_1_instance = node_1_client.instance
            node_1_install = node_1_client.install_directory
            node_1_ip = self.machine.ip_address
            if self.cifs == "True":
                node_1_client.stop_service(f"GxCVD({node_1_instance})")
            else:
                base_directory_cvd = self.get_base_cvd_from_instance(node_1_install)
                self.log.info("returned path is %s", base_directory_cvd)
                self.machine.kill_process(process_name=base_directory_cvd)
            self.navigator.navigate_to_file_servers()
            job_id = self.file_server.backup_subclient(self.host_name, "Incremental")
            backup_job = self.commcell.job_controller.get(job_id)
            self.log.info(f"Ran Incremental backup with job-id = {job_id}")
            backup_job.resume(wait_for_job_to_resume=True)
            self.commcell.job_controller.get(job_id).wait_for_completion()
            self.log.info("Starting 1st node services")
            if self.cifs == "True":
                self.machine = Machine(machine_name=node_1_ip,
                                       username=self.machine_username, password=self.machine_password)
                command = self.machine.join_path(node_1_client.install_directory, "Base", "GxAdmin.exe").replace(
                    " ", "' '") + " -consoleMode -startsvcgrp ALL"
                self.machine.execute_command(command)
            else:
                self.machine = Machine(node_1_ip, username=self.machine_username, password=self.machine_password)
                self.machine.execute_command(f"simpana -instance {node_1_instance} start")
            time.sleep(10)
            if self.machine.check_directory_exists(source):
                self.machine.remove_directory(source)
            self.machine.rename_file_or_folder(self.fullPath, source)
            self.verify_restore(source, impersonation_args)

            # validate backup/restore while bringing one node down in between job
            partial_modify_test_data = partial(self.machine.modify_test_data, modify=True)
            partial_modify_test_data(self.fullPath)
            self.navigator.navigate_to_file_servers()
            job_id = self.file_server.backup_subclient(self.host_name, "Incremental")
            backup_job = self.commcell.job_controller.get(job_id)
            while not backup_job.phase.upper() == 'BACKUP':
                time.sleep(5)
            # wait until backup state is running
            while not backup_job.status.upper() == "RUNNING":
                time.sleep(3)
            # time.sleep(30)
            self.log.info("Stopping 2nd node services")
            node_2 = self.access_nodes[1]
            node_2_client = self.commcell.clients.get(node_2)
            node_2_instance = node_2_client.instance
            node_2_install = node_2_client.install_directory
            machine2 = Machine(node_2, commcell_object=self.commcell)
            node_2_ip = machine2.ip_address
            if self.cifs == "True":
                node_2_client.stop_service(f"GxCVD({node_2_instance})")
            else:
                base_directory_cvd = self.get_base_cvd_from_instance(node_2_install)
                machine2.kill_process(process_name=base_directory_cvd)
            # time.sleep(60)
            self.log.info("Resuming Backup job")
            backup_job.resume(wait_for_job_to_resume=True)
            self.commcell.job_controller.get(job_id).wait_for_completion()
            if self.machine.check_directory_exists(source):
                self.machine.remove_directory(source)
            self.machine.rename_file_or_folder(self.fullPath, source)
            self.verify_restore(source, impersonation_args)
            self.log.info("Starting 2nd node services")
            if self.cifs == "True":
                machine2 = Machine(node_2_ip, username=self.machine_username, password=self.machine_password)
                command = machine2.join_path(node_2_client.install_directory, "Base", "GxAdmin.exe").replace(
                    " ", "' '") + " -console -startsvcgrp ALL -force 400"
                machine2.execute_command(command)
            else:
                machine2 = Machine(node_2_ip, username=self.machine_username, password=self.machine_password)
                machine2.execute_command(f"simpana -instance {node_2_instance} start")
            time.sleep(10)

            # Validate True-up
            self.navigator.navigate_to_file_servers()
            incPath1 = self.machine.join_path(self.fullPath, "INCREMENTAL2")
            incPath2 = self.machine.join_path(self.fullPath, "INCREMENTAL3")
            if self.cifs == "True":
                impersonation_args = {'username': self.impersonate_username, 'password': self.impersonate_password}
                partial_generate_test_data = partial(self.machine.generate_test_data, **impersonation_args)
            else:
                partial_generate_test_data = partial(self.machine.generate_test_data)
            partial_generate_test_data(incPath1)
            partial_generate_test_data(incPath2)
            job_id = self.file_server.backup_subclient(self.host_name, "Incremental")
            self.commcell.job_controller.get(job_id).wait_for_completion()
            self.log.info("Renaming is going to happen here for the folders")
            full_incr_path_to_rename = self.machine.join_path(self.fullPath, "INCREMENTAL4")
            self.machine.rename_file_or_folder(incPath1, full_incr_path_to_rename)
            self.machine.rename_file_or_folder(incPath2, incPath1)
            self.machine.rename_file_or_folder(full_incr_path_to_rename, incPath2)
            job_id = self.file_server.backup_subclient(self.host_name, "Synthfull")
            self.commcell.job_controller.get(job_id).wait_for_completion()
            job_id = self.file_server.backup_subclient(self.host_name, "Incremental")
            backup_job = self.commcell.job_controller.get(job_id)
            self.commcell.job_controller.get(job_id).wait_for_completion()
            retval = self.fs_helper.validate_trueup(backup_job)
            if retval:
                self.log.info("Trueup ran here")
            else:
                raise Exception("Trueup needs to run but didn't")
            if self.machine.check_directory_exists(source):
                self.machine.remove_directory(source)
            self.machine.rename_file_or_folder(self.fullPath, source)
            self.verify_restore(source, impersonation_args)

            # ***************
            # STEP 3 BEGINS
            # ***************
            # Retire the client
            self.navigator.navigate_to_file_servers()
            self.file_server.retire_server(self.host_name)
            self.file_server.delete_client(self.host_name)

        except Exception as excp:
            handle_testcase_exception(self, excp)

        finally:
            self.log.info("Performing cleanup")
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
