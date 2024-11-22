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

    get_deleted_items() --  gives list of deleted items by browsing subclient

    get_db_list()   --  gives list of shares for which DB is created under job results

    add_test_data() --  Generates test data at the subclient content

    compare_data()  -- compares data at two paths by calculating the checksum

"""
import datetime
import string
from base64 import b64encode
from random import choices
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import CommitCondition, FSHelper
import traceback


class TestCase(CVTestCase):
    """
    Class for executing Nutanix CIFS acceptance test case
    This test case does the following
        Step1, Create Array in the storage Arrays.
        Step2, Create a Nutanix Files Client with Windows File System Agent.
        Step3, Create subclient under the Default Backup Set with
                the provided Subclient Content.
        Step4, Run Backup Sequence as:
                Full
                Create new files -> INCR
                Modify Files -> INCR
                Rename files -> INCR
                Differential
                Delete files -> INCR
                Scan Marking Incremental Job
                Synthetic full
                Incremental (True-Up)
        Step5, Add Shares to subclient content as provided in Inputs
        Step6, Run Backup Sequence as in Step4
        Step7, Run a Restore Sequence as:
                Restore out of place to Client
                Restore in place
                Restore out of place to filer
                ACL restore
                Browse deleted items and restore
                Job based restore
        Step8, Run a commit job Test

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Nutanix Files CIFS Acceptance"
        self.array_id = None
        self.impersonate_user = None
        self.impersonate_password = None
        self.array_name = None
        self.array_user = None
        self.array_password = None
        self.sccontent = None
        self.content_to_add = None
        self.data_access_nodes = None
        self.storage_policy = None
        self.helper = None
        self.client = None
        self.client_machine = None
        self.fs_options = None
        self.sc_content_for_restore = None
        self.options_selector = None
        self.drive = None
        self.sccontent = None
        self.multistream = 5
        self.tcinputs = {
            "ArrayName": None,
            "ArrayUser": None,
            "ArrayPassword": None,
            "Subclient Content": None,
            "CIFSShareUser": None,
            "CIFSSharePassword": None,
            "ProxyClient": None,
            "DataAccessNodes": None,
            "AddShare": None,
        }

    def setup(self):
        """Setup function for test case execution"""

        self.log.info("Executing Nutanix CIFS Acceptance Testcase")
        self.impersonate_user = self.tcinputs['CIFSShareUser']
        self.impersonate_password = b64encode(self.tcinputs['CIFSSharePassword'].encode()).decode()
        self.array_name = self.tcinputs['ArrayName']
        self.array_user = self.tcinputs['ArrayUser']
        self.array_password = b64encode(self.tcinputs['ArrayPassword'].encode()).decode()
        self.sccontent = self.tcinputs['Subclient Content'].split(",")
        self.content_to_add = self.tcinputs['AddShare'].split(",")
        self.data_access_nodes = self.tcinputs['DataAccessNodes']
        self.storage_policy = self.tcinputs['StoragePolicyName']
        self.helper = FSHelper(self)
        self.client_machine = Machine(self.data_access_nodes[0], self.commcell)
        self.options_selector = OptionsSelector(self.commcell)
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
            self.client = self.commcell.clients.get(str(self.array_name))
            self.agent = self.client.agents.get('Windows File System')
            self.backupset = self.agent.backupsets.get('defaultBackupSet')
            self.log.info('Creating new subclient : auto_sub_54383')
            self.subclient = self.backupset.subclients.add(subclient_name='auto_sub_54383',
                                                           storage_policy=self.storage_policy,
                                                           description='Automation')
            self.helper.populate_tc_inputs(self, mandatory=False)

            self.subclient.set_backup_nodes(self.data_access_nodes)
            self.subclient.refresh()
            self.subclient.content = self.sccontent

            properties = self.subclient.properties
            properties['impersonateUser']['userName'] = self.impersonate_user
            properties['impersonateUser']['password'] = self.impersonate_password
            self.subclient.update_properties(properties)

            self.backup_sequence()
            self.log.info('Adding subclient content : %s', self.content_to_add)
            self.sccontent += self.content_to_add
            self.subclient.content = self.sccontent
            self.backup_sequence()

            self.restore_sequence()
            self.subclient.content = self.tcinputs['Subclient Content'].split(",")
            self.commit_test()

        except Exception as exp:
            self.log.info(traceback.print_exc())
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
            Modify Files -> INCR
            Rename files -> INCR
            Differential
            Delete files -> INCR
            Scan Marking Incremental Job
            Synthetic full
            Incremental (True-Up)
        """
        self.log.info("Initiating backup sequence :")
        self.log.info("     Full")
        self.log.info("     Create new files -> INCR")
        self.log.info("     Modify Files -> INCR")
        self.log.info("     Rename files -> INCR")
        self.log.info("     Differential")
        self.log.info("     Delete files -> INCR")
        self.log.info("     Scan Marking Incremental Job")
        self.log.info("     Synthetic full")
        self.log.info("     Incremental (True-Up)")

        self.log.info("Running FULL Backup.")
        self.helper.run_backup_verify(backup_level="Full")
        #self.log.info('Getting list of Shares for which DB is created.')
        #self.get_db_list()

        test_paths = self.add_test_data()

        self.log.info("Running incremental Backup")
        jobs = self.helper.run_backup_verify(backup_level="Incremental")
        if self.client_machine.get_logs_for_job_from_file(jobs[0].job_id, 'FileScan.log', 'No of Items from the SnapDiff'):
            self.log.info('SnapDiff was kicked for this incremental job')
        else:
            self.log.info('SnapDiff was not kicked for this incremental job')
            raise Exception('SnapDiff was not kicked for this incremental job')

        self.log.info('Modifying test Data')
        for path in test_paths:
            self.client_machine.modify_test_data(path, modify=True)
        self.log.info("Running incremental Job after modifying files.")
        self.helper.run_backup_verify(backup_level="Incremental")

        self.log.info("Renaming Test Data.")
        for path in test_paths:
            self.client_machine.modify_test_data(path, rename=True)
        self.log.info("Running incremental Job after renaming Files.")
        self.helper.run_backup_verify(backup_level="Incremental")

        self.log.info("A job submitted as Differential, should be getting converted into an Incremental backup.")
        self.helper.run_backup_verify(backup_level="Differential")

        self.log.info("Deleting Test Data .")
        for path in test_paths:
            self.client_machine.remove_directory(path)
        self.log.info("Running incremental Job after deleting files.")
        self.helper.run_backup_verify(backup_level="Incremental")

        self.log.info("Running Scan Marking incremental Job.")
        self.helper.run_backup_verify(backup_level="Incremental")

        self.helper.run_backup_verify(backup_level="Synthetic_Full")

        self.log.info('Adding Test Data')
        self.add_test_data()

        self.log.info("Running True-Up (Synth->Incr)  Job.")
        jobs = self.helper.run_backup_verify(backup_level="Incremental")
        if self.client_machine.get_logs_for_job_from_file(jobs[0].job_id, 'FileScan.log', 'No of Items from the SnapDiff'):
            self.log.info('SnapDiff was  kicked for trueup job.')
        else:
            self.log.info('SnapDiff was not kicked for this trueup job.')

    def restore_sequence(self):
        """Function to run restore sequence as:
            Restore out of place to Client
            Restore in place
            Restore out of place to filer
            ACL restore
            Browse deleted items and restore
            Job based restore

        """
        self.log.info("Initiating Restore Sequence:")
        self.log.info("     Restore out of place to Client")
        self.log.info("     Restore in place")
        self.log.info("     Restore out of place to filer")
        self.log.info("     ACL restore")
        self.log.info("     Browse deleted items and restore")
        self.log.info("     Job based restore")

        self.sc_content_for_restore = []
        for count in range(len(self.sccontent)):
            self.sc_content_for_restore += [count]
            self.sc_content_for_restore[count] = ((self.sccontent[count]).replace("\\\\", "UNC-NT_"))

        proxy_restore_path = self.client_machine.join_path(self.drive, 'test_restore_54383')
        self.log.info('Running out of place restore to WINDOWS Client')
        job = self.helper.restore_out_of_place(client=self.tcinputs['ProxyClient'],
                                               destination_path=proxy_restore_path,
                                               paths=self.sc_content_for_restore,
                                               restore_data_and_acl=True,
                                               preserve_level=2)
        if not job.wait_for_completion():
            raise Exception('Restore to Windows Client Failed.Error : {0}'.format(job.delay_reason))
        self.log.info('Restore to Windows Client successful.')

        self.log.info("Comparing the restored data with original data")
        for count in range(len(self.sccontent)):
            share_restore_path = self.client_machine.join_path(proxy_restore_path,
                                                               self.sc_content_for_restore[count])
            self.compare_data(self.sccontent[count], share_restore_path)

        job = self.subclient.restore_in_place(paths=self.sc_content_for_restore,
                                              fs_options=self.fs_options,
                                              proxy_client=self.tcinputs['ProxyClient'])
        self.log.info('Running In place restore. Job ID : %s', str(job.job_id))
        if not job.wait_for_completion():
            raise Exception("Failed to run In-place restore job with error: {0}".format(job.delay_reason))
        self.log.info('Restore in place successful.')

        self.log.info("Comparing in-place restored data with previous out-of-place restored data")
        for count in range(len(self.sccontent)):
            share_restore_path = self.client_machine.join_path(proxy_restore_path,
                                                               self.sc_content_for_restore[count])
            self.compare_data(self.sccontent[count], share_restore_path)

        self.log.info('Running Multi Stream Out of place restore to filer.')
        restore_path = self.client_machine.join_path(self.sccontent[0], 'restore54383')
        job = self.helper.restore_out_of_place(paths=self.sc_content_for_restore,
                                               destination_path=restore_path,
                                               client=self.tcinputs['ProxyClient'],
                                               impersonate_user=self.impersonate_user,
                                               impersonate_password=self.impersonate_password,
                                               no_of_streams=self.multistream,
                                               preserve_level=2)
        if not job.wait_for_completion():
            raise Exception("Failed to run restore job with error: {0}".format(job.delay_reason))

        self.log.info("Comparing restored data at filer with original data")
        for count in range(len(self.sccontent)):
            share_restore_path_at_client = self.client_machine.join_path(proxy_restore_path,
                                                                         self.sc_content_for_restore[count])
            share_restore_path_at_filer = self.client_machine.join_path(restore_path,
                                                                        self.sc_content_for_restore[count])
            self.compare_data(share_restore_path_at_client, share_restore_path_at_filer)

        job = self.subclient.restore_in_place(paths=self.sc_content_for_restore,
                                              fs_options=self.fs_options,
                                              proxy_client=self.tcinputs['ProxyClient'],
                                              restore_data_and_acl=False)
        self.log.info('Running ACL restore. Job ID : %s', str(job.job_id))
        if not job.wait_for_completion():
            raise Exception("Failed to run ACL restore job with error: {0}".format(job.delay_reason))
        self.log.info('ACL restore successful.')

        diff_list = self.get_deleted_items()
        job = self.subclient.restore_in_place(paths=diff_list,
                                              fs_options=self.fs_options,
                                              proxy_client=self.tcinputs['ProxyClient'])
        self.log.info('Running In place restore for deleted items. Job ID : %s', str(job.job_id))
        if not job.wait_for_completion():
            raise Exception("Failed to run In-place restore job with error: {0}".
                            format(job.delay_reason))
        self.log.info('Restore in place for deleted items successful.')

        last_backup_job = self.subclient.find_latest_job(lookup_time=10)
        job = self.subclient.restore_in_place(paths=self.sc_content_for_restore,
                                              from_time=last_backup_job.start_time,
                                              to_time=last_backup_job.end_time,
                                              fs_options=self.fs_options,
                                              proxy_client=self.tcinputs['ProxyClient'])
        self.log.info('Running Job based In place restore for deleted items. Job ID : %s',
                      str(job.job_id))
        if not job.wait_for_completion():
            raise Exception("Failed to run In-place restore job with error: {0}".
                            format(job.delay_reason))
        self.log.info('Restore in place for deleted items successful.')

    def get_deleted_items(self):
        """ This functions runs a browse and gives the list of deleted items by
            comparing browse content with actual content
        """

        today = datetime.datetime.today()
        yesterday = today - datetime.timedelta(days=1)
        yesterday = str(yesterday).split('.')[0]

        browse_list = []
        for count in range(len(self.sccontent)):
            browse_list += [count]
            browse_list[count] = ((self.sccontent[count]).replace("\\\\", "UNC-NT_"))

        for item in browse_list:
            browse_list.extend(self.subclient.browse(path=item,
                                                     show_deleted=True,
                                                     from_time=yesterday)[0])

        browse_list = browse_list[len(self.sccontent):]
        browse_list.sort()

        actual_list = []
        for item in self.sccontent:
            actual_list.extend(self.client_machine.get_items_list(item))
        for count in range(len(actual_list)):
            actual_list[count] = ((actual_list[count]).replace("\\\\", "UNC-NT_"))

        diff = [item for item in browse_list if item not in actual_list]
        self.log.info("Deleted Items : %s", diff)
        return diff

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

    def get_db_list(self):
        """
        Get the list of Shares for which the Db is created
        under job results
        """
        jr_path = list(self.helper.subclient_job_results_directory.values())[0]
        full_path = self.client_machine.join_path(jr_path, self.tcinputs['ArrayName'])
        folders = self.client_machine.scan_directory(full_path, recursive=False)
        for item in folders:
            self.log.info('     Database created for %s', item['path'].split('\\')[-1])

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

    def compare_data(self, path1, path2):
        """Compares the checksum of two data-paths
            Arguments:
                path1   : path of first data source

                path2   : path of 2nd data source

            Raises Exception if checksum do not matches
        """
        self.log.info("First Path is .. %s", str(path1))
        self.log.info("Second Path is .. %s", str(path2))
        result = self.client_machine.compare_checksum(path1, path2)
        if not result[0]:
            self.log.info("Data at two paths do not match: %s", result[1])
            raise Exception("Data at two paths do not match")
        self.log.info('Comparison successful , data at both paths is identical')
