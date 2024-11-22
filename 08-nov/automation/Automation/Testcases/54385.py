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
from MediaAgents.MAUtils.mahelper import DedupeHelper
from FileSystem.FSUtils.fshelper import CommitCondition, FSHelper


class TestCase(CVTestCase):
    """
    Class for executing Nutanix NFS acceptance test case
    This test case does the following
        Step1, Create Array in the storage Arrays.
        Step2, Create a Nutanix Files Client with Linux File System Agent.
        Step3, Create subclient under the Default Backup Set with
                the provided Subclient Content.
        Step4, Run Backup Sequence as:
                Full
                Create new files -> INCR
                Modify Files -> INCR
                Rename files -> INCR
                Delete files -> INCR
                Synthetic full
                Incremental (True-Up)
        Step5, Add Shares to subclient content as provided in Inputs
        Step6, Run Backup Sequence as in Step4
        Step7, Run a Restore Sequence as:
                Restore out of place to Client
                Restore in place
                Restore out of place to filer
                ACL restore
        Step8, Run a commit job Test
    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = "Nutanix Files NFS Acceptance"
        self.array_id = None
        self.client = None
        self.content_to_add = None
        self.data_access_nodes = None
        self.mahelper = None
        self.array_name = None
        self.array_user = None
        self.array_password = None
        self.commserv_obj = None
        self.nfs_mount_dir = None
        self.sccontent = None
        self.machine_paths = None
        self.storage_policy = None
        self.helper = None
        self.client_machine = None
        self.nfs_mount_dir = None
        self.options_selector = None
        self.drive = None
        self.multistream = 5
        self.client_machine = None
        self.tcinputs = {
            "ArrayName": None,
            "ArrayUser": None,
            "ArrayPassword": None,
            "Subclient Content": None,
            "ProxyClient": None,
            "DataAccessNodes": None,
            "AddShare": None,
        }
        self.cycle_last_backup = None
        self.cycle_first_backup = None
        self.local_timezone = None
        self.cycle_ftime = None
        self.cycle_ttime = None

    def setup(self):
        self.log.info("Executing Nutanix NFS Acceptance Testcase")
        self.mahelper = DedupeHelper(self)
        self.array_name = self.tcinputs['ArrayName']
        self.array_user = self.tcinputs['ArrayUser']
        self.array_password = b64encode(self.tcinputs['ArrayPassword'].encode()).decode()
        self.commserv_obj = Machine(self.commcell.commserv_name, self.commcell)
        self.nfs_mount_dir = '/' + self.tcinputs['ArrayName']
        self.sccontent = self.tcinputs['Subclient Content']
        self.content_to_add = f"{self.array_name}:{self.tcinputs['AddShare']}"
        self.data_access_nodes = self.tcinputs['DataAccessNodes']
        self.storage_policy = self.tcinputs['StoragePolicyName']
        self.helper = FSHelper(self)        
        self.options_selector = OptionsSelector(self.commcell)
        self.machine_paths = []
        self.paths = []
        self.client_machine = Machine(self.data_access_nodes[0], self.commcell)
        self.machine_paths.append(self.client_machine.join_path(f"{self.tcinputs['ArrayName']}:", self.sccontent))
        self.paths.append(self.client_machine.join_path('', self.tcinputs['ArrayName'], self.sccontent))
        self.sccontent = self.machine_paths
        self.drive = self.options_selector.get_drive(self.client_machine)
        self.nfs_mount_dir = self.client_machine.join_path('', self.tcinputs['ArrayName'], '')
        self.multistream = 5
        
    def run(self):
        """Main function for test case execution"""

        try:

            self.log.info('Mounting the nfs path on client : %s', self.client_machine.machine_name)
            self.client_machine.mount_nfs_share(self.nfs_mount_dir, self.tcinputs['ArrayName'], '/')

            self.log.info('Creating array in storage arrays')
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
            self.backupset = self.agent.backupsets.get('defaultbackupset')
            self.log.info('Creating new subclient : auto_sub_54385')
            self.subclient = self.backupset.subclients.add(subclient_name='auto_sub_54385',
                                                           storage_policy=self.storage_policy,
                                                           description='Automation')
            self.subclient.network_share_auto_mount = True
            self.helper.populate_tc_inputs(self, mandatory=False)
            self.log.info("The subclient content to be set as %s", str(self.sccontent))
            self.subclient.content = self.sccontent
            self.subclient.set_backup_nodes(self.data_access_nodes)
            self.subclient.refresh()                  
            self.backup_sequence()

            self.log.info('Adding subclient content : %s', str(self.content_to_add))
            for item in self.content_to_add:
                self.machine_paths.append(self.content_to_add)
            self.sccontent = self.machine_paths
            self.subclient.content = self.sccontent
            self.backup_sequence()

            self.restore_sequence()

            self.commit_test()

        except Exception as exp:
            self.status = 'FAILED'
            self.log.info('TestCase failed with error: %s', str(exp))

    def tear_down(self):
        try:

            if self.client_machine:
                self.log.info('Unmounting Network FS')
                self.client_machine.unmount_path(self.nfs_mount_dir, force_unmount=True)
                self.client_machine.disconnect()
            if self.array_id:
                self.log.info('Deleting Array.')
                self.commcell.array_management.delete_array(self.array_id)
            if self.client:
                self.log.info('Deleting client.')
                self.commcell.clients.delete(self.client.name)

        except Exception as exp:
            self.log.info('Teardown function failed with error : %s', str(exp))

    def backup_sequence(self):
        """Function to run Backup Sequence as:
            Full
            Create new files -> INCR
            Modify Files -> INCR
            Rename files -> INCR
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
        self.log.info("     Delete files -> INCR")
        self.log.info("     Scan Marking Incremental Job")
        self.log.info("     Synthetic full")
        self.log.info("     Incremental (True-Up)")

        
        self.log.info("Running FuLL Backup.")
        self.helper.run_backup_verify(backup_level="Full")

        self.cycle_first_backup = self.subclient.find_latest_job(lookup_time=10)
        date_tuple = dt_tuple=tuple([int(x) for x in self.cycle_first_backup.start_time[:10].split('-')])+tuple([int(x) for x in self.cycle_first_backup.start_time[11:].split(':')])

        self.cycle_ftime = datetime.datetime(*date_tuple) - datetime.timedelta(hours = 7)
        self.log.info("The start time of backup is " + str(self.cycle_ftime))

        test_paths = self.add_test_data()

        self.log.info("Running incremental Job.")
        jobs = self.helper.run_backup_verify(backup_level="Incremental")
        log_results = self.mahelper.parse_log(client=self.data_access_nodes[0],
                                              log_file='FileScan.log',
                                              jobid=jobs[0].job_id,
                                              single_file=True,
                                              regex='No of Items from the SnapDiff')
        if log_results[0]:
            self.log.info('SnapDiff was kicked for this incremental job')
        else:
            self.log.info('SnapDiff was not kicked for this incremental job')
            raise Exception('SnapDiff was not kicked for this incremental job')

        self.log.info("Modifying Test Data.")
        for path in test_paths:
            self.client_machine.modify_test_data(path, modify=True)
        self.log.info("Running incremental Job after modifying files.")
        self.helper.run_backup_verify(backup_level="Incremental")

        self.log.info("Renaming data")
        for path in test_paths:
            self.client_machine.modify_test_data(path, rename=True)
        self.log.info("Running incremental Job after renaming Files.")
        self.helper.run_backup_verify(backup_level="Incremental")

        self.log.info("Deleting Test Data .")
        for path in test_paths:
            self.client_machine.remove_directory(path)

        self.log.info("Running incremental Job after deleting files.")
        self.helper.run_backup_verify(backup_level="Incremental")

        self.log.info("Running Scan Marking incremental Job.")
        self.helper.run_backup_verify(backup_level="Incremental")

        self.cycle_last_backup = self.subclient.find_latest_job(lookup_time=10)
        date_tuple = dt_tuple=tuple([int(x) for x in self.cycle_last_backup.end_time[:10].split('-')])+tuple([int(x) for x in self.cycle_last_backup.end_time[11:].split(':')])
        self.cycle_ttime = datetime.datetime(*date_tuple) - datetime.timedelta(hours = 7)
        self.log.info("The Cycle end time is " + str(self.cycle_ttime))
        

        self.log.info("Running Synth-Full Backup.")
        self.helper.run_backup_verify(backup_level="Synthetic_Full")

        self.log.info("Adding Test Data.")
        self.add_test_data()

        self.log.info("Running Incremental after Synth Full.")
        jobs = self.helper.run_backup_verify(backup_level="Incremental")
        log_results = self.mahelper.parse_log(client=self.data_access_nodes[0],
                                              log_file='FileScan.log',
                                              jobid=jobs[0].job_id,
                                              single_file=True,
                                              regex= 'files/folders backed up by TrueUp')
        if log_results[0]:
            self.log.info('Trueup was kicked off for Incremental after Synth Full job')
        else:
            self.log.info('Trueup was not kicked off for Incremental after Synth Full job')        

        log_results = self.mahelper.parse_log(client=self.data_access_nodes[0],
                                              log_file='FileScan.log',
                                              jobid=jobs[0].job_id,
                                              single_file=True,
                                              regex='No of Items from the SnapDiff')
        if log_results[0]:
            self.log.info('SnapDiff was kicked for this true-up job')
        else:
            self.log.info('SnapDiff was not kicked for this true-up job')

    def restore_sequence(self):
        """Function to run restore sequence as:
            Restore out of place to Client
            Restore in place
            Restore out of place to filer
            ACL restore
        """
        self.log.info("Initiating Restore Sequence:")
        self.log.info("     Restore out of place to Client")
        self.log.info("     Restore in place")
        self.log.info("     Restore out of place to filer")
        self.log.info("     ACL restore")

        proxy_restore_path = self.client_machine.join_path(self.drive, 'test_restore_54385')
        self.log.info('Running out of place restore to UNIX Client')
        job = self.helper.restore_out_of_place(client=self.tcinputs['ProxyClient'],
                                               destination_path=proxy_restore_path,
                                               paths=self.paths,
                                               restore_data_and_acl=True,
                                               preserve_level=2)
        if not job.wait_for_completion():
            raise Exception("Failed to run Out of place restore job with error: {0}".
                            format(job.delay_reason))
        self.log.info('Restore Out Of place to Unix Client successful.')

        self.log.info("Comparing the restored data with original data")
        for count in range(len(self.paths)):
            share_restore_path = self.client_machine.join_path(proxy_restore_path,
                                                               self.paths[count])
            self.compare_data(self.paths[count], share_restore_path)

        job = self.subclient.restore_in_place(paths=self.paths,
                                              proxy_client=self.tcinputs['ProxyClient'])
        self.log.info('Running In place restore. Job ID : %s', str(job.job_id))
        if not job.wait_for_completion():
            raise Exception("Failed to run In-place restore job with error: {0}".format(job.delay_reason))
        self.log.info('Restore in place successful.')

        self.log.info("Comparing in-place restored data with previous out-of-place restored data")
        for count in range(len(self.paths)):
            share_restore_path = self.client_machine.join_path(proxy_restore_path,
                                                               self.paths[count])
            self.compare_data(self.paths[count], share_restore_path)

        self.log.info('Running Multi Stream Out of place restore to filer.')
        restore_path = self.client_machine.join_path(self.paths[0], 'restore_54385')
        job = self.helper.restore_out_of_place(paths=self.paths,
                                               destination_path=restore_path,
                                               client=self.tcinputs['ProxyClient'],
                                               preserve_level=2,
                                               no_of_streams=self.multistream)
        if not job.wait_for_completion():
            raise Exception("Failed to run Out of place restore job with error: {0}".
                            format(job.delay_reason))
        self.log.info('Restore Out Of place to filer successful.')

        self.log.info("Comparing restored data at filer with original data")
        for count in range(len(self.paths)):
            share_restore_path_at_client = self.client_machine.join_path(proxy_restore_path,
                                                                         self.paths[count])
            share_restore_path_at_filer = self.client_machine.join_path(restore_path,
                                                                        self.paths[count])
            self.compare_data(share_restore_path_at_filer, share_restore_path_at_client)

        job = self.subclient.restore_in_place(paths=self.paths,
                                              proxy_client=self.tcinputs['ProxyClient'],
                                              restore_data_and_acl=False)
        self.log.info('Running ACL restore. Job ID : %s', str(job.job_id))
        if not job.wait_for_completion():
            raise Exception("Failed to run ACL restore job with error: {0}".format(job.delay_reason))
        self.log.info('ACL restore successful.')


    def get_deleted_items(self):
        """ This functions runs a browse and gives the list of deleted items by
            comparing browse content with actual content
        """
        browse_list = self.paths[:]
        for item in browse_list:
            browse_list.extend(self.subclient.browse(path=item,
                                                     show_deleted=True,
                                                     from_time = str(self.cycle_ftime),
                                                     to_time = str(self.cycle_ttime))[0])

        browse_list = browse_list[len(self.paths):]
        
        browse_list.sort()
        actual_list = []
        for item in self.paths:
            actual_list.extend(self.client_machine.get_items_list(item))

        self.log.info("Actual list is " +str(actual_list))


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
        test_path = self.client_machine.join_path('/TEST_DATA/',
                                                  ''.join(choices(string.ascii_uppercase, k=7)))
        self.client_machine.generate_test_data(test_path)
        self.log.info('Testdata generated at %s', test_path)
        self.client_machine.copy_folder(test_path, self.paths[0])
        self.log.info('Run a full backup and commit it')
        job_1 = self.subclient.backup('Full')
        self.helper.commit_job(job_1, threshold=3, commit_condition=CommitCondition.FILES)
        self.log.info('Get the expected commit files')
        expected_commit_files = self.helper.create_expected_commit_files(job_1)
        self.log.info('Add test data for Incremental Backup')
        test_path = self.client_machine.join_path('/TEST_DATA/',
                                                  ''.join(choices(string.ascii_uppercase, k=7)))
        self.client_machine.generate_test_data(test_path)
        self.log.info('Testdata generated at %s', test_path)
        self.client_machine.copy_folder(test_path, self.paths[0])
        self.log.info('Running incremental job')
        job = self.subclient.backup('Incremental')
        self.log.info("Incremental job id: %s ", job.job_id)
        if not job.wait_for_completion():
            self.log.info("Incremental job failed. Job id : %s", job.job_id)
            raise Exception
        self.log.info('Get the actual commit files')
        actual_commit_files = self.helper.get_actual_commit_files(job_1)
        self.helper.validate_commit_files(expected_commit_files, actual_commit_files)

    def check_db_exists(self):
        """
         Get the list of Shares for which the Db is created
         under job results
         """

        jr_path = list(self.helper.subclient_job_results_directory.values())[0]
        inodes = []
        for item in self.paths:
            output = self.client_machine.execute_command("stat --format '%i' {0}".format(item))
            inode = str(output.formatted_output)
            inodes.append(inode)
        for count in range(len(inodes)):
            db_dir = "/{simpana-device-*-"+inodes[count]+"}_FullBackupDatabase"
            output = self.client_machine.execute_command(
                'if ls {0}; then echo "TRUE"; fi'.format(jr_path+db_dir))
            if output.formatted_output[-1][-1] == 'TRUE':
                self.log.info('\tDB created for %s', self.sccontent[count])
            else:
                self.log.info('\tDB not created for %s', self.sccontent[count])

    def add_test_data(self):
        """
        Adds test under every path in subclient content

        Returns:
            list    --  paths where test data is copied
        """
        list_paths = []
        path_for_generating_test_data = self.client_machine.join_path(self.drive, 'TEST_DATA')
        for item in self.paths:
            random_dir_name = ''.join(choices(string.ascii_uppercase, k=7))
            path = self.client_machine.join_path(path_for_generating_test_data, random_dir_name)
            self.log.info('Generating test data at %s', path)
            self.client_machine.generate_test_data(path)
            self.log.info('Copying %s to %s', path, item)
            self.client_machine.copy_folder(path, item)
            list_paths.append(self.client_machine.join_path(item, random_dir_name))

        return list_paths

    def compare_data(self, path1, path2):
        """Compares the checksum of two data-paths
                    Arguments:
                        path1   : path of first data source

                        path2   : path of 2nd data source

                    Raises Exception if checksum do not matches
        """
        result = self.client_machine.compare_checksum(path1, path2)
        if not result[0]:
            self.log.info("Data at two paths do not match: %s", result[1])
            raise Exception("Data at two paths do not match")
        self.log.info('Comparison successful , data at both paths is identical')
