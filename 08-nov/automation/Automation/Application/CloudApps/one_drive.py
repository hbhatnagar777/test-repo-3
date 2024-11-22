# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main Module for invoking OneDrive APIs.

OneDrive is the only class defined in this file.

OneDrive: Class for performing OneDrive/OneNote related operations

OneDrive:

        __init__(self, cc_object)           --  Initializes the OneDrive object

        discover(self)                      --  Method to discover users on azure AD

        create_files()                      --  This method creates and
                                                upload files on user's OneDrive

        get_file_properties()               --  Method to fetch file properties from
        OneDrive Automation folder and store them to local DB

        get_folder_id_from_graph()         --  Method to fetch folder id of
        the automation folder

        _get_files_list()                   --  Method to get the list of file metadata

        compare_file_properties()           --  Method to compare file properties

        _compare_files(self, user_id)       --  Compares the file properties of
        a single user

        delete_folder()                     --  Method to delete automation folder
        from user OneDrive

        _process_response()                 --  Process the Graph API response and
        returns the minimal dict

        request()                           --  Method to make Graph API requests

        get_user_details()                  --  Get a OneDrive user's details

        create_onenote_notebook()           --  Create Notebook on user's account

        get_onenote_notebook_id()           --  Get OneNote notebook ID

        create_onenote_section()            --  Create Section on user's account

        get_onenote_section_id()            --  Get OneNote section ID

        create_onenote_page()               --  Create a page under desired section

        create_onenote_section_group()      --  Create Section Group in user's account

        get_onenote_section_group_id()      --  Get OneNote section's ID

        generate_onenote_data()             --  Recursive function to generate OneNote data on user's account

        list_onenote_items()                --  Fetch relative paths and page content for all OneNote items

        get_page_content()                  --  Gets content of all the pages in a section

        compare_onenote_restore_metadata()  --  Fetches and compares new OneNote metadata with metadata before restore

"""

import os
import re
import json
import time
from collections import deque
from requests.exceptions import HTTPError
from oauthlib.oauth2.rfc6749.errors import TokenExpiredError
from AutomationUtils.machine import Machine
from .wiki import Wiki
from .exception import CVCloudException
from . import constants
from .csdb_helper import CSDBHelper


class OneDrive:
    """Class for performing OneDrive related operations."""

    def __init__(self, cc_object):
        """Initializes the oneDrive object.

                Args:

                    cc_object  (Object)  --  instance of cloud_connector module


                Returns:

                    object  --  instance of OneDrive class

        """

        self.tc_object = cc_object.tc_object
        self.tc_inputs = self.tc_object.tcinputs
        self.log = self.tc_object.log
        self.api_name = self.__class__.__name__
        self.auth_object = cc_object.one_drive_auth
        self.auth_object.authenticate_client()
        self.dbo = cc_object.dbo
        self.sqlite = cc_object.sqlite
        self.wiki = Wiki(self.log)
        self.machine = Machine()
        self.graph_endpoint = constants.MS_GRAPH_ENDPOINT
        if self.tc_inputs.get('cloudRegion', 1) == 5:
            self.graph_endpoint = constants.GCC_HIGH_MS_GRAPH_ENDPOINT
        self.headers = {
            'Content-Type': 'application/json',
            'Host': 'graph.microsoft.com'
        }
        self.csdb = CSDBHelper(self.tc_object)

    def discover(self):
        """Method to discover users on azure AD"""

        try:
            users_endpoint = (f'{self.graph_endpoint}'
                              f'{constants.MS_GET_USERS}'
                              f'?$top={str(constants.USER_PAGE_SIZE)}')
            self.log.info('users_endpoint:%s', users_endpoint)

            response = self.request(url=users_endpoint, headers=self.headers)
            self.log.info('response:%s', response)
            self.log.info('response length: %s', len(response.get('value')))
            self.dbo.save_into_table('users', response.get('value'), '_list')

            while '@odata.nextLink' in response:
                self.log.info('@odata.nextLink:%s', response.get('@odata.nextLink'))
                response = self.request(url=response.get('@odata.nextLink'), headers=self.headers)
                self.dbo.save_into_table('users', response.get('value'), '_list')
                self.log.info('response:%s', response)
        except Exception as excp:
            self.log.exception('Exception while discovering users')
            raise CVCloudException(self.api_name, '101', str(excp))

    def create_files(self, unicode_data=False,
                     no_of_docs=constants.NO_OF_DOCS_TO_CREATE,
                     word=True,
                     pdf=False,
                     google_docs=False,
                     csvfile=False,
                     pptx=False,
                     xlsx=False,
                     image=False,
                     html=False,
                     code=False,
                     folder=False,
                     new_folder=True,
                     user=None,
                     folder_path=None,
                     folder_id=None):
        """This method creates and upload files on user's OneDrive

                Args:

                    unicode_data  (boolean)  --  True if unicode data files
                    have to be created

                    no_of_docs  (int)  --  Number of files to create and upload

                    word  (boolean)  --  True if pdf files have to be created

                    pdf  (boolean)  --  True if pdf files have to be created

                    google_docs  (boolean)  --  True if text files have to be created

                    csvfile  (boolean)  --  True if csv files have to be created

                    pptx  (boolean)  --  True if pptx files have to be created

                    xlsx  (boolean)  --  True if excel files have to be created

                    image  (boolean)  --  True if image files have to be created

                    html  (boolean)  --  True if html files have to be created

                    code  (boolean)  --  True if source code files have to be created

                    folder  (boolean)  --  True if folder has to be created with all the above given files

                    new_folder  (boolean)  --  True if a new folder has to be
                    created on user's GDrive

                    user  (str)   --  SMTP address of the user

                    folder_path (str)   --  Path to location where file has to be created

                    folder_id (str)     --  Id of folder to which file has to be created

        """

        if user:
            sc_content = [{'SMTPAddress': user}]
        else:
            sc_content = self.tc_object.subclient.content
        for content in sc_content:
            user_id = content.get('SMTPAddress')
            self.wiki.create_docx(
                no_of_docs=no_of_docs,
                unicode_data=unicode_data,
                word=word,
                pdf=pdf,
                google_docs=google_docs,
                csvfile=csvfile,
                pptx=pptx,
                xlsx=xlsx,
                image=image,
                html=html,
                code=code,
                folder=folder,
                ca_type='onedrive')

            try:
                self.log.info(
                    'creating documents into users OneDrive: "%s"', user_id)
                if new_folder:
                    parent_folder_id = self.create_folder(folder_name=constants.ONEDRIVE_FOLDER, user_id=user_id, location='root')
                else:
                    self.log.info('uploading files to existing folder')
                self.log.info('Purging the latest files db before saving current properties')
                self.dbo.dbo.purge_table(f'{user_id}{constants.LATEST_FILES}')

                def upload_file(user_id, folder_id, folder_path, file_path, file_name):
                    self.log.info('uploading file: %s', file_path)
                    self.log.info('filename: %s', file_name)
                    if folder_id:
                        file_endpoint = (
                            f'{self.graph_endpoint}'
                            f'{constants.MS_GET_USERS}'
                            f'{constants.MS_UPLOAD_FILE_WITH_ID.format(user_id, folder_id, file_name)}'
                        )
                    elif folder_path == 'root' or folder_path == '/':
                        file_endpoint = (
                            f'{self.graph_endpoint}'
                            f'{constants.MS_GET_USERS}'
                            f'{constants.MS_UPLOAD_FILE_TO_ROOT.format(user_id, file_name)}'
                        )
                    else:
                        if not folder_path:
                            folder_path = constants.ONEDRIVE_FOLDER
                        file_endpoint = (
                            f'{self.graph_endpoint}'
                            f'{constants.MS_GET_USERS}'
                            f'{constants.MS_UPLOAD_FILE.format(user_id, folder_path, file_name)}'
                        )
                    self.log.info('Upload file endpoint: %s', file_endpoint)
                    headers = self.headers.copy()
                    headers['Content-Type'] = 'text/plain'
                    resp = self.request(
                        url=file_endpoint, method='PUT', data=open(
                            file_path, mode='rb'), headers=headers)
                    self.log.info('file creation response: %s', resp)
                    processed_response = self._process_response({'value': [resp]})
                    self.dbo.save_into_table(user_id, processed_response, constants.LATEST_FILES)

                upload_files_list = []
                for root, directories, files in os.walk(
                        str(constants.ONEDRIVE_DOCUMENT_DIRECTORY)):
                    for directory in directories:
                        dir_path = os.path.join(root, directory)
                        dir_id = self.create_folder(folder_name=directory, user_id=user_id, location=dir_path, parent_folder_id=parent_folder_id)
                        # Upload files inside the folder
                        for file_name in os.listdir(dir_path):
                            upload_files_list.append(file_name)
                            file_path = os.path.join(dir_path, file_name)
                            upload_file(user_id, dir_id, dir_path, file_path, file_name)

                    for file_name in files:
                        if file_name not in upload_files_list:
                            # Join the two strings in order to form the full filepath.
                            file_path = os.path.join(root, file_name)
                            upload_file(user_id, folder_path, folder_id, file_path, file_name)


            except Exception as excp:
                self.log.exception('exception occurred while creating folder on OneDrive')
                raise CVCloudException(self.api_name, '103', str(excp))

    def get_file_properties(self,
                            user=None,
                            folder=constants.ONEDRIVE_FOLDER,
                            save_to_db_folder=False):
        """
        Method to fetch file properties from OneDrive Automation folder and store them to local DB

            Agrs:

                user  (str)   --  SMTP address of the user

        """

        if user:
            sc_content = [{'SMTPAddress': user}]
        else:
            sc_content = self.tc_object.subclient.content

        try:
            for content in sc_content:
                user_id = content.get('SMTPAddress')

                folder_id = self.get_folder_id_from_graph(user_id, folder)
                self.log.info(f'Fetching items from {folder} folder')

                if save_to_db_folder:
                    self._get_files_list(user_id, folder_id, save_to_db=True, folder_name=folder)
                else:
                    self._get_files_list(user_id, folder_id, save_to_db=True)

        except Exception as excp:
            self.log.exception('Exception while get file properties')
            raise CVCloudException(self.api_name, '104', str(excp))

    def get_folder_id_from_graph(self,
                                 user_id,
                                 folder=constants.ONEDRIVE_FOLDER,
                                 parent_folder_id=None):
        """This method fetches the folder id of the automation folder on users OneDrive
           THIS METHOD ALSO WORKS FOR FETCHING FILE ID
           --> In the place of folder, just pass the file name as argument

                Args:

                    user_id (str)   --  User SMTP address

                    folder (str)    --  folder/file to be searched for

                    parent_folder_id (str)  --  Id of the folder to search in

                Returns:

                    folder_id   (str)   --  ID of the automation folder

        """
        try:
            is_root_checked = False
            if parent_folder_id:
                is_root_checked = True

            if folder == 'root':
                get_root_id_endpoint = (
                    f'{self.graph_endpoint}'
                    f'{constants.MS_GET_USERS}'
                    f'{constants.MS_GET_ROOT_ID.format(user_id)}'
                )
                self.log.info('Get root children endpoint: %s', get_root_id_endpoint)

                response = self.request(url=get_root_id_endpoint, headers=self.headers)
                root_id = response.get("id", None)
                if root_id:
                    return root_id
                else:
                    raise Exception("Failed to obtain ID of root location")

            get_root_children_endpoint = (
                f'{self.graph_endpoint}'
                f'{constants.MS_GET_USERS}'
                f'{constants.MS_GET_ROOT_CHILDREN.format(user_id)}'
            )

            folder_id = None
            folder_id_list = list()

            folder_to_be_checked = None
            if parent_folder_id:
                folder_to_be_checked = parent_folder_id

            while not folder_id:

                if is_root_checked:
                    get_root_children_endpoint = (
                        f'{self.graph_endpoint}'
                        f'{constants.MS_GET_USERS}'
                        f'{constants.MS_GET_FOLDER_CHILDREN.format(user_id, folder_to_be_checked)}'
                    )

                self.log.info('Get folder children endpoint: %s', get_root_children_endpoint)
                self.log.info('Folder to search for: %s', folder)
                response = self.request(url=get_root_children_endpoint, headers=self.headers)
                for element in response.get('value'):
                    if element.get('name') == folder:
                        folder_id = element.get('id')
                        self.log.info('Got folder ID from Graph: %s', folder_id)
                        self.dbo.dbo.purge_table(f'{user_id}{constants.FOLDER_TABLE}')
                        self.dbo.save_into_table(user_id, element, constants.FOLDER_TABLE)
                        break
                    elif element.get('folder'):
                        folder_id_list.append(element.get('id'))

                if not folder_id:
                    if '@odata.nextLink' in response:
                        get_root_children_endpoint = response['@odata.nextLink']
                    elif folder_id_list:
                        is_root_checked = True
                        folder_to_be_checked = folder_id_list.pop()
                    else:
                        self.log.error('Folder does not exist on OneDrive')
                        break

            return folder_id

        except Exception as excp:
            self.log.exception(
                'Exception occurred while fetching item id from MS Graph.')
            raise CVCloudException(self.api_name, '107', str(excp))

    def _get_files_list(self, user_id, folder_id, save_to_db=True, folder_name=None):
        """This method gets the list of file metadata from users OneDrive

                Args:

                    user_id (str)   --  SMTP address of the user

                    folder_id   (str)   --  ID of the folder from file properties have to be fetched

                    save_to_db  (bool)  --  If true, file properties will be saved to local db
                    If false, files properties will be returned

                Returns:

                    file_properties (list)  --  list of file properties dicts

        """
        final_response = []
        get_folder_children_endpoint = (
            f'{self.graph_endpoint}'
            f'{constants.MS_GET_USERS}'
            f'{constants.MS_GET_FOLDER_CHILDREN.format(user_id, folder_id)}'
        )
        self.log.info('Get folder children endpoint: %s', get_folder_children_endpoint)

        response = self.request(url=get_folder_children_endpoint, headers=self.headers)
        self.log.info('response:%s', response)
        processed_response = self._process_response(response)

        if save_to_db:
            self.log.info('Purging the db before saving current properties')
            if folder_name:
                self.dbo.dbo.purge_table(f'{user_id}{constants.ONEDRIVE_TABLE}_{folder_name}')
            else:
                self.dbo.dbo.purge_table(f'{user_id}{constants.ONEDRIVE_TABLE}')
            self.dbo.save_into_table(
                user_id,
                processed_response,
                data_type=constants.ONEDRIVE_TABLE)
        else:
            final_response = processed_response

        while '@odata.nextLink' in response:
            self.log.info('@odata.nextLink:%s', response.get('@odata.nextLink'))
            response = self.request(url=response.get('@odata.nextLink'), headers=self.headers)
            self.log.info('response:%s', response)
            processed_response = self._process_response(response)

            if save_to_db:
                self.dbo.save_into_table(
                    user_id,
                    processed_response,
                    data_type=constants.ONEDRIVE_TABLE)
            else:
                final_response.extend(processed_response)

        return final_response

    def compare_file_properties(self, oop=False, to_disk=False, incremental=False, user_id=None, restore_as_copy=False):
        """Method to compare file properties before backup and after restore."""

        try:
            if user_id:
                sc_content = [{'SMTPAddress': user_id}]
            else:
                sc_content = self.tc_object.subclient.content
            if not oop:
                for content in sc_content:
                    user_id = content.get('SMTPAddress')
                    if restore_as_copy:
                        self._compare_files(user_id=user_id, incremental=incremental, restore_as_copy=restore_as_copy)
                    else:
                        self._compare_files(user_id=user_id, incremental=incremental)
            else:
                if to_disk:
                    # This is OOP restore to disk
                    self.log.info('This is oop restore to disk comparison')
                    if not user_id:
                        job_list = self.dbo.get_content('job_list_disk')[0]['job_list']
                        user_id = job_list[3]
                    self.download_files(user=user_id)
                    source_path = os.path.join(constants.ONEDRIVE_DOWNLOAD_DIRECTORY, user_id)
                    destination_path = constants.DESTINATION_TO_DISK_AFTER_RESTORE % (
                        constants.DESTINATION_TO_DISK,
                        user_id,
                        constants.ONEDRIVE_FOLDER)
                    self.log.info('destination path on proxy client: %s', destination_path)
                    proxy_client = Machine(
                        self.tc_object.proxy_client,
                        self.tc_object.commcell)

                    diff = self.machine.compare_folders(destination_machine=proxy_client,
                                                        source_path=source_path,
                                                        destination_path=destination_path)

                    if diff:
                        self.log.error('Following files are not matching after restore', diff)
                        raise CVCloudException(self.api_name, '111')
                    self.log.info('File hashes are matching after disk restore')
                    proxy_client.remove_directory(destination_path)
                else:
                    # This is OOP to other user account
                    job_list = self.dbo.get_content('job_list_oop')[-1]['job_list']
                    dest_user_id = job_list[2]
                    self.get_file_properties(user=user_id)
                    self.log.info("Now comparing files")
                    if restore_as_copy:
                        self._compare_files(user_id=user_id, restore_as_copy=restore_as_copy, dest_user_id=dest_user_id)
                    else:
                        self._compare_files(user_id=user_id, dest_user_id=dest_user_id)

        except Exception as excp:
            self.log.exception('Exception in compare_files operation on OneDrive')
            raise CVCloudException(self.api_name, '107', str(excp))

    def _compare_files(self, user_id, incremental=False, folder=None, restore_as_copy=False, dest_user_id=None):
        """Method to compare files on OneDrive with file metadata in local db

                Args:
                    user_id  (str)   --  SMTP address of the user
                    dest_user_id    (str) --    SMTP address of the destination user if OOP
                Raises exception on comparison failure
        """
        if incremental:
            user_table = self.dbo.get_content(f'{user_id}{constants.LATEST_FILES}')
            self.log.info(user_table)
        else:
            if folder:
                user_table = self.dbo.get_content(f'{user_id}{constants.ONEDRIVE_TABLE}_{folder}')
                if dest_user_id:
                    folder_id = self.get_folder_id_from_graph(dest_user_id, folder)
                else:
                    folder_id = self.get_folder_id_from_graph(user_id, folder)
            else:
                user_table = self.dbo.get_content(f'{user_id}{constants.ONEDRIVE_TABLE}')

        if not folder:
            if dest_user_id:
                folder_id = self.get_folder_id_from_graph(dest_user_id)
            else:
                folder_id = self.get_folder_id_from_graph(user_id)

        if not folder_id:
            raise CVCloudException(self.api_name, '105')

        if dest_user_id:
            files_list = self._get_files_list(dest_user_id, folder_id, save_to_db=False)
        else:
            files_list = self._get_files_list(user_id, folder_id, save_to_db=False)

        # User table -- Created items in user account
        # Files list -- Items fetched after restore from Onedrive
        self.log.info('Number of Backed up documents: %s', len(user_table))
        self.log.info('Number of restored documents: %s', len(files_list))

        if len(user_table) != len(files_list):
            # If restore as copy Check restore files count is double of backup files count
            if restore_as_copy:
                if (2 * len(user_table)) != len(files_list):
                    self.log.info(f'Obtained file count: {len(files_list)}')
                    self.log.error(
                        'For Restore as a copy, the number of documents present '
                        'in user\'s OneDrive does not match the expected count '
                        'which is double the count of backed up items')
                    raise CVCloudException(self.api_name, '108')
            else:
                self.log.info(f'Obtained file count: {len(files_list)}')
                self.log.error(
                    'Number of restored documents is different than'
                    'the number of backed up documents.')
                raise CVCloudException(self.api_name, '108')

        if restore_as_copy:
            backed_up_files_list = []
            restored_files_list = []
            for file in user_table:
                backed_up_files_list.append(file.get('name'))

            # Add copied files to backed up files list
            for file in user_table:
                files = file.get('name').split('.')
                file_name = f'{files[0]} 1' + "." + files[1]
                backed_up_files_list.append(file_name)

            for file in files_list:
                restored_files_list.append(file.get('name'))

            match_count = 0
            for backup_file in backed_up_files_list:
                for restore_file in restored_files_list:
                    if backup_file == restore_file:
                        match_count += 1

            if match_count != len(restored_files_list):
                self.log.exception('All files did not match from backup and restore files list')
                raise CVCloudException(self.api_name, '109')
        else:
            # Files metadata verification
            for file_metadata in files_list:
                self.log.info('file metadata: %s', file_metadata)
                match = False
                for file in user_table:
                    self.log.info('file from user table: %s', file)
                    # If OOP parent path differs in the starting
                    if 'quickXorHash' in file and dest_user_id:
                        if file.get('quickXorHash') == file_metadata.get('quickXorHash') and file.get(
                                'parentPath').split('/')[-1] == file_metadata.get('parentPath').split('/')[-1]:
                            self.log.info('file properties are matching')
                            match = True
                            break
                    elif 'childCount' in file and dest_user_id:
                        if file.get('childCount') == file_metadata.get('childCount') and file.get(
                                'parentPath').split('/')[-1] == file_metadata.get('parentPath').split('/')[-1]:
                            self.log.info('folder properties are matching')
                            match = True
                            break
                    elif 'quickXorHash' in file:
                        if file.get('quickXorHash') == file_metadata.get('quickXorHash') and file.get(
                                'parentPath') == file_metadata.get('parentPath'):
                            self.log.info('file properties are matching')
                            match = True
                            break
                    elif 'childCount' in file:
                        if file.get('childCount') == file_metadata.get('childCount') and file.get(
                                'parentPath') == file_metadata.get('parentPath'):
                            self.log.info('folder properties are matching')
                            match = True
                            break
                if not match:
                    self.log.exception('File properties are not matching after restore')
                    raise CVCloudException(self.api_name, '109')

    def compare_files_with_db(self,
                              user_id,
                              folder=constants.ONEDRIVE_FOLDER,
                              restore_as_copy=False):
        """Method to compare files on OneDrive with file metadata in local db

                Args:

                    user_id  (str)   --  SMTP address of the user

                Raises exception on comparison failure

        """
        self._compare_files(user_id=user_id,
                            incremental=False,
                            folder=folder,
                            restore_as_copy=restore_as_copy)

    def compare_onedrive_data_of_two_users(self,
                                           user_id1,
                                           user_id2,
                                           folder1=constants.ONEDRIVE_FOLDER,
                                           folder_list2=None):
        """Method to compare folders Out of place restore of two users in OneDrive

                        Args:

                            user_id1  (str)   --  SMTP address of the user1

                            user_id2  (str)   --  SMTP address of the user2

                            folder1 (str) --  Folder name of user1

                            folder_list2 (list) --List of Folder names of user2

                        Raises exception on comparison failure

        """
        try:
            # Expand folder1
            folder_id1 = self.get_folder_id_from_graph(user_id1, folder1)
            if not folder_id1:
                raise CVCloudException(self.api_name, '105')

            folder_list1 = self._get_files_list(user_id1, folder_id1, save_to_db=False)
            local_folder_list1 = []
            for _folder in folder_list1:
                inner_folder_id1 = self.get_folder_id_from_graph(user_id1, _folder.get("name"))
                inner_folder_list1 = self._get_files_list(user_id1, inner_folder_id1, save_to_db=False)
                for _inner_folder in inner_folder_list1:
                    local_folder_list1.append(_inner_folder.get("name"))

            # Iterate folder1, folder2 list
            common_folders_list = set(local_folder_list1).intersection(set(folder_list2))
            for folder in common_folders_list:
                self.compare_content_of_two_folders(user_id1, user_id2, folder, folder)
            # for _folder1 in local_folder_list1:
            #     for _folder2 in folder_list2:
            #         if _folder1 == _folder2:
            #             self._compare_files_two_users(user_id1, user_id2, _folder1, _folder2)

        except Exception as excp:
            self.log.exception('Exception while comparing the OneDrive data of two users')
            raise CVCloudException(self.api_name, '107', str(excp))

    def compare_content_of_two_folders(self,
                                       user_id1,
                                       user_id2,
                                       folder1=constants.ONEDRIVE_FOLDER,
                                       folder2=constants.ONEDRIVE_FOLDER,
                                       check_folder_level=True):
        """Method to compare folders of two users in OneDrive

                        Args:

                            user_id1  (str)   --  SMTP address of the user1

                            user_id2  (str)   --  SMTP address of the user2

                            folder1 (str) --    Folder name of user1

                            folder2 (str) --    Folder name of user2

                            check_folder_level (bool)   --  Check if one folder is on the same level as other

                        Raises exception on comparison failure

        """

        folder_id1 = self.get_folder_id_from_graph(user_id1, folder1)
        folder_id2 = self.get_folder_id_from_graph(user_id2, folder2)
        if not (folder_id1 or folder_id2):
            raise CVCloudException(self.api_name, '105')

        files_list1 = self._get_files_list(user_id1, folder_id1, save_to_db=False)
        files_list2 = self._get_files_list(user_id2, folder_id2, save_to_db=False)

        file_dictionary1, file_dictionary2 = {}, {}

        for files_list, file_dictionary in [(files_list1, file_dictionary1), (files_list2, file_dictionary2)]:
            for file_data in files_list:
                file_dictionary[file_data['name']] = file_data

        files_list_big, files_list_small = (file_dictionary1, file_dictionary2) \
            if len(file_dictionary1) > len(file_dictionary2) else (file_dictionary2, file_dictionary1)

        for file_name, file_metadata1 in files_list_big.items():

            if file_name not in files_list_small.keys():
                raise CVCloudException(self.api_name, '107', f'File {file_name} is not present in one folder location')

            file_metadata2 = files_list_small[file_name]

            match = False
            # In case file size is 0, quickXorHash is None
            if ('size' in file_metadata1 and 'size' in file_metadata2 and
                    file_metadata1.get('size') == 0 and file_metadata2.get('size') == 0):
                match = True
            elif 'quickXorHash' in file_metadata1 and 'quickXorHash' in file_metadata2:
                if file_metadata1.get('quickXorHash') == file_metadata2.get('quickXorHash'):
                    match = True
            elif 'childCount' in file_metadata1 and 'childCount' in file_metadata2:
                if file_metadata1.get('childCount') == file_metadata2.get('childCount'):
                    match = True

            if check_folder_level and (file_metadata1.get('parentPath') != file_metadata2.get('parentPath')):
                match = False

            if match:
                self.log.info(f'Properties for entity {file_name}, match')
            else:
                self.log.exception(f'File/Folder properties do not match after restore\n'
                                   f'Entity-1 Properties: {file_metadata1}\nEntity-2 Properties: {file_metadata2}')
                raise CVCloudException(self.api_name, '109')

    def _compare_file(self, user_id, file_name, folder_name=constants.ONEDRIVE_FOLDER, incremental=False):
        """Method to compare individual file on OneDrive with file metadata in local db

                Args:

                    user_id  (str)   --  SMTP address of the user

                    file_name (str)  -- File name to compare against local db

                    folder_name (str) -- Folder name to compare agains local db

                Raises exception on comparison failure

        """
        if incremental:
            user_table = self.dbo.get_content(f'{user_id}{constants.LATEST_FILES}')
        else:
            user_table = self.dbo.get_content(f'{user_id}{constants.ONEDRIVE_TABLE}')
        folder_id = self.get_folder_id_from_graph(user_id, folder=folder_name)
        if not folder_id or not file_name:
            raise CVCloudException(self.api_name, '105')

        files_list = self._get_files_list(user_id, folder_id, save_to_db=False)
        for file_metadata in files_list:
            self.log.info('file metadata: %s', file_metadata)
            one_drive_file_name = file_metadata['name']
            if one_drive_file_name == file_name:
                match = False
                for file in user_table:
                    _file_name = file['name']
                    if _file_name == file_name:
                        self.log.info('file from user table: %s', file)
                        if 'quickXorHash' in file:
                            if file.get('quickXorHash') == file_metadata.get('quickXorHash') and file.get(
                                    'parentPath') == file_metadata.get('parentPath'):
                                self.log.info('file properties are matching')
                                match = True
                                break
                        elif 'childCount' in file:
                            if file.get('childCount') == file_metadata.get('childCount') and file.get(
                                    'parentPath') == file_metadata.get('parentPath'):
                                self.log.info('folder properties are matching')
                                match = True
                                break
                        if not match:
                            self.log.exception('File properties are not matching after restore')
                            raise CVCloudException(self.api_name, '109')

    def delete_folder(self, user_id=None, folder_name=constants.ONEDRIVE_FOLDER, folder_id=None, parent_folder_id=None):
        """Method to delete the automation folder from user OneDrive.

                Args:

                    user_id (str)   --  User SMTP Address

                    folder_name  (str)  --  Name of the folder to delete
                        Default: ONEDRIVE_FOLDER value from constants

                    folder_id (str)     --  Id of folder to be deleted

        """
        try:
            if user_id:
                sc_content = [{'SMTPAddress': user_id}]
            else:
                sc_content = self.tc_object.subclient.content

            for content in sc_content:
                user_id = content.get('SMTPAddress')
                if not folder_id:
                    folder_id = self.get_folder_id_from_graph(user_id, folder_name)
                    if folder_name is not constants.ONEDRIVE_FOLDER and folder_id is None:
                        raise Exception('Unable to obtain folder id for deletion of folder')
                    elif folder_name is constants.ONEDRIVE_FOLDER and folder_id is None:
                        return

                delete_folder_endpoint = (
                    f'{self.graph_endpoint}'
                    f'{constants.MS_GET_USERS}'
                    f'{constants.MS_DELETE_ITEM.format(user_id, folder_id)}'
                )
                self.log.info('Delete folder endpoint: %s', delete_folder_endpoint)
                resp = self.request(
                    url=delete_folder_endpoint,
                    method='DELETE',
                    headers=self.headers)
                self.log.info('Delete folder response: %s', resp)
        except Exception as excp:
            self.log.exception('Exception while deleting folder on OneDrive.')
            raise CVCloudException(self.api_name, '107', str(excp))

    def download_files(self, user=None):
        """
        Method to download all the files from OneDrive Automation folder.
        Folder id is fetched from local DB file.

            Args:

                user    (str)   --  SMTP Address of the user

        """
        if user:
            sc_content = [{'SMTPAddress': user}]
        else:
            sc_content = self.tc_object.subclient.content

        try:
            for content in sc_content:
                user_id = content.get('SMTPAddress')

                db_content = self.dbo.get_content(f'{user_id}{constants.ONEDRIVE_TABLE}')

                download_directory = os.path.join(constants.ONEDRIVE_DOWNLOAD_DIRECTORY, user_id)

                os.makedirs(download_directory, exist_ok=True)
                self.log.info('Downloading the files')

                for files in db_content:
                    self.log.info('file: %s', files)
                    self.download_single_file(
                        user_id=user_id,
                        file_path=files['parentPath'] + '/' + files['name'],
                        download_directory=download_directory
                    )

        except Exception as excp:
            self.log.exception('Exception in download_files operation on OneDrive')
            raise CVCloudException(self.api_name, '107', str(excp))

    def download_single_file(self, user_id, file_path, download_directory):
        """Method to download a single file from OneDrive based on the file path.
        File is downloaded in one drive download folder defined in constants file.

                Args:

                    user_id    (str)   --  SMTP Address of the user

                    file_path (str)  --  File path relative to OneDrive root folder

                    download_directory (str)  --  Directory name to download files into

        """
        try:
            download_file_endpoint = (
                f'{self.graph_endpoint}'
                f'{constants.MS_GET_USERS}/{user_id}{file_path}'
            )

            self.log.info('Download file endpoint: %s', download_file_endpoint)
            resp = self.request(url=download_file_endpoint, headers=self.headers)
            download_url = resp['@microsoft.graph.downloadUrl']
            self.log.info('Download file url: %s', download_url)
            resp = self.request(url=download_url)
            self.log.info('Download file response: %s', resp)
            file_name = file_path.split('/')[-1]
            download_file_path = os.path.join(download_directory, file_name)
            self.log.info('Download file location: %s', download_file_path)
            with open(download_file_path, 'wb') as fp:
                fp.write(resp.content)

        except Exception as excp:
            self.log.exception('Exception in download_single_file operation on OneDrive')
            raise CVCloudException(self.api_name, '107', str(excp))

    def _process_response(self, response):
        """Method to process the response got from MS Graph API.
        This method returns name, etag, ctag and size of the file

            Args:

                    response    (dict)  --  Raw response got from MS Graph API Call

            Returns:

                processed_response  (list)  --  List of minimal dicts containing
                name, etag, ctag, size, id of the files

        """
        try:
            processed_response = []
            if 'value' in response:
                for element in response.get('value'):
                    temp_element = {
                        'eTag': element.get('eTag'),
                        'id': element.get('id'),
                        'name': element.get('name'),
                        'cTag': element.get('cTag'),
                        'size': element.get('size'),
                        'parentPath': element.get('parentReference').get('path')
                    }

                    if 'file' in element:
                        temp_element['quickXorHash'] = element.get('file', {}).get('hashes', {}).get('quickXorHash')

                    if 'folder' in element:
                        temp_element['childCount'] = element.get('folder').get('childCount')

                    processed_response.append(temp_element)
                return processed_response
            else:
                self.log.error('Invalid input response for the method')
                raise CVCloudException(self.api_name, '106')
        except Exception as excp:
            self.log.exception('Exception while processing graph response.')
            raise CVCloudException(self.api_name, '107', str(excp))

    def request(self, url=None, method='GET', data=None, headers=None):
        """Method to make a request to Graph URL via OAUTH request method

                Args:

                    url (str)   --  API Endpoint to make request to

                    method (str)    --  API call method

                    Valid Values:
                        GET

                        POST

                        PUT

                        DELETE

                        PATCH

                    data (dict) --  Data to be sent with POST/PUT requests

                    headers (dict)  --  Request headers.

                    Default:

                    self._headers

                    Access token is automatically appended by
                    OAuth2Session class request method used in this module.

        """

        try:
            if not self.auth_object.oauth.authorized:
                self.auth_object.authenticate_client()

            time_out = 0

            while time_out <= 3:

                try:

                    if method in ['GET', 'DELETE']:
                        resp = self.auth_object.oauth.request(
                            method=method, url=url, headers=headers)
                    elif method in ['POST', 'PUT', 'PATCH']:
                        self.log.info('This is a %s method', method)
                        self.log.info('data: %s', data)
                        resp = self.auth_object.oauth.request(
                            method=method, url=url, data=data, headers=headers)

                    else:
                        self.log.error('Method %s not supported', method)
                        raise CVCloudException(self.api_name, '102')
                    self.log.info('status code: %s', resp.status_code)
                    if not resp.ok:
                        self.log.error('error: %s', resp.json())
                        resp.raise_for_status()
                    else:
                        self.log.info('Got success response code: %s', resp.status_code)
                        try:
                            return resp.json()
                        except Exception:
                            return resp
                except HTTPError:
                    # If the error is a rate limit, connection error or backend error,
                    # wait and try again.
                    time_out += 1
                    self.log.error('Encountered HTTP Error: {0}'.format(resp.status_code))
                    # Handle the error accordingly [400, 404, 429, 500, 503]

                    if resp.status_code == 401:
                        self.log.error('Request unauthorized.Trying to authenticate client..')
                        self.auth_object.authenticate_client()
                        continue
                    if resp.status_code == 404 and method == 'DELETE':
                        self.log.info('Item does not exist on OneDrive')
                        break
                    if resp.status_code == 404 and method == 'GET':
                        self.log.info('User does not exist on OneDrive')
                        break
                    elif resp.status_code == 429:
                        self.log.info(
                            'Got throttled from MS server. '
                            'Waiting for few seconds before trying again')
                        time.sleep(120)
                        # This is backend error from MS Graph so we need to retry after waiting
                        # In case of throttling error, MS recommends to wait two whole minutes
                        # Refer (https://docs.microsoft.com/en-us/sharepoint/dev/general-development/
                        # how-to-avoid-getting-throttled-or-blocked-in-sharepoint-online#search-query
                        # -volume-limits-when-using-app-only-authentication-with-sitesreadall-permission)
                        continue
                    elif resp.status_code == 500:
                        self.log.info(
                            'This is internal server error from MS Graph. '
                            'Waiting for few seconds before trying again')
                        time.sleep(time_out * 10)
                        # This is backend error from MS Graph so we need to retry after waiting
                        continue
                    elif resp.status_code == 501:
                        self.log.info('The requested feature isn’t implemented.')
                        raise
                    elif resp.status_code == 503:
                        self.log.info(
                            'Service unavailable currently. '
                            'Waiting as per Retry-After header and try again.')
                        t_value = resp.headers.get('Retry-After')
                        time.sleep(t_value)
                        continue
                    elif resp.status_code == 504:
                        self.log.info('Gateway timeout error. Retry after sometime.')
                        time.sleep(time_out * 10)
                        # This is backend error from MS Graph so we need to retry after waiting
                        continue
                    elif resp.status_code == 507:
                        self.log.info(
                            'Insufficient Storage. The maximum storage quota has been reached.')
                        raise
                    elif resp.status_code == 509:
                        self.log.info('Bandwidth Limit Exceeded')
                        raise
                except TokenExpiredError:
                    self.log.warning('Token expired. fetching a new token and trying again.')
                    self.auth_object.authenticate_client()
                    continue
            if time_out > 3:
                self.log.error('Maximum retries for Graph request exceeded.')
                raise CVCloudException(self.api_name, '110')
        except Exception as excp:
            self.log.exception('Exception while processing graph response.')
            raise CVCloudException(self.api_name, '107', str(excp))

    def delete_single_file(self, file_name=None, user_id=None, file_id=None):
        """Method to delete a single file from OneDrive based on the file path.

                Args:

                    user_id    (str)   --  SMTP Address of the user

                    file_name (str)  --  File name to Delete from OneDrive account

                    file_id (str)   --  Id of file to be deleted from OneDrive account

        """
        try:
            if user_id:
                sc_content = [{'SMTPAddress': user_id}]
            else:
                sc_content = self.tc_object.subclient.content

            for content in sc_content:
                user_id = content.get('SMTPAddress')

                if not file_id:

                    self.get_file_properties(user=user_id)
                    file_content = self.dbo.get_content(f'{user_id}{constants.ONEDRIVE_TABLE}')

                    file_id = None
                    for i in file_content:
                        if i['name'] == file_name:
                            file_id = i['id']
                            break

                    if file_id is None:
                        raise Exception('Unable to obtain file id for deletion of file')

                delete_file_endpoint = (
                    f'{self.graph_endpoint}'
                    f'{constants.MS_GET_USERS}'
                    f'{constants.MS_DELETE_ITEM.format(user_id, file_id)}'
                )
                self.log.info('Delete file endpoint: %s', delete_file_endpoint)
                resp = self.request(
                    url=delete_file_endpoint,
                    method='DELETE',
                    headers=self.headers)
                self.log.info('Delete file response: %s', resp)

        except Exception as excp:
            self.log.exception('Exception while deleting file on OneDrive.')
            raise CVCloudException(self.api_name, '107', str(excp))

    def upload_files_to_onedrive(self, file_location, no_of_files):
        """ Method to generate files and upload them to one_drive.

                Args:

                    file_location    (str)   --  file location on the machine to generate files
                                                    (Example: file_location - 'C:\Temp')
                    no_of_files (str)  --  Number of files to generate in the file location to upload

        """
        self.machine.generate_test_data(file_path=file_location, dirs=1, files=no_of_files)
        user_id = None
        sc_content = self.tc_object.subclient.content

        for content in sc_content:
            user_id = content.get('SMTPAddress')
        try:
            folder_endpoint = f'{self.graph_endpoint}{constants.MS_GET_USERS}' \
                              f'/{user_id}{constants.MS_CREATE_FOLDER}'

            data = {
                "name": "AutomationFolder",
                "folder": {},
                "@microsoft.graph.conflictBehavior": "replace"
            }

            resp = self.request(method='POST', url=folder_endpoint, data=json.dumps(data), headers=self.headers)
            self.log.info('folder creation response: %s', resp)

            for root, dirs, files in os.walk(file_location):
                if os.path.basename(root) == 'regular':
                    for file in files:
                        file_path = os.path.join(root, file)
                        file_endpoint = (f'{self.graph_endpoint}'
                                         f'{constants.MS_GET_USERS}'
                                         f'{constants.MS_UPLOAD_FILE.format(user_id, "AutomationFolder", file)}'
                                         )
                        self.headers = self.headers.copy()
                        self.headers['Content-Type'] = 'text/plain'
                        resp = self.request(
                            url=file_endpoint,
                            method='PUT',
                            data=open(file_path, mode='rb'),
                            headers=self.headers)
                        self.log.info('Files uploading response: %s', resp)
        except Exception as excp:
            self.log.exception('exception occurred while creating files on OneDrive')
            raise CVCloudException(self.api_name, '103', str(excp))

    def verify_finalize_phase(self, job_id):
        """Method to verify onedrive backup finalize phase.

            Args:

                job_id   (str)   --  id of a backup job

        """
        user_id = None
        sc_content = self.tc_object.subclient.content
        for content in sc_content:
            user_id = content.get('SMTPAddress')

        try:
            job_info = self.sqlite.get_job_info_local_db(job_id=job_id)
            job_info = job_info[0]
            if job_info:
                if job_info[0] == int(job_id):
                    self.log.info('Job id from the local db: [%s]', job_info[0])

                    if job_info[1] == 'ok':
                        self.log.info('Job Status from the local db: [%s]', job_info[1])
                    else:
                        self.log.info('Job Status from the local db: [%s]', job_info[1])
                        raise Exception('Finalize phase failed')

                    change_link = job_info[2]
                    token = change_link.rsplit('=', 1)[1]

                    file_endpoint = (f'{self.graph_endpoint}'
                                     f'{constants.MS_GET_USERS}'
                                     f'{constants.ONEDRIVE_DELTA_QUERY.format(user_id, token)}'
                                     )

                    resp = self.request(method='GET', url=file_endpoint, headers=self.headers)
                    if resp['value']:
                        raise Exception('Failed to Update the Change link token')
                    else:
                        self.log.info('Successfully updated change link token')

                else:
                    raise Exception('Error in getting Job info from Local DB')

            path = self.machine.get_registry_value(f'{constants.REG_KEY_BASE}', f'{constants.PATH_KEY}')
            temp_sqlite_file = (
                f'{path}'
                f'{constants.ONEDRIVE_JOB_DIRECTORY_PATH.format(self.tc_object.subclient.subclient_id, f"Temp_{user_id}")}'
            )
            if os.path.exists(temp_sqlite_file):
                raise Exception("Temporary local db failed to move")
            else:
                self.log.info("Temporary local db successfully moved")

        except Exception as excp:
            self.log.exception('Exception during Finalize phase verification')
            raise CVCloudException(self.api_name, '112', str(excp))

    def discover_groups(self):
        """Method to discover users on azure AD"""

        try:
            groups_endpoint = (f'{self.graph_endpoint}'
                               f'{constants.MS_GET_GROUPS}'
                               f'?$top={str(constants.USER_PAGE_SIZE)}')
            self.log.info('groups_endpoint:%s', groups_endpoint)

            response = self.request(url=groups_endpoint, headers=self.headers)
            self.log.info('response:%s', response)
            self.log.info('response length: %s', len(response.get('value')))
            self.dbo.save_into_table('groups', response.get('value'), '_list')

            while '@odata.nextLink' in response:
                self.log.info('@odata.nextLink:%s', response.get('@odata.nextLink'))
                response = self.request(url=response.get('@odata.nextLink'), headers=self.headers)
                self.dbo.save_into_table('groups', response.get('value'), '_list')
                self.log.info('response:%s', response)
                self.log.info('response length: %s', len(response.get('value')))
        except Exception as excp:
            self.log.exception('Exception while discovering groups')
            raise CVCloudException(self.api_name, '101', str(excp))

    def discover_group_members(self, group_name):
        """Method to discover members of a group on azure AD"""
        try:
            group_id_endpoint = (f'{self.graph_endpoint}'
                                 f'{constants.MS_GET_GROUPS}'
                                 f'?$filter=startsWith(displayName,\'{group_name}\')')
            self.log.info('groups_endpoint:%s', group_id_endpoint)
            response = self.request(url=group_id_endpoint, headers=self.headers)
            self.log.info(':%s', response)
            group_id = response['value'][0]['id']
            self.log.info(f'group id: {group_id}')

            members_endpoint = (f'{self.graph_endpoint}'
                                f'{constants.MS_GET_GROUPS}'
                                f'{constants.MS_GET_GROUP_MEMBERS.format(group_id)}')
            self.log.info('group_members_endpoint:%s', members_endpoint)

            response = self.request(url=members_endpoint, headers=self.headers)
            self.log.info('response:%s', response)
            self.log.info('response length: %s', len(response.get('value')))
            self.dbo.save_into_table(f'{group_name.lower()}_members', response.get('value'), '_list')

            while '@odata.nextLink' in response:
                self.log.info('@odata.nextLink:%s', response.get('@odata.nextLink'))
                response = self.request(url=response.get('@odata.nextLink'), headers=self.headers)
                self.dbo.save_into_table('groups', response.get('value'), '_list')
                self.log.info('response:%s', response)
                self.log.info('response length: %s', len(response.get('value')))
        except Exception as excp:
            self.log.exception('Exception while discovering group members')
            raise CVCloudException(self.api_name, '101', str(excp))

    def __check_if_user_exists(self, user_name, tenant_domain):
        """
        Method to check if user already exists in the tenant

        Args:
            user_name (str):        The name of the user
            tenant_domain (str):    The tenant domain to which the user belongs to

        """
        try:
            user_exist_endpoint = (f'{self.graph_endpoint}'
                                   f'{constants.MS_GET_USERS}'
                                   f'/{user_name}@{tenant_domain}')
            self.log.info(f'user_exist_endpoint: {user_exist_endpoint}')
            response = self.request(url=user_exist_endpoint, headers=self.headers)
            self.log.info(f'response:{response}')
            if response is not None:
                self.log.info(f'User exists on the tenant')
                return True
            self.log.info(f'User does not exist on the tenant')
            return False

        except Exception as excp:
            self.log.exception('Exception while checking if user exists')
            raise CVCloudException(self.api_name, '101', str(excp))

    def create_user(self, user_name, password, tenant_domain):
        """
        Method to create user on Azure AD

        Args:
            user_name (str):        The name of the user
            password (str):         Password of the new user
            tenant_domain (str):    The tenant domain on which the user has to be created

        """

        try:
            # If user already exists, delete user
            if self.__check_if_user_exists(user_name, tenant_domain):
                self.log.info(f'User already exists on OneDrive - Deleting user')
                self.delete_user(user_name=user_name, tenant_domain=tenant_domain)

            # Create user
            users_endpoint = (f'{self.graph_endpoint}'
                              f'{constants.MS_GET_USERS}')
            data = constants.ONEDRIVE_NEW_USER
            data['userPrincipalName'] = f'{user_name}@{tenant_domain}'
            data['mailNickname'] = f'{user_name}'
            data['passwordProfile']['password'] = password
            self.log.info('users_endpoint:%s', users_endpoint)

            response = self.request(url=users_endpoint,
                                    method='POST',
                                    data=json.dumps(data),
                                    headers=self.headers)
            self.log.info('response:%s', response)
            self.dbo.save_into_table('new_users', response, '_list')
            self.log.info(f'Successfully created user: {user_name}')
        except Exception as excp:
            self.log.exception('Exception while creating user')
            raise CVCloudException(self.api_name, '101', str(excp))

    def update_user_email_id(self, user_name, new_email_id, tenant_domain):
        """
        Method to update email id of user on Azure AD

        Args:
            user_name (str):    User whose email id has to be changed
            new_email_id (str): New user name to be updated in email
            tenant_domain (str):    Domain to which the user belongs

        """
        try:
            # If user with updated email id already exists, delete user
            if self.__check_if_user_exists(new_email_id, tenant_domain):
                self.log.info(f'User already exists on OneDrive - Deleting user')
                self.delete_user(user_name=new_email_id, tenant_domain=tenant_domain)

            users_endpoint = (f'{self.graph_endpoint}'
                              f'{constants.MS_GET_USERS}/'
                              f'{user_name}@{tenant_domain}')
            data = constants.ONEDRIVE_UPDATE_USER
            data['userPrincipalName'] = f'{new_email_id}@{tenant_domain}'
            data['mailNickname'] = f'{new_email_id}'
            self.log.info('users_endpoint:%s', users_endpoint)

            response = self.request(url=users_endpoint,
                                    method='PATCH',
                                    data=json.dumps(data),
                                    headers=self.headers)
            self.log.info('response:%s', response)
            self.log.info(f'Successfully updated user: {user_name}')
        except Exception as excp:
            self.log.exception('Exception while updating user')
            raise CVCloudException(self.api_name, '101', str(excp))

    def delete_user(self, user_name, tenant_domain):
        """
        Deletes the given user from the Azure AD

        Args:
            user_name (str):    User to be deleted
            tenant_domain(str): Domain to which the user belongs

        """
        try:
            user_endpoint = (f'{self.graph_endpoint}'
                             f'{constants.MS_GET_USERS}/'
                             f'{user_name}@{tenant_domain}')

            response = self.request(url=user_endpoint, method='DELETE', headers=self.headers)
            self.log.info('response:%s', response)
            self.log.info(f'Successfully deleted user: {user_name}')

        except Exception as excp:
            self.log.exception('Exception while deleting user')
            raise CVCloudException(self.api_name, '101', str(excp))

    def __check_if_group_exists(self, group_name):
        """
        Method to check if user already exists in the tenant

        Args:
            group_name (str):       The name of the group

        """
        try:
            group_exist_endpoint = (f"{self.graph_endpoint}"
                                    f"{constants.MS_GET_GROUPS}"
                                    f"?$filter=displayName eq '{group_name}'")
            self.log.info(f'user_exist_endpoint: {group_exist_endpoint}')
            response = self.request(url=group_exist_endpoint, headers=self.headers)
            self.log.info(f'response:{response}')
            group_ids = list()
            if response is not None:
                for group in response['value']:
                    group_ids.append(group['id'])
            return group_ids

        except Exception as excp:
            self.log.exception('Exception while checking if group exists')
            raise CVCloudException(self.api_name, '101', str(excp))

    def create_group(self, group_name):
        """
        Creates the given group

        Args:
            group_name (str):   Group to be created

        """
        try:
            group_id_list = self.__check_if_group_exists(group_name)
            for group_id in group_id_list:
                self.log.info(f'Deleting group with id: {group_id}')
                self.delete_group(group_id=group_id)
            group_endpoint = (f'{self.graph_endpoint}'
                              f'{constants.MS_GET_GROUPS}')
            data = constants.ONEDRIVE_NEW_GROUP
            data['displayName'] = group_name
            data['mailNickname'] = f'{group_name}'
            self.log.info('group_endpoint:%s', group_endpoint)

            response = self.request(url=group_endpoint,
                                    method='POST',
                                    data=json.dumps(data),
                                    headers=self.headers)
            self.log.info('response:%s', response)
            self.dbo.save_into_table('new_groups', response, '_list')
            self.log.info(f'Successfully created group: {group_name}')
        except Exception as excp:
            self.log.exception('Exception while creating group')
            raise CVCloudException(self.api_name, '101', str(excp))

    def delete_group(self, group_name=None, group_id=None):
        """
        Deletes the given group

        Args:
            group_name (str):   Group to be deleted
            group_id (str):     Id of group to be deleted

        """
        try:
            if group_name:
                group_id = None
                details = self.dbo.get_content('new_groups_list')
                for group in details:
                    if group['mailNickname'] == group_name:
                        group_id = group['id']
            group_endpoint = (f'{self.graph_endpoint}'
                              f'{constants.MS_GET_GROUPS}/{group_id}')

            response = self.request(url=group_endpoint, method='DELETE', headers=self.headers)
            self.log.info('response:%s', response)
            self.log.info(f'Successfully deleted group: {group_name}')

        except Exception as excp:
            self.log.exception('Exception while deleting user')
            raise CVCloudException(self.api_name, '101', str(excp))

    def add_group_member(self, member, group_name):
        """
        Adds the given users to the group in Azure AD

        Args:
            member (str):       User to be added to the group
            group_name (str):   Group to which users have to be added

        """
        try:
            group_id = None
            details = self.dbo.get_content('new_groups_list')
            for group in details:
                if group['mailNickname'] == group_name:
                    group_id = group['id']
            group_endpoint = (f'{self.graph_endpoint}'
                              f'{constants.MS_GET_GROUPS}'
                              f'{constants.MS_GET_GROUP_MEMBERS.format(group_id)}/$ref')

            user_id = None
            details = self.dbo.get_content('new_users_list')
            for user in details:
                if user['userPrincipalName'].split('@')[0] == member:
                    user_id = user["id"]
            data = dict()
            data["@odata.id"] = f'{self.graph_endpoint}{constants.MS_GET_USERS}/{user_id}'

            response = self.request(url=group_endpoint,
                                    method='POST',
                                    data=json.dumps(data),
                                    headers=self.headers)
            self.log.info('response:%s', response)
            self.log.info(f'Successfully added member {member} to group {group_name}')

        except Exception as excp:
            self.log.exception('Exception while adding group member')
            raise CVCloudException(self.api_name, '101', str(excp))

    def remove_group_member(self, member, group_name):
        """
        Removes the given members from group in Azure AD

        Args:
            member (str):       User to be removed from the group
            group_name (str):   Group from which users have to be removed

        """
        try:
            group_id = None
            details = self.dbo.get_content('new_groups_list')
            for group in details:
                if group['mailNickname'] == group_name:
                    group_id = group['id']

            user_id = None
            details = self.dbo.get_content('new_users_list')
            for user in details:
                if user['userPrincipalName'].split('@')[0] == member:
                    user_id = user["id"]

            group_endpoint = (f'{self.graph_endpoint}'
                              f'{constants.MS_GET_GROUPS}'
                              f'{constants.MS_GET_GROUP_MEMBERS.format(group_id)}'
                              f'/{user_id}/$ref')

            response = self.request(url=group_endpoint, method='DELETE', headers=self.headers)
            self.log.info('response:%s', response)
            self.log.info(f'Successfully removed member {member} from group {group_name}')

        except Exception as excp:
            self.log.exception('Exception while removing group member')
            raise CVCloudException(self.api_name, '101', str(excp))

    def launch_autodiscovery_via_cli(self, app_name):
        """
        Launch Auto-Discovery on the proxy via command line

        Args:
            app_name (str):     Name of the Office 365 Client for which
                                Autodiscovery is to be launched

        """
        proxy = Machine(machine_name=self.tc_object.instance.proxy_client,
                        commcell_object=self.tc_object.commcell)
        path = proxy.get_registry_value(f'{constants.REG_KEY_BASE}', f'{constants.BASE_KEY}')
        self.log.info(f'Path: {path}')
        instance = proxy.instance
        self.log.info(f'Instance: {instance}')
        client_id, subclient_id = self.csdb.get_subclient_id(app_name)
        client_name, machine_name = self.csdb.get_access_node_details(app_name)

        command = (
            'start-process '
            '-filepath "cvCloudDiscoverV2.exe" '
            f'-workingDirectory "{path}" '
            f'-ArgumentList "-j 0 -a 2:{subclient_id} -c {machine_name} -m {machine_name} '
            f'-t 2 -r 0 -i 0 -d 12 -ci {client_id} -refresh 0 -cn {client_name} -vm {instance}"'
        )
        self.log.info(f'Launch Auto-discovery command: {command}')

        proxy.execute_command(command)
        self.log.info('Auto-discovery launched')

    def __get_items_in_folder(self, user, folder_id=None, folder_path=None):
        """
        Get the ids and names of files and folders inside another folder

        Args:
            user (str)          --  UPN of user
            folder_id (str)     --  Id of folder
            folder_path (str)   --  Path to folder

        Returns:
            folder_id_list (list)   --  List of folder Ids
            file_id_list (list)     --  List of file Ids
            folder_name_list (list) --  List of folder names
            file_name_list (list)   --  List of file names

        """
        try:
            folder_id_list = list()
            file_id_list = list()
            folder_name_list = list()
            file_name_list = list()

            if folder_path:
                get_folder_children_endpoint = (
                    f'{self.graph_endpoint}'
                    f'{constants.MS_GET_USERS}'
                    f'{constants.MS_GET_FOLDER_CHILDREN_PATH.format(user, folder_path)}'
                    f'?$select=id,name,folder,file'
                )
            else:
                if not folder_id:
                    folder_id = self.get_folder_id_from_graph(user, 'root')
                get_folder_children_endpoint = (
                    f'{self.graph_endpoint}'
                    f'{constants.MS_GET_USERS}'
                    f'{constants.MS_GET_FOLDER_CHILDREN.format(user, folder_id)}'
                    f'?$select=id,name,folder,file'
                )
            self.log.info('Get folder children endpoint: %s', get_folder_children_endpoint)

            response = self.request(url=get_folder_children_endpoint, headers=self.headers)
            self.log.info('response:%s', response)
            for item in response.get('value', []):
                if 'folder' in item:
                    folder_id_list.append(item['id'])
                    folder_name_list.append(item['name'])
                if 'file' in item:
                    file_id_list.append(item['id'])
                    file_name_list.append(item['name'])

            while '@odata.nextLink' in response:
                self.log.info('@odata.nextLink:%s', response.get('@odata.nextLink'))
                response = self.request(url=response.get('@odata.nextLink'), headers=self.headers)
                self.log.info('response:%s', response)
                for item in response.get('value', []):
                    if 'folder' in item:
                        folder_id_list.append(item['id'])
                        folder_name_list.append(item['name'])
                    if 'file' in item:
                        file_id_list.append(item['id'])
                        file_name_list.append(item['name'])

            return folder_id_list, file_id_list, folder_name_list, file_name_list

        except Exception as excp:
            self.log.exception(
                'Exception occurred while fetching items from MS Graph.')
            raise CVCloudException(self.api_name, '107', str(excp))

    def get_all_onedrive_items(self, user_id, folder_path=None):
        """
        Gets all files and folders in OneDrive
        Not restricted to AutomationFolder

        Args:
            user_id (str)       --  email id of user
            folder_path (str)   --  path of current folder
                                    Required for recursion

        Returns:
            folder_hierarchy (dict):    Dictionary containing folder hierarchy
                                        Format:-
                                        { folder_name : [file_list],
                                                        [{folder1: [...], [...]},
                                                         {folder2: [...], [...]}]
                                        }

        """
        try:
            _, _, folder_names, file_names = self.__get_items_in_folder(
                user=user_id, folder_path=folder_path)

            folders = list()
            if folder_path is None:
                for folder in folder_names:
                    folder_dict = self.get_all_onedrive_items(user_id, folder)
                    folders.append(folder_dict)
                onedrive_folder_hierarchy = {'root': [file_names, folders]}
                self.log.info(f'OneDrive Folder Hierarchy: {onedrive_folder_hierarchy}')
                return onedrive_folder_hierarchy
            else:
                for folder in folder_names:
                    folder_dict = self.get_all_onedrive_items(user_id, f'{folder_path}/{folder}')
                    folders.append(folder_dict)
                folder_hierarchy = {folder_path.split('/')[-1]: [file_names, folders]}
                return folder_hierarchy

        except Exception as excp:
            self.log.exception(
                'Exception occurred while fetching file names from MS Graph.')
            raise CVCloudException(self.api_name, '107', str(excp))

    def create_folder(self, folder_name, user_id, location=None, parent_folder_id=None):
        """
        Method to create a folder on OneDrive at the given location

        Args:
            folder_name (str)       --  Name of the folder
            location (str)          --  Path from root to where folder has to be created
            user_id (str)           --  UPN of the user
            parent_folder_id (str)  --  Id of the parent folder

        Returns:
            folder_id (str)     -- ID of the created folder

        """
        try:
            if parent_folder_id:
                path = f'/{user_id}{constants.MS_CREATE_FOLDERS.format(parent_folder_id)}'
            else:
                path = constants.MS_GET_FOLDER_CHILDREN_PATH.format(user_id, location)
                if location == 'root' or location == '/':
                    path = f'/{user_id}{constants.MS_CREATE_FOLDER}'

            folder_endpoint = f'{self.graph_endpoint}{constants.MS_GET_USERS}{path}'
            self.log.info(f"folder_endpoint: {folder_endpoint}")
            self.headers['Content-Type'] = 'application/json'

            data = {
                "name": folder_name,
                "folder": {},
                "@microsoft.graph.conflictBehavior": "replace"
            }

            resp = self.request(method='POST', url=folder_endpoint, data=json.dumps(data), headers=self.headers)
            self.log.info('folder creation response: %s', resp)
            self.dbo.save_into_table(user_id, resp, constants.FOLDER_TABLE)
            folder_id = resp['id']
            return folder_id

        except Exception as excp:
            self.log.exception('exception occurred while creating folder on OneDrive')
            raise CVCloudException(self.api_name, '103', str(excp))

    def generate_onedrive_data(self,
                               folder_count,
                               folder_depth,
                               file_count,
                               user_id,
                               current_depth=1,
                               current_path='root'):
        """
        Method to generate OneDrive data with folder hierarchy and files

        Args:
            folder_count (int)  --  No of folders to be created inside a folder
            folder_depth (int)  --  How much hierarchy required for folders
            file_count (int)    --  No of files to be created per folder
            user_id (str)       --  UPN of user
            current_depth (int) --  Current Depth of folder hierarchy
                                    Required for implementing recursion
            current_path (str)  --  Current path of folder hierarchy
                                    Required for recursion

        """
        try:
            if current_depth > folder_depth:
                return
            else:
                if current_depth == 1:
                    self.create_files(no_of_docs=file_count, new_folder=False, user=user_id, folder_path='root')
                for count in range(folder_count):
                    folder_name = f'{"Sub" * (current_depth - 1)}Folder{count + 1}'
                    folder_id = self.create_folder(folder_name=folder_name, user_id=user_id, location=current_path)
                    self.create_files(no_of_docs=file_count, new_folder=False, user=user_id, folder_id=folder_id)
                    self.generate_onedrive_data(
                        folder_count=folder_count,
                        folder_depth=folder_depth,
                        file_count=file_count,
                        user_id=user_id,
                        current_depth=current_depth + 1,
                        current_path=folder_name if current_depth == 1 else f'{current_path}/{folder_name}')

        except Exception as excp:
            self.log.exception('exception occurred while generating data on OneDrive')
            raise CVCloudException(self.api_name, '103', str(excp))

    def delete_all_data_on_onedrive(self, user):
        """
        Deletes all data on OneDrive

        Args:
            user (str)  --  UPN of user whose data has to be deleted

        """
        try:
            folder_list, file_list, _, _ = self.__get_items_in_folder(user=user)

            for folder in folder_list:
                self.delete_folder(user_id=user, folder_id=folder)

            for file in file_list:
                self.delete_single_file(user_id=user, file_id=file)

        except Exception as excp:
            self.log.exception('exception occurred while deleting data on OneDrive')
            raise CVCloudException(self.api_name, '103', str(excp))

    def modify_file_content(self, user, file_name=None, file_id=None):
        """
        Modify the content of a file

        Args:
            user (str)      --  UPN of user
            file_name (str) --  Name of file to be modified
            file_id (str)   --  Id of file to be modified

        """
        try:
            if file_name:
                file_id = self.get_folder_id_from_graph(user_id=user, folder=file_name)

            if not file_id:
                raise Exception('Please provide either file name or file id')

            wiki_message = self.wiki.create_message_from_wiki()
            content = wiki_message['body'].encode('utf-8')

            file_endpoint = (
                f'{self.graph_endpoint}'
                f'{constants.MS_GET_USERS}'
                f'{constants.MS_UPDATE_FILE.format(user, file_id)}'
            )
            self.log.info('Update file endpoint: %s', file_endpoint)
            headers = self.headers.copy()
            headers['Content-Type'] = 'text/plain'
            resp = self.request(
                url=file_endpoint, method='PUT', data=content, headers=headers)
            self.log.info('file updation response: %s', resp)

        except Exception as excp:
            self.log.exception(
                'Exception occurred while modifying content of file')
            raise CVCloudException(self.api_name, '107', str(excp))

    def rename_file_or_folder(self, current_name, new_name, user, location=None):
        """
        Rename a file or folder

        Args:
            current_name (str)          --  Current name of the item
            new_name (str)              --  New name to be given
            user (str)                  --  UPN of the user
            location (str)              --  Folder where the item is located

        """
        try:
            if location:
                source_folder_list = deque(location.split('/'))
                parent_folder_id = None
                for i in range(len(source_folder_list)):
                    folder_name = source_folder_list.popleft()
                    parent_folder_id = self.get_folder_id_from_graph(user_id=user,
                                                                     folder=folder_name,
                                                                     parent_folder_id=parent_folder_id)
                item_id = self.get_folder_id_from_graph(user_id=user,
                                                        folder=current_name,
                                                        parent_folder_id=parent_folder_id)
            else:
                item_id = self.get_folder_id_from_graph(user_id=user, folder=current_name)

            rename_endpoint = (
                f'{self.graph_endpoint}'
                f'{constants.MS_GET_USERS}'
                f'{constants.MS_UPDATE_DRIVEITEM.format(user, item_id)}'
            )
            data = {
                "name": new_name
            }
            resp = self.request(method='PATCH',
                                url=rename_endpoint,
                                data=json.dumps(data),
                                headers=self.headers)
            self.log.info('rename item response: %s', resp)
            if resp.get('name') != new_name:
                raise Exception('Error Occurred: New name does not match with given name')
            else:
                self.log.info(f'Successfully renamed item from {current_name} to {new_name}')

        except Exception as excp:
            self.log.exception(
                'Exception occurred while renaming file/folder')
            raise CVCloudException(self.api_name, '107', str(excp))

    def move_file_or_folder(self, item_name, source, destination, user):
        """
        Move a file or folder

        Args:
            item_name (str)     --  Name of the item
            source (str)        --  Location to be moved from
            destination (str)   --  Location to be moved to
            user (str)          --  UPN of the user

        """
        try:
            source_folder_list = deque(source.split('/'))
            parent_folder_id = None
            for i in range(len(source_folder_list)):
                folder_name = source_folder_list.popleft()
                parent_folder_id = self.get_folder_id_from_graph(user_id=user,
                                                                 folder=folder_name,
                                                                 parent_folder_id=parent_folder_id)
            item_id = self.get_folder_id_from_graph(user_id=user,
                                                    folder=item_name,
                                                    parent_folder_id=parent_folder_id)

            destination_folder_list = deque(destination.split('/'))
            new_parent_folder_id = None
            for i in range(len(destination_folder_list)):
                folder_name = destination_folder_list.popleft()
                new_parent_folder_id = self.get_folder_id_from_graph(user_id=user,
                                                                     folder=folder_name,
                                                                     parent_folder_id=new_parent_folder_id)

            move_endpoint = (
                f'{self.graph_endpoint}'
                f'{constants.MS_GET_USERS}'
                f'{constants.MS_UPDATE_DRIVEITEM.format(user, item_id)}'
            )
            data = {
                "parentReference": {
                    "id": new_parent_folder_id
                }
            }
            resp = self.request(method='PATCH',
                                url=move_endpoint,
                                data=json.dumps(data),
                                headers=self.headers)
            self.log.info('move item response: %s', resp)
            if resp.get('parentReference', None).get('id', '') != new_parent_folder_id:
                raise Exception('Error Occurred: New location does not match with given location')
            else:
                self.log.info(f'Successfully moved the item')
        except Exception as excp:
            self.log.exception(
                'Exception occurred while moving file/folder')
            raise CVCloudException(self.api_name, '107', str(excp))

    def get_folder_structure_on_disk(self, user_id, replace_root=None):
        """ Fetch structure of user's data after disk-restore
            if file does not have any extension it is considered as a folder

            Args:
                user_id (str): User's SMTP address
                replace_root (str): Replace User level folder with given name if not None

            Returns:
                folder_structure (dict) : Dictionary object containing relative paths to folders
                                          mapped to list of files they contain
        """

        path_on_disk = f'{constants.DESTINATION_TO_DISK}\\{user_id}\\{constants.MY_DRIVE_FOLDER}'
        self.log.info(f'Path on proxy client: {path_on_disk}')

        proxy_client = Machine(self.tc_object.instance.proxy_client, self.tc_object.commcell)

        if not proxy_client.check_directory_exists(path_on_disk):
            raise CVCloudException(self.api_name, '107', (f'Path: [{path_on_disk}] does not exist on client '
                                                          f'{self.tc_object.instance.proxy_client}'))

        data = proxy_client.get_items_list(path_on_disk)

        file_regex = re.compile(r"(\.[A-Za-z0-9]*)$")
        folder_structure = {}

        for entity in data:
            if file_regex.search(entity):
                entity = entity.replace(path_on_disk, '')
                entity = entity.replace("\\", "/")
                folder_path, file = entity.rsplit('/', 1)
                folder = f'{user_id}{folder_path}'

                # Replace user level folder with given name
                if replace_root:
                    folder = f'{replace_root}{folder_path}'

                # Add content to folder structure
                if not folder_structure.get(folder):
                    folder_structure[folder] = []
                folder_structure[folder].append(file)

        return folder_structure

    def get_user_details(self, user):
        """
            Fetches the details of a user

            Args:
                user (str):    User SMTP address

            Returns:
                user details (dict)
        """
        try:
            get_user_details_endpoint = (
                f'{self.graph_endpoint}'
                f'{constants.MS_GET_USERS}'
                f'/{user}'
            )
            self.log.info('Get user details endpoint: %s', get_user_details_endpoint)
            response = self.request(url=get_user_details_endpoint, method='GET', headers=self.headers)
            self.log.info('response:%s', response)
            return response

        except Exception as exception:
            self.log.exception('Exception while fetching user details')
            raise CVCloudException(self.api_name, '101', str(exception))

    def create_onenote_notebook(self, user_id, notebook_name):
        """
            Method to create a notebook in user's account

            Args:
                user_id (str):    User SMTP address
                notebook_name (str):    Unique notebook name

            Returns:
                nodebook_id (str)
        """
        try:
            notebook_endpoint = (f'{self.graph_endpoint}'
                                 f'{constants.MS_GET_USERS}'
                                 f'{constants.MS_CREATE_NOTEBOOK.format(user_id)}')
            self.log.info(f"notebook_endpoint: {notebook_endpoint}")
            self.headers['Content-Type'] = 'application/json'

            data = {
                "displayName": notebook_name
            }

            resp = self.request(method='POST', url=notebook_endpoint, data=json.dumps(data), headers=self.headers)
            self.log.info('notebook creation response: %s', resp)

            notebook_id = resp['id']
            return notebook_id

        except Exception as exception:
            self.log.exception('exception occurred while creating notebook')
            raise CVCloudException(self.api_name, '103', str(exception))

    def get_onenote_notebook_id(self, user_id, notebook_name):
        """
            Method to get a notebook's id in user's account

            Args:
                user_id (str):    User SMTP address
                notebook_name (str):    Unique notebook name
            Returns:
                nodebook_id (str)
        """
        try:
            notebook_endpoint = (f'{self.graph_endpoint}'
                                 f'{constants.MS_GET_USERS}'
                                 f'{constants.MS_CREATE_NOTEBOOK.format(user_id)}')
            self.log.info(f"notebook_endpoint: {notebook_endpoint}")
            self.headers['Content-Type'] = 'application/json'

            resp = self.request(method='GET', url=notebook_endpoint, headers=self.headers)
            for notebook in resp['value']:
                if notebook_name == notebook['displayName']:
                    return notebook['id']

            while resp.get('@odata.nextLink'):
                resp = self.request(method='GET', url=notebook_endpoint, headers=self.headers)
                for notebook in resp['value']:
                    if notebook_name == notebook['displayName']:
                        return notebook['id']

            raise CVCloudException(self.api_name, '107', f'No notebook found with name: {notebook_name}')

        except Exception as exception:
            self.log.exception('exception occurred while fetching notebook id')
            raise CVCloudException(self.api_name, '103', str(exception))

    def create_onenote_section(self, user_id, section_name, notebook_id=None, section_group_id=None):
        """
            Method to create section in a notebook or section group

            Args:
                user_id (str):    User SMTP address
                notebook_id (str):  Notebook ID under which section is to be created
                section_name (str):    Unique section name
                section_group_id (str): Section Group ID under which section is to created
            Returns:
                section_id (str)
        """
        try:
            if notebook_id:
                section_endpoint = (f'{self.graph_endpoint}'
                                    f'{constants.MS_GET_USERS}'
                                    f'{constants.MS_CREATE_SECTION.format(user_id, notebook_id)}')
            elif section_group_id:
                section_endpoint = (f'{self.graph_endpoint}'
                                    f'{constants.MS_GET_USERS}'
                                    f'{constants.MS_CREATE_SECTION_IN_SECTION_GROUP.format(user_id, section_group_id)}')
            else:
                raise Exception('Either provide Notebook-ID or Section-Group-ID to create a section')
            self.log.info(f"section_endpoint: {section_endpoint}")
            self.headers['Content-Type'] = 'application/json'

            data = {
                "displayName": section_name
            }

            resp = self.request(method='POST', url=section_endpoint, data=json.dumps(data), headers=self.headers)
            self.log.info('section creation response: %s', resp)

            section_id = resp['id']
            return section_id
        except Exception as exception:
            self.log.exception('exception occurred while creating section')
            raise CVCloudException(self.api_name, '103', str(exception))

    def get_onenote_section_id(self, user_id, notebook_id, section_name):
        """
            Method to get a section's id in user's account

            Args:
                user_id (str):    User SMTP address
                notebook_id (str):  Notebook ID under which section is present
                section_name (str):    Unique section name
            Returns:
                section_id (str)
        """
        try:
            section_endpoint = (f'{self.graph_endpoint}'
                                f'{constants.MS_GET_USERS}'
                                f'{constants.MS_CREATE_SECTION.format(user_id, notebook_id)}')
            self.log.info(f"section_endpoint: {section_endpoint}")

            resp = self.request(method='GET', url=section_endpoint, headers=self.headers)
            for section in resp['value']:
                if section_name == section['displayName']:
                    return section['id']

            while resp.get('@odata.nextLink'):
                resp = self.request(method='GET', url=section_endpoint, headers=self.headers)
                for section in resp['value']:
                    if section_name == section['displayName']:
                        return section['id']

            raise CVCloudException(self.api_name, '107', f'No section found with name: {section_name}')

        except Exception as exception:
            self.log.exception('exception occurred while fetching section id')
            raise CVCloudException(self.api_name, '103', str(exception))

    def create_onenote_page(self, user_id, section_id, page_name, page_body):
        """
            Method to create a page

            Args:
                user_id (str):    User SMTP address
                section_id (str):  Section ID under which page is to be created
                page_body (str):    Content for page
                page_name (str):    Unique page name

            Returns:
                page_id (str)
        """
        try:
            page_endpoint = (f'{self.graph_endpoint}'
                             f'{constants.MS_GET_USERS}'
                             f'{constants.MS_CREATE_PAGE.format(user_id, section_id)}')
            self.log.info(f"page_endpoint: {page_endpoint}")
            self.headers['Content-Type'] = 'application/xhtml+xml'

            data = """
                <!DOCTYPE html>
                    <html>
                      <head>
                        <title>{0}</title>
                      </head>
                      <body>
                        <p>{1}</p>
                      </body>
                    </html>
            """.format(page_name, page_body)

            resp = self.request(method='POST', url=page_endpoint, data=json.dumps(data), headers=self.headers)
            self.log.info('page creation response: %s', resp)

            page_id = resp['id']
            return page_id
        except Exception as exception:
            self.log.exception('exception occurred while creating section')
            raise CVCloudException(self.api_name, '103', str(exception))

    def create_onenote_section_group(self, user_id, section_group_name, notebook_id=None, section_group_id=None):
        """
            Creates a section group in notebook

            Args:
                user_id (str):    User SMTP address
                notebook_id (str):  Notebook ID under which section-group is to be created
                section_group_id (str)
                section_group_name (str):    Unique section group name

            Returns:
                section_group_id (str)
        """
        try:
            if notebook_id:
                section_group_endpoint = (f'{self.graph_endpoint}'
                                          f'{constants.MS_GET_USERS}'
                                          f'{constants.MS_CREATE_SECTION_GROUP.format(user_id, notebook_id)}')
            elif section_group_id:
                section_group_endpoint = (f'{self.graph_endpoint}'
                                          f'{constants.MS_GET_USERS}'
                                          f'{constants.MS_CREATE_SUB_SECTION_GROUP.format(user_id, section_group_id)}')
            else:
                raise CVCloudException(self.api_name, '107',
                                       'Either provide Notebook-ID or Section-Group-ID to create a section group')
            self.log.info(f"section_group_endpoint: {section_group_endpoint}")
            self.headers['Content-Type'] = 'application/json'

            data = {
                "displayName": section_group_name
            }

            resp = self.request(method='POST', url=section_group_endpoint, data=json.dumps(data), headers=self.headers)
            self.log.info('section group creation response: %s', resp)

            section_group_id = resp['id']
            return section_group_id
        except Exception as exception:
            self.log.exception('exception occurred while creating section group')
            raise CVCloudException(self.api_name, '103', str(exception))

    def get_onenote_section_group_id(self, user_id, notebook_id, section_group_name):
        """
            Method to get the id of a section group

            Args:
                user_id (str):    User SMTP address
                notebook_id (str):  Notebook ID under which section is present
                section_group_name (str):   Unique section group name
            Returns:
                section_id (str)
        """
        try:
            section_group_endpoint = (f'{self.graph_endpoint}'
                                      f'{constants.MS_GET_USERS}'
                                      f'{constants.MS_CREATE_SECTION_GROUP.format(user_id, notebook_id)}')
            self.log.info(f"section_group_endpoint: {section_group_endpoint}")

            resp = self.request(method='GET', url=section_group_endpoint, headers=self.headers)
            for section_group in resp['value']:
                if section_group_name == section_group['displayName']:
                    return section_group['id']

            while resp.get('@odata.nextLink'):
                resp = self.request(method='GET', url=section_group_endpoint, headers=self.headers)
                for section_group in resp['value']:
                    if section_group_name == section_group['displayName']:
                        return section_group['id']

            raise CVCloudException(self.api_name, '107', f'No section found with name: {section_group_name}')

        except Exception as exception:
            self.log.exception('exception occurred while fetching section group id')
            raise CVCloudException(self.api_name, '103', str(exception))

    def generate_onenote_data(self, user_id, notebook_count, section_group_count,
                              section_group_depth, section_count, page_count):
        """
            Generates OneNote data on user's account

            Args:
                user_id (str):    User SMTP address
                notebook_count (int):  Number of notebooks to be created
                section_group_count (int): Number of section groups to be created in a notebook/section group
                section_group_depth (int):  Depth of section groups
                section_count (int):    Number of sections to be created under a section_group/notebook
                page_count (int):    Number of pages to be created under one section
        """

        def create_onenote_pages(page_section_id):
            for page_val in range(1, page_count + 1):
                page_name = page_alias.format(page_val)
                page = self.wiki.create_message_from_wiki()
                self.create_onenote_page(user_id, page_section_id, page_name, page['body'])

        def create_onenote_sections(section_section_group_id=None, section_notebook_id=None):
            for section_val in range(1, section_count + 1):
                section_name = section_alias.format(section_val)
                if section_section_group_id:
                    section_id = self.create_onenote_section(
                        user_id, section_name, section_group_id=section_section_group_id)
                elif section_notebook_id:
                    section_id = self.create_onenote_section(user_id, section_name, notebook_id=section_notebook_id)
                else:
                    raise Exception('Inner function did not receive notebook-id/section-group-id as params')
                create_onenote_pages(section_id)

        def generate_onenote_section_data(group_count,
                                          depth,
                                          group_id,
                                          section_notebook_id,
                                          current_depth=1):

            if current_depth > depth:
                return
            else:
                if current_depth == 1:
                    create_onenote_sections(section_notebook_id=section_notebook_id)

                for count in range(group_count):
                    section_group_name = section_group_alias.format(count + 1)

                    if group_id is None:
                        section_group_id = self.create_onenote_section_group(
                            user_id, section_group_name, notebook_id=section_notebook_id)
                    else:
                        section_group_id = self.create_onenote_section_group(user_id, section_group_name,
                                                                             section_group_id=group_id)

                    create_onenote_sections(section_section_group_id=section_group_id)

                    generate_onenote_section_data(
                        group_count=group_count,
                        depth=depth,
                        group_id=section_group_id,
                        section_notebook_id=section_notebook_id,
                        current_depth=current_depth + 1)

        try:
            self.log.info(f'Creating {page_count} pages under {section_count} sections '
                          f'in {section_group_count} section groups over {notebook_count} notebooks')

            notebook_alias = 'Notebook_{}'
            section_alias = 'Section_{}'
            page_alias = 'Page_{}'
            section_group_alias = 'Section_Group_{}'

            for notebook_val in range(1, notebook_count + 1):
                notebook_name = notebook_alias.format(notebook_val)
                notebook_id = self.create_onenote_notebook(user_id, notebook_name)

                generate_onenote_section_data(section_group_count,
                                              section_group_depth,
                                              group_id=None,
                                              section_notebook_id=notebook_id)

            self.log.info(f'OneNote data generated successfully')

        except Exception as exception:
            self.log.exception('exception occurred while generating onenote data')
            raise CVCloudException(self.api_name, '103', str(exception))

    def list_onenote_items(self, user_id):
        """
            Get all sections' relative paths and content belonging to a particular user

            Args:
                user_id (str):    User SMTP address

            Returns:
                section_relative_paths (dict)
        """
        try:
            sections_endpoint = (f'{self.graph_endpoint}'
                                 f'{constants.MS_GET_USERS}'
                                 f'{constants.MS_GET_ALL_SECTIONS.format(user_id)}')
            self.log.info(f"sections_endpoint: {sections_endpoint}")

            section_relative_paths = {}

            resp = self.request(method='GET', url=sections_endpoint, headers=self.headers)
            for section in resp['value']:
                relative_path = section['links']['oneNoteClientUrl']['href'].split('Notebooks/')[1]
                section_id = section['id']
                section_relative_paths[relative_path] = self.get_page_content(user_id, section_id)

            while resp.get('@odata.nextLink'):
                resp = self.request(method='GET', url=sections_endpoint, headers=self.headers)
                sections_endpoint = resp.get('@odata.nextLink')
                for section in resp['value']:
                    relative_path = section['links']['oneNoteClientUrl']['href'].split('Notebooks/')[1]
                    section_id = section['id']
                    section_relative_paths[relative_path] = self.get_page_content(user_id, section_id)

            return section_relative_paths

        except Exception as exception:
            self.log.exception('exception occurred while fetching section id')
            raise CVCloudException(self.api_name, '103', str(exception))

    def get_page_content(self, user_id, section_id):
        """
            Gets content of all the pages in a section

            Args:
                user_id (str):    User SMTP address
                section_id (str):   Section ID
            Returns:
                page_content (dict):  page content dictionary
        """
        try:
            page_content = {}
            page_endpoint = (f'{self.graph_endpoint}'
                             f'{constants.MS_GET_USERS}'
                             f'{constants.MS_CREATE_PAGE.format(user_id, section_id)}')
            self.log.info(f"page_endpoint: {page_endpoint}")

            resp = self.request(method='GET', url=page_endpoint, headers=self.headers)
            for page in resp['value']:
                page_id = page['id']
                page_name = page['title']
                page_content_endpoint = (f'{self.graph_endpoint}'
                                         f'{constants.MS_GET_USERS}'
                                         f'{constants.MS_GET_PAGE_CONTENT.format(user_id, page_id)}')
                page_content_resp = self.request(method='GET', url=page_content_endpoint, headers=self.headers)
                page_content[page_name] = page_content_resp.text

            while resp.get('@odata.nextLink'):
                resp = self.request(method='GET', url=page_endpoint, headers=self.headers)
                for page in resp['value']:
                    page_id = page['id']
                    page_name = page['title']
                    page_content_endpoint = (f'{self.graph_endpoint}'
                                             f'{constants.MS_GET_USERS}'
                                             f'{constants.MS_GET_PAGE_CONTENT.format(user_id, page_id)}')
                    page_content_resp = self.request(method='GET', url=page_content_endpoint, headers=self.headers)
                    page_content[page_name] = page_content_resp.text

            return page_content

        except Exception as exception:
            self.log.exception('exception occurred while fetching page content')
            raise CVCloudException(self.api_name, '103', str(exception))

    def compare_onenote_restore_metadata(self, user_id, metadata):
        """ Fetches and compares new OneNote metadata with metadata before restore

            Args:
                user_id (str): User's SMTP address

                metadata (dict): Dictionary of sections' relative paths and content belonging to a particular user
        """
        new_metadata = self.list_onenote_items(user_id)

        if metadata != new_metadata:
            raise CVCloudException(self.api_name, '107',
                                   f'Restore metadata is different from old data\n'
                                   f'old data: {metadata}\n'
                                   f'new data: {new_metadata}')

        self.log.info('Restore metadata data matched successfully')
