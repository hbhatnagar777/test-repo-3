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
from FileSystem.FSUtils.fshelper import CommitCondition, FSHelper


class TestCase(CVTestCase):
    """
    Class for executing Nutanix CIFS Backup and Restore test case
    This test case does the following
        Step1, Create Array in the storage Arrays.
        Step2, Create a Nutanix Files Client with Windows File System Agent.
        Step3, Create subclient under the Default Backup Set with
                one share Subclient Content.
        Step4, Run Backup Sequence as:
                Full
                Create new files -> INCR
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
        self.name = "Nutanix Files CIFS Share Backup and Restore"
        self.array_id = None
        self.client = None
        self.client_machine = None
        self.impersonate_user = None
        self.impersonate_password = None
        self.array_name = None
        self.array_user = None
        self.array_password = None
        self.data_access_nodes = None
        self.storage_policy = None
        self.sc_content_for_restore = None
        self.shares_list = None
        self.fs_options = None
        self.sccontent = None
        self.options_selector = None
        self.drive = None
        self.helper = None
        self.client_machine = None
        self.tcinputs = {
            "ArrayName": None,
            "ArrayUser": None,
            "ArrayPassword": None,
            "CIFSShareUser": None,
            "CIFSSharePassword": None,
            "ProxyClient": None,
            "DataAccessNodes": None,
        }

    def setup(self):
        """Setup function for test case execution"""

        self.log.info("Executing Nutanix Files CIFS Share Backup and Restore Testcase")
        self.impersonate_user = self.tcinputs['CIFSShareUser']
        self.impersonate_password = b64encode(self.tcinputs['CIFSSharePassword'].encode()).decode()
        self.array_name = self.tcinputs['ArrayName']
        self.array_user = self.tcinputs['ArrayUser']
        self.array_password = b64encode(self.tcinputs['ArrayPassword'].encode()).decode()
        self.data_access_nodes = self.tcinputs['DataAccessNodes']
        self.options_selector = OptionsSelector(self.commcell)
        self.storage_policy = self.tcinputs['StoragePolicyName']
        self.helper = FSHelper(self)
        self.client_machine = Machine(self.data_access_nodes[0], self.commcell)
        self.drive = self.options_selector.get_drive(self.client_machine)

    def run(self):
        """Run function for test case execution"""

        try:

            self.log.info('Creating array in storage arrays : %s', self.array_name)
            self.array_id = self.commcell.array_management.add_array(vendor_name='Nutanix',
                                                                     array_name=self.array_name,
                                                                     username=self.array_user,
                                                                     password=self.array_password,
                                                                     vendor_id = 26, config_data = None)

            self.log.info('Creating new client')
            self.client = self.commcell.clients.add_nutanix_files_client(client_name=self.array_name,
                                                                         array_name=self.array_name,
                                                                         cifs_option=True,
                                                                         nfs_option=False)

            self.fs_options = {'impersonate_user': self.impersonate_user,
                               'impersonate_password': self.impersonate_password,
                               'preserve_level': 1}

            self.agent = self.client.agents.get('Windows File System')
            self.backupset = self.agent.backupsets.get('defaultBackupSet')
            self.log.info('Creating new subclient : auto_sub_54496')
            self.subclient = self.backupset.subclients.add(subclient_name='auto_sub_54496',
                                                           storage_policy=self.storage_policy,
                                                           description='Automation')
            self.helper.populate_tc_inputs(self, mandatory=False)
            self.shares_list = self.client_machine.list_shares_on_network_path(self.array_name,
                                                                               self.tcinputs['CIFSShareUser'],
                                                                               self.tcinputs['CIFSSharePassword'])
            self.log.info('List of Shares : %s', self.shares_list)

            # joining two empty paths for adding double slash i.e \\ at start
            for count in range(len(self.shares_list)):
                self.shares_list[count] = self.client_machine.join_path('', '',
                                                                        self.array_name,
                                                                        self.shares_list[count])
            self.sccontent = [self.shares_list[0]]
            self.log.info('Setting subclient content : %s', self.sccontent)
            self.subclient.content = self.sccontent
            self.subclient.set_backup_nodes(self.data_access_nodes)
            self.subclient.refresh()

            properties = self.subclient.properties
            properties['impersonateUser']['userName'] = self.impersonate_user
            properties['impersonateUser']['password'] = self.impersonate_password
            self.subclient.update_properties(properties)

            self.backup_sequence()
            wildcard_path = self.shares_list[0][:-1] + '?'
            self.log.info('Setting wildcard as subclient content : %s', wildcard_path)
            self.subclient.content = [wildcard_path]
            self.helper.run_backup_verify(backup_level="Full")

            self.log.info('Adding filter content to subclient.')
            list_files = []
            temp_list = self.client_machine.scan_directory(self.shares_list[0], recursive=False)
            for item in temp_list:
                list_files.append(item['path'])
            filter_content = list_files[:len(list_files)//2]
            self.log.info('Setting filter content : %s', filter_content)
            self.subclient.filter_content = filter_content
            self.sccontent = [self.shares_list[0]]
            self.log.info('Setting subclient content after adding filters : %s', self.sccontent)
            self.subclient.content = self.sccontent
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
        if self.client_machine.get_logs_for_job_from_file(job[0].job_id, 'FileScan.log', 'No of Items from the SnapDiff'):
            self.log.info('SnapDiff was kicked for this incremental job')
        else:
            self.log.info('SnapDiff was not kicked for this incremental job')
            raise Exception('SnapDiff was not kicked for this incremental job')

        self.log.info('Adding Shares in subclient content')
        self.sccontent.append(self.shares_list[1])
        self.subclient.content = self.sccontent
        self.log.info('Subclient content : %s', self.subclient.content)
        self.helper.run_backup_verify(backup_level="Incremental")

        list_paths = self.add_test_data()
        self.helper.run_backup_verify(backup_level="Incremental")

        self.log.info('Deleting Share from subclient content. ')
        self.sccontent.remove(self.shares_list[1])
        self.subclient.content = self.sccontent
        self.log.info('Subclient content : %s', self.subclient.content)
        self.helper.run_backup_verify(backup_level="Incremental")

        self.log.info('Deleting Test Data')
        self.client_machine.remove_directory(list_paths[0])
        self.helper.run_backup_verify(backup_level="Incremental")

        self.log.info("Running Scan Marking incremental Job ")
        self.helper.run_backup_verify(backup_level="Incremental")

        self.helper.run_backup_verify(backup_level="Synthetic_Full")

        self.add_test_data()
        self.log.info("Running True-Up (Synth->Incr)")
        job = self.helper.run_backup_verify(backup_level="Incremental")
        if self.client_machine.get_logs_for_job_from_file(job[0].job_id, 'FileScan.log', 'No of Items from the SnapDiff'):
            self.log.info('SnapDiff was kicked for trueup job.')
            raise Exception('SnapDiff was kicked for true-up job')
        else:
            self.log.info('SnapDiff was not kicked for this trueup job.')

    def restore_sequence(self):

        """Function to run restore sequence as:
            Restore in place
            Restore out of place to Client
            Job based restore full the Full job taking place in backup sequence

        """
        self.log.info("Initiating Restore Sequence:")
        self.log.info("     Restore in place")
        self.log.info("     Restore out of place to Client")
        self.log.info("     Job based restore full the Full job taking place in backup sequence")

        self.sc_content_for_restore = []
        for count in range(len(self.sccontent)):
            self.sc_content_for_restore += [count]
            self.sc_content_for_restore[count] = ((self.sccontent[count]).replace("\\\\", "UNC-NT_"))

        job = self.subclient.restore_in_place(paths=self.sc_content_for_restore,
                                              fs_options=self.fs_options,
                                              proxy_client=self.tcinputs['ProxyClient'])
        self.log.info('Running In place restore. Job ID : %s', str(job.job_id))
        if not job.wait_for_completion():
            raise Exception("Failed to run In-place restore job with error: {0}".format(job.delay_reason))
        self.log.info('Restore in place successful.')

        proxy_restore_path = self.client_machine.join_path(self.drive, 'test_restore_54496')
        self.log.info('Running out of place restore to WINDOWS Client')
        job = self.helper.restore_out_of_place(client=self.tcinputs['ProxyClient'],
                                               destination_path=proxy_restore_path,
                                               paths=self.sc_content_for_restore,
                                               restore_data_and_acl=True)
        if not job.wait_for_completion():
            raise Exception('Restore to Windows Client Failed.Error : {0}'.format(job.delay_reason))
        self.log.info('Restore to Windows Client successful.')

        last_backup = self.subclient.find_latest_job(lookup_time=10)
        job = self.subclient.restore_in_place(paths=self.sc_content_for_restore,
                                              from_time=last_backup.start_time,
                                              to_time=last_backup.end_time,
                                              fs_options=self.fs_options,
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
                    list    --  paths where test data is generated
        """
        list_paths = []
        path_for_generating_test_data = self.client_machine.join_path(self.drive, 'TEST_DATA')
        for item in self.sccontent:
            random_dir_name = ''.join(choices(string.ascii_uppercase, k=7))
            path = self.client_machine.join_path(path_for_generating_test_data, random_dir_name)
            self.log.info('Generating test data at %s', path)
            self.client_machine.generate_test_data(path)
            self.log.info('Copying %s to %s', path, item)
            self.client_machine.copy_folder_to_network_share(path, item,
                                                             self.tcinputs['CIFSShareUser'],
                                                             self.tcinputs['CIFSSharePassword'])
            list_paths.append(self.client_machine.join_path(item, random_dir_name))

        return list_paths
