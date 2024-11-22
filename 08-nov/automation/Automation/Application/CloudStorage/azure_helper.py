# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing Azure Blob Storage operations

AzureHelper is the only class defined in this file.

AzureHelper: Helper class to perform Azure Blob Storage operations

AzureHelper :
    __init__()                           --   initializes Azure helper object

    create_container_azure()             --   creates a container in Azure blob storage

    upload_file_azure()                  --   uploads the specified file to Azure blob storage

    download_file_azure()                --   downloads the specified file from Azure blob storage

    delete_file_azure()                  --   deletes the specified file from Azure blob storage

    create_dir_download_file_azure()     --   checks if folder exists locally. If not,
                                                creates a directory and downloads a file to it

    delete_contents_azure()              --   deletes all the contents under the specified paths
                                                from Azure blob storage

    delete_container_azure()             --   deletes the specified container
                                                from Azure blob storage

    download_container_azure()           --   downloads the specified container with all
                                                it's contents from Azure blob storage

    download_contents_azure()            --   downloads all the contents under the specified paths
                                                from the Azure blob storage

    recur()                              --   recursively traverses through the subfolders
                                             and downloads the blobs

   fetch_file_metadata()                -- To fetch file meta data from Azure Blob Storage

   upload_folder_azure()                --To upload all the files present in the given folder

AzureFileShareHelper:
    __init__()                           -- initializes AzureFileShareHelper object

    delete_file_share()                 -- deletes the specified file share from Azure file share storage

    download_file()                     --downloads a file from file share storage

    download_dir()                      --downloads a directory from file share storage

    download_file_share()               --downloads a whole bucket(file share) from file share storage

    azure_file_share_cleanup()          --To remove temp directories created
                                        during azure file share helper object initialization

"""
from datetime import datetime
import mimetypes
import os
from pathlib import Path
import azure.common.exceptions
from azure.storage.blob import BlobServiceClient
from azure.storage.fileshare import ShareServiceClient
from azure.storage.filedatalake import DataLakeServiceClient
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils import logger
from dynamicindex.utils import constants as cs


class AzureHelper(object):
    """Helper class to perform azure blob storage operations"""

    def __init__(self, account_name=None, access_key=None, connect_string=None):
        """Initializes azure helper object
        Args:

            account name (str)   --         account name to the azure storage resorce
                                            default : None

            access_key (str)      --        access key to the azure storage resorce
                                            default : None

            connect_string (str)   --       connection string to the azure storage resorce
                                            default : None
        """
        self.automation_directory = constants.AUTOMATION_DIRECTORY
        self.log = logger.get_log()
        self.machine = Machine()
        self.time_stamp = str(int(datetime.timestamp(datetime.now())))
        self.temp_folder_name = f"AzureTemp_{self.time_stamp}"
        self.common_dir_path = self.machine.join_path(
            constants.TEMP_DIR, self.temp_folder_name)
        self.machine.create_directory(self.common_dir_path,
                                      force_create=True)
        self.account_name = account_name
        self.session = None
        try:
            if access_key and account_name:
                connect_string = \
                    f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={access_key};" \
                    f"EndpointSuffix=core.windows.net"
            elif not connect_string:
                raise Exception("Please provide connect string or account Name and access key")
            self.session = BlobServiceClient.from_connection_string(connect_string)
        except Exception as error:
            self.log.error(
                "The specified account name or account key is invalid")
            self.log.error(error)
            raise error

    def create_container_azure(self, container_name):
        """creates a container to Azure cloud
        Args :

            container_name    (str)     --       name of the new bucket which is to be created

        Returns :
            None

        Raises :
            Exception :
                if the container name is invalid or the container with specified name already exists

        """
        try:
            self.session.create_container(container_name)
        except Exception as error:
            self.log.error(
                "container name is invalid or a container already exists with that name")
            self.log.error(error)
            raise error

    def upload_file_azure(self,
                          container_name,
                          blobname,
                          localfilename):
        """uploads a file to Azure cloud
        Args :

            container_name    (str)    --       name of the bucket to which the file has to be
            uploaded

            blobname          (str)    --       name of the file to be created on the cloud

            localfilename     (str)    --       name of the file in the current directory on the
            local machine

        Returns :
            None

        Raises :
            AzureMissingResourceHttpError :
                If the specified container or the file on the local machine doesn't exist

        """
        try:
            blob_client = self.session.get_blob_client(container_name, blobname)
            with open(localfilename, "rb") as data:
                blob_client.upload_blob(data)

        except azure.common.AzureMissingResourceHttpError as error:
            self.log.error(
                "The specified container or the file on the local machine doesn't exist")
            self.log.error(error)
            raise error

    def download_file_azure(self,
                            container_name,
                            blobname,
                            directory_path):
        """downloads a file from Azure cloud
        Args :

            container_name         (str)        --     name of the azure blob container

            blobname               (str)        --     name of the blob that has to be downloaded

            directory_path          (str)       --     location to download the blob
            where the content has to be downloaded

        Returns :
            None

        Raises :
            AzureMissingResourceHttpError :
                If the specified container or the file does not exist on the cloud

        """
        try:
            file_content = self.session.get_blob_client(container_name, blobname).download_blob().readall()
            head, tail = os.path.split(f"{blobname}")
            download_path = os.path.join(directory_path, tail)

            with open(download_path, "wb") as file:
                file.write(file_content)
        except azure.common.AzureMissingResourceHttpError as error:
            self.log.error(
                "The specified container or the file does not exist on the cloud")
            self.log.error(error)
            raise error

    def delete_file_azure(self, container_name, blobname):
        """deletes a file from Azure cloud
        Args :

            container_name         (str)        --     name of the azure blob container

            blobname               (str)        --     name of the blob that has to be deleted

        Returns :
            None

        Raises :
            AzureMissingResourceHttpError :
                If the specified container or the file does not exist on the cloud

        """
        try:
            self.session.get_blob_client(container_name, blobname).delete_blob()
        except azure.common.AzureMissingResourceHttpError as error:
            self.log.error(
                "The specified container or the file does not exist on the cloud")
            self.log.error(error)
            raise error

    def create_dir_download_file_azure(self, container_name, blobname):
        """checks if folder exists locally. If not, creates a directory and downloads a file to it
        Args :
            container_name (str)     --       name of the container

            blobname       (str)     --       name of the azure blob

        Returns :
            None

        Raises :
            AzureMissingResourceHttpError :
                If the specified container or the file does not exist on the cloud

        """
        if str(blobname)[-1] == "/":
            self.machine.create_directory(self.machine.join_path(os.getcwd(), blobname[:-1]))
        else:
            head, tail = os.path.split(f"{blobname}")
            try:
                if not self.machine.check_directory_exists(self.machine.join_path(os.getcwd(), head)):
                    self.machine.create_directory(self.machine.join_path(os.getcwd(), head))
                data = self.session.get_blob_client(container_name, blobname).download_blob().readall()
                with open(self.machine.join_path(os.getcwd(), head, tail), "wb") as file:
                    file.write(data)
            except azure.common.AzureMissingResourceHttpError as error:
                self.log.error(
                    "The specified container does not exist on the cloud")
                self.log.error(error)
                raise error

    def delete_contents_azure(self, content):
        """deletes the specified contents from Azure cloud
        Args :
            content        (list)    --       Part of the subclient content which has to be
            deleted from the cloud

        Returns :
            None

        Raises :
            AzureMissingResourceHttpError :
                if the specified content does not exist on the cloud

        """
        for item in content:
            windows_path = Path(item)
            container_name = Path(item).parts[1]
            if (len(windows_path.parts)) == 2:
                self.session.delete_container(container_name)
                continue
            path_to_file = ("/".join(item.strip("/").split('/')[1:]))
            generator = self.session.get_container_client(container_name).list_blobs()
            blob_list = []
            for i in generator:
                blob_list.append(i.name)
            try:
                if path_to_file in blob_list:
                    self.session.get_blob_client(container_name, path_to_file).delete_blob()
                else:
                    generator = self.session.get_container_client(container_name).list_blobs(
                        self.machine.join_path(path_to_file, '/'))
                    for blob in generator:
                        self.session.get_blob_client(container_name, blob.name).delete_blob()

            except azure.common.AzureMissingResourceHttpError as error:
                self.log.error(
                    "The specified contents does not exist on the cloud")
                self.log.error(error)
                raise error

    def delete_container_azure(self, container_name):
        """deletes a container from Azure cloud
        Args :

            container_name    (str)     --       name of the container which has to be deleted

        Returns :
            None

        Raises :
            AzureMissingResourceHttpError :
                if the specified container does not exist on the cloud

        """
        try:
            self.log.info(f"Deleting the bucket {container_name}")
            self.session.delete_container(container_name)
        except azure.common.AzureMissingResourceHttpError as error:
            self.log.error(
                "The specified container does not exist on the cloud")
            self.log.error(error)
            raise error

    def download_container_azure(self, container_name, dir_name):
        """downloads a container from Azure cloud
        Args :

            container_name (str)   --   Name of the azure blob container which has to be downloaded

            dir_name (str)         --   Name of the directory to which the container needs to be downloaded

        Returns :
            None

        Raises :
            AzureMissingResourceHttpError :
                If the specified container does not exist on the cloud

        """
        container_client = self.session.get_container_client(container_name)
        generator = container_client.list_blobs()
        local_path = self.machine.join_path(
            self.common_dir_path, dir_name)
        os.mkdir(local_path)
        os.chdir(local_path)
        try:
            # code below lists all the blobs in the container and
            # downloads them one after another
            for blob in generator:
                # check if the path contains a folder structure, create the folder structure
                if "/" in f"{blob.name}":
                    # extract the folder path and check if that folder exists locally,
                    # and if not create it
                    self.create_dir_download_file_azure(container_name, blob.name)
                else:
                    try:
                        data = self.session.get_blob_client(container_name, blob.name).download_blob().readall()
                        with open(blob.name, "wb") as file:
                            file.write(data)
                    except azure.common.AzureMissingResourceHttpError as error:
                        self.log.error(
                            "The specified container does not exist on the cloud")
                        self.log.error(error)
                        raise error
            self.log.info("Downloaded container from cloud successfully.")
        finally:
            os.chdir(self.automation_directory)

    def download_contents_azure(self, content, dir_name, oop_flag):
        """downloads the specified contents from Azure cloud
        Args :
            content       (list)     --      Part of the subclient content which has to be
            downloaded from the cloud

            dir_name      (str)      --      Name of the folder to which the specified contents
            are to be downloaded

            oop_flag      (bool)     --      flag to determine if it's an in place restore
            or an out of place restore

        Returns :
            None

        Raises :
            AzureMissingResourceHttpError :
                If the specified content does not exist on the cloud

        """
        if oop_flag is True:
            container_name = content.replace("/", "")
            self.download_container_azure(container_name, dir_name)
            os.chdir(str(self.automation_directory))
        else:
            os.chdir(self.common_dir_path)
            for item in content:
                try:
                    path_to_file = ("/".join(item.strip("/").split('/')[1:]))
                    container_name = Path(item).parts[1]
                    generator = self.session.get_container_client(container_name).list_blobs()
                    blob_list = []
                    for j in generator:
                        blob_list.append(j.name)
                    if path_to_file == "":
                        self.download_container_azure(container_name, dir_name)
                        os.chdir(self.automation_directory)
                    elif path_to_file in blob_list:
                        if os.path.exists(dir_name) is False:
                            os.mkdir(dir_name)
                        os.chdir(dir_name)
                        self.create_dir_download_file_azure(container_name, path_to_file)
                    else:
                        generator = self.session.get_container_client(container_name).list_blobs(
                            prefix=self.machine.join_path(path_to_file, '/'))
                        if os.path.exists(dir_name) is False:
                            os.mkdir(dir_name)
                        os.chdir(dir_name)
                        # code below lists all the blobs in the container and downloads
                        # them one after another
                        for blob in generator:
                            # check if the path contains a folder structure,
                            # create the folder structure
                            if "/" in f"{blob.name}":
                                # extract the folder path and check if that folder exists locally,
                                # and if not create it
                                head, tail = os.path.split(
                                    f"{blob.name}")
                                if tail:
                                    self.create_dir_download_file_azure(container_name, blob.name)
                                else:
                                    self.recur(container_name, blob.name)
                            else:
                                try:
                                    data = self.session.get_blob_client(container_name,
                                                                        blob.name).download_blob().readall()
                                    with open(blob.name, "wb") as file:
                                        file.write(data)
                                except azure.common.AzureMissingResourceHttpError as error:
                                    self.log.error(
                                        "The specified contents does not exist on the cloud")
                                    self.log.error(error)
                                    raise error
                finally:
                    os.chdir(self.automation_directory)

    def recur(self, container_name, blobname):
        """recursively traverses through the subfolders and downloads the blobs
        Args :
            container_name (str)       --     name of the azure container

            blobname       (str)       --     name of the azure blob

        Returns :
            None

        Raises :
            AzureMissingResourceHttpError :
                If the specified container or object does not exist on the cloud

        """
        generator = self.session.get_container_client(container=container_name).list_blobs(blobname)
        for i in generator:
            head, tail = os.path.split(f"{i.name}")
            if tail:
                self.create_dir_download_file_azure(
                    container_name, i.name)
            else:
                self.recur(container_name, i.name)

    def fetch_file_metadata(self, container_name):
        """
        Fetch the properties meta data for all the file objects in the azure blob container
        Args:

            container_name (str)        : Name of the container to fetch data from

        Returns:
            list                     :  Returns a list of metadata list per object in the blob storage

            Example -
            [{'PATH': 'AZURE\\10364200796756\\PIIFiles\\476_1644340532752\\512\\Lindsey good
            1621204276-3251\\Chester McCormick window 3259.txt', 'PARENT_DIR':
            '10364200796756\\PIIFiles\\476_1644340532752\\512\\Lindsey good 1621204276-3251', 'NAME': 'Chester
            McCormick window 3259.txt', 'FILE_SIZE': 28286, 'MIME_TYPE': 'text/plain', 'MODIFIED_TIME': 'February 08,
            2022 12:16:51 PM', 'CREATED_TIME': 'February 08, 2022 12:16:51 PM', 'ACCESS_TIME': 'February 08,
            2022 12:16:51 PM', 'FILE_OWNER': 'dummy_user', 'PARENT_DIR_PERMISSION': '', 'FILE_PERMISSION': '',
            'FILE_PERMISSION_READABLE': '', 'IS_DIR': 0}, {...}]
        """
        assert container_name not in self.session.list_containers(), "Container does not exist"
        meta_data = list()
        dir_cnt = 0
        for blob in self.session.get_container_client(container_name).list_blobs():
            temp_dict = {}
            temp_dict[cs.FSO_METADATA_FIELD_PATH] = file_path = blob.name.replace('/', '\\')
            file_string_split = file_path.rsplit('\\', 1)
            temp_dict[cs.FSO_METADATA_FIELD_PARENT_DIR] = file_string_split[0]
            temp_dict[cs.FSO_METADATA_FIELD_NAME] = file_string_split[1]
            temp_dict[cs.FSO_METADATA_FIELD_FILE_SIZE] = blob.size
            mime_type, encoding = mimetypes.guess_type(temp_dict[cs.FSO_METADATA_FIELD_NAME])
            if not mime_type:
                mime_type = 'application/octet-stream'
            temp_dict[cs.FSO_METADATA_FIELD_MIME_TYPE] = mime_type
            modified_time_str = datetime.strftime(blob.last_modified.astimezone(),
                                                  "%B %d, %Y %r")
            temp_dict[cs.FSO_METADATA_FIELD_MODIFIED_TIME] = modified_time_str
            temp_dict[cs.FSO_METADATA_FIELD_CREATED_TIME] = datetime.strftime(blob.creation_time.astimezone(),
                                                                              "%B %d, %Y %r")
            temp_dict[cs.FSO_METADATA_FIELD_ACCESS_TIME] = modified_time_str
            temp_dict[cs.FSO_METADATA_FIELD_FILE_OWNER] = self.account_name
            temp_dict[cs.FSO_METADATA_FIELD_PARENT_DIR_PERMISSION] = ""
            temp_dict[cs.FSO_METADATA_FIELD_FILE_PERMISSION] = ""
            temp_dict[cs.FSO_METADATA_FIELD_FILE_PERMISSION_READABLE] = ""
            temp_dict[cs.FSO_METADATA_FIELD_IS_DIR] = 0
            temp_dict[cs.FSO_METADATA_FIELD_FILE_TYPE] = file_string_split[1].rsplit('.')[-1]
            meta_data.append(temp_dict)
        return meta_data

    def upload_folder_azure(self, container_name, local_folder_path):
        """uploads all the fies present in the given folder
            Args:
                container_name : Name of the container to which contents of the folder uploaded

                local_folder_path: local folder that need to be uploaded.
            Returns :
            None

            Raises :
                AzureMissingResourceHttpError :
                    If the specified container or object does not exist on the cloud
        """
        path_remove = local_folder_path[:3]
        container_client = self.session.get_container_client(container_name)

        for root, dirc, files in os.walk(local_folder_path):
            if files:
                for file in files:
                    file_path_on_azure = os.path.join(root, file).replace(path_remove, "")
                    file_path_on_local = os.path.join(root, file)

                    blob_client = container_client.get_blob_client(file_path_on_azure)

                    with open(file_path_on_local, 'rb') as data:
                        blob_client.upload_blob(data)

    def get_metadata(self, container_name):
        """
        Retrieves the metadata of all the objects in the given container
        Args:
            container_name(str) -- container name
        Returns:
            dict( key:object name , value: metadata)
        """
        container_client = self.session.get_container_client(container_name)
        generator = container_client.list_blobs()
        container_prop = container_client.get_container_properties().__dict__
        del container_prop['last_modified']
        del container_prop['etag']
        metadata = {container_name: container_client.get_container_properties().__dict__}
        for blob in generator:
            prop = container_client.get_blob_client(blob.name).get_blob_properties().__dict__
            del prop['last_modified']
            del prop['etag']
            del prop['creation_time']
            metadata[blob.name] = prop
        return metadata

    def get_tags(self, container_name):
        """Retrieves the tags for the objects in the given containers
        Args:
            container_name(str) -- container name
        Returns:
            dict( key:object name , value: Tags)
        """
        container_client = self.session.get_container_client(container_name)
        generator = container_client.list_blobs()
        tags = {}
        for blob in generator:
            tags[blob.name] = container_client.get_blob_client(blob.name).get_blob_tags()
        return tags

    def azure_helper_cleanup(self):
        """
        To remove temp directories created
        during azure helper object initialization
        """
        self.machine.remove_directory(self.common_dir_path)


class AzureFileShareHelper(object):
    def __init__(self, account_name=None, access_key=None, connect_string=None):
        """Initializes AzureFileShareHelper object
        Args:

            account name (str)   --         account name to the azure storage resource
                                            default : None

            access_key (str)      --        access key to the azure storage resource
                                            default : None

            connect_string (str)   --       connection string to the azure storage resource
                                            default : None
        """
        self.automation_directory = constants.AUTOMATION_DIRECTORY
        self.log = logger.get_log()
        self.machine = Machine()
        self.time_stamp = str(int(datetime.timestamp(datetime.now())))
        self.temp_folder_name = f"AzureFilesTemp_{self.time_stamp}"
        self.common_dir_path = self.machine.join_path(
            constants.TEMP_DIR, self.temp_folder_name)
        self.machine.create_directory(self.common_dir_path,
                                      force_create=True)
        self.session = None
        self.metadata = {}
        try:
            if access_key and account_name:
                connect_string = \
                    f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={access_key};" \
                    f"EndpointSuffix=core.windows.net"
            elif not connect_string:
                raise Exception("Please provide connect string or account Name and access key")
            self.session = ShareServiceClient.from_connection_string(connect_string)
        except Exception as error:
            self.log.error(
                "The specified account name or account key is invalid")
            self.log.error(error)
            raise error

    def delete_file_share(self, file_share_name):
        """deletes a file share from Azure cloud
                Args :

                    file_share_name    (str)     --       name of the share which has to be deleted

                Returns :
                    None

                Raises :
                    AzureMissingResourceHttpError :
                        if the specified container does not exist on the cloud

                """
        try:
            share_client = self.session.get_share_client(file_share_name)
            share_client.delete_share()
        except azure.common.AzureMissingResourceHttpError as error:
            self.log.error(
                "The specified container does not exist on the cloud")
            self.log.error(error)
            raise error

    def download_file(self, file_client, download_location):
        """Helper method for download file share method. this method downloads a file.
                        Args :
                            file_client     (object)  -- it is a ShareFileClient object in azure.storage.fileshare sdk.

                            download_location    (str) -- path to which file need to be downloaded.

                        Returns :
                            None

                        Raises :
                            AzureMissingResourceHttpError :
                                If the specified content does not exist on the cloud

        """
        file_name = file_client.file_name
        dest_path = os.path.join(download_location, file_name)
        with open(dest_path, "wb") as file_handle:
            data = file_client.download_file()
            data.readinto(file_handle)

    def download_dir(self, directory_client):
        """Helper method for download file share method. this method downloads the contents in a folder.
                        Args :
                            directory_client     (object)  -- it is a ShareDirectoryClient object.
                        Returns :
                            None

                        Raises :
                            AzureMissingResourceHttpError :
                                If the specified content does not exist on the cloud

        """
        cd = os.getcwd()
        list_dirs_and_files = directory_client.list_directories_and_files()
        dir_name = directory_client.directory_path.split('/')[-1]
        os.mkdir(dir_name)
        os.chdir(dir_name)
        for file_or_dir in list_dirs_and_files:
            if file_or_dir.is_directory:
                sub_directory_client = directory_client.get_subdirectory_client(file_or_dir.name)
                self.download_dir(sub_directory_client)
                self.metadata[file_or_dir.name] = directory_client.get_directory_properties()
            else:
                file_client = directory_client.get_file_client(file_or_dir.name)
                self.download_file(file_client, os.getcwd())
                metadata = file_client.get_file_properties()
                del metadata['last_modified']
                del metadata['etag']
                del metadata['change_time']
                del metadata['last_write_time']
                self.metadata[file_or_dir.name] = metadata
        os.chdir(cd)

    def download_file_share(self, file_share_name, dir_name):
        """downloads the specified contents from Azure cloud
                Args :
                    file_share_name     (str)       -- name of the file share which need to be downloaded

                    dir_name    (str)           -- folder_name to which file-share need to be downloaded

                Returns :
                    None

                Raises :
                    AzureMissingResourceHttpError :
                        If the specified content does not exist on the cloud

                """
        local_path = self.machine.join_path(
            self.common_dir_path, dir_name)
        os.mkdir(local_path)
        os.chdir(local_path)
        file_share_client = self.session.get_share_client(file_share_name)
        list_dirs_and_files = file_share_client.list_directories_and_files()
        self.metadata = {}
        for file_or_dir in list_dirs_and_files:
            if file_or_dir.is_directory:
                directory_client = file_share_client.get_directory_client(file_or_dir.name)
                self.download_dir(directory_client)
                self.metadata[file_or_dir.name] = directory_client.get_directory_properties()
            else:
                file_client = file_share_client.get_file_client(file_or_dir.name)
                self.download_file(file_client, os.getcwd())
                metadata = file_client.get_file_properties()
                del metadata['last_modified']
                del metadata['etag']
                del metadata['change_time']
                del metadata['last_write_time']
                self.metadata[file_or_dir.name] = metadata
        os.chdir(self.automation_directory)

    def azure_file_share_cleanup(self):
        """
        To remove temp directories created
        during azure file share helper object initialization
        """
        self.machine.remove_directory(self.common_dir_path)


class AzureDataLakeHelper(object):
    def __init__(self, account_name=None, access_key=None, connect_string=None):
        """Initializes AzureFileShareHelper object
        Args:

            account name (str)   --         account name to the azure storage resource
                                            default : None

            access_key (str)      --        access key to the azure storage resource
                                            default : None

            connect_string (str)   --       connection string to the azure storage resource
                                            default : None
        """
        self.file_share_client = None
        self.automation_directory = constants.AUTOMATION_DIRECTORY
        self.log = logger.get_log()
        self.machine = Machine()
        self.time_stamp = str(int(datetime.timestamp(datetime.now())))
        self.temp_folder_name = f"AzureDlTemp_{self.time_stamp}"
        self.common_dir_path = self.machine.join_path(
            constants.TEMP_DIR, self.temp_folder_name)
        self.machine.create_directory(self.common_dir_path,
                                      force_create=True)
        self.session = None
        try:
            if access_key and account_name:
                connect_string = \
                    f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={access_key};" \
                    f"EndpointSuffix=core.windows.net"
            elif not connect_string:
                raise Exception("Please provide connect string or account Name and access key")
            self.session = DataLakeServiceClient.from_connection_string(connect_string)
        except Exception as error:
            self.log.error(
                "The specified account name or account key is invalid")
            self.log.error(error)
            raise error

    def delete_container_azure_dl(self, container_name):
        """deletes a container from Azure cloud
        Args :

            container_name    (str)     --       name of the container which has to be deleted

        Returns :
            None

        Raises :
            AzureMissingResourceHttpError :
                if the specified container does not exist on the cloud

        """
        try:
            file_system_client = self.session.get_file_system_client(container_name)
            file_system_client.delete_file_system()
        except azure.common.AzureMissingResourceHttpError as error:
            self.log.error(
                "The specified container does not exist on the cloud")
            self.log.error(error)
            raise error

    def download_file(self, file_name):
        """Helper method for download file share method. this method downloads a file.
                        Args :
                            file_client     (object)  -- it is a ShareFileClient object in azure.storage.fileshare sdk.

                            download_location    (str) -- path to which file need to be downloaded.

                        Returns :
                            None

                        Raises :
                            AzureMissingResourceHttpError :
                                If the specified content does not exist on the cloud

        """
        file_client = self.file_share_client.get_file_client(file_name)
        head, tail = os.path.split(file_name)
        data = file_client.download_file().readall()
        with open(self.machine.join_path(os.getcwd(), head, tail), "wb") as file:
            file.write(data)

    def download_container_dl(self, file_system_name, dir_name):
        """downloads the specified contents from Azure cloud
                Args :
                    file_system_name     (str)       -- name of the file share which need to be downloaded

                    dir_name    (str)           -- folder_name to which file-share need to be downloaded

                Returns :
                    None

                Raises :
                    AzureMissingResourceHttpError :
                        If the specified content does not exist on the cloud

                """
        local_path = self.machine.join_path(
            self.common_dir_path, dir_name)
        os.mkdir(local_path)
        os.chdir(local_path)
        self.file_share_client = self.session.get_file_system_client(file_system_name)
        list_dirs_and_files = self.file_share_client.get_paths()
        for i in list_dirs_and_files:
            if i.is_directory:
                os.mkdir(i.name)
            else:
                self.download_file(i.name)
        os.chdir(self.automation_directory)

    def azure_data_lake_cleanup(self):
        """
        To remove temp directories created
        during azure file share helper object initialization
        """
        self.machine.remove_directory(self.common_dir_path)
