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
    setup()         --  setup function of this test case
    run()           --  run function of this test case
    tear_down()     --  tear down function of this test case
"""
import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Application.CloudApps import constants as cloud_apps_constants
from Application.CloudApps.cloud_connector import CloudConnector

class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name                (str)       --  name of this test case
                applicable_os   (str)       —  applicable os for this test case
                                                            Ex: self.os_list.WINDOWS
                 product            (str)     —  applicable product for this test case
                                                                 Ex: self.products_list.FILESYSTEM
                features             (str)      —  qcconstants feature_list item
                                                             Ex: self.features_list.DATAPROTECTION
                 show_to_user   (bool)    —  test case flag to determine if the test case is
                                                             to be shown to user or not
                      Accept:
                                           True    –   test case will be shown to user from commcell gui
                                           False   –   test case will not be shown to user
                        default: False
                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type
        """
        super(TestCase, self).__init__()
        self.name = 'Verification of all types of out of place restores using all possible combinations in both scenarios when ' \
                    'items exists at the destination and when Item does not exist at the location for OneDrive V2 ' \
                    'agent . '
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.CLOUDCONNECTOR
        self.feature = self.features_list.AUTOMATION
        self.show_to_user = True
        self.proxy_client = None
        self.cv_cloud_object = None
        self.users = None
        self.oop_user = None
        self.client_name = None
        self.number_of_docs = None
        self.o365_plan = None
        self.dbo = None
        self.tcinputs = {
            'ServerPlanName': None,
            'IndexServer': None,
            'AccessNodes': None,
            'O365Plan': None,
            'NumberOfDocs': None,
            'Users': None,
            'OopUser': None,
            'application_id': None,
            'application_key_value': None,
            'azure_directory_id': None
        }

    def _initialize_sdk_objects(self):
        """Initializes the sdk objects after app creation"""

        self.log.info(f'Create client object for: {self.client_name}')
        self._client = self.commcell.clients.get(self.client_name)

        self.log.info(f'Create agent object for: {cloud_apps_constants.ONEDRIVE_AGENT}')
        self._agent = self._client.agents.get(cloud_apps_constants.ONEDRIVE_AGENT)

        self.log.info(f'Create instance object for: {cloud_apps_constants.ONEDRIVE_INSTANCE}')
        self._instance = self._agent.instances.get(cloud_apps_constants.ONEDRIVE_INSTANCE)

        self.log.info(f'Create backupset object for: {cloud_apps_constants.ONEDRIVE_BACKUPSET}')
        self._backupset = self._instance.backupsets.get(cloud_apps_constants.ONEDRIVE_BACKUPSET)

        self.log.info(f'Create sub-client object for: {cloud_apps_constants.ONEDRIVE_SUBCLIENT}')
        self._subclient = self._backupset.subclients.get(cloud_apps_constants.ONEDRIVE_SUBCLIENT)

    def run_and_verify_discovery(self):

        """Run discovery and verify its completion"""

        # Run discovery
        self.log.info(f'Running the discovery')
        self.subclient.run_subclient_discovery()

        # Verify discovery
        self.log.info(f'Verifying the discovery')
        status, res = self.subclient.verify_discovery_onedrive_for_business_client()
        if status:
            self.log.info("Discovery successful")
        else:
            raise Exception("Discovery is not successful")

    def delete_data_and_add_users(self):

        """ Deletes data in Onedrive users and adds the AD group to client and creates new data in them"""

        # Delete data on Onedrive user accounts
        for user in self.users:
            self.log.info(f'Deleting data on {user}\'s OneDrive')
            self.cv_cloud_object.one_drive.delete_all_data_on_onedrive(user)

        # Add users to client
        self.log.info(f'Adding users: {self.users} to client')
        self.subclient.add_users_onedrive_for_business_client(self.users, self.o365_plan)

        # Create data in users Onedrive
        self.log.info(f'Generating new data on {self.users} OneDrive')
        for i in range(len(self.users)):
            self.log.info(f'Creating {self.number_of_docs} files in {self.users[i]}\'s OneDrive')
            self.cv_cloud_object.one_drive.create_files(no_of_docs=self.number_of_docs, user=self.users[i])

        # Renaming for deleted items
        self.cv_cloud_object.one_drive.rename_file_or_folder(cloud_apps_constants.ONEDRIVE_FOLDER,
                                                             "Old_" + cloud_apps_constants.ONEDRIVE_FOLDER,
                                                             self.users[3])

    def run_backup(self):

        """ Runs backup of all users in the client """

        # Run backup of all users
        self.log.info('Run an incremental level backup')
        backup_job = self.client.backup_all_users_in_client()
        if not backup_job.wait_for_completion():
            raise Exception(
                "Failed to run FULL backup with error: {0}".format(backup_job.delay_reason)
            )
        self.log.info("Backup job: %s completed successfully", backup_job.job_id)

    def verify_restore(self, restore_job, user, **kwargs):

        """ Verifies the restore job completion and it's statistics

            Args:
                restore_job (object)         --  instance of the restore job
                user (string)                --  Restored user
                oop (bool)                   --  Flag to check oop or not

         """

        # Verify restore job completion
        self.cv_cloud_object.cvoperations.check_job_status(job=restore_job, backup_level_tc='Restore')
        if restore_job.status == 'Completed':
            self.log.info("Restore completed")
        else:
            raise Exception(f"Restore not completed with {restore_job.pending_reason}")

        oopUser = kwargs.get('oopUser', None)
        restore_as_copy = kwargs.get('restore_as_copy', False)

        # Verify restore stats
        if oopUser:
            data = {'job_list': [restore_job.job_id, user, self.oop_user, user]}
            self.dbo.save_into_table('job', data, data_type='_list_oop')
            self.cv_cloud_object.one_drive.compare_file_properties(oop=True, to_disk=False, incremental=True,
                                                                   user_id=user,restore_as_copy=restore_as_copy)
        else:
            self.cv_cloud_object.one_drive.compare_file_properties(oop=False, to_disk=False, incremental=True,
                                                                   user_id=user, restore_as_copy=restore_as_copy)

        number_of_items_restored = self.cv_cloud_object.cvoperations.get_number_of_successful_items(restore_job)
        number_of_skipped_items = restore_job.details['jobDetail']['attemptsInfo'][0]['numSkipped']

        if number_of_items_restored + number_of_skipped_items == (self.number_of_docs+1)+2:
            self.log.info("The number of files restored matches with number of files in Onedrive")
        else:
            raise Exception(
                f"Restore verification is not success: {number_of_items_restored+number_of_skipped_items} {self.number_of_docs+3} not matched")

    def perform_oop_restores(self, skip_file_permissions = True):
        if not skip_file_permissions:
            self.log.info('Run OOP restores with skip_file_permissions option disabled')
        # Files doesn't exist in destination

        self.log.info('Deleting all data in destination account for OOP restore')
        self.cv_cloud_object.one_drive.delete_all_data_on_onedrive(self.oop_user)

        # Restore with 'skip' option
        self.log.info(f'Run OOP restore with skip option for user: {self.users[0]} when files does not exist')
        job1 = self.subclient.out_of_place_restore_onedrive_for_business_client(users=[self.users[0]],
                                                               destination_path=self.oop_user, skip_file_permissions=skip_file_permissions)

        self.verify_restore(job1, self.users[0], oopUser=self.oop_user)

        # Restore with 'skip' option
        self.log.info(f'Run OOP restore with skip option for user: {self.users[0]} when files exist')
        job2 = self.subclient.out_of_place_restore_onedrive_for_business_client(users=[self.users[0]],
                                                               destination_path=self.oop_user, skip_file_permissions=skip_file_permissions)

        self.verify_restore(job2, self.users[0], oopUser=self.oop_user)

        # Restore with 'restore as a copy' option
        self.log.info(
            f'Run OOP restore with restore as a copy option for user: {self.users[1]} when files does not exist')
        job3 = self.subclient.out_of_place_restore_onedrive_for_business_client(users=[self.users[1]],
                                                               destination_path=self.oop_user, restore_as_copy=True, skip_file_permissions=skip_file_permissions)

        self.verify_restore(job3, self.users[1], oopUser=self.oop_user, restore_as_copy=True)

        # Restore with 'restore as a copy' option
        self.log.info(
            f'Run OOP restore with restore as a copy option for user: {self.users[1]} when files exist')
        job4 = self.subclient.out_of_place_restore_onedrive_for_business_client(users=[self.users[1]],
                                                               destination_path=self.oop_user, restore_as_copy=True, skip_file_permissions=skip_file_permissions)

        self.verify_restore(job4, self.users[1], oopUser=self.oop_user, restore_as_copy=True)

        # Restore with 'unconditional overwrite' option
        self.log.info(
            f'Run OOP restore with unconditional overwrite option for user: {self.users[2]} when files does not exist')
        job5 = self.subclient.out_of_place_restore_onedrive_for_business_client(users=[self.users[2]],
                                                               destination_path=self.oop_user, overwrite=True, skip_file_permissions=skip_file_permissions)

        self.verify_restore(job5, self.users[2], oopUser=self.oop_user)

        # Restore with 'unconditional overwrite' option
        self.log.info(
            f'Run OOP restore with unconditional overwrite option for user: {self.users[2]} when files exist')
        job6 = self.subclient.out_of_place_restore_onedrive_for_business_client(users=[self.users[2]],
                                                               destination_path=self.oop_user, overwrite=True, skip_file_permissions=skip_file_permissions)

        self.verify_restore(job6, self.users[2], oopUser=self.oop_user)

    def perform_inplace_restores(self, skip_file_permissions=True):
        if not skip_file_permissions:
            self.log.info('Run inplace restores with skip_file_permissions option disabled')

        # Files exist in destination

        # Restore with 'skip' option
        self.log.info(f'Run inplace restore with skip option for user: {self.users[0]} when files exist')
        job1 = self.subclient.in_place_restore_onedrive_for_business_client(users=[self.users[0]], skip_file_permissions=skip_file_permissions)
        self.verify_restore(job1, self.users[0])

        # Restore with 'restore as a copy' option
        self.log.info(
            f'Run inplace restore with restore as a copy option for user: {self.users[1]} when files exist')
        job2 = self.subclient.in_place_restore_onedrive_for_business_client(users=[self.users[1]], restore_as_copy=True, skip_file_permissions=skip_file_permissions)
        self.verify_restore(job2, self.users[1], restore_as_copy=True)

        # Restore with 'unconditional overwrite' option
        self.log.info(
            f'Run inplace restore with unconditional overwrite option for user: {self.users[2]} when files exist')
        job3 = self.subclient.in_place_restore_onedrive_for_business_client(users=[self.users[2]], overwrite=True, skip_file_permissions=skip_file_permissions)
        self.verify_restore(job3, self.users[2])

        # Files doesn't exist in destination

        self.log.info('Deleting all data in Onedrive user accounts for inplace restore')
        for user in self.users:
            self.cv_cloud_object.one_drive.delete_all_data_on_onedrive(user)

        # Restore with 'skip' option
        self.log.info(f'Run inplace restore with skip option for user: {self.users[0]} when files does not exist')
        job1 = self.subclient.in_place_restore_onedrive_for_business_client(users=[self.users[0]], skip_file_permissions=skip_file_permissions)
        self.verify_restore(job1, self.users[0])

        # Restore with 'restore as a copy' option
        self.log.info(
            f'Run inplace restore with restore as a copy option for user: {self.users[1]} when files does not exist')
        job2 = self.subclient.in_place_restore_onedrive_for_business_client(users=[self.users[1]], restore_as_copy=True, skip_file_permissions=skip_file_permissions)
        self.verify_restore(job2, self.users[1], restore_as_copy=True)

        # Restore with 'unconditional overwrite' option
        self.log.info(
            f'Run inplace restore with unconditional overwrite option for user: {self.users[2]} when files does not exist')
        job3 = self.subclient.in_place_restore_onedrive_for_business_client(users=[self.users[2]], overwrite=True, skip_file_permissions=skip_file_permissions)
        self.verify_restore(job3, self.users[2])

    def verify_include_deleted_items_option(self):

        # Delete data and create new data

        self.cv_cloud_object.one_drive.delete_all_data_on_onedrive(self.users[3])
        self.cv_cloud_object.one_drive.create_files(no_of_docs=self.number_of_docs, user=self.users[3])

        # Run an incremental backup
        self.run_backup()

        # Perform restore with include deleted items option disabled

        restore_job1 = self.subclient.in_place_restore_onedrive_for_business_client(users=[self.users[3]], include_deleted_items=False)
        self.cv_cloud_object.cvoperations.check_job_status(job=restore_job1, backup_level_tc='Restore')
        if restore_job1.status == 'Completed':
            self.log.info("Restore completed")
        else:
            raise Exception(f"Restore not completed with {restore_job1.pending_reason}")

        number_of_items_restored = self.cv_cloud_object.cvoperations.get_number_of_successful_items(restore_job1)
        number_of_skipped_items = restore_job1.details['jobDetail']['attemptsInfo'][0]['numSkipped']

        if number_of_items_restored + number_of_skipped_items == (self.number_of_docs+1)+2:
            self.log.info("The number of files restored matches with number of files in Onedrive")
        else:
            raise Exception(
                f"Restore verification is not success: {number_of_items_restored + number_of_skipped_items} {self.number_of_docs + 3} not matched")

        # Perform restore with include deleted items option enabled

        restore_job2 = self.subclient.in_place_restore_onedrive_for_business_client(users=[self.users[3]], include_deleted_items=True)
        self.cv_cloud_object.cvoperations.check_job_status(job=restore_job2, backup_level_tc='Restore')
        if restore_job2.status == 'Completed':
            self.log.info("Restore completed")
        else:
            raise Exception(f"Restore not completed with {restore_job2.pending_reason}")
        number_of_items_restored = self.cv_cloud_object.cvoperations.get_number_of_successful_items(restore_job2)
        number_of_skipped_items = restore_job2.details['jobDetail']['attemptsInfo'][0]['numSkipped']
        if number_of_items_restored + number_of_skipped_items == (self.number_of_docs+1)*2 + 2:
            self.log.info("The number of files restored matches with number of files in Onedrive")
        else:
            raise Exception(
                f"Restore verification is not success: {number_of_items_restored + number_of_skipped_items} {self.number_of_docs*2 + 4} not matched")

    def setup(self):
        """Setup function of this test case"""

        # Create a client
        self.client_name = 'OD_70938'
        self.log.info(f'Creating OneDrive client: {self.client_name}')
        self.commcell.clients.add_onedrive_for_business_client(client_name=self.client_name,
                                                     server_plan=self.tcinputs.get('ServerPlanName'),
                                                     azure_directory_id=self.tcinputs.get("azure_directory_id"),
                                                     azure_app_id=self.tcinputs.get("application_id"),
                                                     azure_app_key_id=self.tcinputs.get("application_key_value"),
                                                     **{
                                                         'index_server': self.tcinputs.get('IndexServer'),
                                                         'access_nodes_list': self.tcinputs.get('AccessNodes')
                                                     })

        # Verify client creation
        if self.commcell.clients.has_client(self.client_name):
            self.log.info("Client is created.")

        self._initialize_sdk_objects()
        self.users = self.tcinputs.get('Users')
        self.oop_user = self.tcinputs.get('OopUser')
        self.number_of_docs = self.tcinputs.get('NumberOfDocs')
        self.o365_plan = self.tcinputs.get('O365Plan')
        self.proxy_client = self.tcinputs['AccessNodes'][0]
        self.cv_cloud_object = CloudConnector(self)
        self.cv_cloud_object.cvoperations.cleanup()
        self.dbo = self.cv_cloud_object.dbo

    def run(self):
        """Run function of this test case"""
        try:

            self.run_and_verify_discovery()

            self.delete_data_and_add_users()

            # run backup of all users
            self.run_backup()

            self.log.info(f'Assigning skip, restore as a copy, unconditional overwrite respectively to {self.users[0]}, {self.users[1]}, {self.users[2]}')

            # Perform OOP restores
            self.log.info("Peroforming OOP restore with skip file permissions enabled")
            self.perform_oop_restores()

            # Perform OOP restores with skip file permissions disabled
            self.log.info("Peroforming OOP restore with skip file permissions disabled")
            self.perform_oop_restores(skip_file_permissions=False)

            ''''# Include deleted items option verification
            self.log.info("Performing restores of inactive items")
            self.verify_include_deleted_items_option()'''

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            self.log.info(f'Test case status: {self.status}')
            # Delete the client
            if self.status == "PASSED":
                self.cv_cloud_object.cvoperations.delete_client(self.client_name)

            # Clear user's onedrive
            for user in self.users:
                self.cv_cloud_object.one_drive.delete_all_data_on_onedrive(user)
            self.cv_cloud_object.one_drive.delete_all_data_on_onedrive(self.oop_user)

            # Clear temp
            self.cv_cloud_object.cvoperations.cleanup()

        except Exception as exception:
            self.log.error(f'Failed to delete client with exception: {str(exception)}')