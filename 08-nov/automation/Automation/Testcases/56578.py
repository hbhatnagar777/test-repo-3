# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test case to enable Ransomware Protection on existing Storage Pool of Hyperscale setup
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

    unlabelling_mountlevel() - unlabelling at cvstorage context at mount level

    check_fstab_mount_level() - to check whether the fstab entries are properly tagged with
     'cvstrorage' context

    create_denial_log() - create denials log file if doesn't exist

    rotate_audit_log() - rotate audit.log before logging for this  test case

    writing_denial_logs() - writing denail logs

basic idea of the test case:
Enabling Ransomware Protection for  Gluster Based Mountpaths
when storagepool is already present(Mount Level)

prerequisites:
HyperScale setup
1.	Already imaged hyperscale nodes with 1.5 ISO and updated to intended Service Pack.
2.	The required rpms for enabling SELinux should be already present on the node
3.	To meet (2), usually an OS upgrade is recommended.

input json file arguments required:
"56578": {
          "username": "",
          "password": "",
          "ControlNodes": {
            "MA1": "",
            "MA2": "",
            "MA3": ""
          },
          "ClientName" : "CS Client Name",
          "Agent" : "",
          "Storage_Pool_Name": "",
        }

Design steps:
1. checks whether it's a hyperscale node or not.
2. checks all the prerequistes are met - OS version, rpms , single instance
3. checks ransomware enabled already if enabled - bail out
4. create a storagepool
5. rotate audit log and create denials_log file if not created previously
6. enable ransomware protection(Run ./cvsecurity.py enable_protection -i InstanceID),
    copy contents of fstab.
7. checks fstab is properly tagged before reboot.
8. Run protect disk library(./cvsecurity.py protect_disk_library -i InstanceID)
9. verify protection mode - enforcing/permissive
10. checks fstab has tagged only allowed entries
11. validate cvstorage context tagging in /ws/* using ls -Z
12. validate cvbackup context tagging on only allowed process from config file  using pstree -z
13. validate whether mount paths are protected after doing some backups
	Performing penetration testing on protected mount paths
	 ( append content, delete content, add file)
14. Pause Protection and resume protection
15. add denial logs from audit.log to denials_log file.
16. disable protection

"""

import time
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.hyperscale_helper_duplicate import HyperScaleHelper
from AutomationUtils.options_selector import OptionsSelector
from Install import install_helper
from AutomationUtils import (constants, commonutils)
from MediaAgents.MAUtils import mahelper
from MediaAgents.MAUtils.unix_ransomware_helper_duplicate import UnixRansomwareHelper

class TestCase(CVTestCase):
    """Hyperscale TestCase to enable Ransomware Protection on existing StoragePool"""
    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case to enable Ransomware Protection on Hyperscale " \
                    "Setup having Existing StoragePool"
        self.result_string = ""
        self.backupset = ""
        self.subclient_obj = ""
        self.job_obj = ""
        self.username = ""
        self.password = ""
        self.client = ""
        self.subclient_name = ""
        self.mediaagent = ""
        self.control_nodes = {}
        self.ma1 = ""
        self.ma2 = ""
        self.ma3 = ""
        self.ma4 = ""
        self.ma5 = ""
        self.ma6 = ""
        self.mas = []
        self.ma_sessions = []
        self.install_helper_objs = []
        self.ransomware_helper_objs = []
        self.storage_pool_name = ""
        self.sql_sq_password = ""
        self.sql_login = ""
        self.policy_name = ""
        self.policy = ""
        self.content_path = ""
        self.mm_helper = None
        self.hyperscale_helper = None
        self.opt_selector = None
        self.agent = ""
        self.client_machine = ""
        self.client_name = ""
        self.backupset_name = ""
        self.ma_session1 = ""
        self.ma_session2 = ""
        self.ma_session3 = ""
        self.install_helper_obj1 = ""
        self.install_helper_obj2 = ""
        self.install_helper_obj3 = ""
        self.ransomware_helper1 = ""
        self.ransomware_helper2 = ""
        self.ransomware_helper3 = ""
        self.audit_denial_path = ""
        self.testcase_path_client = ""
        self.subclient = ""
        self.tcinputs = {
            "Storage_Pool_Name": None,
            "username": None,
            "password": None,
            "ControlNodes": {
                "MA1": None,
                "MA2": None,
                "MA3": None,
            },
            "ClientName": None,
            "AgentName" : None
        }

    def setup(self):
        """Initializes test case variables"""
        self.username = self.tcinputs.get("username")
        self.password = self.tcinputs.get("password")
        self.control_nodes = self.tcinputs.get("ControlNodes")
        self.ma1 = self.control_nodes.get('MA1')
        self.ma2 = self.control_nodes.get('MA2')
        self.ma3 = self.control_nodes.get('MA3')
        self.mas.extend((self.ma1, self.ma2, self.ma3))
        self.storage_pool_name = self.tcinputs.get("Storage_Pool_Name")
        self.client_name = self.tcinputs.get('ClientName')
        self.client = self.commcell.clients.get(self.tcinputs.get("ClientName"))
        self.agent = self.client.agents.get(self.tcinputs.get("AgentName"))
        self.backupset_name = f"{self.id}_backupset"
        self.subclient_name = f"{self.id}_subclient"
        self.policy_name = self.id + "_Policy1"
        self.mm_helper = mahelper.MMHelper(self)
        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = self.opt_selector.get_machine_object(self.tcinputs.get("ClientName"))
        self.ma_session1 = self.opt_selector.get_machine_object(self.control_nodes.get('MA1'))
        self.ma_session2 = self.opt_selector.get_machine_object(self.control_nodes.get('MA2'))
        self.ma_session3 = self.opt_selector.get_machine_object(self.control_nodes.get('MA3'))
        self.ma_sessions.extend((self.ma_session1, self.ma_session2, self.ma_session3))
        self.install_helper_obj1 = install_helper.InstallHelper(self.commcell, self.ma_session1)
        self.install_helper_obj2 = install_helper.InstallHelper(self.commcell, self.ma_session2)
        self.install_helper_obj3 = install_helper.InstallHelper(self.commcell, self.ma_session3)
        self.install_helper_objs.extend((self.install_helper_obj1,self.install_helper_obj2,
                                        self.install_helper_obj3))

        self.ransomware_helper1 = UnixRansomwareHelper(
            self.ma_session1, self.commcell, self.log)
        self.ransomware_helper2 = UnixRansomwareHelper(
            self.ma_session2, self.commcell, self.log)
        self.ransomware_helper3 = UnixRansomwareHelper(
            self.ma_session3, self.commcell, self.log)
        self.ransomware_helper_objs.extend(
            (self.ransomware_helper1,
             self.ransomware_helper2,
             self.ransomware_helper3))
        self.audit_denial_path = f'{self.ma_session1.client_object.log_directory}/{self.id}' \
                                 f'_audit_denials.log'
        # sql connection
        self.sql_sq_password = commonutils.get_cvadmin_password(self.commcell)
        self.sql_login = "sqladmin_cv"

    def unlabelling_mountlevel(self, ma_session, ransomware_helper_obj):
        """Unlabelling CVStorage tag from mount level
           Args:
               ma_session - Machine Object of MA
               ransomware_helper_obj - helper file object
           Returns : None
           """
        self.log.info("Un labelling cvstorage tag from mount level")
        self.log.info("Copying back the contents of  /etc/fstab from /root")
        if ma_session.check_file_exists("/root/fstab"):
            ma_session.copy_folder("/root/fstab", "/etc/")
        mount_paths = ransomware_helper_obj.hyperscale_get_protected_mountpaths()
        self.log.error("checking selinux context in /ws/")
        command = "ls -Z /ws/ | grep 'cvstorage' | awk '{print$5}'"
        self.log.info("Command: %s", command)
        output = ma_session.execute_command(command)
        if len(output.output) == 0:
            self.log.info("removing labels is successful")
        else:
            self.log.error("lables are not removed properly")
            raise Exception("Labels are not removed")
        for mountpath in mount_paths:
            if ransomware_helper_obj.hyperscale_validate_mountpath_protected(mountpath, self.id):
                self.log.error("Mountpath still protected, disable failed")
                raise Exception("Mountpath still protected, disable failed")

    def check_fstab_mount_level(self, ma_session):
        """check fstab entries after protect library and before reboot
           Args:
               ma_session - Machine Object of MA
           Returns : None
           """
        self.log.info("check fstab entries after protect library and before reboot")
        command = "ls /ws"
        self.log.info("Command : %s", command)
        output = ma_session.execute_command(command)
        expected_tagging_entries = output.output.split('\n')[1:-1]
        command = "cat /etc/fstab | grep 'cvstorage' | awk '{print$2}'"
        self.log.info("Command: %s", command)
        output = ma_session.execute_command(command)
        fstab_tagged_paths = output.output.split('\n')[:-1]
        fstab_tagged_paths = [mountpath[4:] for mountpath in fstab_tagged_paths]
        if ma_session.compare_lists(expected_tagging_entries, fstab_tagged_paths, sort_list=True):
            self.log.info("fstab entries tagged correctly")
        else:
            self.log.error("fstab entries not tagged correctly ")
            raise Exception("fstab entries not tagged properly")

    def create_resources(self, client_machine, backupset_name, subclient_name, policy_name, agent):
        """
        Args:
            client_machine: client machine object
            backupset_name: backupset name
            subclient_name: subclient name
            policy_name: Storage Policy name
            agent: File System
        Returns : None
        """
        drive_path_client = self.opt_selector.get_drive(client_machine)
        # creating testcase directory,content path
        self.testcase_path_client = f"{drive_path_client}{self.id}"
        self.content_path = client_machine.join_path(self.testcase_path_client, "content_path")
        if not client_machine.check_directory_exists(self.content_path):
            output = client_machine.create_directory(self.content_path)
            self.log.info("content path created",output)

        # create backupset
        self.backupset = self.mm_helper.configure_backupset(
            backupset_name, agent)

        if self.mm_helper.create_uncompressable_data(
                self.client_name, self.content_path, 1):
            self.log.info("generated content for subclient %s", subclient_name)

        storage_pool_details = self.hyperscale_helper.get_storage_pool_details(
            self.storage_pool_name)
        library_id = storage_pool_details._storage_pool_properties[
            'storagePoolDetails']['libraryList'][0]['library']['libraryId']
        gdsp = storage_pool_details.storage_pool_id
        self.log.info("Creating Policy")
        if not self.commcell.storage_policies.has_policy(policy_name):
            self.log.info("Policy does not exists, Creating %s", policy_name)
            self.policy = self.commcell.storage_policies.add(
                policy_name,
                self.hyperscale_helper.get_library_details(library_id)[2],
                self.ma1,
                global_policy_name=self.hyperscale_helper.get_policy_details(gdsp)[2])
        else:
            self.log.info("Policy exists")
            self.policy = self.commcell.storage_policies.get(policy_name)
        # create subclient and add content
        self.log.info("Creating sub client %s if not exists", subclient_name)

        if not self.backupset.subclients.has_subclient(subclient_name):
            self.subclient = self.mm_helper.configure_subclient(
                backupset_name,
                subclient_name,
                policy_name,
                self.content_path,
                agent)
        else:
            self.subclient.storage_policy = policy_name

    def cleanup_resources(self):
        """
        common function to remove the created resources of this testcase
        Removes -- (if exist)
                - Content directory
                - storage policy
                - backupset
                - StoragePool
        Returns : None
        """
        self.log.info("**************Clean up resources***************")
        try:
            # delete the generated content for this testcase if any
            # machine object initialised earlier
            if self.client_machine.check_directory_exists(self.content_path):
                self.client_machine.remove_directory(self.content_path)
                self.log.info("Deleted the generated data.")
            else:
                self.log.info("Content directory does not exist.")

            self.log.info("deleting backupset and Storage Policy of the test case")
            if self.agent.backupsets.has_backupset(self.backupset_name):
                self.agent.backupsets.delete(self.backupset_name)
                self.log.info("backup set deleted")
            else:
                self.log.info("backup set does not exist")

            if self.commcell.storage_policies.has_policy(self.policy_name):
                self.commcell.storage_policies.delete(self.policy_name)
            else:
                self.log.info("StoragePolicy doesnot exists")
            self.log.info("Clearing out StoragePool %s", self.storage_pool_name)
            self.hyperscale_helper.clean_up_storage_pool(
                self.storage_pool_name, self.sql_login, self.sql_sq_password)
            self.log.info("clean up successful")
        except Exception as exp:
            self.log.error("cleanup failed with issue: %s", exp)

    def run_backup_job(self, job_type):
        """running a backup job depending on argument
        Args :  job_type       (str)           type of backjob job
                                            (FULL, Synthetic_full)
        Returns : None
        """
        self.log.info("Starting backup job type: %s", job_type)
        job = self.subclient.backup(job_type)
        self.log.info("Backup job: %s", str(job.job_id))
        self.log.info("job type: %s", job_type)
        if not job.wait_for_completion():
            raise Exception(
                "Job {0} Failed with {1}".format(
                    job.job_id, job.delay_reason))
        self.log.info("job %s complete", job.job_id)

    def check_gluster_brick_status(self):
        """
        Checks gluster bricks are healthy  or not
        Returns: True /False

        """
        # check gluster bricks are healthy
        disk_uuids = self.hyperscale_helper.get_disk_uuid(self.mas)
        all_nodes = self.hyperscale_helper.get_all_nodes(self.storage_pool_name)
        gluster_brick_status = self.hyperscale_helper.gluster_disk_health(
            all_nodes, disk_uuids)

        # check gluster mount happened
        gluster_mount_status = True
        rows = self.hyperscale_helper.get_associated_mas(self.storage_pool_name)
        for node in rows:
            gluster_mount_status = gluster_mount_status & self.hyperscale_helper.gluster_mount(
                node[0])

        return  gluster_brick_status & gluster_mount_status

    def create_denial_log(self):
        """
        clear content of  denial log file and create log file for the denial logs
        Returns : None
        """
        output = self.ma_session1.check_file_exists(self.audit_denial_path)
        if not output:
            output = self.ma_session1.create_file(self.audit_denial_path, '')
            self.log.info(output)

        else:
            self.log.info("clear content of denial log file")
            command = f'echo > {self.audit_denial_path}'
            self.log.info("Command : %s ", command)
            output = self.ma_session1.execute_command(command)
            self.log.info(f"output {output.output} + {output.exception}")

    def rotate_audit_log(self, ma_session):
        """Rotate audit log, to log logs for the TC
        Args :
            ma_session     : media_agent object
        Returns : None
        """
        command = "service auditd rotate"
        self.log.info(f"command : {command}")
        output = ma_session.execute_command(command)
        self.log.info(f"output : {output.output}")
        if output.formatted_output != 'Rotating logs: [  OK  ]':
            self.log.error(f"audit log not rotated, exception : {output.exception}")
            raise Exception(f"audit log not rotated, exception: {output.exception}")

    def writing_denial_logs(self):
        """writing denials of audit.log file into another file.
            Returns : None
        """
        self.log.info("writing to the denials file")
        for ma_session in self.ma_sessions:
            command = "cat /var/log/audit/audit.log | grep 'cvstorage'"
            self.log.info("Command : %s ", command)
            output = ma_session.execute_command(command)
            command = f"echo '{output.output}' >> {self.audit_denial_path}"
            output = self.ma_session1.execute_command(command)
            self.log.info(output.output)

    def run(self):
        """Main function for test case execution"""
        try:
            # system requirements and check whether it is hyperscale node or not
            for ransomware_helper_obj in self.ransomware_helper_objs:
                if ransomware_helper_obj.check_sys_req():
                    self.log.info("All System Requirements are met")
                else:
                    self.log.error("System Requirements are not met")
                    raise Exception("System Requirements are not met")
                if not ransomware_helper_obj.check_hyperscale_machine():
                    self.log.error("Not a Hyperscale Node ")
                    raise Exception("System Requirements are not met")

            # check Ransomware enabled or not if enabled bail out
            for media_agent, ransomware_helper_obj in zip(self.mas, self.ransomware_helper_objs):
                self.log.info(
                    "checking whether selinux is enabled or not on Node : %s",
                    media_agent)
                if not ransomware_helper_obj.ransomware_protection_status():
                    self.log.info("SELinux is disabled on Node : %s", media_agent)
                else:
                    self.log.error("SELinux is already enable on Node : %s", media_agent)
                    raise Exception("SELinux is already enabled on Node")

            # creating storagepool
            status = self.hyperscale_helper.check_if_storage_pool_is_present(
                self.storage_pool_name)
            rows = self.hyperscale_helper.get_associated_mas(self.storage_pool_name)
            self.log.info("Number of nodes in the current storage pool = %s", str(len(rows)))
            if status is True:
                self.log.info("Storage pool : %s already present, attempting deletion",
                              self.storage_pool_name)
                self.hyperscale_helper.clean_up_storage_pool(self.storage_pool_name,
                                                             self.sql_login, self.sql_sq_password)
                status = True
                attempts = 5
                while status is True and attempts != 0:
                    status = self.hyperscale_helper.check_if_storage_pool_is_present(
                        self.storage_pool_name)
                    if status is True:
                        self.log.info("Storage pool present, cleanup is not happened yet")
                    time.sleep(30)
                    attempts = attempts - 1
                if status is True:
                    raise Exception("Storage Pool present, cleanup is not successful")
                self.log.info("Storage Pool cleanup is Successful")
            else:
                self.log.info("Storage pool : %s is not present", self.storage_pool_name)
            # Create a fresh storage pool
            # Get disk uuids for all nodes
            disk_uuids = self.hyperscale_helper.get_disk_uuid(self.mas)
            self.log.info(disk_uuids)
            self.log.info("creating storage pool: %s", self.storage_pool_name)
            status, response = self.hyperscale_helper.create_storage_pool(
                self.storage_pool_name, self.ma1, self.ma2, self.ma3)
            status = self.hyperscale_helper.validate_storage(self.storage_pool_name)
            self.log.info(response)
            status = False
            attempts = 5
            while status is False and attempts != 0:
                status = self.hyperscale_helper.check_if_storage_pool_is_present(
                    self.storage_pool_name)
                if status is False:
                    self.log.info("Storage pool not present, waiting for entry to be added")
                time.sleep(30)
                attempts = attempts - 1
            if status is False:
                raise Exception("Storage Pool creation failed")
            self.log.info("Storage Pool creation Successful")

            rows = self.hyperscale_helper.get_associated_mas(self.storage_pool_name)
            self.log.info("Number of nodes in the current storage pool = %s ", str(len(rows)))
            self.log.info("Current storage pool contains the following nodes: ")
            for row in rows:
                self.log.info(row[0])
            self.log.info(
                "Additional time for the MAs to populate the CSDB"
                " with brick health and blcok device health info ")
            time.sleep(400)

            if not self.check_gluster_brick_status():
                self.log.error("Gluster brick status bad")
                raise Exception("Gluster brick status bad")

            self.create_denial_log()

            # enable Ransomware protection
            # copying contents of fstab entry
            #checks fstab before reboot
            # Running Protect Disk Library
            # Reboot the Node
            # check  CV Services running

            for ma_session, ransomware_helper_obj in zip(
                    self.ma_sessions, self.ransomware_helper_objs):
                ransomware_helper_obj.enable_protection_linux(library_present=True)
                self.check_fstab_mount_level(ma_session)
                self.rotate_audit_log(ma_session)
                status = False
                attempts = 10
                while status is False and attempts != 0:
                    status = ransomware_helper_obj.ransomware_protection_status()
                    if status is False:
                        self.log.info("Ransomware protection is not enabled yet waiting for some time")
                    time.sleep(100)
                    attempts = attempts - 1
                if status is False:
                    raise Exception("Ransomware protection is not enabled")
                self.log.info("Ransomware is enabled ")

            # CheckReadiness of Nodes
            for ma_session, install_helper_obj in zip(self.ma_sessions, self.install_helper_objs):
                if not install_helper_obj.wait_for_services(client = ma_session.client_object):
                    self.log.info("client ma is ready")

            # check glusterservice is up
            for ma_session in self.ma_sessions:
                if self.hyperscale_helper.is_gluster_services_online(ma_session):
                    self.log.info('gluster service is active (running)')
                else:
                    self.log.error(f"Gluster failed to come online on {ma_session.machine_name}")
                    raise Exception(f"Gluster Service Inactive on {ma_session.machine_name}")

            # check gluster volume status
            if self.hyperscale_helper.gluster_volume_status(self.ma_sessions[0]) :
                self.log.info("Gluster volume is online")
            else:
                self.log.error("gluster volume is not online")
                raise Exception("Gluster volume is offline")

            if not self.check_gluster_brick_status():
                self.log.error("Gluster brick status bad")
                raise Exception("Gluster brick status bad")

            # check Peers are connected
            if self.hyperscale_helper.check_peer_status(self.ma_sessions[0]):
                self.log.info("Peers all are connected")
            else:
                self.log.error("Peers are not connected")
                raise Exception("Peers are not connected")

            # check SELinux enabled/disabled
            for media_agent, ransomware_helper_obj in zip(self.mas, self.ransomware_helper_objs):
                if ransomware_helper_obj.ransomware_protection_status():
                    self.log.info("SELinux is enable on Node : %s", media_agent)
                else:
                    self.log.error("SELinux is disabled on Node : %s", media_agent)
                    raise Exception("SELinux disabled")

            # Check the SELinux protection mode
            for media_agent, ransomware_helper_obj in zip(self.mas, self.ransomware_helper_objs):
                if not ransomware_helper_obj.check_ransomware_mode():
                    self.log.error(f"SELinux is not in enforcing mode on {media_agent}")
                    raise Exception(f"SELinux is not in enforcing mode on {media_agent}")

            # to get protected mount paths and check whether fstab has tagged only allowed entries
            # check sSELinuxLabelMode mount/file
            # checking sSELinuxProtectedMountPath registry has all the entries.
            # check cvstorage context is tagged in /ws/*
            # check selinux context tagging on cv process
            for media_agent, ma_session, ransomware_helper_obj in zip(self.mas, self.ma_sessions,
                                                                      self.ransomware_helper_objs):
                protected_mount_paths = ransomware_helper_obj.hyperscale_get_protected_mountpaths()

                if ransomware_helper_obj.hyperscale_selinux_label_mode() == 'mount':
                    self.log.info("selinuxlabel mode is set to mount")
                else:
                    self.log.error(f"selinuxlabel mode is not properly set on node {media_agent}")
                    raise Exception(f"Error in SELinux label mode on node {media_agent}")

                # checking fstab
                command = "cat /etc/fstab | grep 'cvstorage' | awk '{print$2}'"
                self.log.info("Command: %s", command)
                output = ma_session.execute_command(command)
                fstab_tagged_paths = output.output.split('\n')[:-1]
                if ma_session.compare_lists(
                        protected_mount_paths,
                        fstab_tagged_paths,
                        sort_list=True):
                    self.log.info("fstab entries are correctly tagged")
                else:
                    for path in fstab_tagged_paths:
                        if path not in protected_mount_paths:
                            self.log.error(
                                "The entry : %s is not allowed to get tagged with"
                                " cvstorage_t context", path)
                            raise Exception("Labelling Error")
                    for path in protected_mount_paths:
                        if path not in fstab_tagged_paths:
                            self.log.error(
                                "The protected mountpath : %s  not get tagged with"
                                " cvstorage_t context", path)
                            raise Exception("Labelling Error")
                # check tagging in /ws/*
                if ransomware_helper_obj.hyperscale_validate_ws_selinux_tagging\
                            (self.hyperscale_helper, self.storage_pool_name):
                    self.log.info(f"cvstorage context is correctly tagged in /ws directory"
                                  f" on node {media_agent}")
                else:
                    self.log.error(f"cvstorage context is not tagged correctly in /ws directory"
                                   f" on node {media_agent}")
                    raise Exception(f"cvstorage context is not tagged properly on node"
                                    f" {media_agent}")

                # check selinux tagging on cvprocess
                if ransomware_helper_obj.hyperscale_validate_process_selinux_tagging():
                    self.log.info(f"CV process got properly tagged with selinux context"
                                  f" on node {media_agent}")
                else:
                    self.log.error(f"CV process not properly tagged with selinux context"
                                   f" on node {media_agent}")
                    raise Exception(f"CV Process not Properly tagged with selinux context"
                                    f" on node {media_agent}")

            # generate_content for backup and Create storagepolicy , subclinet and run full backup
            # generate content for subclient
            self.create_resources(self.client_machine, self.backupset_name,
                                  self.subclient_name, self.policy_name,self.agent)

            #do backup
            self.run_backup_job("FULL")

            # check whether the gluster mountpaths are protected
            for ransomware_helper_obj in self.ransomware_helper_objs:
                protected_mount_paths = ransomware_helper_obj.hyperscale_get_protected_mountpaths()
                for mount_path in protected_mount_paths:
                    if not ransomware_helper_obj.\
                            hyperscale_validate_mountpath_protected(mount_path, self.id):
                        self.log.error("Mountpath : %s is not write protected", mount_path)
                        raise Exception("SeLinux is not working, mountpath is not write protected")

            # pause protection and resume protection
            for media_agent, ransomware_helper_obj in\
                    zip(self.mas, self.ransomware_helper_objs):
                protected_mount_paths = ransomware_helper_obj.hyperscale_get_protected_mountpaths()

                #pause_protection
                ransomware_helper_obj.pause_protection()
                if ransomware_helper_obj.check_ransomware_mode():
                    self.log.error(f"Failed to pause Protection on node {media_agent}")
                    raise Exception(f"Failed to pause Protection on node {media_agent}")

                # check tagging in /ws/*
                if ransomware_helper_obj.hyperscale_validate_ws_selinux_tagging\
                            (self.hyperscale_helper, self.storage_pool_name):
                    self.log.info(f"cvstorage context is correctly tagged in /ws directory"
                                  f" on node {media_agent}")
                else:
                    self.log.error(f"cvstorage context is not tagged correctly in /ws directory"
                                   f" on node {media_agent}")
                    raise Exception(f"cvstorage context is not tagged properly on "
                                    f"node {media_agent}")

                # check selinux tagging on cvprocess
                if ransomware_helper_obj.hyperscale_validate_process_selinux_tagging():
                    self.log.info(f"CV process got properly tagged with selinux context"
                                  f" on node {media_agent}")
                else:
                    self.log.error(f"CV process not properly tagged with selinux context"
                                   f" on node {media_agent}")
                    raise Exception(f"CV Process not Properly tagged with selinux context"
                                    f" on node {media_agent}")

                for mount_path in protected_mount_paths:
                    if not ransomware_helper_obj.hyperscale_validate_mountpath_protected\
                                (mount_path, self.id):
                        self.log.info("Mount path : %s is not write protected , "
                                      "Pause Protection is successful", mount_path)
                    else:
                        self.log.error("Mount path : %s is write protected, "
                                       "Pause Protection is not successful", mount_path)
                        raise Exception("Pause Protection Failed")

                #resume_protection
                ransomware_helper_obj.resume_protection()
                if not ransomware_helper_obj.check_ransomware_mode():
                    self.log.error(f"Failed to resume Protection on node {media_agent}")
                    raise Exception(f"Failed to resume Protection on node {media_agent}")

                # check tagging in /ws/*
                if ransomware_helper_obj.hyperscale_validate_ws_selinux_tagging\
                            (self.hyperscale_helper, self.storage_pool_name):
                    self.log.info(f"cvstorage context is correctly tagged in /ws"
                                  f" directory on node {media_agent}")
                else:
                    self.log.error(f"cvstorage context is not tagged correctly in /ws directory"
                                   f" on node {media_agent}")
                    raise Exception(f"cvstorage context is not tagged properly on node"
                                    f" {media_agent}")

                # check selinux tagging on cvprocess
                if ransomware_helper_obj.hyperscale_validate_process_selinux_tagging():
                    self.log.info(f"CV process got properly tagged with selinux context"
                                  f" on node {media_agent}")
                else:
                    self.log.error(f"CV process not properly tagged with selinux context"
                                   f" on node {media_agent}")
                    raise Exception(f"CV Process not Properly tagged with selinux context"
                                    f" on node {media_agent}")

                for mount_path in protected_mount_paths:
                    if ransomware_helper_obj.hyperscale_validate_mountpath_protected\
                                (mount_path, self.id):
                        self.log.info(
                            "Mount path : %s is write protected , Resume Protection is successful",
                            mount_path)
                    else:
                        self.log.error(
                            "Mount path : %s is not write protected, Resume Protection is"
                            " not successful", mount_path)
                        raise Exception(f"Resume Protection Failed on node {media_agent}")
        except Exception as exp:
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)

    def tear_down(self):
        """Tear down function for this test case"""
        # Deleting created objects for backup and to disable ransomware Protection
        # Turnoff maintenance mode

        self.log.info("Turnoff Maintainence Mode")
        for media_agent in self.mas:
            media_session = self.commcell.media_agents.get(media_agent)
            media_session.mark_for_maintenance(False)
        time.sleep(60)
        self.writing_denial_logs()
        for ma_session, ransomware_helper_obj in \
                zip(self.ma_sessions, self.ransomware_helper_objs):
            ransomware_helper_obj.disable_selinux()
            self.unlabelling_mountlevel(ma_session, ransomware_helper_obj)

        # cleanup resources created for the test case
        self.cleanup_resources()
        self.log.info("************Test Case Execution completed successfully******************")
