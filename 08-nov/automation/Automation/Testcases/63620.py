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
from cvpysdk.constants import AdvancedJobDetailType
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Application.CloudApps import constants as cloud_apps_constants
from Application.CloudApps.cloud_connector import CloudConnector
from AutomationUtils.machine import Machine
from Application.Exchange.exchange_sqlite_helper import SQLiteHelper


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
        self.name = 'Verification of Finalize phase for OneDrive V2 client'
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.CLOUDCONNECTOR
        self.feature = self.features_list.AUTOMATION
        self.show_to_user = True
        self.proxy_client = None
        self.cv_cloud_object = None
        self.users = None
        self.skip_user = None
        self.user_guid_list = None
        self.job = None
        self.client_name = None
        self.number_of_docs = None
        self.o365_plan = None
        self.subclient_job_res_dir = None
        self.job_res_dir = None
        self.machine = None
        self.sqlite_helper = None
        self.tcinputs = {
            'ServerPlanName': None,
            'IndexServer': None,
            'AccessNode': None,
            'O365Plan': None,
            'NumberOfDocs': None,
            'Users': None,
            'SkipUser': None,
            'MachineHostName': None,
            'MachineUserName': None,
            'MachinePassword': None,
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

    def create_data(self, **kwargs):

        # Create data in user's Onedrive
        pdf = kwargs.get("pdf", False)
        xlsx = kwargs.get("xlsx", False)
        pptx = kwargs.get("pptx", False)

        self.log.info(f'Generating new data on {self.users} OneDrive')
        for i in range(len(self.users)):
            self.log.info(f'Creating {self.number_of_docs} files in {self.users[i]}\'s OneDrive')
            if pdf:
                self.cv_cloud_object.one_drive.create_files(no_of_docs=self.number_of_docs, user=self.users[i], word=False, pdf=pdf)
                break
            if xlsx:
                self.cv_cloud_object.one_drive.create_files(no_of_docs=self.number_of_docs, user=self.users[i], word=False, xlsx=xlsx)
                break
            if pptx:
                self.cv_cloud_object.one_drive.create_files(no_of_docs=self.number_of_docs, user=self.users[i], word=False, pptx=pptx)
                break

            self.cv_cloud_object.one_drive.create_files(no_of_docs=self.number_of_docs, user=self.users[i])

    def run_backup(self, verify=False):

        """ Runs backup of all users in the client """

        # Run backup of all users
        self.log.info('Run incremental level backup')
        backup_job = self.client.backup_all_users_in_client()

        self.cv_cloud_object.cvoperations.check_job_status(job=backup_job, backup_level_tc=constants.backup_level.INCREMENTAL.value)
        number_of_skipped_files = backup_job.details['jobDetail']['attemptsInfo'][0]['numSkipped']
        number_of_failed_files = backup_job.details['jobDetail']['attemptsInfo'][0]['numFailures']
        number_of_backedup_files = self.cv_cloud_object.cvoperations.get_number_of_successful_items(backup_job)

        if number_of_backedup_files == 0 and number_of_failed_files == self.number_of_docs:
            self.log.info("User failed to backup")

        if number_of_failed_files > 0:
            self.log.info("User completed with errors")

        self.log.info(f"Skipped files count: {number_of_skipped_files}")
        self.log.info(f"Backedup files count: {number_of_backedup_files}")
        self.log.info(f"Failed files count: {number_of_failed_files}")

        # Verify backup
        if verify:
            if number_of_backedup_files != self.number_of_docs:
                raise Exception(
                    f'Number of files present in onedrive({self.number_of_docs}) does not match with the backed up files({number_of_backedup_files}).')

        return backup_job

    def verify_subclient_dir(self):

        for i in range(len(self.user_guid_list)):
            user_guid_folder_name = self.user_guid_list[i].lower().replace('x', '-')
            user_guid_folder_path = self.machine.join_path(self.subclient_job_res_dir, user_guid_folder_name)

            # verify the files that need to exist in Subclient directory
            if self.machine.check_file_exists(self.machine.join_path(user_guid_folder_path, 'CloudUserInfo.db3')) and \
                    self.machine.check_file_exists(
                        self.machine.join_path(user_guid_folder_path, 'ExIndexOffset.dat')) and \
                    self.machine.check_file_exists(
                        self.machine.join_path(user_guid_folder_path, 'FilesPendingTobeBackedup.txt')) and \
                    self.machine.check_file_exists(
                        self.machine.join_path(user_guid_folder_path, 'ExMsgListPreviousJobFailedMsgs.xml')) and \
                    self.machine.check_file_exists(self.machine.join_path(user_guid_folder_path, 'PrevNodeCache.txt')):

                self.log.info("Expected files are present in sub-client results directory")

            else:
                raise Exception(
                    "Expected files are not present in sub-client results directory"
                )

    def verify_jobid_dir(self):
        self.job_res_dir = self.machine.join_path(self.client.job_results_directory,
                                                  str(self.commcell.commcell_id),
                                                  str(self.commcell.commcell_id),
                                                  str(self.job.job_id)
                                                  )

        for i in range(len(self.user_guid_list)):
            user_guid_folder_name = self.user_guid_list[i].lower().replace('x', '-')
            user_guid_folder_path = self.machine.join_path(self.job_res_dir, user_guid_folder_name)

            # verify the files that doesn't need to exist in jobid directory
            if self.machine.check_file_exists(self.machine.join_path(user_guid_folder_path, 'CloudUserInfo.db3')) and \
                    self.machine.check_file_exists(
                        self.machine.join_path(user_guid_folder_path, 'ExIndexOffset.dat')) and \
                    self.machine.check_file_exists(
                        self.machine.join_path(user_guid_folder_path, 'FilesPendingTobeBackedup.txt')) and \
                    self.machine.check_file_exists(
                        self.machine.join_path(user_guid_folder_path, 'ExMsgListCurrentJobFailedMsgs.xml')) and \
                    self.machine.check_file_exists(self.machine.join_path(user_guid_folder_path, 'NodeCache.txt')):

                raise Exception(
                    "Expected files are present in jobid results directory"
                )

            else:
                self.log.info("Expected files are not present in jobid results directory")

    def verify_updates(self, first_job_user_res, second_job_user_res, first_job_subclient_res, second_job_subclient_res):
        for first_job_user_guid in first_job_user_res:
            for second_job_user_guid in second_job_user_res:
                if first_job_user_guid == second_job_user_guid:
                    if first_job_user_res[first_job_user_guid][1] != second_job_user_res[second_job_user_guid][1] and \
                            first_job_user_res[first_job_user_guid][2] != second_job_user_res[second_job_user_guid][2]:
                        self.log.info(
                            f"prevChangeLink, nextIncRefTime are updating for user: {first_job_user_guid} in CloudUserInfo"
                        )
                    else:
                        raise Exception(
                            f"prevChangeLink, nextIncRefTime are not updating for user: {first_job_user_guid} in CloudUserInfo"
                        )
        for first_job_user_guid in first_job_subclient_res:
            for second_job_user_guid in second_job_subclient_res:
                if first_job_user_guid == second_job_user_guid:
                    if first_job_user_guid not in self.user_guid_list:
                        if first_job_subclient_res[first_job_user_guid][2] != \
                                second_job_subclient_res[second_job_user_guid][2]:
                            self.log.info(
                                f"nextIncrementalRefTime are updating for skipped user: {first_job_user_guid} in ExMBJobInfo"
                            )
                        else:
                            raise Exception(
                                f"nextIncrementalRefTime are not updating for skipped user: {first_job_user_guid} in ExMBJobInfo"
                            )
                    else:
                        if first_job_subclient_res[first_job_user_guid][2] != \
                                second_job_subclient_res[second_job_user_guid][2] and \
                                first_job_subclient_res[first_job_user_guid][3] != \
                                second_job_subclient_res[second_job_user_guid][3]:
                            self.log.info(
                                f"nextIncrementalRefTime, previousChangeLink are updating for user: {first_job_user_guid} in ExMBJobInfo"
                            )
                        else:
                            raise Exception(
                                f"nextIncrementalRefTime, previousChangeLink are not updating for user: {first_job_user_guid} in ExMBJobInfo"
                            )

    def set_or_unset_reg_key(self, set=True, value=0):

        if set:
            # set registry key to simulate backup file failure
            self.log.info('Setting registry key on access node to simulate backup failure')
            self.machine.create_registry(cloud_apps_constants.REG_KEY_IDATAAGENT,
                                         cloud_apps_constants.SIMULATE_FAILURE_ITEMS_KEY,
                                         value,
                                         reg_type=cloud_apps_constants.SIMULATE_FAILURE_ITEMS_REG_TYPE)
            self.log.info('Set the registry key successfully')
        else:
            # remove registry key
            self.log.info('Removing registry key from access node')
            self.machine.remove_registry(cloud_apps_constants.REG_KEY_IDATAAGENT,
                                         cloud_apps_constants.SIMULATE_FAILURE_ITEMS_KEY)
            self.log.info('Removed the registry key successfully')

    def verify_finalize(self,failed=False):

        self.log.info(f'Job start time: {self.job.start_timestamp}')

        dat_query = "select indexingGUID, curJobID, prevArchiveJobID, nextIncrementalRefTime, " \
                    "previousChangeLink from ArchiveResults"

        sqlite_res = self.sqlite_helper.execute_dat_file_query(self.subclient_job_res_dir,
                                                               file_name="ExMBJobInfo.dat",
                                                               query=dat_query)

        subclient_level_res = {sqlite_res[i][0]: [sqlite_res[i][1], str(sqlite_res[i][2]), str(sqlite_res[i][3]), sqlite_res[i][4]] for i in range(len(sqlite_res))}

        # Check all the values in ExMBJobInfo.dat file
        for user_guid in subclient_level_res:
            if user_guid in self.user_guid_list:
                if subclient_level_res[user_guid][1] == self.job.job_id and subclient_level_res[user_guid][0] == 0 and \
                        subclient_level_res[user_guid][2] == str(self.job.start_timestamp):
                    self.log.info(
                        f"Expected values are present in ExMBJobInfo.dat of user: {user_guid}")
                else:
                    if failed:
                        self.log.info('Failed user backup does not set the values in ExMBJobInfo')
                        continue
                    raise Exception(
                        f" Expected values are not present in ExMBJobInfo.dat of user: {user_guid}"
                    )
            else:
                if subclient_level_res[user_guid][2] == str(self.job.start_timestamp) and subclient_level_res[user_guid][1] == '0' and len(subclient_level_res[user_guid][3]) == 0 and not failed:
                    self.log.info(
                        f"Expected values are present in ExMBJobInfo.dat of skipped user: {user_guid}")
                else:
                    if failed:
                        self.log.info('Failed user backup does not set the values in ExMBJobInfo')
                        continue
                    raise Exception(
                        f" Expected values are not present in ExMBJobInfo.dat of skipped user: {user_guid}"
                    )

        dat_query = "select prevJobID, prevChangeLink, nextIncRefTime, curJobID, curIncRefTime, " \
                    "curChangeLink from CloudArchiveResults"

        user_level_res = {}

        for user_guid in subclient_level_res:
            if user_guid in self.user_guid_list:
                sqlite_res = self.sqlite_helper.execute_dat_file_query(
                    self.machine.join_path(self.subclient_job_res_dir, user_guid),
                    file_name="CloudUserInfo.db3",
                    query=dat_query)
                user_level_res[user_guid] = list(sqlite_res[0])

        for user_guid in user_level_res:
            if user_level_res[user_guid][3] == user_level_res[user_guid][4] == len(user_level_res[user_guid][5]) == 0 and \
                str(user_level_res[user_guid][0]) == str(self.job.job_id) and \
                    str(user_level_res[user_guid][2]) == str(self.job.start_timestamp):
                self.log.info(f"Expected values are present in CloudUserInfo.db3 of user: {user_guid}")
            else:
                if failed:
                    self.log.info('Failed user backup does not set the values in CloudUserInfo')
                    continue
                raise Exception(f"Expected values are not present in CloudUserInfo.db3 of user: {user_guid}")

        return subclient_level_res, user_level_res

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
        self.user_guid_list = self.subclient._get_user_guids(self.users)
        self.user_guid_list = [self.user_guid_list[i].lower().replace('x', '-') for i in range(len(self.user_guid_list))]
        self.subclient.data_readers = 1
        self.skip_user = self.tcinputs.get('SkipUser')
        self.number_of_docs = self.tcinputs.get('NumberOfDocs')
        self.o365_plan = self.tcinputs.get('O365Plan')
        self.proxy_client = self.tcinputs['AccessNode']
        self.cv_cloud_object = CloudConnector(self)
        self.cv_cloud_object.cvoperations.cleanup()
        self.machine = Machine(self.tcinputs['AccessNode'], self.commcell)
        self.subclient_job_res_dir = self.cv_cloud_object.cvoperations.get_job_results_dir()
        self.sqlite_helper = SQLiteHelper(self, proxy_machine=self.machine, username=self.tcinputs['MachineUserName'],
                                          password=self.tcinputs['MachinePassword'])

        # Delete data on user's Onedrive
        for user in self.users:
            self.log.info(f'Deleting data on {user}\'s OneDrive')
            self.cv_cloud_object.one_drive.delete_all_data_on_onedrive(user)

    def run(self):
        """Run function of this test case"""
        try:

            self.run_and_verify_discovery()

            # Add users to client
            self.log.info(f'Adding users: {self.users, self.skip_user} to client')
            self.subclient.add_users_onedrive_for_business_client(self.users, self.o365_plan)
            self.subclient.add_users_onedrive_for_business_client([self.skip_user], self.o365_plan)

            self.create_data(pdf=True)

            # Run first backup of all users
            self.job = self.run_backup(verify=True)

            # Verify it's finalize phase
            first_job_subclient_res, first_job_user_res = self.verify_finalize()
            self.verify_subclient_dir()
            self.verify_jobid_dir()
            self.log.info(
                f"Sub-client results directory created: {self.subclient_job_res_dir} with {self.machine.get_items_list(self.subclient_job_res_dir)}")

            self.create_data()

            # Run second backup for successful user
            self.job = self.run_backup(verify=True)

            # Verify it's finalize phase
            second_job_subclient_res, second_job_user_res = self.verify_finalize()
            self.verify_subclient_dir()
            self.verify_jobid_dir()
            self.verify_updates(first_job_user_res, second_job_user_res, first_job_subclient_res, second_job_subclient_res)

            self.create_data(xlsx=True)
            self.set_or_unset_reg_key(value = self.number_of_docs-2)

            # Run third backup for cwe user
            self.job = self.run_backup()
            self.set_or_unset_reg_key(set=False)

            # Verify it's finalize phase
            third_job_subclient_res, third_job_user_res = self.verify_finalize()
            self.verify_subclient_dir()
            self.verify_jobid_dir()
            self.verify_updates(second_job_user_res, third_job_user_res, second_job_subclient_res,
                                third_job_subclient_res)

            self.create_data(pptx=True)

            self.instance.modify_connection_settings(self.tcinputs.get("application_id", ""),
                                                     self.tcinputs.get("azure_directory_id", ""),
                                                     "Wrong Password")
            self.log.info("Azure app credentials set wrong for simulating failure backup")

            # Run fourth backup for failed user
            self.job = self.subclient.run_user_level_backup_onedrive_for_business_client(self.users)
            self.job._wait_for_status(status="Pending")
            self.job.kill(wait_for_job_to_kill=True)
            self.log.info("Fourth job finished")


            self.instance.modify_connection_settings(self.tcinputs.get("application_id", ""),
                                                     self.tcinputs.get("azure_directory_id", ""),
                                                     self.tcinputs.get("application_key_value", ""))
            self.log.info("Azure app set back with correct credentials")

            # Verify it's finalize phase
            fourth_job_subclient_res, fourth_job_user_res = self.verify_finalize(failed=True)
            self.verify_subclient_dir()
            self.verify_jobid_dir()

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

            # Delete data on user's Onedrive
            for user in self.users:
                self.log.info(f'Deleting data on {user}\'s OneDrive')
                self.cv_cloud_object.one_drive.delete_all_data_on_onedrive(user)

            # Clear temp
            self.cv_cloud_object.cvoperations.cleanup()
        except Exception as exception:
            self.log.error(f'Failed to delete client with exception: {str(exception)}')
