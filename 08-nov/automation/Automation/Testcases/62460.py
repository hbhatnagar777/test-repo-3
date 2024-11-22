# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""" Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                                  --  initialize TestCase class

    setup()                                     --  sets up the variables required for running the testcase

    run()                                       --  run function of this test case

    teardown()                                  --  tears down the things created for running the testcase

    _initialize_sdk_objects()                   --  initializes the sdk objects after app creation

    convert_folder_structure_to_dictionary()    --  Convert the folder structure to python dictionary for comparison

    rename_files()                              --  Rename files on OneDrive

    change_file_folder_names_and_structure()    --  Change folder structure on OneDrive

    compare_folder_structures()                 --  Compares folder structure for incremental jobs

"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Application.CloudApps.cloud_connector import CloudConnector
from Application.CloudApps import constants as cloud_apps_constants
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "OneDrive v2 file/folder structure change and rename detection"
        self.users = None
        self.cvcloud_object = None
        self.folder_structure = None
        self.folder_structure_dictionary = {}
        self.in_place_folder_structure_dictionary = {}
        self.out_of_place_folder_structure_dictionary = {}
        self.disk_restore_folder_structure_dictionary = {}
        self.folder_count = None
        self.file_count = None
        self.client_name = None
        self.o365_plan = None
        self.out_of_place_destination_user = None
        self.tcinputs = {
            'ServerPlanName': None,
            'IndexServer': None,
            'AccessNodes': None,
            'O365Plan': None,
            'Users': None,
            'folder_count': None,
            'file_count': None,
            'application_id': None,
            'application_key_value': None,
            'azure_directory_id': None,
            'out_of_place_destination_user': None
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

    def setup(self):
        """Setup function of this test case"""
        self.client_name = "OD_62460"
        self.log.info(f'Checking if OneDrive client : {self.client_name} already exists')
        if self.commcell.clients.has_client(self.client_name):
            self.log.info(f'OneDrive client : {self.client_name} already exists, deleting the client')
            self.commcell.clients.delete(self.client_name)
            self.log.info(f'Successfully deleted OneDrive client : {self.client_name} ')
        else:
            self.log.info(f'OneDrive client : {self.client_name} does not exists')
        self.log.info(f'Creating new OneDrive client : {self.client_name}')
        self.commcell.clients.add_onedrive_for_business_client(client_name=self.client_name,
                                                     server_plan=self.tcinputs.get('ServerPlanName'),
                                                     azure_directory_id=self.tcinputs.get("azure_directory_id"),
                                                     azure_app_id=self.tcinputs.get("application_id"),
                                                     azure_app_key_id=self.tcinputs.get("application_key_value"),
                                                     **{
                                                         'index_server': self.tcinputs.get('IndexServer'),
                                                         'access_nodes_list': self.tcinputs.get('AccessNodes')
                                                     })
        self._initialize_sdk_objects()

        self.users = self.tcinputs['Users'].split(",")
        self.o365_plan = self.tcinputs['O365Plan']
        self.file_count = self.tcinputs['file_count']
        self.folder_count = self.tcinputs['folder_count']
        self.out_of_place_destination_user = self.tcinputs['out_of_place_destination_user']

        # Creating CloudConnector object
        self.cvcloud_object = CloudConnector(self)
        self.cvcloud_object.cvoperations.cleanup()

    def convert_folder_structure_to_dictionary(self,
                                               folder_structure,
                                               folder_structure_dictionary,
                                               path='',
                                               out_of_place_source_user=None):
        """ Convert the folder structure to python dictionary inplace for comparison

            Args:
                folder_structure (dict): Dictionary containing folder hierarchy
                                        Format:-
                                        { folder_name : [file_list],
                                                        [{folder1: [...], [...]},
                                                         {folder2: [...], [...]}]}
                folder_structure_dictionary (dict) : dictionary object to append relative paths to
                path (path) : initial path parent folder, for root folder default is empty string
                out_of_place_source_user (str) : source user of out-of-place restore
                                                 for conversion to parent folder(user level) to root level
                    default None
        """
        try:
            for folder_name, sub_folder_structure in folder_structure.items():
                exact_path = folder_name if path == '' else f'{path}/{folder_name}'
                if out_of_place_source_user:
                    exact_path = exact_path.replace(out_of_place_source_user, 'root')
                folder_structure_dictionary[exact_path] = sub_folder_structure[0]
                for sub_folder in sub_folder_structure[1]:
                    self.convert_folder_structure_to_dictionary(sub_folder, folder_structure_dictionary, exact_path)
        except Exception as exception:
            raise Exception(f'Folder structure to dictionary failed with exception: {str(exception)}')

    def rename_files(self):
        """
            Rename files on OneDrive
        """
        try:
            file_name = 'renamed_file_{}{}'
            file_counter = 1
            for folder_name, file_list in self.folder_structure_dictionary.items():
                for i in range(len(file_list)):
                    # Add file extension type to renamed file if any
                    old_file_extension_list = file_list[i].split('.', 1)
                    extension = f'.{old_file_extension_list[1]}' if len(old_file_extension_list) > 1 else ''
                    new_file_name = file_name.format(file_counter, extension)

                    # rename files in one drive
                    self.cvcloud_object.one_drive.rename_file_or_folder(
                        file_list[i], new_file_name, self.users[0], folder_name)

                    # rename files in current folder structure dictionary
                    file_list[i] = new_file_name
                    file_counter += 1
        except Exception as exception:
            raise Exception(f'Failed to rename files on OneDrive: {str(exception)}')

    def change_file_folder_names_and_structure(self):
        """
            Change folder structure on OneDrive
        """
        try:
            # change file names
            self.rename_files()

            root = 'root'
            folder = 'Folder{}'
            folder_path = f'{root}/{folder}'
            folder_rename = 'New_Folder{}'
            folder_rename_path = f'{root}/{folder_rename}'
            sub_folder = 'SubFolder{}'
            sub_folder_path = f'{root}/{folder}/{sub_folder}'
            sub_folder_rename = 'F{}_SubFolder{}'
            sub_folder_rename_path = f'{root}/{folder_rename}/{sub_folder_rename}'

            for folder_counter in range(1, self.folder_count + 1):
                for sub_folder_counter in range(1, self.folder_count + 1):
                    if folder_counter != sub_folder_counter:
                        source = folder_path.format(sub_folder_counter)
                        destination = folder_path.format(folder_counter)
                        sub_folder_new_name = sub_folder_rename.format(sub_folder_counter, folder_counter)

                        # change sub-folder names in OneDrive
                        self.cvcloud_object.one_drive.rename_file_or_folder(
                            sub_folder.format(folder_counter), sub_folder_new_name, self.users[0], source)

                        # change structure in OneDrive
                        self.cvcloud_object.one_drive.move_file_or_folder(
                            sub_folder_new_name, source, destination, self.users[0])

                        # change folder name and structure in folder dictionary
                        self.folder_structure_dictionary[
                            sub_folder_rename_path.format(
                                folder_counter,
                                sub_folder_counter,
                                folder_counter)] = self.folder_structure_dictionary.pop(
                            sub_folder_path.format(
                                sub_folder_counter,
                                folder_counter))
                    else:
                        self.cvcloud_object.one_drive.rename_file_or_folder(sub_folder.format(folder_counter),
                                                                            sub_folder_rename.format(folder_counter,
                                                                                                     folder_counter),
                                                                            self.users[0],
                                                                            folder_path.format(folder_counter))

                        self.folder_structure_dictionary[
                            sub_folder_rename_path.format(
                                folder_counter,
                                folder_counter,
                                folder_counter)] = self.folder_structure_dictionary.pop(
                            sub_folder_path.format(
                                folder_counter,
                                folder_counter))

            for folder_counter in range(1, self.folder_count + 1):
                self.cvcloud_object.one_drive.rename_file_or_folder(folder.format(folder_counter),
                                                                    folder_rename.format(folder_counter),
                                                                    self.users[0],
                                                                    'root')
                self.folder_structure_dictionary[
                    folder_rename_path.format(
                        folder_counter)] = self.folder_structure_dictionary.pop(
                    folder_path.format(folder_counter))

        except Exception as exception:
            raise Exception(f'Folder structure to dictionary failed with exception: {str(exception)}')

    def compare_folder_structures(self, folder_structure1, folder_structure2):
        """
            Compares folder structure

            Args:
                folder_structure1 (dict)
                folder_structure2 (dict)

            Raises:
                Exception:
                    Folder structure does not match
        """
        for folder_path, file_list in folder_structure1.items():
            if set(file_list) != set(folder_structure2[folder_path]):
                raise Exception(f'Folder structure does not match '
                                f'Folder structure post backup: {folder_structure1} ;'
                                f'Folder structure post restore: {folder_structure2}')
        self.log.info('Folder structures match.')

    def run(self):
        """Run function of this test case"""
        try:
            # Delete Data on source user's OneDrive
            self.log.info(f'Deleting data on {self.users[0]}\'s OneDrive')
            self.cvcloud_object.one_drive.delete_all_data_on_onedrive(self.users[0])

            # Add data to user
            self.log.info(f'Creating data on {self.users[0]}\'s OneDrive')
            self.cvcloud_object.one_drive.generate_onedrive_data(folder_count=self.folder_count,
                                                                 folder_depth=2,
                                                                 file_count=self.file_count,
                                                                 user_id=self.users[0])

            # Get the folder structure
            self.log.info('Fetching the folder structure from OneDrive')
            self.folder_structure = self.cvcloud_object.one_drive.get_all_onedrive_items(user_id=self.users[0])
            self.convert_folder_structure_to_dictionary(self.folder_structure, self.folder_structure_dictionary)

            # Verify discovery completion or wait for discovery to complete
            self.log.info(f'Waiting until discovery is complete')
            self.cvcloud_object.cvoperations.wait_until_discovery_is_complete()

            # Add user to client
            self.log.info(f'Adding users: {self.users} to client')
            self.subclient.add_users_onedrive_for_business_client([self.users[0]], self.o365_plan)

            # Run initial backup
            backup_level = constants.backup_level.INCREMENTAL.value
            self.log.info('Run initial sub-client level backup')
            backup_job = self.client.backup_all_users_in_client()
            self.cvcloud_object.cvoperations.check_job_status(job=backup_job, backup_level_tc=backup_level)

            # Change structure and rename files on OneDrive and local folder structure
            self.log.info('Changing file/folder names and structure')
            self.change_file_folder_names_and_structure()

            # Run 2nd incremental backup
            self.log.info('Run 2nd incremental sub-client level backup')
            backup_job = self.client.backup_all_users_in_client()
            self.cvcloud_object.cvoperations.check_job_status(job=backup_job, backup_level_tc=backup_level)

            # Delete Data on source user's OneDrive
            self.log.info(f'Deleting data on {self.users[0]}\'s OneDrive')
            self.cvcloud_object.one_drive.delete_all_data_on_onedrive(self.users[0])

            # Run inplace restore
            restore_level = 'RESTORE'
            self.log.info(f'Run in-place restore for user: {self.users[0]}')
            inplace_restore_job = self.client.in_place_restore(self.users)
            self.cvcloud_object.cvoperations.check_job_status(job=inplace_restore_job, backup_level_tc=restore_level)

            # Get folder structure after in-place restore is complete
            self.log.info('Fetching in-place folder structure as restore is complete')
            folder_structure_in_place = self.cvcloud_object.one_drive.get_all_onedrive_items(user_id=self.users[0])
            self.convert_folder_structure_to_dictionary(folder_structure_in_place,
                                                        self.in_place_folder_structure_dictionary)

            # Cross-check in place restore
            self.log.info('Compare the folder structures')
            self.compare_folder_structures(self.folder_structure_dictionary, self.in_place_folder_structure_dictionary)

            # Delete data on out-of-place user's OneDrive
            self.log.info(f'Deleting data on out-of-place user\'s drive [{self.out_of_place_destination_user}]')
            self.cvcloud_object.one_drive.delete_all_data_on_onedrive(self.out_of_place_destination_user)

            # Run out-of-place restore
            self.log.info(f'Run out-of-place restore for user: {self.users[0]}')
            out_of_place_restore_job = self.client.out_of_place_restore(self.users, self.out_of_place_destination_user)
            self.cvcloud_object.cvoperations.check_job_status(job=out_of_place_restore_job,
                                                              backup_level_tc=restore_level)

            # Fetch folder structure for out of place user
            self.log.info('Fetching the folder structure from OneDrive')
            self.folder_structure = self.cvcloud_object.one_drive.get_all_onedrive_items(
                user_id=self.out_of_place_destination_user, folder_path=self.users[0])
            self.convert_folder_structure_to_dictionary(self.folder_structure,
                                                        self.out_of_place_folder_structure_dictionary,
                                                        out_of_place_source_user=self.users[0])

            # Cross-check out-of-place place restore
            self.log.info('Compare the folder structures for out-of-place restore')
            self.compare_folder_structures(self.folder_structure_dictionary,
                                           self.out_of_place_folder_structure_dictionary)

            # Delete data if present on disk location
            destination_user_path = f'{cloud_apps_constants.DESTINATION_TO_DISK}\\{self.users[0]}'
            proxy_client = Machine(self.instance.proxy_client, self.commcell)
            if proxy_client.check_directory_exists(destination_user_path):
                proxy_client.remove_directory(destination_user_path)

            # Run disk restore
            self.log.info(f'Run disk restore for user: {self.users[0]}')
            disk_restore_job = self.client.disk_restore(self.users,
                                                        self.instance.proxy_client,
                                                        cloud_apps_constants.DESTINATION_TO_DISK)
            self.cvcloud_object.cvoperations.check_job_status(job=disk_restore_job,
                                                              backup_level_tc=restore_level)

            # Fetch folder structure for disk-restore
            self.disk_restore_folder_structure_dictionary = \
                self.cvcloud_object.one_drive.get_folder_structure_on_disk(self.users[0], replace_root='root')

            # Cross-check disk restore
            self.log.info('Compare the folder structures for disk restore')
            self.compare_folder_structures(self.folder_structure_dictionary,
                                           self.disk_restore_folder_structure_dictionary)

        except Exception as exception:
            self.log.error(f'Failed to execute test case with error: {str(exception)}')
            self.result_string = str(exception)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        try:
            if self.status == constants.PASSED:
                self.log.info(f'Test case status: {self.status}')
                # Delete the client if test case is successful
                self.cvcloud_object.cvoperations.delete_client(self.client_name)
                # Clear user's Onedrive
                self.cvcloud_object.one_drive.delete_all_data_on_onedrive(self.users[0])
                # Clear data on destination user's drive
                self.cvcloud_object.one_drive.delete_all_data_on_onedrive(self.out_of_place_destination_user)
                self.cvcloud_object.cvoperations.cleanup()
        except Exception as exception:
            self.log.error(f'Failed to delete client with exception: {str(exception)}')
