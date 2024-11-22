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

    unlabelling_filelevel() - unlabelling at cvstorage context at mount level

    check_fstab_file_level() - to check whether the fstab entries are properly
    tagged with 'cvstrorage' context

    create_denial_log() - create denials log file if doesn't exist

    rotate_audit_log() - rotate audit.log before logging for this  test case

    writing_denial_logs() - writing denail logs to logfile

    enable_protection() - enables ransomware protection on the node

    validate_protection() - checks whethere mount paths are protected

    brick_replacement() - triggers brick replacement on the node

basic idea of the test case:
Enabling Ransomware Protection for  Gluster Based Mountpaths
when storagepool is not  present already(File Level)

prerequisites:
HyperScale setup
1.	Already imaged hyperscale nodes with 1.5 ISO and updated to intended Service Pack.
2.	The required rpms for enabling SELinux should be already present on the node
3.	To meet (2), usually an OS upgrade is recommended.

input json file arguments required:
"58134": {
          "username": "",
          "password": "",
          "ControlNodes": {
            "MA1": "",
            "MA2": "",
            "MA3": ""
          },
          "Storage_Pool_Name": "",
        }

Design steps:
1. checks whether it's a hyperscale node or not.
2. checks all the prerequistes are met - OS version, rpms , single instance
3. checks ransomware enabled already if enabled - bail out
4. rotate audit log and create denials_log file if not created previously
5. enable ransomware protection(Run ./cvsecurity.py enable_protection -i InstanceID),
    copy contents of fstab.
6. checks fstab is properly tagged before reboot.
7. verify protection mode - enforcing/permissive
8. create a storagepool
9. checks fstab has tagged only allowed entries
10. validate cvstorage context tagging in /ws/* using ls -Z
11. validate cvbackup context tagging on only allowed process from config file  using pstree -z
12. Trigger brick replacment
13. check fstab and /ws/ for cvcontext
14. validate whether mount paths are protected after doing some backups
	Performing penetration testing on protected mount paths
	 ( append content, delete content, add file)
15. add denial logs from audit.log to denials_log file.
16. disable protection

"""

import time
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from AutomationUtils.options_selector import OptionsSelector
from Install import install_helper
from AutomationUtils import (constants, commonutils)
from MediaAgents.MAUtils import mahelper
from MediaAgents.MAUtils.unix_ransomware_helper import UnixRansomwareHelper
from AutomationUtils import config


class TestCase(CVTestCase):
    """Hyperscale TestCase to enable Ransomware Protection on existing StoragePool"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case to enable Ransomware Protection on Hyperscale Setup before  " \
                    " StoragePool Creation - File Level"
        self.result_string = ""
        self.backupset = ""
        self.client = ""
        self.client_name = ""
        self.client_obj = ""
        self.subclient_name = ""
        self.control_nodes = {}
        self.ma1 = ""
        self.ma2 = ""
        self.ma3 = ""
        self.mas = []
        self.node = ""
        self.brick = ""
        self.device_os_path = ""
        self.new_device_os_path = ""
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
        self.client_machine = ""
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
            "ControlNodes": {
                "MA1": None,
                "MA2": None,
                "MA3": None,
            },
            "MA": "",
            "Brick": ""
        }

    def setup(self):
        """Initializes test case variables"""
        self.control_nodes = self.tcinputs.get("ControlNodes")
        self.ma1 = self.control_nodes.get('MA1')
        self.ma2 = self.control_nodes.get('MA2')
        self.ma3 = self.control_nodes.get('MA3')
        self.mas.extend((self.ma1, self.ma2, self.ma3))
        self.storage_pool_name = self.tcinputs.get("Storage_Pool_Name")
        self.node = self.tcinputs["MA"]
        self.brick = self.tcinputs["Brick"]
        self.device_os_path = '/ws/' + self.brick
        self.client = self.commcell.commserv_client
        self.client_name = self.commcell.commserv_name
        self.client_obj = self.commcell.clients.get(self.client_name)
        self.agent = self.client_obj.agents.get("FILE SYSTEM")
        self.agent = self.client.agents.get("File System")
        self.backupset_name = f"{self.id}_backupset"
        self.subclient_name = f"{self.id}_subclient"
        self.policy_name = self.id + "_Policy1"
        self.mm_helper = mahelper.MMHelper(self)
        self.mm_dedupe_helper = mahelper.DedupeHelper(self)
        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = self.opt_selector.get_machine_object(self.client)
        self.ma_session = self.opt_selector.get_machine_object(self.node)
        self.ma_session1 = self.opt_selector.get_machine_object(self.control_nodes.get('MA1'))
        self.ma_session2 = self.opt_selector.get_machine_object(self.control_nodes.get('MA2'))
        self.ma_session3 = self.opt_selector.get_machine_object(self.control_nodes.get('MA3'))
        self.ma_sessions.extend((self.ma_session1, self.ma_session2, self.ma_session3))
        self.install_helper_obj1 = install_helper.InstallHelper(self.commcell, self.ma_session1)
        self.install_helper_obj2 = install_helper.InstallHelper(self.commcell, self.ma_session2)
        self.install_helper_obj3 = install_helper.InstallHelper(self.commcell, self.ma_session3)
        self.install_helper_objs.extend((self.install_helper_obj1, self.install_helper_obj2,
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
        self.sql_login = config.get_config().SQL.Username
        self.sql_sq_password = config.get_config().SQL.Password

    def unlabelling_filelevel(self, ma_session, ransomware_helper_obj):
        """Un labelling cvstorage tag from file level
        Args:
               ma_session - Machine Object of MA
               ransomware_helper_obj - helper file object
        Returns : None
        """
        self.log.info("Un labelling cvstorage tag from File level")
        self.log.info("Copying back the contents of  /etc/fstab from /root")
        if ma_session.check_file_exists("/root/fstab"):
            ma_session.copy_folder("/root/fstab", "/etc/")
        self.log.info("Removing context on fstab entries")
        command = """sed -i 's/,context="system_u:object_r:cvstorage_t:s0"//g' /root/fstab"""
        self.log.info(command)
        ma_session.execute_command(command)
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
        self.log.info("Un labelling cvstorage tag from file level")
        for mountpath in mount_paths:
            if 'glus' not in mountpath:
                command = f"chcon -R system_u:object_r:unlabeled_t:s0 {mountpath}"
                self.log.info("command: %s", command)
                output = ma_session.execute_command(command)
                self.log.info(output.output)
                if ransomware_helper_obj.hyperscale_validate_mountpath_protected \
                            (mountpath, self.id):
                    self.log.error(f"Mountpath still protected, disable failed", {mountpath})
                    raise Exception(f"Mountpath still protected, disable failed", {mountpath})

    def check_fstab_file_level(self, ma_session):
        """chekcs fstab has all the tagging happened properly
            Args:
               ma_session - Machine Object of MA
            Returns : None
           """
        self.log.info("check fstab entries after protect library and before reboot")
        command = "ls /ws"
        self.log.info("Command : %s", command)
        output = ma_session.execute_command(command)
        expected_tagging_entries = output.output.split('\n')[1:-1]
        expected_tagging_entries = [path for path in expected_tagging_entries if 'glus' in path]
        command = "cat /etc/fstab | grep 'cvstorage' | awk '{print$2}'"
        self.log.info("Command: %s", command)
        output = ma_session.execute_command(command)
        fstab_tagged_paths = output.output.split('\n')[:-1]
        fstab_tagged_paths = [mountpath[4:] for mountpath in fstab_tagged_paths]
        if ma_session.compare_lists(expected_tagging_entries, fstab_tagged_paths, sort_list=True)[0]:
            self.log.info("fstab entries tagged correctly")
        else:
            self.log.error("fstab entries not tagged correctly ")
            raise Exception("fstab entries not tagged properly")

    def create_resources(self, client_machine, backupset_name, subclient_name, policy_name, agent):
        """
        creates storagepool, subclient and adds content for the Test case
        creating storagepool
        Args:
            client_machine: client machine object
            backupset_name: backupset name
            subclient_name: subclient name
            policy_name: Storage Policy name
            agent: File System
        Returns : None
        """
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
        attempts = 15
        rows = ""
        while not rows and attempts!=0 :
            query = f"select * from MMDiskHWInfo as MD , APP_Client as AP where AP.id = MD.hostId and" \
                    f" AP.name = '{self.ma1}' and MD.BrickHealth=23"
            self.csdb.execute()
            rows = self.csdb.fetch_all_rows()
            time.sleep(60)
            attempts = attempts-1
        if attempts ==0 and rows=="" :
            self.log.error("CSDB not populated with Nodes details")
            raise Exception("CSDB not populated with Nodes details")

        if not self.check_gluster_brick_status():
            self.log.error("Gluster brick status bad")
            raise Exception("Gluster brick status bad")

        # check glusterservice is up
        for ma_session in self.ma_sessions:
            if self.hyperscale_helper.is_gluster_services_online(ma_session):
                self.log.info(f'gluster service is active (running) on {ma_session.machine_name} ')
            else:
                self.log.error(f"Gluster failed to come online on {ma_session.machine_name}")
                raise Exception("Gluster Service Inactive")

        # check gluster volume status
        if self.hyperscale_helper.gluster_volume_status(self.ma_sessions[0]):
            self.log.info("Gluster volume is online")
        else:
            self.log.error("gluster volume is not online")
            raise Exception("Gluster volume is offline")
        # check Peers are connected
        if self.hyperscale_helper.check_peer_status(self.ma_sessions[0]):
            self.log.info("Peers all are connected")
        else:
            self.log.error("Peers are not connected")
        drive_path_client = self.opt_selector.get_drive(client_machine)
        # creating testcase directory,content path
        self.testcase_path_client = f"{drive_path_client}{self.id}"
        self.content_path = client_machine.join_path(self.testcase_path_client, "content_path")
        if client_machine.check_directory_exists(self.content_path):
            self.client_machine.remove_directory(self.content_path)
            self.log.info("Deleted the generated data.")
        output = client_machine.create_directory(self.content_path)
        self.log.info("content path created %s", output)

        # create backupset
        self.backupset = self.mm_helper.configure_backupset(
            backupset_name, agent)

        if self.mm_helper.create_uncompressable_data(
                self.client, self.content_path, 1):
            self.log.info("generated content for subclient %s", subclient_name)

        storage_pool_details = self.hyperscale_helper.get_storage_pool_details(
            self.storage_pool_name)
        library_id = storage_pool_details._storage_pool_properties[
            'storagePoolDetails']['libraryList'][0]['library']['libraryId']
        gdsp = storage_pool_details.storage_pool_id
        self.log.info("Creating Policy")
        if not self.commcell.storage_policies.has_policy(policy_name):
            self.log.info("Policy does not exist, Creating %s", policy_name)
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

        return gluster_brick_status & gluster_mount_status

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

    def brick_replacement(self):
        """triggering brick replacment.
            Returns : None
        """
        nodes = self.hyperscale_helper.get_all_nodes_hostids(self.storage_pool_name)
        self.log.info("All node ids associated with pool are %s", nodes)

        # Getting node and disk for replacement
        self.log.info("Getting node and disk for replacement")
        self.node_id = self.hyperscale_helper.get_host_id(self.node)
        self.log.info("Node %s, host_id is %s", self.node, self.node_id)

        # Checking node part of storage pool or not ( handle it api doen't handle it, would disturb other node)
        if int(self.node_id) not in nodes:
            self.log.error("Node %s not part of Pool %s", self.node,
                           self.storage_pool_name)
            raise Exception("Node not part of Storage Pool")
        else:
            self.log.info("Node %s part of Pool %s", self.node,
                          self.storage_pool_name)

        # checking brick part of node
        self.log.info("device_os_path: %s", self.device_os_path)
        brick_info = self.hyperscale_helper.node_brick_info(self.node_id, self.device_os_path)
        self.disk_id = str(brick_info[4])
        self.log.info("Disk id %s for brick %s ", self.disk_id, self.device_os_path)

        # checking brick part of pool and gluster
        gluster_brick = self.hyperscale_helper.check_gluster_brick_online(self.node, self.storage_pool_name,
                                                                          self.device_os_path)

        # Checking brick health of brick being replaced
        self.hyperscale_helper.gluster_healthy_brick_status(self.node_id, self.device_os_path)

        # Getting gluster size info before triggering replace
        glus_info_before = self.hyperscale_helper.gluster_vol_info(self.node)

        self.log.info("****************Replacing disk ******************")
        status_fstab = True
        self.log.info("Getting sd name for the disk")
        self.sd_name = self.hyperscale_helper.sd_name_for_disk(self.node, self.device_os_path)
        # Check flag status
        flag = self.hyperscale_helper.brick_flag_status(hostid=self.node_id, device_os=self.device_os_path)
        # Trigger disk replacement, check fstab entry
        entry_old = self.hyperscale_helper.check_fstab_entry(self.node, self.device_os_path)
        if not entry_old:
            self.log.error("No entry in fstab for %s", self.device_os_path)
            raise Exception("No entry in fstab check disk")
        if not flag & 4:
            # Check flag status

            self.log.info("flag status before replace")
            self.hyperscale_helper.brick_flag_status(hostid=self.node_id, device_os=self.device_os_path)

            # Un Mounting disk
            self.log.info("Un mounting disk %s to make it offline and bad", self.device_os_path)
            self.hyperscale_helper.unmount_brick(self.node, self.device_os_path, self.storage_pool_name)
            flag = self.hyperscale_helper.brick_flag_status(hostid=self.node_id, device_os=self.device_os_path)
            count = 20
            while not flag & 16 and count >= 0:
                self.log.info("waiting to reflect offline for disk %s", self.device_os_path)
                flag = self.hyperscale_helper.brick_flag_status(self.node_id, self.device_os_path)
                count -= 1
                time.sleep(120)
            self.log.info("Disk %s offline", self.device_os_path)
            self.hyperscale_helper.gluster_healthy_brick_status(self.node_id, self.device_os_path)

            flag, response = self.hyperscale_helper.replace_brick(media_agent=self.node, brick_id=self.disk_id,
                                                                  pool=self.storage_pool_name)

            # Checking new disk availability
            disk_available_stauts = self.hyperscale_helper.replace_brick_available(self.node)
            if not disk_available_stauts:
                self.log.error("No disk available for replacement")

            # Replace success failure logs
            status, response_log = self.hyperscale_helper.replace_log_status(self.node)
            self.log.info("Status of Replace %s", status)
            for log in response_log:
                self.log.info(log)
            # Repalce failure re mounting the disk again
            if not status:
                self.hyperscale_helper.mount_brick(self.node, self.device_os_path, self.storage_pool_name)
                raise Exception(response_log)
            else:
                self.hyperscale_helper.formatting_replaced_disk(self.node, self.sd_name)
                status_reset = self.hyperscale_helper.verify_reset_brick(self.node, self.storage_pool_name,
                                                                         self.device_os_path)

        else:
            status_fstab = True
            self.log.info("Replace request cannot be submitted as previous request in progress")

        # for replace submitted
        # New disk
        new_brick_info = self.hyperscale_helper.get_disk_by_disk_id(self.disk_id)
        self.new_device_os_path = str(new_brick_info[3])
        self.log.info("old device path %s and new device path %s", self.device_os_path,
                      self.new_device_os_path)
        flag = self.hyperscale_helper.brick_flag_status(self.node_id, self.new_device_os_path)

        # Check entries for heal
        if not self.hyperscale_helper.gluster_heal_entries(self.node, self.storage_pool_name):
            self.log.info("Entries not zero yet")
        else:
            self.log.info("heal success and entries 0 now")

        # Checking new disk health
        self.hyperscale_helper.gluster_healthy_brick_status(self.node_id, self.new_device_os_path)

        # for replace submitted
        flag = self.hyperscale_helper.brick_flag_status(self.node_id, self.new_device_os_path)
        # check fstab entries for replace
        entry_new = self.hyperscale_helper.check_fstab_entry(self.node, self.new_device_os_path)
        if not entry_new:
            self.log.error("No entry in fstab for %s", self.new_device_os_path)
        if status_fstab is False:
            status_fstab, res = self.hyperscale_helper.replace_fstab_entry(self.node, entry_old,
                                                                           entry_new)
            if status_fstab is False:
                self.log.error(res)
                raise Exception(res)

        attempts = 60
        status_heal = False
        while status_heal is False and int(flag) != 1 and status_fstab is True:
            if status_heal is False:
                status_heal = self.hyperscale_helper.heal_disk_entry(self.node, self.new_device_os_path)
            if int(flag) != 1:
                flag = self.hyperscale_helper.brick_flag_status(self.node_id, self.new_device_os_path)
            self.log.info("Waiting for flag set to 1")
            time.sleep(300)
        if attempts ==0 and flag!=1 :
            self.log.info("Flag not set 1 for Replaced brick ")
            raise Exception("Flag not set 1 for Replaced brick ")
        # Checking new brick part of gluster or not
        replaced_gluster_brick = self.hyperscale_helper.check_gluster_brick_online(self.node,
                                                                                   self.storage_pool_name,
                                                                                   self.new_device_os_path)

        # Checking gluster size after replacement
        glus_info_after = self.hyperscale_helper.gluster_vol_info(self.node)
        glus_size_staus = self.hyperscale_helper.verify_replace_gluster_size(glus_info_before, glus_info_after)
        if not glus_size_staus:
            self.log.info("Gluster size not same after replacement")
        else:
            self.log.info("Brick Replacement completed successfully")

    def enable_protection(self):
        """
                  enable Ransomware protection
                  copying contents of fstab entry
                  checks fstab before reboot
                  Reboot the Node
                  check  CV Services running

                    Returns : None
                """

        for ma_session, ransomware_helper_obj in zip(self.ma_sessions,
                                                     self.ransomware_helper_objs):
            self.log.info(f"Enabling protection on {ma_session.machine_name}")
            ransomware_helper_obj.enable_protection_linux(library_present=False)
            self.check_fstab_file_level(ma_session)
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
            if not install_helper_obj.wait_for_services(client=ma_session.client_object):
                self.log.info("client ma is ready")

        # check SELinux enabled/disabled
        for ma_session, ransomware_helper_obj in zip(self.ma_sessions, self.ransomware_helper_objs):
            if ransomware_helper_obj.ransomware_protection_status():
                self.log.info("SELinux is enable on Node : %s", ma_session.machine_name)
            else:
                self.log.error("SELinux is disabled on Node : %s", ma_session.machine_name)
                raise Exception("SELinux disabled")

        # Check the SELinux protection mode
        for media_agent, ransomware_helper_obj in zip(self.mas, self.ransomware_helper_objs):
            if not ransomware_helper_obj.check_ransomware_mode():
                self.log.error(f"SELinux is not in enforcing mode on {media_agent}")
                raise Exception(f"SELinux is not in enforcing mode on {media_agent}")
        time.sleep(300)

    def validate_protection(self):
        """
          to get protected mount paths and check whether fstab has tagged only allowed entries
          check sSELinuxLabelMode mount/file
          checking sSELinuxProtectedMountPath registry has all the entries.
          check cvstorage context is tagged in /ws/*
          check selinux context tagging on cv process

          Returns : None
        """
        for media_agent, ma_session, ransomware_helper_obj in zip(self.mas, self.ma_sessions,
                                                                  self.ransomware_helper_objs):

            if ransomware_helper_obj.hyperscale_selinux_label_mode() == 'file':
                self.log.info(f"selinuxlabel mode is set to File level on node {media_agent}")
            else:
                self.log.error(f"selinuxlabel mode is not properly set on node {media_agent}")
                raise Exception(f"Error in SELinux label mode on node {media_agent}")
            # checking fstab
            self.check_fstab_file_level(ma_session)

            # check tagging in /ws/*

            if ransomware_helper_obj.hyperscale_validate_ws_selinux_tagging \
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
                    raise Exception("Not a Hyperscale Node")
                if ransomware_helper_obj.check_hyperscale_gluster():
                    self.log.error("Not a Hyperscale 1.5")
                    raise Exception("Not a Hyperscale 1.5")

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

            self.create_denial_log()

            # do backup
            self.run_backup_job("FULL")

            self.enable_protection()

            self.validate_protection()

            # generate_content for backup and Create storagepolicy , subclinet and run full backup
            # generate content for subclient
            self.create_resources(self.client_machine, self.backupset_name,
                                  self.subclient_name, self.policy_name, self.agent)

            store = self.hyperscale_helper.get_active_files_store(self.storage_pool_name)
            quick_dv2 = self.mm_dedupe_helper.run_dv2_job(store, 'full', 'quick')
            Query = f"select count(*) from archchunkddbdrop where sidbstoreid={store.store_id}"
            self.csdb.execute(Query)
            rows = self.csdb.fetch_all_rows()
            if rows[0] != '0':
                self.log.info("Validate DV2 is failed : archchunkddbdrop table has entries")
                raise Exception("Validate DV2 is failed : archchunkddbdrop table has entries")

            command = f"wc -l {self.ma_session.client_object.log_directory}/CVMA.log"
            self.log.info(command)
            output = self.ma_session.execute_command(command)
            lines = int(output.output.split()[0])
            self.log.info(f"number of CVMA log lines before brick replacement {lines}")

            self.log.info("*************************Replacing Brick*************************")
            self.brick_replacement()

            #verify the CVMA log for storagepool protecion replace suceeded

            log_line = f"CVMAGlusStoragePool::ReplaceDisk [  ]  storage protection replace operation succeeded [{self.device_os_path}]"
            line_num, line = self.hyperscale_helper.search_log_line(self.ma_session, '/var/log/commvault/Log_Files/CVMA.log', log_line, from_line=lines, last=True, tries=100, interval=5,
                            fixed_string=True)
            if not line :
                self.log.error(f"Storage Protection Replace operation logs are not found on {self.node} CVMA.log")
                raise Exception(f"Storage Protection Replace operation logs are not found on {self.node} CVMA.log")
            self.log.info(f"Log line : {line} found at line : {line_num} on {self.node}")

            # verify cvcontext tagging on replaced brick fstab entry
            self.log.info("verify cvcontext tagging on replaced brick fstab entry")

            command = f"cat /etc/fstab | grep {self.device_os_path} "
            command = command + " | awk '{print$4}' "
            output = self.ma_session.execute_command(command)
            if 'context="system_u:object_r:cvstorage_t:s0"' not in output.output:
                self.log.error(f"Context is not tagged properly for {self.device_os_path} brick in fstab on {self.node}")
                raise Exception(f"Context is not tagged properly for {self.device_os_path} brick in fstab on {self.node} ")

            # verify cvcontext tagging on bricks after replacement
            self.log.info("verify cvcontext tagging on replaced brick")
            command = f"ls -Z /ws | grep {self.brick}"
            command = command + " | awk '{print$4}' "
            output = self.ma_session.execute_command(command)
            if 'system_u:object_r:cvstorage_t:s0' not in output.output.split('\n')[0]:
                self.log.error(f"Context is not tagged properly for {self.device_os_path} brick on {self.node}")
                raise Exception(f"Context is not tagged properly for {self.device_os_path} brick on {self.node}")

            # check whether the gluster mountpaths are protected
            for media_agent, ransomware_helper_obj in \
                    zip(self.mas, self.ransomware_helper_objs):
                protected_mount_paths = ransomware_helper_obj.hyperscale_get_protected_mountpaths()
                for mount_path in protected_mount_paths:
                    if not ransomware_helper_obj.\
                            hyperscale_validate_mountpath_protected(mount_path, self.id):
                        self.log.error("Mountpath : %s is not write protected", mount_path)
                        raise Exception(f"SeLinux is not working, mountpath is not write "
                                        f"protected on node {media_agent}")
            self.log.info("************Test Case Execution completed successfully******************")

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
            self.unlabelling_filelevel(ma_session, ransomware_helper_obj)

            # clearing the properties folder under /etc/CommvaultRegistry/Galaxy/Instance00x/0/.properties
            delete_file_path = f"/etc/CommVaultRegistry/Galaxy/{ma_session.instance}/MediaAgent/0/.properties"
            self.log.info("Deleting File: %s", delete_file_path)
            output = ma_session.delete_file(delete_file_path)

            # clearing the regkeys related to SELinux
            regkeys_to_clear = ['sProtectDiskLibraryStorageEnabled', 'sRestartCVSecurity', 'sSELinuxLabelMode',
                                'sSELinuxProtectedMountPaths', 'sSELinuxSecurityEnabled']
            for regkey in regkeys_to_clear:
                command = f"sed -i '/{regkey}/d' {ma_session.key % ('MediaAgent')}"
                self.log.info("Command: %s", command)
                output = ma_session.execute_command(command)
        # cleanup resources created for the test case
        self.cleanup_resources()
