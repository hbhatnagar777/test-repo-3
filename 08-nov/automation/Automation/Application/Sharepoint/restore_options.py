# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
main file for validating all the options for restores

Class:
Restore - class defined for validating  all restores options

"""
from deepdiff import DeepDiff
from AutomationUtils.machine import Machine
from Application.Sharepoint import sharepointconstants as constants
from Application.Office365.solr_helper import SolrHelper
import requests
import pandas as pd
import io


class Restore(object):
    """Class for performing Restore related operations."""

    def __init__(self, sp_object):
        """Initializes the Restore object

            Args:

                sp_object (Object)  --  instance of SharePoint module

        """
        self.sp_object = sp_object
        self.tc_object = sp_object.tc_object
        self.log = self.tc_object.log
        self.app_name = self.__class__.__name__
        self.csdb = sp_object.csdb
        self.browse_response = None
        self.solr_obj = SolrHelper(self.sp_object)

    def get_path_for_v1_restore(self):
        """Gets paths for restore from browse response for v1 client"""
        folder_url = self.tc_object.testdata.testdata_metadata.get(self.sp_object.site_url, {}).get("Folder", {}).get(
            "Folder Name", "")
        list_url = self.tc_object.testdata.testdata_metadata.get(self.sp_object.site_url, {}).get("List", {}).get(
            "Title", "")
        weirdchar = self.browse_response[0].split(":")[1][0]
        return [f"{self.browse_response[0]}\\{weirdchar}\\{constants.DEFAULT_LIBRARY}\\{folder_url}",
                f"{self.browse_response[0]}\\{weirdchar}\\Lists\\{list_url}"]

    def extract_guid(self, path, search_and_delete_all=False):
        """Extracts the CV_OBJECT_GUID/SP_WEB_GUID using paths from Solr for a Sharepoint path. These GUIDs are
        required for deleting data from Sharepoint V2 Index.

            Args:
                path    (str)                       :   The Sharepoint path to be converted
                search_and_delete_all (bool)        :   If true returns the SPWebGUID else CVObjectGUID

            Returns:

                str             :       CVObjectGUID or SPWebGUID of the passed item path

        """
        data_needed = "CVObjectGUID"
        if search_and_delete_all:
            data_needed = "SPWebGUID"
        self.solr_obj.set_cvsolr_base_url()
        full_path = ("\\" + path).replace("\\", "\\\\")  # Escape the backslash for Solr query
        solr_query_url = self.solr_obj.create_solr_query({
            "Url": f'"{full_path}"'
        }, {data_needed})
        self.log.info(f"Query for getting path node: {solr_query_url}")
        try:
            response = requests.get(solr_query_url)
            response_dict = response.json()['response']['docs'][0]
            return f'{response_dict[data_needed]}'

        except Exception as exp:
            self.log.error(f'Error trying to get CV_OBJECT_GUIDs for path node for {path}: {exp}')
            raise exp

    def extract_state_of_item(self, path):
        """Extracts "IsVisible", "ItemState" of files/folders using paths from Solr for a Sharepoint path.

            Args:
                path    (str)    :   The Sharepoint path to be converted

            Returns:

                str             :    State of the item who path is passed in the format: IsVisible,ItemState

        """
        full_path = ("\\" + path).replace("\\", "\\\\")  # Escape the backslash for Solr query
        solr_query_url = self.solr_obj.create_solr_query({
            "Url": f'"{full_path}"'
        }, {"IsVisible", "ItemState"})
        self.log.info(f"Query for getting state of item: {solr_query_url}")

        try:
            response = requests.get(solr_query_url)
            response_dict = response.json()['response']['docs'][0]
            return f'{response_dict["IsVisible"]},{response_dict["ItemState"]}'

        except Exception as exp:
            self.log.error(f'Error trying to get state of item for path {path}: {exp}')
            raise exp

    def extract_path_node(self, path):
        """Extracts the path node using GUIDs from Solr for a Sharepoint path. Path nodes are
        required for restore QSDK API for Sharepoint V2 Restores.

            Example:   "\\https://cvautomation.sharepoint.com/sites/TestSPAutomationSite7\\
                        Contents\\Shared Documents\\59555 - Test Automation Folder" is converted
                        to "100,c8641c5c22f28a8273302afd820fe8cb,0d6e6901f6f2820041efccf00cedbc13"

            Args:

                path    (str)   :       The Sharepoint path to be converted

            Returns:

                str             :       Path node compatible with Restore QSDK API

        """
        full_path = ("\\" + path).replace("\\", "\\\\")  # Escape the backslash for Solr query
        solr_query_url = self.solr_obj.create_solr_query({
            "Url": f'"{full_path}"'
        }, {"ObjectType", "SPWebGUID", "CVObjectGUID"})
        self.log.info(f"Query for getting path node: {solr_query_url}")

        try:
            response = requests.get(solr_query_url)
            response_dict = response.json()['response']['docs'][0]
            return (f'{response_dict["ObjectType"]},{response_dict["SPWebGUID"]},'
                    f'{response_dict["CVObjectGUID"]}')

        except Exception as exp:
            self.log.error(f'Error trying to get GUIDs for path node for {path}: {exp}')
            raise exp

    def get_path_for_restore(self, folder=None, list=None, file=None, v2_restore=False):
        """Gets paths for restore from browse response

            Args:

                folder      (bool)  --      whether to get path for folder

                list        (bool)  --      whether to get path for list

                file        (bool)  --      whether to get path for file

                v2_restore  (bool)  --      Whether to use new restore paths

        """
        try:
            paths = []
            if not self.browse_response:
                self.log.exception("Browse response was not checked yet")
                raise Exception("Browse response was not checked yet")
            self.solr_obj.set_cvsolr_base_url()

            site_metadata = self.tc_object.testdata.testdata_metadata.get(self.sp_object.site_url, {})
            if file:
                for url in self.browse_response:
                    if url != "MB":
                        site_url = url.split("\\")[1]
                        file_name = self.tc_object.testdata.json_value.Folder.FILES[0].Name or ""
                        if (url.split("\\")[-1] == file_name
                                and site_url == self.sp_object.site_url):
                            file_url = url
                            if v2_restore:
                                paths.append(self.extract_path_node(file_url))
                            else:
                                paths.append(file_url)
                            break
            if folder:
                for url in self.browse_response:
                    if url != "MB":
                        site_url = url.split("\\")[1]
                        folder_name = (site_metadata.get("Folder") or [{}])[0].get("Folder Name", "")
                        if url.split("\\")[-1] == folder_name and site_url == self.sp_object.site_url:
                            folder_url = url
                            if v2_restore:
                                paths.append(self.extract_path_node(folder_url))
                            else:
                                paths.append(folder_url)
                            break
            if list:
                for url in self.browse_response:
                    if url != "MB":
                        site_url = url.split("\\")[1]
                        list_title = site_metadata.get("List", {}).get("Title", "")
                        if url.split("\\")[-1] == list_title and site_url == self.sp_object.site_url:
                            list_url = url
                            if v2_restore:
                                paths.append(self.extract_path_node(list_url))
                            else:
                                paths.append(list_url)
                            break
            return paths
        except Exception as exception:
            self.log.exception("Exception while getting path for restore job: %s", str(exception))
            raise exception

    def verify_browse_response(self, browse_paths, exclude_paths):
        """Verifies browse response

            Args:

                browse_paths (list)         --    list of paths that should be in browse response

                exclude_paths (list)        --    list of paths that should not be in browse response

        """
        try:
            if self.browse_response:
                if browse_paths:
                    for path in browse_paths:
                        if not self.sp_object.v1:
                            path = "MB\\" + path
                        if path in self.browse_response:
                            self.log.info(f"Browse for restore has {path} entry as expected")
                        else:
                            self.log.exception(f"Browse for restore is not successful for entry {path}")
                            raise Exception(f"Browse for restore is not successful for entry {path}")
                if exclude_paths:
                    for path in exclude_paths:
                        path = "MB\\" + path
                        if path in self.browse_response:
                            self.log.exception(f"Browse for restore has {path} entry")
                            raise Exception(f"Browse for restore has {path} entry")
                        else:
                            self.log.info(f"Browse for restore does not have {path} entry as expected")
            else:
                self.log.exception("Browse response is not set")
                raise Exception("Browse response is not set")
        except Exception as exception:
            self.log.exception("Exception while verifying browse paths: %s", str(exception))
            raise exception

    def browse_restore_content_and_verify_browse_response(self, browse_args=None, **kwargs):
        """Browses content for restore and verifies the browse response

            Args:

                browse_args (dict)         -- dictionary of browse arguments
                Example:

                    from_time (str)         --  from time for browse
                                                    Example: from_time = "0"

                    to_time (str)           --  to time for browse
                                                    Example: to_time = "1606204288"
            Kwargs:

                browse_paths (list)         --  list of paths that should be present in browse response
                                                Example:
                                                [
                                                   "MB\\https://test.sharepoint.com/sites/TestSite\\Subsites\\sub_1",
                                                   "MB\\https://test.sharepoint.com/sites/TestSite\\Subsites\\sub_2"
                                                ]
                exclude_browse_paths (list)  --  list of paths that should not be present in browse response
                                                Example:
                                                [
                                                   "MB\\https://test.sharepoint.com/sites/TestSite",
                                                   "MB\\https://test.sharepoint.com/sites/TestSite2\\Subsites\\sub"
                                                ]


        """
        if browse_args is None:
            browse_args = {}
        try:
            self.log.info("Browsing content for restore")
            paths, dictionary = self.sp_object.cvoperations.subclient.browse(path=r"\MB", **browse_args)
            self.browse_response = paths
            if self.browse_response:
                if not self.sp_object.v1:
                    self.verify_browse_response(kwargs.get("browse_paths", []), kwargs.get("exclude_browse_paths", []))
            else:
                self.log.error("No content available for restore")
                raise Exception("Content not available for restore")
        except Exception as exception:
            self.log.exception("Exception occurred during browse: %s", str(exception))
            raise exception

    def validate_browse_for_restore(self, include_subsite_end_url_list, exclude_subsite_end_url_list=None):
        """Validates browse for restore

            Args:

                include_subsite_end_url_list (list)    --   list of subsites end urls
                                                            Example: ["sub1", "sub2"]

                exclude_subsite_end_url_list (list)    --   list of subsites end urls to be excluded in browse response
                                                            Example: ["sub1", "sub2"]
        """
        try:
            self.sp_object.cvoperations.wait_time(60, f"Waiting before browse")
            subsite_include_browse_list = []
            subsite_exclude_browse_list = []
            for site in include_subsite_end_url_list:
                if site == '':
                    subsite_include_browse_list.append(self.sp_object.site_url + "\\Contents")
                else:
                    subsite_include_browse_list.append(self.sp_object.site_url + "\\Subsites\\" + site)
            if exclude_subsite_end_url_list:
                for site in exclude_subsite_end_url_list:
                    if site == '':
                        subsite_exclude_browse_list.append(self.sp_object.site_url + "\\Contents")
                    else:
                        subsite_exclude_browse_list.append(self.sp_object.site_url + "\\Subsites\\" + site)
            self.browse_restore_content_and_verify_browse_response(
                browse_paths=subsite_include_browse_list,
                exclude_browse_paths=subsite_exclude_browse_list)
        except Exception as exception:
            self.log.exception("Exception while validating browse response: %s", str(exception))
            raise exception

    def compare_backup_and_restore_metadata(self,
                                            backup_metadata,
                                            restore_metadata,
                                            exclude_paths=None):
        """Compares backup metadata and restore metadata

            Args:

                backup_metadata (dict)      --      metadata of backed up content
                                                    Example:
                                                        {
                                                            "Id":1,
                                                            "Title":"Test Title",
                                                            "MajorVersion":3,
                                                            "MinorVersion":0,
                                                            "Name":"Test File"
                                                        }

                restore_metadata (dict)     --      metadata of restored content
                                                    Example:
                                                        {
                                                            "Id":1,
                                                            "Title":"Test Title",
                                                            "MajorVersion":3,
                                                            "MinorVersion":0,
                                                            "Name":"Test File"
                                                        }

                exclude_paths (set)        --      properties to exclude while validating
                                                   Example:
                                                       {
                                                            "root['ContentTag']",
                                                            "root['UniqueId']",
                                                            "root['ETag']"
                                                       }
        """
        try:
            diff = DeepDiff(backup_metadata, restore_metadata, exclude_paths=exclude_paths, ignore_string_case=True)
            if diff:
                if 'dictionary_item_removed' in diff.keys():
                    # By default title field is not enabled after restore. An MR is created for this. Will remove the
                    # following code once it is resolved
                    if "root['Title']" in diff.get('dictionary_item_removed')[0]:
                        list_title = self.tc_object.testdata.json_value.List.TITLE
                        item_title = self.sp_object.get_sp_list_item_title(list_title)
                        if backup_metadata.get("Title") == item_title:
                            self.log.info("Backup and restore metadata are validated")
                else:
                    self.log.error("Difference in metadata {0}".format(diff))
                    self.log.exception("Backup and restore metadata are not same")
                    raise Exception("Backup and restore metadata are not same")
            else:
                self.log.info("Backup and restore metadata are validated")
        except Exception as exception:
            self.log.exception("Exception while comparing metadata: %s", str(exception))
            raise exception

    def validate_restored_files(self, testdata_metadata=None, backup_metadata_index=-1, latest_version=False,
                                oop_site=None):
        """Validates restored files in the folder

            Args:

                testdata_metadata       (dict)      :   testdata metadata of the parent folder

                backup_metadata_index   (int)       :   index of the backup metadata list to consider
                                                        it can be any number with in list length range
                                                        Default: -1 (takes latest backup metadata)

                latest_version          (bool)      :   whether to validate only latest version metadata or
                                                        all versions metadata
                                                        Default: False (validates all versions)

                oop_site                (str)       :   out of place restore site if it is oop restore validation

        """
        if not testdata_metadata:
            testdata_metadata = (self.tc_object.testdata.testdata_metadata.get(
                self.sp_object.site_url, {}).get("Folder", [{}]) or [{}])[0]

        if "Folder" in testdata_metadata:
            for folder_metadata in testdata_metadata["Folder"]:
                self.validate_restored_files(testdata_metadata=folder_metadata,
                                             backup_metadata_index=backup_metadata_index,
                                             latest_version=latest_version, oop_site=oop_site)

        try:
            self.log.info("Collecting and validating metadata of files")
            files = list(testdata_metadata.get("Files", {}).keys())
            exclude_paths = {"root['ContentTag']", "root['UniqueId']", "root['ETag']",
                             "root['TimeCreated']", "root['TimeLastModified']", "root['MajorVersion']",
                             "root['UIVersion']", "root['UIVersionLabel']", "root['Versions Metadata']"}
            if oop_site:
                exclude_paths.add("root['ServerRelativeUrl']")
                site_name = "/".join(oop_site.split("/")[4:])
            else:
                site_name = "/".join(self.sp_object.site_url.split("/")[4:])
            folder_url = "/sites/" + site_name + f"/{'/'.join(testdata_metadata.get('Folder URL', '').split('/')[3:])}"
            if latest_version:
                exclude_paths.add("root['Versions Metadata']")
            for file in files:
                backup_metadata = testdata_metadata.get("Files").get(file)[backup_metadata_index]
                if oop_site:
                    self.tc_object.testdata.update_file_metadata(file, folder_url, testdata_metadata,
                                                                 oop_site=oop_site)
                else:
                    self.tc_object.testdata.update_file_metadata(file, folder_url, testdata_metadata)
                restore_metadata = testdata_metadata.get("Files").get(file)[-1]
                testdata_metadata.get("Files").get(file).pop()
                if latest_version:
                    if len(restore_metadata["Versions Metadata"]) > 0:
                        self.log.exception("Didn't restore only latest version")
                        raise Exception("Didn't restore only latest version")
                self.compare_backup_and_restore_metadata(backup_metadata, restore_metadata,
                                                         exclude_paths=exclude_paths)
                self.log.info(f"{file} is validated successfully")
        except Exception as exception:
            self.log.exception("Exception while validating file metadata: %s", str(exception))
            raise exception

    def validate_restored_list_items(self, backup_metadata_index=-1, latest_version=False, overwrite_restore=False,
                                     oop_site=None):
        """Validates restored list items in the list

             Args:

                backup_metadata_index (int)     --      index of the backup metadata list to consider
                                                        it can be any number with in list length range
                                                        Default: -1 (takes latest backup metadata)

                latest_version (boolean)         --     whether to validate only latest version metadata or
                                                        all versions metadata
                                                        Default: False (validates all versions)

                overwrite_restore (boolean)      --     whether the restore done is an overwrite restore or not

                oop_site (str)                   --     out of place restore site if it is oop restore validation

        """
        try:
            self.log.info("Collecting and validating metadata of list items")
            list_items = self.tc_object.testdata.json_value.List.LIST_ITEMS
            list_title = self.tc_object.testdata.json_value.List.TITLE
            exclude_paths = {"root['ContentTypeId']", "root['GUID']", "root['ItemChildCount']",
                             "root['FolderChildCount']", "root['Id']", "root['ID']",
                             "root['OData__UIVersionString']", "root['Versions Metadata']"}
            if latest_version:
                exclude_paths.add("root['OData__UIVersionString']")

            # update list items with restored items' metadata
            restore_list_item_ids_range_start = 1
            restore_list_item_ids_range_end = len(list_items)
            if overwrite_restore:
                restore_list_item_ids_range_start += 1
                restore_list_item_ids_range_end *= 2
            for list_item_id in range(restore_list_item_ids_range_start, restore_list_item_ids_range_end + 1):
                if oop_site:
                    self.tc_object.testdata.update_list_item_metadata(list_title, list_item_id, oop_site)
                else:
                    self.tc_object.testdata.update_list_item_metadata(list_title, list_item_id)
            # since last metadata present in metadata list is the restored metadata (at -1), everything else is
            # at -2 and less (if not overwrite restore since overwrite restore will have new metadata for new item IDs)
            if not overwrite_restore:
                backup_metadata_index = backup_metadata_index - 1

            complete_restored_list_metadata = self.tc_object.testdata.testdata_metadata.get(
                self.sp_object.site_url, {}).get("List", {}).get("List Items", {})
            list_item_id = 1
            for list_item in list_items:
                backup_metadata = \
                    self.tc_object.testdata.testdata_metadata.get(self.sp_object.site_url, {}).get("List", {}).get(
                        "List Items", {}).get(list_item_id, [])[backup_metadata_index]
                restore_metadata = {}
                for restore_list_item_id in range(restore_list_item_ids_range_start,
                                                  restore_list_item_ids_range_end + 1):
                    if complete_restored_list_metadata.get(restore_list_item_id)[-1].get(
                            'Title') == backup_metadata.get('Title'):
                        restore_metadata = complete_restored_list_metadata.get(restore_list_item_id)[-1]
                        break
                if latest_version:
                    if len(restore_metadata["Versions Metadata"]) > 1 and restore_metadata[
                        'OData__UIVersionString'] != "1.0":
                        self.log.exception("Didn't restore only latest version")
                        raise Exception("Didn't restore only latest version")

                for v in range(0, len(restore_metadata['Versions Metadata'])):
                    exclude_paths.add("root['Versions Metadata'][" + str(v) + "]['ParentUniqueId']")

                self.compare_backup_and_restore_metadata(backup_metadata, restore_metadata,
                                                         exclude_paths=exclude_paths)
                self.log.info(f"list item {list_item.Title} is validated successfully")
                list_item_id = list_item_id + 1
            for list_item_id in range(restore_list_item_ids_range_start, restore_list_item_ids_range_end + 1):
                self.tc_object.testdata.testdata_metadata.get(
                    self.sp_object.site_url, {}).get("List", {}).get("List Items", {}).get(list_item_id).pop()
        except Exception as exception:
            self.log.exception("Exception while validating list item metadata: %s", str(exception))
            raise exception

    def validate_restore_vectors(self, job_id, file_versions, parent_count=3):
        """Validates restore vectors for multiple incrementals on SharePoint site

            Args:

                job_id          (int)   :       Job ID of the restore job

                file_versions   (int)   :       Number of file versions backed up

                parent_count    (int)   :       Number of parents to the file (E.g: folder, document library, site)

        """
        if file_versions is None:
            raise ValueError("Pass the number of file versions as the 'file_versions' argument")
        if 'DataDirectoryPath' not in self.tc_object.tcinputs:
            raise ValueError('Provide the local JR data directory path of the coordinator. Value at regkey: '
                             r'HKLM\SOFTWARE\CommVault Systems\Galaxy\[Instance #]\Base\szDataDirectoryPath')
        data_dir_path = self.tc_object.tcinputs['DataDirectoryPath']
        for site_url in self.sp_object.site_url_list:
            full_path = ("\\MB\\" + site_url).replace("\\", "\\\\")
            solr_query_url = self.solr_obj.create_solr_query({
                "Url": f'"{full_path}"'
            }, {"CVObjectGUID"})
            try:
                response = requests.get(solr_query_url)
                response_dict = response.json()['response']['docs'][0]
                site_guid = response_dict["CVObjectGUID"]
            except Exception as e:
                self.log.error(f'Error trying to get GUIDs for URL for {site_url}: {e}')
                raise
            machine_obj = Machine(self.sp_object.access_nodes_list[0], self.sp_object.tc_object.commcell)
            staged_objects_path = machine_obj.join_path(data_dir_path, 'iDataAgent', 'JobResults', 'CV_JobResults',
                                                        '2', '0', job_id, 'SP-Restore', site_guid)
            try:
                target_file = 'StagedObjects.csv'
                for f in machine_obj.get_files_in_path(staged_objects_path, recurse=False):
                    if target_file in f:
                        file = f
                        break
                else:
                    raise Exception(f'{target_file} not found')
                folder_count = len(machine_obj.get_folders_in_path(staged_objects_path, recurse=False))
                file = io.StringIO(machine_obj.read_file(file))
            except Exception as e:
                self.log.error(f"Folder path '{staged_objects_path}' doesn't seem to exist. Please check if "
                               "'bKeepStagedFiles.Restore' or 'bKeepStagedFiles' is set in the access node")
                raise Exception(f"Error occured while getting StagedObjects file: {e}")
            csv_data = pd.read_csv(file)
            staged_urls = [url for url in csv_data['Url'] if 'sharepoint' in url]
            self.log.info('Staged URLs:\n' + '\n'.join(staged_urls))
            staged_urls_count = len(staged_urls)
            self.log.info(f'{staged_urls_count = }, {file_versions = }, {parent_count = }')
            if staged_urls_count - file_versions != parent_count or staged_urls_count != folder_count:
                raise Exception(f'Latest versions not restored for file parents for {site_url}')
            self.log.info(f'Restore vectors verified for {site_url}')

    def restore_and_validate_sharepoint_content(self, restore_args=None, folder=None, list=None, file=None,
                                                backup_metadata_index=-1, site_url_list=None,
                                                sites_to_validate=None, multiple_access_nodes=False,
                                                v2_restore=False, validate_restore_vectors=False, file_versions=None):
        """Restores the selected content

            Args:

                restore_args                (dict)  --      dictionary of restore parameters
                                                                Example: restore_args = {
                                                                                    "overwrite": True,
                                                                                    "showDeletedItems": True
                                                                                    }

                folder                      (bool)  --      whether to restore folder if it is granular level restore

                list                        (bool)  --      whether to restore list if it is granular level restore

                file                        (bool)  --      whether to restore file if it is granular level restore

                backup_metadata_index       (int)   --      index of the backup metadata to consider

                site_url_list               (list)  --      if you want to restore multiple sites

                sites_to_validate           (list)  --      if you want to validate multiple sites

                multiple_access_nodes       (bool)  --      whether to validate restore is running on
                                                            multiple access nodes

                v2_restore                  (bool)  --      Whether to use new restore paths

                validate_restore_vectors    (bool)  --      Whether to validate restore vectors instead of metadata

                file_versisons              (int)   --      Number of file versions restored
        """
        if restore_args is None:
            restore_args = {}
        try:
            if site_url_list:
                restore_args['paths'] = restore_args.get('paths', []) + ["MB\\" + url for url in site_url_list]
            if restore_args.get("paths", []):
                # SharePoint Online with new (v2) restore
                if not self.sp_object.v1 and v2_restore:
                    v2_paths = []
                    self.solr_obj.set_cvsolr_base_url()
                    for path in restore_args["paths"]:
                        v2_paths.append(self.extract_path_node(path))
                    restore_args["paths"] = v2_paths.copy()
            else:
                if self.sp_object.v1:
                    restore_args["paths"] = self.get_path_for_v1_restore()
                else:
                    restore_args["paths"] = self.get_path_for_restore(folder, list, file, v2_restore)
            if site_url_list:
                self.log.info("Restoring site collections")
            else:
                self.log.info("Restoring folder and list")
            self.log.info("Path for restore:{0}".format(restore_args["paths"]))
            restore_job = self.sp_object.cvoperations.run_restore(
                multiple_access_nodes=multiple_access_nodes, **restore_args)
            self.log.info("Collecting metadata from SharePoint Site and validating it")
            if not sites_to_validate:
                if site_url_list:
                    sites_to_validate = site_url_list
                else:
                    sites_to_validate = [self.sp_object.site_url]
            if validate_restore_vectors:
                self.validate_restore_vectors(restore_job.job_id, file_versions=file_versions)
            else:
                for site in sites_to_validate:
                    self.sp_object.site_url = site
                    self.log.info(f"Validating restore metadata for {site}")
                    if folder:
                        self.validate_restored_files(backup_metadata_index=backup_metadata_index,
                                                     latest_version=restore_args.get("latest_version", False),
                                                     oop_site=restore_args.get("destination_site", ""))
                    if list:
                        self.validate_restored_list_items(backup_metadata_index=backup_metadata_index,
                                                          latest_version=restore_args.get("latest_version", False),
                                                          overwrite_restore=restore_args.get("overwrite", False),
                                                          oop_site=restore_args.get("destination_site", ""))
            self.tc_object.testdata.share_point_data_flag = True
            return restore_job
        except Exception as exception:
            self.log.exception("Exception while validating restore job: %s", str(exception))
            raise exception

    def process_disk_files(self, file_list, item=None):
        """Returns only file names from file paths of disk files

            Args:

                file_list (list)             --  list of disk files

                item (boolean)               --  whether it is a restored item or default created folder file list

        """
        try:
            dat_count = 0
            user_group_merged_files_count = 0
            files = []
            for file in file_list:
                file_name = file.split("\\")[-1]
                if file_name.endswith(".dat"):
                    dat_count = dat_count + 1
                elif "_UserGroup_" in file_name:
                    user_group_merged_files_count = user_group_merged_files_count + 1
                else:
                    files.append(file_name)
            if user_group_merged_files_count == 0 and (item == "root" or item == "cvtempbackup"):
                self.log.error(f"user group files not restored for {item}")
                raise Exception(f"user group files not restored for {item}")
            elif dat_count == 0 and item == "restored_item":
                self.log.error(f".dat files not restored for {item}")
                raise Exception(f".dat files not restored for {item}")
            else:
                self.log.info(dat_count, " .dat files restored")
            return files
        except Exception as exception:
            self.log.exception('An error occurred while processing disk files')
            raise exception

    def compare_restore_disk_native_files(self, restore_items, destination_client, destination_dir, num_of_backups):
        """Compare file properties for disk restores

            Args:

                restore_items (dict)        --  list of restored items

                destination_client (str)    --  client name where the disk restore happened

                destination_dir (str)       --  path where the disk restore happened

                num_of_backups (int)        -- number of backups ran before disk restore

        """
        try:
            machine_obj = Machine(destination_client, self.tc_object.commcell)
            if not machine_obj.check_directory_exists(destination_dir):
                raise Exception("The directory does not exist")
            disk_restore_files = constants.DISK_RESTORE_AS_NATIVE_FILES_VALIDATE_FILES
            restored_disk_files = []
            root_files_num = len(disk_restore_files.get("root")) + num_of_backups
            restored_items_count = 0
            disk_folders = machine_obj.get_folders_in_path(folder_path=destination_dir, recurse=False)
            disk_folders.extend(machine_obj.get_folders_in_path(folder_path=disk_folders[0]))
            for folder in disk_folders:
                if folder.endswith("\\Lists"):
                    continue
                if folder.split("\\")[-1] == "cvtempbackup":
                    cvtempbackup_files = machine_obj.get_files_in_path(folder_path=folder)
                    restored_disk_files.append(
                        ("cvtempbackup", self.process_disk_files(cvtempbackup_files, "cvtempbackup"), folder))
                elif folder.split("\\")[-1] in restore_items:
                    restored_items_count = restored_items_count + 1
                    item_files = machine_obj.get_files_in_path(folder_path=folder, recurse=False)
                    restored_disk_files.append(
                        ("restored_item", self.process_disk_files(item_files, "restored_item"), folder))
                else:
                    root_files = machine_obj.get_files_in_path(folder_path=folder, recurse=False)
                    restored_disk_files.append(("root", self.process_disk_files(root_files, "root"), folder))
            for item_files in restored_disk_files:
                self.log.info(f"Restored files: {item_files[1]}")
                self.log.info(f"Files to be restored: {disk_restore_files.get(item_files[0])}")
                for file in disk_restore_files.get(item_files[0]):
                    if file not in item_files[1]:
                        self.log.exception(f"Disk files for {item_files[2]} are not validated")
                        raise Exception(f"Disk files for {item_files[2]} are not validated")
                    self.log.info(f"Disk files for {item_files[2]} are validated")
            else:
                if restored_items_count == len(restore_items):
                    self.log.info("All disk files are validated")
                    remote_machine = Machine(destination_client, self.sp_object.cvoperations.commcell)
                    remote_machine.remove_directory(destination_dir, 0)
                else:
                    self.log.exception("All disk files are not restored")
        except Exception as exception:
            self.log.exception('An error occurred while validating restore to disk as native files')
            raise exception

    def compare_restore_disk_original_files(self, machine_obj, testdata_metadata, parent_dir):
        """Compare file properties for disk restores

            Args:

                machine_obj             (Machine)       :   Machine class object of the destination client

                testdata_metadata       (dict)          :   Testdata metadata of parent folder

                parent_dir              (str)           :   Path to the restored folder on the client
        """
        try:
            destination_dir = machine_obj.join_path(parent_dir, testdata_metadata.get("Folder URL").split(
                "/", 3)[-1].replace("shared documents", "Shared Documents"))
            if not machine_obj.check_directory_exists(destination_dir):
                raise Exception(f"The directory {destination_dir} does not exist")

            disk_restored_files_properties = machine_obj.scan_directory(path=destination_dir, filter_type="file",
                                                                        recursive=False)
            if "Folder" in testdata_metadata:
                for folder in testdata_metadata["Folder"]:
                    self.compare_restore_disk_original_files(machine_obj, folder, parent_dir)

            file_properties_dict = {
                props["path"].split(machine_obj.os_sep)[-1]: props for props in disk_restored_files_properties
            }
            for file, file_metadata in testdata_metadata["Files"].items():
                file = file.replace('%', '%25')
                if file not in file_properties_dict or file_properties_dict[file]["size"] != file_metadata[-1]["Length"]:
                    raise Exception(f"{file} is not restored properly in {destination_dir}")

            self.log.info(f"{destination_dir} has been restored correctly")
            machine_obj.remove_directory(destination_dir, 0)
        except Exception as exception:
            self.log.exception('An error occurred while validating restore to disk as original files')
            raise exception
