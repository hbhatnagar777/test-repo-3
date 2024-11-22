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

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

    backup_sequence() --  runs a sequence of different types of backups

    restore_sequence()  --  runs a sequence of different types of resores

    commit_test()   --  verifies commit job feature is working fine or not

    add_test_data() --  Generates test data at the subclient content

"""

import string
from base64 import b64encode
from random import choices
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.mahelper import DedupeHelper
from FileSystem.FSUtils.fshelper import CommitCondition, FSHelper


class TestCase(CVTestCase):
    """
    Class for executing Nutanix NFS Backup and Restore TestCase
    Step1, Create Array in the storage Arrays.
        Step2, Create a Nutanix Files Client with Windows File System Agent.
        Step3, Create subclient under the Default Backup Set with
                one share Subclient Content.
        Step4, Run Backup Sequence as:
                Full
                Create new files -> INCR
                Create new files -> Differential
                Add Share -> INCR
                Create new files -> INCR
                Delete Shares -> INCR
                Delete files -> INCR
                Scan Marking Incremental
                Synthetic full
                Incremental (True-Up)
        Step5, Add WildCard at Share Level as content Path
        Step6, Run Backup Sequence as in Step4
        Step7, Add Filter Content in Subclient and one Share as Subclient content
        Step9, Run Backup Sequence as in Step4
        Step10, Run a Restore Sequence as:
                Restore in place
                Restore out of place to Client
                Job based restore
        Step11, Run a commit job Test
    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Nutanix Files NFS Share Backup and Restore"
        self.array_id = None
        self.array_name = None
        self.array_user = None
        self.array_password = None
        self.data_access_nodes = None
        self.storage_policy = None
        self.helper = None
        self.mahelper = None

        self.nfs_mount_dir = None
        self.client = None
        self.shares_list = None
        self.client_machine = None
        self.nas_client = None
        self.machine_paths = []
        self.options_selector = None
        self.drive = None
        self.sccontent = None
        self.addcontent = None
        self.tcinputs = {
            "ArrayName": None,
            "ArrayUser": None,
            "ArrayPassword": None,
            "ProxyClient": None,
            "DataAccessNodes": None,
        }

    def setup(self):
        """Setup function for test case execution"""

        self.log.info("Executing Nutanix Files NFS Share Backup and Restore Testcase")
        self.array_name = self.tcinputs['ArrayName']
        self.array_user = self.tcinputs['ArrayUser']
        self.array_password = b64encode(self.tcinputs['ArrayPassword'].encode()).decode()
        self.data_access_nodes = self.tcinputs['DataAccessNodes']
        self.storage_policy = self.tcinputs['StoragePolicyName']
        self.sccontent = self.tcinputs['Subclient Content']
        self.addcontent = f"/{self.tcinputs['ArrayName']}{self.tcinputs['AddShare']}"
        self.options_selector = OptionsSelector(self.commcell)
        self.helper = FSHelper(self)
        self.mahelper = DedupeHelper(self)
        self.client_machine = Machine(self.data_access_nodes[0], self.commcell)
        self.drive = self.options_selector.get_drive(self.client_machine)
        self.nfs_mount_dir = self.client_machine.join_path('', self.tcinputs['ArrayName'], '')

    def run(self):
        """Run function for test case execution"""

        try:
            self.log.info('Mounting the nfs path on client : %s', self.client_machine.machine_name)
            self.client_machine.mount_nfs_share(self.nfs_mount_dir, self.tcinputs['ArrayName'], '/')
            self.log.info('Creating array in storage arrays : %s', self.array_name)
            self.array_id = self.commcell.array_management.add_array(vendor_name='Nutanix',
                                                                     array_name=self.array_name,
                                                                     username=self.array_user,
                                                                     password=self.array_password,
                                                                     vendor_id = 26, config_data = None)

            self.log.info('Creating new client')
            self.client = self.commcell.clients.add_nutanix_files_client(client_name=self.array_name,
                                                                         array_name=self.array_name,
                                                                         cifs_option=False,
                                                                         nfs_option=True)
            self.agent = self.client.agents.get('Linux File System')
            self.backupset = self.agent.backupsets.get('defaultBackupSet')
            self.log.info('Creating new subclient : auto_sub_54497')
            self.subclient = self.backupset.subclients.add(subclient_name='auto_sub_54497',
                                                           storage_policy=self.storage_policy,
                                                           description='Automation')
            self.helper.populate_tc_inputs(self, mandatory=False)
            self.shares_list = self.client_machine.scan_directory(self.nfs_mount_dir,
                                                                  recursive=False)[1:]
            for count in range(len(self.shares_list)):
                self.shares_list[count] = self.shares_list[count]['path']

            self.log.info('List of Shares : %s', [item.split('/')[-1] for item in self.shares_list])
            for item in self.shares_list:
                self.client_machine.scan_directory(item, recursive=False)[1:]
            

            self.machine_paths.append(self.client_machine.join_path(f"/{self.tcinputs['ArrayName']}", self.sccontent))            
            self.subclient.content = self.machine_paths
            self.log.info('Setting subclient content : %s', str(self.subclient.content))
            self.subclient.set_backup_nodes(self.data_access_nodes)
            self.subclient.refresh()

            self.backup_sequence()

            wildcard_path = f"{str(self.machine_paths[0])}/Test?"
            self.log.info('Setting wildcard as subclient content : %s', wildcard_path)
            self.subclient.content = [wildcard_path]
            self.helper.run_backup_verify(backup_level="Full")

            self.log.info('Adding filter content to subclient.')
            list_files = []
            scan_dir = f"{str(self.machine_paths[0])}/Test1"
            temp_list = self.client_machine.scan_directory(scan_dir, recursive=False)
            for item in temp_list:
                if item['path'] == scan_dir:
                   continue
                list_files.append(f"/{item['path'].strip('/')}")
            filter_content = list_files[:len(list_files) // 2]
            self.log.info('Setting filter content : %s', filter_content)
            self.subclient.filter_content = filter_content
            self.helper.run_backup_verify(backup_level="Full")

            self.subclient.content = self.machine_paths
            self.log.info("Subclient content is " + str(self.subclient.content))
            self.backup_sequence()

            self.restore_sequence()

            self.commit_test()

        except Exception as exp:
            self.status = 'FAILED'
            self.log.error('Failed to execute test case with error: %s', str(exp))

    def tear_down(self):
        """Tear Down function for the test case"""
        try:

            if self.client_machine:
                self.log.info('Unmounting NFS')
                self.client_machine.unmount_path(self.nfs_mount_dir, force_unmount=True)
                self.client_machine.disconnect()
            if self.array_id:
                self.log.info('Deleting Array.')
                self.commcell.array_management.delete_array(self.array_id)
            if self.client:
                self.log.info('Deleting client.')
                self.commcell.clients.delete(self.client.name)

        except Exception as exp:
            self.log.error('Failed to execute teardown with error: %s', str(exp))

    def backup_sequence(self):
        """Function to run Backup Sequence as:
            Full
            Create new files -> INCR
            Add Share -> INCR
            Create new files -> INCR
            Delete Shares -> INCR
            Delete files -> INCR
            Scan Marking Incremental
            Synthetic full
            Incremental (True-Up)
        """

        self.log.info("Initiating backup sequence :")
        self.log.info("     Full")
        self.log.info("     Create new files -> INCR")
        self.log.info("     Add Share -> INCR")
        self.log.info("     Create new files -> INCR")
        self.log.info("     Delete Shares -> INCR")
        self.log.info("     Delete files -> INCR")
        self.log.info("     Scan Marking Incremental")
        self.log.info("     Synthetic Full Backup")
        self.log.info("     Incremental (True-Up)")

        self.helper.run_backup_verify(backup_level='Full')

        self.add_test_data()
        job = self.helper.run_backup_verify(backup_level="Incremental")
        log_results = self.mahelper.parse_log(client=self.data_access_nodes[0],
                                              log_file='FileScan.log',
                                              jobid=job[0].job_id,
                                              single_file=True,
                                              regex='No of Items from the SnapDiff')
        if log_results[0]:
            self.log.info('SnapDiff was kicked for this incremental job')
        else:
            self.log.info('SnapDiff was not kicked for this incremental job')

        self.log.info('Adding Share %s in subclient content', str(self.addcontent))
        self.machine_paths.append(self.addcontent)
        self.sccontent = [item.strip('/') for item in self.machine_paths]
        self.subclient.content = self.sccontent
        self.log.info('Subclient content : %s', self.subclient.content)
        self.helper.run_backup_verify(backup_level="Incremental")

        list_paths = self.add_test_data()
        self.helper.run_backup_verify(backup_level="Incremental")

        self.log.info('Deleting Share from subclient content. ')
        self.machine_paths.remove(self.addcontent)
        self.sccontent = [item.strip('/') for item in self.machine_paths]
        self.subclient.content = self.sccontent
        self.log.info('Subclient content : %s', self.subclient.content)
        self.helper.run_backup_verify(backup_level="Incremental")

        self.log.info('Deleting Test Data')
        self.client_machine.remove_directory(list_paths[0])
        self.helper.run_backup_verify(backup_level="Incremental")

        '''self.log.info("Running Scan Marking incremental Job ")
        self.helper.run_backup_verify(backup_level="Incremental", scan_marking=True)'''

        self.helper.run_backup_verify(backup_level="Synthetic_Full")

        self.add_test_data()
        self.log.info("Running True-Up (Synth->Incr)")
        job = self.helper.run_backup_verify(backup_level="Incremental")
        log_results = self.mahelper.parse_log(client=self.data_access_nodes[0],
                                              log_file='FileScan.log',
                                              jobid=job[0].job_id,
                                              single_file=True,
                                              regex= 'files/folders backed up by TrueUp')
        if log_results[0]:
            self.log.info('Trueup was kicked off for Incremental after Synth Full job')
        else:
            self.log.info('Trueup was not kicked off for Incremental after Synth Full job')        

        log_results = self.mahelper.parse_log(client=self.data_access_nodes[0],
                                              log_file='FileScan.log',
                                              jobid=job[0].job_id,
                                              single_file=True,
                                              regex='No of Items from the SnapDiff')
        if log_results[0]:
            self.log.info('SnapDiff was kicked for this true-up job')
        else:
            self.log.info('SnapDiff was not kicked for this true-up job')

    def restore_sequence(self):

        """Function to run restore sequence as:
            Restore in place
            Restore out of place to filer
            Restore out of place to Client
            ACL restore
            Browse deleted items and restore
            Job based restore full the Full job taking place in backup sequence

        """
        self.log.info("Initiating Restore Sequence:")
        self.log.info("     Restore in place")
        self.log.info("     Restore out of place to filer")
        self.log.info("     Restore out of place to Client")
        self.log.info("     ACL restore")
        self.log.info("     Browse deleted items and restore")
        self.log.info("     Job based restore full the Full job taking place in backup sequence")

        job = self.subclient.restore_in_place(paths=['/'],
                                              proxy_client=self.tcinputs['ProxyClient'])
        self.log.info('Running In place restore. Job ID : %s', str(job.job_id))
        if not job.wait_for_completion():
            raise Exception("Failed to run In-place restore job with error: {0}".format(job.delay_reason))
        self.log.info('Restore in place successful.')

        proxy_restore_path = self.client_machine.join_path(self.drive, 'test_restore_54497')
        self.log.info('Running out of place restore to WINDOWS Client')
        job = self.helper.restore_out_of_place(client=self.tcinputs['ProxyClient'],
                                               destination_path=proxy_restore_path,
                                               paths=['/'],
                                               restore_data_and_acl=True)
        if not job.wait_for_completion():
            raise Exception('Restore to Windows Client Failed.Error : {0}'.format(job.delay_reason))
        self.log.info('Restore to Windows Client successful.')

        last_backup = self.subclient.find_latest_job(lookup_time=10)
        job = self.subclient.restore_in_place(paths=['/'],
                                              from_time=last_backup.start_time,
                                              to_time=last_backup.end_time,
                                              proxy_client=self.tcinputs['ProxyClient'])
        self.log.info('Running Job based In place restore for deleted items. Job ID : %s',
                      str(job.job_id))
        if not job.wait_for_completion():
            raise Exception("Failed to run In-place restore job with error: {0}".
                            format(job.delay_reason))
        self.log.info('Restore in place for deleted items successful.')

    def commit_test(self):
        """
        This functions commits a full job and
        checks if next incremental picks file which
        were not backed up by commit job.
        """

        self.log.info("Commit Job Test:")
        self.log.info("     Full (Commit)")
        self.log.info("     Incremental")

        self.log.info('Add test data for FULL backup')
        self.add_test_data()
        self.log.info('Run a full backup and commit it')
        job_1 = self.subclient.backup('Full')
        self.helper.commit_job(job_1, threshold=3, commit_condition=CommitCondition.FILES)
        self.log.info('Get the expected commit files')
        expected_commit_files = self.helper.create_expected_commit_files(job_1)
        self.log.info('Add test data for Incremental Backup')
        self.add_test_data()
        self.log.info('Running Incremental job.')
        job = self.subclient.backup('Incremental')
        self.log.info("Incremental job id: %s ", job.job_id)
        if not job.wait_for_completion():
            self.log.info("Incremental job failed. Job id : %s", job.job_id)
            raise Exception
        self.log.info('Get the actual commit files')
        actual_commit_files = self.helper.get_actual_commit_files(job_1)
        self.helper.validate_commit_files(expected_commit_files, actual_commit_files)

    def add_test_data(self):
        """
        Adds test under every path in subclient content

        Returns:
            list    --  paths where test data is copied
        """
        list_paths = []
        test_path = self.client_machine.join_path(self.drive, 'TEST_DATA')
        for item in self.machine_paths:
            random_dir_name = ''.join(choices(string.ascii_uppercase, k=7))
            path = self.client_machine.join_path(test_path, random_dir_name)
            self.log.info('Generating test data at %s', path)
            self.client_machine.generate_test_data(path)
            self.log.info('Copying %s to %s', path, item)
            self.client_machine.copy_folder(path, item)
            list_paths.append(self.client_machine.join_path(item, random_dir_name))

        return list_paths
