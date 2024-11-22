"""Main module for generating data for testcases"""

from AutomationUtils import constants
from .sharepointconstants import (
    TEST_DATA_GENERATION_JSON,
    DEFAULT_LIBRARY,
    SPECIAL_DATA_FOLDER_PATH,
    DATA_GENERATION_PATH,
    LIST_VERSIONS_UNWANTED_PROPERTIES,
    FILE_VERSIONS_UNWANTED_PROPERTIES
)
from types import SimpleNamespace
import os
import random
import string
import time
import json
import zipfile


class TestData:
    """Class to create testdata for SharePoint testcases"""

    def __init__(self, sp_object):
        """Initializes the test data object

            Args:

                sp_object (object)     --  instance of the SharePoint object

        """

        self.sp_object = sp_object
        self.testcase_id = str(sp_object.tc_object.id)
        self.log = self.sp_object.log
        self.json_value = self.read_data_from_json()
        self.share_point_data_flag = None
        self.list_attachment_files = []
        self.library_name = DEFAULT_LIBRARY
        if 'CustomLibrary' in sp_object.tc_object.tcinputs:
            self.library_name = sp_object.tc_object.tcinputs['CustomLibrary']
            self.log.info(f'Using custom library {self.library_name}')
        try:
            self.json_value = getattr(self.json_value, ("t" + self.testcase_id))
        except Exception:
            self.json_value = None
            self.log.exception(f"Test data is not found for the test case {self.testcase_id}")
        self.testdata_metadata = {}

    @staticmethod
    def read_data_from_json():
        """Method to read data from JSON file

            Returns:

                sheet_number (int)  --  sheet number to read the test data

        """
        with open(TEST_DATA_GENERATION_JSON, 'r') as f:
            return json.load(f, object_hook=lambda d: SimpleNamespace(**d))

    @staticmethod
    def generate_file(file_name, size=None):
        """Generates the file and populates data

            Args:

                file_name (str)      --   name of the file

                size (int)           --   size of file in bytes

        """
        if os.path.exists(file_name):
            os.remove(file_name)
        if not size:
            size = random.randint(50, 100)
        chars = ''.join([random.choice(string.ascii_letters) for i in range(size)]) + "\n"
        with open(file_name, 'w') as f:
            f.write(chars)
        return file_name

    @staticmethod
    def delete_file(file_name):
        """Deletes the specified file

            Args:

                file_name (str)      --      name of the file

        """
        if os.path.exists(file_name):
            os.remove(file_name)
        else:
            raise Exception("The file does not exist")

    def process_metadata(self, dictionary, list_item_versions=False, file_versions=False):
        """Returns only required fields in metadata and  removes all unwanted fields

            Args:

                dictionary (dict)             --      metadata dictionary

                list_item_versions (boolean)  --      whether it is a list item metadata with versions

        """
        try:
            processed_dictionary = {key: dictionary.get(key) for key in dictionary
                                    if not isinstance(dictionary.get(key), dict)}
            if list_item_versions:
                return {x: processed_dictionary[x] for x in processed_dictionary if
                        x not in LIST_VERSIONS_UNWANTED_PROPERTIES}

            elif file_versions:
                return {x: processed_dictionary[x] for x in processed_dictionary if
                        x not in FILE_VERSIONS_UNWANTED_PROPERTIES}
            else:
                return processed_dictionary
        except Exception as e:
            self.log.debug(f'Exception: {e}, {dictionary = }')
            raise e

    @staticmethod
    def update_file(file_name):
        """Updates the specified file

            Args:

                file_name (str)      --      name of the file

        """
        file = open(file_name, "a")
        size = random.randint(50, 100)
        chars = ''.join([random.choice(string.ascii_letters) for i in range(size)]) + "\n"
        file.write(chars)
        file.close()

    def create_list(self):
        """Creates SharePoint list"""
        try:
            self.log.info("Creating list")
            list = self.json_value.List
            list_title = list.TITLE
            if list.OP_TYPE.lower() == "create":
                self.log.info("Deleting the list if it exists")
                if self.sp_object.get_sp_list_metadata(list_title):
                    self.log.info("List exists")
                    self.sp_object.delete_sp_list(list_title)
                    self.log.info("Deleted the existing list")
                request_body = {
                    "AllowContentTypes": True,
                    "BaseTemplate": 100,
                    "ContentTypesEnabled": True,
                    "Description": "This is a list created for test automation",
                    "EnableVersioning": True,
                    "Title": list_title
                }
                list_metadata = self.sp_object.create_sp_list(request_body)
                self.testdata_metadata[self.sp_object.site_url]["List"] = {
                    "List Metadata": self.process_metadata(list_metadata),
                    "Title": list_title,
                    "Columns": [],
                    "List Items": {}
                }
                self.log.info("{0} list created successfully".format(self.testdata_metadata.get(
                    self.sp_object.site_url, {}).get("List", "").get("Title", "")))
        except Exception as exception:
            self.log.exception("Exception while creating list: %s", exception)
            raise exception

    def add_list_column(self, list_guid, title, field_id):
        """Adds column to SharePoint list

            Args:

                list_guid (str)      --      guid of the list

                title (str)          --      title of the column

                field_id (int)       --      field id of column i.e., type of the column

        """
        try:
            request_body = {
                "__metadata": {
                    "type": "SP.Field"
                },
                "Title": title,
                "FieldTypeKind": field_id
            }
            return self.sp_object.create_list_custom_column(list_guid, request_body)
        except Exception as exception:
            self.log.exception("Exception while adding list column: %s", exception)
            raise exception

    def create_custom_columns_in_list(self):
        """Creates custom columns for list"""
        try:
            self.log.info("Creating Custom Columns")
            list_columns = self.json_value.List.COLUMNS
            list_guid = self.testdata_metadata.get(self.sp_object.site_url, {}).get("List", {}).get("List Metadata",
                                                                                                    {}).get("Id", "")
            for column in list_columns:
                result = self.add_list_column(list_guid, column.Title, column.FieldTypeKind)
                self.testdata_metadata[self.sp_object.site_url]["List"]["Columns"].append(
                    [result.get("StaticName"), result.get("Title"), result.get("FieldTypeKind")])
            self.log.info("Custom columns are created successfully")
        except Exception as exception:
            self.log.exception("Exception while adding columns to the list: %s", exception)
            raise exception

    @staticmethod
    def generate_test_value_for_list_item_column(field_type_kind):
        """Generates test value for the list item based on column type

            Args:

                field_type_kind (int)       --      field id of column i.e., type of the column

        """
        size = random.randint(50, 100)
        if field_type_kind == 1 or field_type_kind == 9:
            return size
        elif field_type_kind == 2:
            return ''.join([random.choice(string.ascii_letters) for i in range(size)])
        elif field_type_kind == 3:
            return ''.join([random.choice(string.ascii_letters) for i in range(size)]) + "\n" + \
                ''.join([random.choice(string.ascii_letters) for i in range(size)])

    def update_list_item_metadata(self, list_title, list_item_id, oop_site=None):
        """Updates list item metadata dict

            Args:

                list_title (str)          --    title of the list

                list_item_id (int)        --    id of the list item

                oop_site (str)            --    out of place restore site

        """
        try:
            if oop_site:
                source_site = self.sp_object.site_url
                self.sp_object.site_url = oop_site
            list_item_metadata = self.process_metadata(
                self.sp_object.get_sp_list_item_metadata(list_title, str(list_item_id)))
            list_item_metadata["Versions Metadata"] = [self.process_metadata(i, list_item_versions=True) for i in
                                                       self.sp_object.get_sp_list_item_metadata(
                                                           list_title,
                                                           str(list_item_id),
                                                           "Versions"
                                                       ).get("results", [])]
            list_item_metadata["List Attachment Metadata"] = [self.process_metadata(i) for i in
                                                              self.sp_object.get_sp_list_item_metadata(
                                                                  list_title,
                                                                  str(list_item_id),
                                                                  "AttachmentFiles"
                                                              ).get("results", [])]
            if oop_site:
                self.sp_object.site_url = source_site
            if list_item_id in self.testdata_metadata[self.sp_object.site_url]["List"]["List Items"].keys():
                self.testdata_metadata[self.sp_object.site_url]["List"]["List Items"][list_item_id].append(
                    list_item_metadata)
            else:
                self.testdata_metadata[self.sp_object.site_url]["List"]["List Items"][list_item_metadata.get("Id")] = [
                    list_item_metadata]
            self.log.info("Fetched updated list item metadata")
        except Exception as exception:
            self.log.exception("Exception while updating list item metadata: %s", exception)
            raise exception

    def update_list_item(self, list_title, list_item_title, list_item_id=None):
        """Updates/Creates list item of the list

             Args:

                list_title (str)          --    title of the list

                list_item_title (str)     --    title of the list item

                list_item_id (int)        --    id of the list item

        """
        try:
            request_body = {
                "Title": list_item_title
            }
            columns = self.testdata_metadata.get(self.sp_object.site_url, {}).get("List").get("Columns")
            for column in columns:
                request_body[column[0]] = self.generate_test_value_for_list_item_column(column[2])
            if list_item_id:
                self.sp_object.update_sp_list_item(list_title, request_body, str(list_item_id))
                self.log.info(f"List Item with id {list_item_id} is updated successfully")
            else:
                result = self.process_metadata(self.sp_object.create_sp_list_item(list_title, request_body))
                list_item_id = result.get("Id")
                self.log.info(f"List Item with id {list_item_id} is created successfully")
            return list_item_id
        except Exception as exception:
            self.log.exception("Exception while adding list items in the list: %s", exception)
            raise exception

    def add_list_item(self, list_title, list_item, versions=True):
        """Adds a list item

             Args:

                list_title (str)          --    title of the list

                list_item (config)        --    config object of list item

                versions (boolean)        --    whether all versions enabled or not

        """
        try:
            list_id = self.update_list_item(list_title, list_item.Title)
            if versions:
                version_num = random.randint(2, 4)
                self.log.info(f"Creating {version_num} additional versions")
                for i in range(version_num):
                    self.update_list_item(list_title, list_item.Title, list_id)
            if hasattr(list_item, "FILE_NAME"):
                self.generate_file(list_item.FILE_NAME)
                self.list_attachment_files.append(list_item.FILE_NAME)
                self.sp_object.upload_sp_list_attachment(list_title, list_id, list_item.FILE_NAME)
            self.update_list_item_metadata(list_title, list_id)
        except Exception as exception:
            self.log.exception("Exception while adding list item in the list: %s", exception)
            raise exception

    def add_list_items(self, create_time, versions=True):
        """Adds list items to the list

            Args:

                create_time (str)         --    when to create the list item in the testcase

                versions (boolean)        --    whether all versions enabled or not

        """
        try:
            self.log.info("Adding list items with versions")
            list_items = self.json_value.List.LIST_ITEMS
            list_title = self.json_value.List.TITLE
            for list_item in list_items:
                if create_time == list_item.CREATE_TIME:
                    self.add_list_item(list_title, list_item, versions)
            self.log.info("List items are created successfully")
        except Exception as exception:
            self.log.exception("Exception while adding list items in the list: %s", exception)
            raise exception

    def update_list_items(self, versions=False):
        """Updates list items in the list

            Args:

                versions (boolean)        --    whether all versions enabled or not

        """
        try:
            deleted_list_items = 0
            self.log.info("Updating list items in list")
            list_items = self.json_value.List.LIST_ITEMS
            list_title = self.json_value.List.TITLE
            index = 1
            for list_item in list_items:
                list_item_id = index
                if list_item.OP_TYPE == "DELETE":
                    deleted_list_items += 1
                    self.sp_object.delete_sp_list_item(list_title, list_item_id)
                    self.log.info(f"Deleted list item with id {list_item_id}")
                elif list_item.OP_TYPE == "EDIT":
                    self.update_list_item(list_title, list_item.Title, list_item_id)
                    if hasattr(list_item, "FILE_NAME"):
                        file_name = self.generate_file("List_Attachment_Edit.txt")
                        if file_name not in self.list_attachment_files:
                            self.list_attachment_files.append(file_name)
                        self.sp_object.upload_sp_list_attachment(list_title, list_item_id, file_name)
                    self.update_list_item_metadata(list_title, list_item_id)
                elif list_item.OP_TYPE == "CREATE":
                    self.add_list_item(list_title, list_item, versions)
                index = index + 1
            return deleted_list_items
        except Exception as exception:
            self.log.exception("Exception while updating list: %s", exception)
            raise exception

    def create_folder(self, folder_structure_json, base_folder, create_time, versions, large_files_size,
                      testdata_metadata):
        """Creates folder/s and its files in a library

            Args:

                folder_structure_json (object)  :   JSON object storing the folder structure to be created and its files

                base_folder (str)               :   Base folder URL of the current folder

                create_time (str)               :   when to create the file in the testcase

                versions (boolean)              :   whether versions enabled or not

                large_files_size (int)          :   size of files in bytes

                testdata_metadata   (dict)      :   testdata metadata of the parent
        """
        try:
            self.log.info("Creating a folder")
            folders = folder_structure_json.Folder
            if type(folders) is not list:
                folders = [folders]
            for folder in folders:
                folder_name = folder.NAME
                folder_url = base_folder + "/" + folder_name
                self.log.info("Delete the folder if exists")
                if self.sp_object.get_sp_folder_metadata(folder_url):
                    self.log.info(f"{folder_name} folder exists")
                    self.sp_object.delete_sp_file_or_folder(folder_url)
                    self.log.info("Deleted the existing folder")
                request_body = {
                    "ServerRelativeUrl": folder_url
                }
                self.sp_object.create_sp_folder(request_body)
                self.log.info("{0} folder created successfully".format(folder_url))

                if "Folder" not in testdata_metadata:
                    testdata_metadata["Folder"] = []
                child_metadata = {
                    "Folder Name": folder_name,
                    "Folder URL": folder_url
                }
                testdata_metadata["Folder"].append(child_metadata)
                if folder.FILES:
                    self.create_files(folder, folder_url, create_time, child_metadata, versions, large_files_size)
                if hasattr(folder, 'Folder'):
                    self.create_folder(folder, folder_url, create_time, versions, large_files_size, child_metadata)
                self.log.info(f"Created folder {folder_name} successfully")
        except Exception as exception:
            self.log.exception("Exception while creating a folder: %s", exception)
            raise exception

    def edit_folder_name(self):
        """Appends timestamp to folder name in the document library"""
        try:
            folder = self.json_value.Folder
            folder_name = folder.NAME
            self.log.info(f"Editing {folder_name} folder name")
            site_name = "/".join(self.sp_object.site_url.split("/")[4:])
            folder_url = "/sites/" + site_name + f"/{self.library_name}/" + folder_name
            updated_name = folder_name.split('_')[0] + f'_{int(time.time())}'
            self.sp_object.rename_sp_folder(folder_url, updated_name)
            self.log.info("{0} folder name edited successfully".format(folder_url))
            self.testdata_metadata[self.sp_object.site_url]["Folder"] = {
                "Folder Name": updated_name,
                "Folder URL": folder_url
            }
            setattr(self.json_value.Folder, 'NAME', updated_name)
            self.log.info(f"Edited {updated_name} folder name successfully")
        except Exception as exception:
            self.log.exception("Exception while editing folder name: %s", exception)
            raise exception

    def edit_library_description(self):
        """Sets timestamp as the document library description"""
        try:
            self.log.info(f"Editing {self.library_name} library description")
            description = str(int(time.time()))
            self.sp_object.edit_sp_library_description(self.library_name, description)
            self.log.info(f'Edited {self.library_name} library description successfully')
        except Exception as exception:
            self.log.exception("Exception while editing document library description: %s", exception)
            raise exception

    def edit_site_description(self):
        """Sets timestamp as the site description"""
        try:
            self.log.info(f"Editing site description of {self.sp_object.site_url}")
            description = str(int(time.time()))
            self.sp_object.edit_site_description(description)
            self.log.info(f'Edited {self.sp_object.site_url} site description successfully')
        except Exception as exception:
            self.log.exception("Exception while editing site description: %s", exception)
            raise exception

    def update_file_metadata(self, file_name, folder_path, testdata_metadata, oop_site=None):
        """Updates file metadata

            Args:

                file_name           (str)       :   name of the file

                folder_path         (str)       :   path of the folder

                testdata_metadata   (dict)      :   testdata metadata

                oop_site            (str)       :   out of place restore site

        """
        try:
            if oop_site:
                source_site = self.sp_object.site_url
                self.sp_object.site_url = oop_site
            file_metadata = self.process_metadata(self.sp_object.get_sp_file_metadata(file_name, folder_path))
            file_metadata["Versions Metadata"] = [self.process_metadata(i, file_versions=True) for i in
                                                  self.sp_object.get_sp_file_metadata(file_name, folder_path,
                                                                                      "Versions").get("results", [])]
            if oop_site:
                self.sp_object.site_url = source_site

            if "Files" not in testdata_metadata:
                testdata_metadata["Files"] = {}

            if file_name in testdata_metadata["Files"].keys():
                testdata_metadata["Files"][file_name].append(file_metadata)
            else:
                testdata_metadata["Files"][file_name] = [file_metadata]
            self.log.info("Fetched updated file metadata")
        except Exception as exception:
            self.log.exception("Exception while getting updated file metadata: %s", exception)
            raise exception

    def update_sp_file(self, file_name, folder_path):
        """ Updates the provided file

            Args:

                file_name (str)        --      name of the file

                folder_path (str)      --      path of the folder

        """
        try:
            self.update_file(file_name)
            self.sp_object.upload_sp_binary_file(folder_path, file_name)
            self.log.info("{0} file updated successfully".format(file_name))
        except Exception as exception:
            self.log.exception("Exception while updating file: %s", exception)
            raise exception

    def create_file(self, file, folder_path, parent_metadata, versions=True, large_files_size=None):
        """Creates file in a given library or folder

            Args:

                file                (SimpleNamespace)       :   config object for file

                folder_path         (str)                   :   path of the folder

                parent_metadata     (dict)                  :   testdata metadata of parent folder

                versions            (bool)                  :   whether all versions enabled or not

                large_files_size    (int)                   ;   size of files in bytes

        """
        try:
            file_name = file.Name
            self.generate_file(file_name, large_files_size)
            if versions:
                version_num = random.randint(3, 4)
            else:
                version_num = 1
            self.log.info(f"Creating/Adding {version_num} versions to the file")
            for i in range(version_num):
                self.update_sp_file(file_name, folder_path)
            self.update_file_metadata(file_name, folder_path, parent_metadata)
            self.log.info("File with versions is uploaded in folder")
        except Exception as exception:
            self.log.exception("Exception while creating a folder: %s", exception)
            raise exception

    def create_files(self, folder_structure, base_url, create_time, parent_metadata, versions=True,
                     large_files_size=None):
        """Creates files in given library or folder

            Args:

                folder_structure    (SimpleNamespace)       :   JSON object containing the folder/files structure

                base_url            (str)                   :   The base URL from where files need to be created

                create_time         (str)                   :   when to create the file in the testcase

                parent_metadata     (dict)                  :   testdata metadata of parent folder

                versions            (bool)                  :   whether versions enabled or not

                large_files_size    (int)                   :   size of files in bytes
        """
        try:
            self.log.info("Creating files in folder")
            files = folder_structure.FILES
            for file in files:
                if create_time == file.CREATE_TIME:
                    self.create_file(file, base_url, parent_metadata, versions, large_files_size)
            self.log.info("Created files inside folder")
        except Exception as exception:
            self.log.exception("Exception while creating a folder: %s", exception)
            raise exception

    def update_files(self, folder=None, testdata_metadata=None, folder_url=None, versions=False):
        """Updates files in the folder

            Args:

                folder              (SimpleNamespace)       :   config object for folder

                testdata_metadata   (dict)                  :   testdata metadata of parent

                folder_url          (str)                   :   Server relative URL for the folder

                versions            (bool)                  :   whether versions enabled or not

        """
        if not folder:
            folder = self.json_value.Folder

        if not testdata_metadata:
            testdata_metadata = self.testdata_metadata[self.sp_object.site_url]["Folder"][0]

        if not folder_url:
            site_name = "/".join(self.sp_object.site_url.split("/")[4:])
            folder_url = f"/sites/{site_name}/{self.library_name}/{folder.NAME}"
        else:
            folder_url += f"/{folder.NAME}"

        if hasattr(folder, "Folder"):
            for i, child_folder in enumerate(folder.Folder):
                self.update_files(child_folder, testdata_metadata["Folder"][i], folder_url, versions)

        try:
            deleted_files = 0

            self.log.info("Updating files in folder")
            for file in folder.FILES:
                if file.OP_TYPE == "DELETE":
                    file_relative_url = folder_url + "/" + file.Name
                    self.sp_object.delete_sp_file_or_folder(file_relative_url)
                    deleted_files += 1
                    self.log.info(f"{file_relative_url} is deleted successfully")
                elif file.OP_TYPE == "EDIT":
                    self.create_file(file, folder_url, testdata_metadata, versions)
                elif file.OP_TYPE == "CREATE":
                    self.create_file(file, folder_url, testdata_metadata, versions)
            return deleted_files
        except Exception as exception:
            self.log.exception(f"Exception while updating files: {exception}")
            raise exception

    def populate_folder_json(self, json_value, folder_path):
        """Recursively populates folder JSON

            Args:

                json_value  (dict)      :   JSON value

                folder_path (str)       :   Path to folder

            Returns:

                SimpleNamespace         :   JSON value as a SimpleNamespace
        """
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)

            if os.path.isdir(item_path):
                if "Folder" not in json_value:
                    json_value["Folder"] = []

                child_folder_json = {
                    "OP_TYPE": "CREATE",
                    "NAME": item
                }
                child_folder_json = self.populate_folder_json(child_folder_json, item_path)
                json_value["Folder"].append(child_folder_json)

            else:
                if "FILES" not in json_value:
                    json_value["FILES"] = []

                child_file_json = {
                    "OP_TYPE": "EDIT",
                    "CREATE_TIME": "create before backup",
                    "Name": item
                }
                json_value["FILES"].append(SimpleNamespace(**child_file_json))

        return SimpleNamespace(**json_value)

    def upload_special_folder(self):
        """Uploads the special data folder to Sharepoint"""
        if not os.path.isfile(SPECIAL_DATA_FOLDER_PATH):
            raise Exception(f"Ensure the zip file {SPECIAL_DATA_FOLDER_PATH} exists at {DATA_GENERATION_PATH}."
                            "Copy the zip file from a trusted VM")

        folder_path = os.path.splitext(SPECIAL_DATA_FOLDER_PATH)[0]
        if not os.path.isdir(folder_path):
            with zipfile.ZipFile(SPECIAL_DATA_FOLDER_PATH, "r") as z:
                z.extractall(DATA_GENERATION_PATH)

        root_folder = os.path.splitext(os.path.basename(SPECIAL_DATA_FOLDER_PATH))[0]
        json_value = self.populate_folder_json({
            "OP_TYPE": "CREATE",
            "NAME": root_folder
        }, folder_path)

        root_folder_config = self.json_value.Folder
        if hasattr(root_folder_config, "Folder"):
            root_folder_config.Folder.append(json_value)
        else:
            setattr(root_folder_config, "Folder", [json_value])

    def create_site_structure_for_backup(self, site_url_list, folder=None, list=None, special_data_folder=None,
                                         versions=True, large_files_size=None):
        """Creates the sample site structure for backup
            1. Create a folder under document library
                - Create a folder
                - Upload a file with some random content
            2. Create a list

            Args:

                site_url_list       (list)      :   list of sites in which testdata should be generated

                folder              (bool)      :   whether create test data for folder

                list                (bool)      :   whether create test data for list

                special_data_folder (bool)      :   whether to upload the special data folder

                versions            (bool)      :   whether all versions enabled or not

                large_files_size    (int)       :   size of files in bytes

        """
        try:
            for site_url in site_url_list:
                self.sp_object.site_url = site_url
                site_metadata = self.sp_object.get_site_properties(root_site=True)
                self.testdata_metadata[site_url] = {
                    'Title': site_metadata.get('Title', "")
                }
                if special_data_folder:
                    self.upload_special_folder()
                    folder = True
                if folder:
                    site_name = "/".join(self.sp_object.site_url.split("/")[4:])
                    base_folder = "/sites/" + site_name + f"/{self.library_name}"

                    self.create_folder(folder_structure_json=self.json_value, base_folder=base_folder,
                                       create_time="create before backup", versions=versions,
                                       large_files_size=large_files_size,
                                       testdata_metadata=self.testdata_metadata[site_url])
                if list:
                    self.create_list()
                    self.create_custom_columns_in_list()
                    self.add_list_items(create_time="create before backup", versions=versions)
            self.share_point_data_flag = True
        except Exception as exception:
            self.log.exception("Exception while creating site structure on SharePoint Site: %s", str(exception))
            raise exception

    def create_test_subsites(self, num_of_sites=2):
        """Creates subsites in a SharePoint site

             Args:

                num_of_sites (int)       --    number of sites to be created
        """
        try:
            site_url_list = [self.sp_object.site_url]
            subsite_list = []
            for i in range(1, num_of_sites + 1):
                title = "Test Subsite - " + str(i)
                url = "subsite_" + str(i)
                subsite_list.append({
                    "Title": "Test Subsite - " + str(i),
                    "Url End": "subsite_" + str(i)
                })
                site_url_list.append(self.sp_object.site_url + "/" + url)
            subsites_metadata_dict = self.sp_object.create_subsites(subsite_list)
            self.log.info(f"Sites used in this test case: {site_url_list}")
            return site_url_list, subsites_metadata_dict
        except Exception as exception:
            self.log.exception("Exception while creating subsite on SharePoint Site: %s", str(exception))
            raise exception

    def get_subsites_end_url_list(self, subsites_list):
        """Returns the end url list of subsites

            Args:

                    subsites_list (list)    --  list of subsites URLS

        """
        subsites_end_url_list = []
        for site in subsites_list:
            if site == self.sp_object.site_url:
                subsites_end_url_list.append('')
            else:
                site_end_url = site.split("sites/")[1]
                subsites_end_url_list.append(site_end_url[site_end_url.find('/') + 1:])
        return subsites_end_url_list

    def modify_backup_content(self, folder=None, list=None, site_url=None):
        """Modifies SharePoint backup content

            Args:

                folder (boolean)           --    whether modify test data for folder

                list (boolean)             --    whether modify test data for list

                site_url (str)             --   url of site in which content is modified

        """
        try:
            deleted_items = 0
            if site_url:
                source_site = self.sp_object.site_url
                self.sp_object.site_url = site_url
            self.log.info(f"Modifying content for {self.sp_object.site_url}")
            if folder:
                deleted_items += self.update_files()
                self.log.info("Updated files inside folder")
            if list:
                deleted_items += self.update_list_items()
                self.log.info("List items are updated successfully")
            if site_url:
                self.sp_object.site_url = source_site
            return deleted_items
        except Exception as exception:
            self.log.exception("Exception while modifying backup content: %s", str(exception))
            raise exception

    def modify_content_before_restore(self, folder=None, list=None, site_url=None):
        """Modifies the content on SharePoint site

            Args:

                folder (boolean)           --    whether modify test data for folder

                list (boolean)             --    whether modify test data for list

                site_url (str)             --   url of site in which content is modified

        """
        try:
            if site_url:
                self.sp_object.site_url = site_url
            self.log.info(f"Modifying content for {self.sp_object.site_url} before restore")
            if folder:
                self.log.info("Adding versions to the file in folder")
                files = self.json_value.Folder.FILES
                folder_name = self.json_value.Folder.NAME
                site_name = "/".join(self.sp_object.site_url.split("/")[4:])
                folder_url = "/sites/" + site_name + f"/{self.library_name}/" + folder_name
                for file in files:
                    if file.OP_TYPE != "DELETE":
                        self.update_sp_file(file.Name, folder_url)
                self.log.info("Added versions all the files")
            if list:
                self.log.info("Editing list items")
                list_items = self.json_value.List.LIST_ITEMS
                list_title = self.json_value.List.TITLE
                index = 1
                for list_item in list_items:
                    list_item_id = index
                    if list_item.OP_TYPE != "DELETE":
                        self.update_list_item(list_title, list_item.Title, list_item_id)
                        if hasattr(list_item, "FILE_NAME"):
                            file_name = self.generate_file("List_Attachment_Before_Restore.txt")
                            if file_name not in self.list_attachment_files:
                                self.list_attachment_files.append(file_name)
                            self.sp_object.upload_sp_list_attachment(list_title, list_item_id, file_name)
                    index = index + 1
                self.log.info("Added versions to all list items")
        except Exception as exception:
            self.log.exception("Exception while modifying content on SharePoint site: %s", str(exception))
            raise exception

    def delete_backup_content(self, delete_folder=None, delete_list=None):
        """Deletes the backed up content

            Args:

                delete_folder (boolean)           --    whether delete test data of folder

                delete_list (boolean)             --    whether delete test data of list

        """
        try:
            deleted_objects_count = 0
            if delete_folder:
                self.log.info("Deleting folder from sharepoint site")
                folders = self.json_value.Folder
                if type(folders) is not list:
                    folders = [folders]
                for folder in folders:
                    folder_name = folder.NAME
                    site_name = "/".join(self.sp_object.site_url.split("/")[4:])
                    folder_url = "/sites/" + site_name + f"/{self.library_name}/" + folder_name
                    self.sp_object.delete_sp_file_or_folder(folder_url)
                    deleted_objects_count += 1
                    self.log.info("{0} is deleted from sharepoint site".format(folder_url))
            if delete_list:
                self.log.info("Deleting list from sharepoint site")
                delete_list = self.json_value.List
                list_title = delete_list.TITLE
                self.sp_object.delete_sp_list(list_title)
                deleted_objects_count += 1
                self.log.info("List {0} is deleted successfully from sharepoint site".format(list_title))
            self.log.info("Deleted backup content successfully")
            self.share_point_data_flag = False
            return deleted_objects_count
        except Exception as exception:
            self.log.exception("Exception while deleting backup content: %s", str(exception))
            raise exception

    def delete_disk_files(self):
        """Deletes that are created on system to upload into SharePoint"""
        try:
            self.log.info("Deleting files on disk")
            files = self.json_value.Folder.FILES
            for file in files:
                self.delete_file(file.Name)
                self.log.info(f"Deleted file {file.Name}")
            for file in self.list_attachment_files:
                self.delete_file(file)
                self.log.info(f"Deleted file {file}")
        except Exception as exception:
            self.log.exception("Exception while deleting files on disk: %s", exception)

    def delete_backup_site_structure(self, site_url_list=None, folder=None, list=None, force=None):
        """Deletes the SharePoint site structure created for running testcase

            Args:

                site_url_list   (str)       :   list of sites

                folder          (bool)      :   whether delete test data of folder

                list            (bool)      :   whether delete test data of list

                force           (bool)      :   whether to ignore data flag and testcase status
        """
        try:
            deleted_objects_count = 0
            if site_url_list is None:
                if self.sp_object.site_url_list:
                    site_url_list = self.sp_object.site_url_list
                else:
                    site_url_list = [self.sp_object.site_url]

            if force or self.share_point_data_flag and self.sp_object.tc_object.status != constants.FAILED:
                for site in site_url_list:
                    self.sp_object.site_url = site
                    deleted_objects_count += self.delete_backup_content(folder, list)
                    self.log.info("SharePoint site structure created for running testcase is deleted")
            else:
                self.log.info("Testcase got failed in between or Test data is already deleted on SharePoint Site")
            return deleted_objects_count
        except Exception as exception:
            self.log.exception("Exception while deleting backup site structure: %s", exception)
            raise exception
