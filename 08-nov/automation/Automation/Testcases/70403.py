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
from AutomationUtils.machine import Machine

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
        self.name = 'Cover restartability testcases for restore job'
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
        self.machine = None
        self.tcinputs = {
            'ServerPlanName': None,
            'IndexServer': None,
            'AccessNode': None,
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

        # Verify discovery completion or wait for discovery to complete
        self.log.info(f'Waiting until discovery is complete')
        self.cv_cloud_object.cvoperations.wait_until_discovery_is_complete()

        # Verify discovery
        self.log.info(f'Verifying the discovery')
        status, res = self.subclient.verify_discovery_onedrive_for_business_client()
        if status:
            self.log.info("Discovery successful")
        else:
            raise Exception("Discovery is not successful")

    def run_backup(self):

        """ Runs backup of all users in the client """

        # Run backup of all users
        self.log.info('Run 1st incremental level backup')
        backup_job = self.client.backup_all_users_in_client()

        if not backup_job.wait_for_completion():
            raise Exception(
                "Failed to run FULL backup with error: {0}".format(backup_job.delay_reason)
            )
        self.log.info("Backup job: %s completed successfully", backup_job.job_id)

    def verify_restart(self, skip_file_permissions=True):

        # Run a restore and verify restartability while restarting cv services

        self.log.info(f'Run OOP restore with for user: {self.users[0]} with skip file permissions option enabled')
        restore_job = self.subclient.out_of_place_restore_onedrive_for_business_client(users=[self.users[0]],
                                                                      destination_path=self.oop_user,
                                                                      skip_file_permissions=True)

        while restore_job.status.lower() == 'running':
            time.sleep(150)
            self.log.info('Restarting services on access node')
            try:
                self.machine.restart_all_cv_services()
            except Exception as exp:
                self.log.info("Services are being restarted, but no response")
            break

        time.sleep(120)

        restore_job._wait_for_status('pending')
        if restore_job.status.lower() == 'pending':
            self.log.info('Job went into pending state')

        time.sleep(20)

        restore_job.resume(wait_for_job_to_resume=True)
        if restore_job.status.lower() == 'running':
            self.log.info('Resumed')

        self.verify_restore(restore_job, self.users[0], oopUser=self.oop_user)

        # Delete data on destination
        self.log.info(f'Deleting data on {self.oop_user}\'s OneDrive')
        self.cv_cloud_object.one_drive.delete_all_data_on_onedrive(self.oop_user)

        # Run an OOP restore and verify restartability after more than 2000 items processed
        self.log.info(f'Run OOP restore with for user: {self.users[0]} with skip file permissions option enabled')
        restore_job = self.subclient.out_of_place_restore_onedrive_for_business_client(users=[self.users[0]],
                                                                      destination_path=self.oop_user,
                                                                      skip_file_permissions=skip_file_permissions)

        while restore_job.status.lower() in ["running", "suspended"]:
            time.sleep(120)
            restore_job.pause(wait_for_job_to_pause=True)
            self.log.info("Suspended")
            n1 = restore_job.num_of_files_transferred
            self.log.info(f"{n1} files transferred until now")
            if n1 > 2000:
                self.log.info("More than 2000 processed.")
                restore_job.resume(wait_for_job_to_resume=True)
                self.log.info("Resumed")
                break

            restore_job.resume(wait_for_job_to_resume=True)
            self.log.info("Resumed")

        self.verify_restore(restore_job, self.users[0], oopUser=self.oop_user)

        # Delete data on destination
        self.log.info(f'Deleting data on {self.oop_user}\'s OneDrive')
        self.cv_cloud_object.one_drive.delete_all_data_on_onedrive(self.oop_user)

        # Run another OOP restore and verify restartability after less than 2000 items processed
        self.log.info(f'Run OOP restore with for user: {self.users[0]} with skip file permissions option enabled')
        restore_job = self.subclient.out_of_place_restore_onedrive_for_business_client(users=[self.users[0]],
                                                                      destination_path=self.oop_user,
                                                                      skip_file_permissions=skip_file_permissions)

        while restore_job.status.lower() in ["running", "suspended"]:
            time.sleep(90)
            restore_job.pause(wait_for_job_to_pause=True)
            self.log.info("Suspended")
            n1 = restore_job.num_of_files_transferred
            self.log.info(f"{n1} files transferred until now")
            if n1>500 and n1<2000:
                self.log.info("More than 500 processed.")
                restore_job.resume(wait_for_job_to_resume=True)
                self.log.info("Resumed")
                break

            restore_job.resume(wait_for_job_to_resume=True)
            self.log.info("Resumed")

        self.verify_restore(restore_job, self.users[0], oopUser=self.oop_user)

        # Delete data on destination
        self.log.info(f'Deleting data on {self.oop_user}\'s OneDrive')
        self.cv_cloud_object.one_drive.delete_all_data_on_onedrive(self.oop_user)

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

        data = {'job_list': [restore_job.job_id, user, self.oop_user, user]}
        self.dbo.save_into_table('job', data, data_type='_list_oop')

        oopUser = kwargs.get('oopUser', None)
        restore_as_copy = kwargs.get('restore_as_copy', False)

        # Verify restore stats
        self.cv_cloud_object.one_drive.compare_file_properties(oop=True, to_disk=False, incremental=False,
                                                                   user_id=oopUser,restore_as_copy=restore_as_copy)


        number_of_items_restored = self.cv_cloud_object.cvoperations.get_number_of_successful_items(restore_job)
        number_of_skipped_items = restore_job.details['jobDetail']['attemptsInfo'][0]['numSkipped']

        self.log.info(f"Number of items restored: {number_of_items_restored}, Number of items skipped: {number_of_skipped_items}")

        if number_of_items_restored == self.number_of_docs:
            self.log.info("The number of files restored matches with number of files in Onedrive")
        else:
            raise Exception(
                f"Restore verification is not success: number_of_items_restored+number_of_skipped_items = {number_of_items_restored+number_of_skipped_items} and number_of_docs = {self.number_of_docs} not matched")

    def setup(self):
        """Setup function of this test case"""

        # Create a client
        self.client_name = cloud_apps_constants.ONEDRIVE_CLIENT.format(str(int(time.time())))
        self.log.info(f'Creating OneDrive client: {self.client_name}')
        self.commcell.clients.add_onedrive_for_business_client(client_name=self.client_name,
                                                     server_plan=self.tcinputs.get('ServerPlanName'),
                                                     azure_directory_id=self.tcinputs.get("azure_directory_id"),
                                                     azure_app_id=self.tcinputs.get("application_id"),
                                                     azure_app_key_id=self.tcinputs.get("application_key_value"),
                                                     **{
                                                         'index_server': self.tcinputs.get('IndexServer'),
                                                         'access_nodes_list': [self.tcinputs.get('AccessNode')]
                                                     })

        # Verify client creation
        if self.commcell.clients.has_client(self.client_name):
            self.log.info("Client is created.")

        self._initialize_sdk_objects()
        self.users = self.tcinputs.get('Users')
        self.oop_user = self.tcinputs.get('OopUser')
        self.number_of_docs = self.tcinputs.get('NumberOfDocs')
        self.o365_plan = self.tcinputs.get('O365Plan')
        self.proxy_client = self.tcinputs['AccessNode']
        self.cv_cloud_object = CloudConnector(self)
        self.cv_cloud_object.cvoperations.cleanup()
        self.dbo = self.cv_cloud_object.dbo
        self.machine = Machine(self.tcinputs['AccessNode'], self.commcell)

    def run(self):
        """Run function of this test case"""
        try:
            self.run_and_verify_discovery()

            # Add users to client
            self.log.info(f'Adding users: {self.users} to client')
            self.subclient.add_users_onedrive_for_business_client(self.users, self.o365_plan)

            # Delete data on destination
            self.log.info(f'Deleting data on {self.oop_user}\'s OneDrive')
            self.cv_cloud_object.one_drive.delete_all_data_on_onedrive(self.oop_user)

            # run backup of all users
            self.run_backup()

            # Verify restartability of restores
            self.verify_restart(skip_file_permissions=True)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            self.log.info(f'Test case status: {self.status}')

            # Delete the client
            self.cv_cloud_object.cvoperations.delete_client(self.client_name)

            # Delete data on destination
            self.log.info(f'Deleting data on {self.oop_user}\'s OneDrive')
            self.cv_cloud_object.one_drive.delete_all_data_on_onedrive(self.oop_user)

            # Clear temp
            self.cv_cloud_object.cvoperations.cleanup()
        except Exception as exception:
            self.log.error(f'Failed to delete client with exception: {str(exception)}')