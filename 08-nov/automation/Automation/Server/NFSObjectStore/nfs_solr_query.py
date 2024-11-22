# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""File for performing NFS server related operations in Commcell

ObjectstoreSolrHelper is the only class defined in this.

ObjectstoreSolrHelper: Provides methods which are relevant to
                       NFS index related operations

ObjectstoreSolrHelper:
    __init__()                       --  initialize instance of the
    ObjectstoreSolrHelper class

    create_solr_query()             --  creates solr query for given NFS index core

    create_url_and_get_response()   --  Helper method to get results from a url

    check_if_error_in_response()    --  Method to check if response has error

    check_is_visisble()             --  check for is_visible flag set to given value for files

    collect_index_details()         -- collect_index_details

    collect_archfile_details()      -- collects archfile Ids for given list of files

    validate_deleted_items_index()  -- validates deleted files details are cleared in latest core

    validate_is_pruned()            -- validates is_pruned flag for given file names

    validate_afiles_after_synthfull() -- validates afiles are prunable and archfile Ids are carried
    forward correctly

"""
import requests
import json

from AutomationUtils import logger
from Application.Exchange.SolrSearchHelper import SolrSearchHelper
from dynamicindex.Datacube.dcube_solr_helper import SolrHelper as dCubeSolrHelper
from Application.Exchange.ExchangeMailbox.solr_helper import SolrHelper


class ObjectstoreSolrHelper:
    """Base class to execute solr related operations """

    def __init__(self, tc_obj, index_server_cloud):
        """Initialize instance of the ObjectstoreSolrHelper class..
            Args:
                tc_obj (obj)    -- test case object

                index_server_cloud (str)    --  name of solr cloud server used in objectstore

            Returns:
                object - instance of the ObjectstoreClientUtils class

            Raises:
                Exception:
                    if any error occurs in Initialize

        """
        self.log = logger.get_log()
        self.solr_search_obj = SolrSearchHelper(tc_obj)
        clientnames = self.solr_search_obj.get_index_server_client_names(index_server_cloud)

        # get base URL
        dcube_helper_obj = dCubeSolrHelper(tc_obj)
        base_client = str(clientnames[0][0])
        self.base_url = dcube_helper_obj.get_solr_baseurl(base_client, 5)
        self.log.info(self.base_url)
        self.nfs_index_cores = {'extent': 'nfsindexextent',
                                'version': 'nfsindexversion',
                                'latest': 'nfsindexlatest'}

    def create_solr_query(self, index_core, select_dict=None, attr_list=None, op_params=None):
        """creates solr query for given NFS index core
            Args:
                index_core(str)     --  NFS index core to query the search

                select_dict(dict)   --  dictionary containing select query

                 attr_list (list)   -- attribute list

                op_params(dictionary)       --  Other params and values for solr query
                                                (Ex: start, rows)

            Returns:
                The solr url based on params
        """
        try:
            self.log.info("Creating solr URL")
            search_query = f'q='
            simple_search=0
            if select_dict:
                for key, value in select_dict.items():
                    if isinstance(value, list):
                        search_query += f'{key}:{str(value[0])}'
                        for val in value[1:]:
                            search_query += f' OR {key}:{str(val)}'
                        search_query += " AND "
                    elif key=="keyword":
                        search_query += "("+value+")"
                        simple_search=1
                        break
                    else:
                        search_query = search_query + f'{key}:{str(value)} AND '

            if simple_search==0:
                search_query = search_query[:-5]
            self.log.info("Search query: %s" % search_query)
            field_query = ""
            if attr_list:
                field_query = "&fl="
                for item in attr_list:
                    field_query += f'{str(item)},'
                field_query = field_query[:-1]
                self.log.info("Field query formed: %s" % field_query)
            ex_query = ""
            if not op_params:
                op_params = {'wt': "json", "rows": "50"}
            else:
                op_params['wt'] = "json"
            for key, value in op_params.items():
                if value is None:
                    ex_query += f'&{key}'
                else:
                    ex_query += f'&{key}={str(value)}'
            self.log.info("Optional parameters are: %s" % ex_query)

            final_url = (f'{self.base_url}'
                         f'/{self.nfs_index_cores[index_core]}/'
                         f'select?'
                         f'{search_query}'
                         f'{field_query}'
                         f'{ex_query}')
            return final_url

        except Exception as excp:
            self.log.exception("Exception while creating solr query: %s" % str(excp))
            raise excp

    def create_url_and_get_response(self,
                                    index_core,
                                    select_dict=None,
                                    attr_list=None,
                                    op_params=None):
        """Helper method to get results from a url
            Args:
                index_core(str)     --  NFS index core to query the search

                select_dict(dict)   --  dictionary containing select query

                attr_list (list)   -- attribute list

                op_params(dictionary)       --  Other params and values for solr query
                                                (Ex: start, rows)

            Returns:
                The solr url based on params
        """
        if index_core not in self.nfs_index_cores:
            self.log.exception("%s core is not valid. available cores:%s" % (index_core,
                                                                             list(self.nfs_index_cores.keys())))
        try:
            solr_url = self.create_solr_query(index_core, select_dict=select_dict,
                                              attr_list=attr_list, op_params=op_params)
            self.log.info("URL formed from the details provided is: %s" % solr_url)
            response = requests.get(url=solr_url)
            self.check_if_error_in_response(response)
            results = json.loads(response.content)
            return results['response']['docs']
        except Exception as excp:
            raise excp

    def check_if_error_in_response(self, response):
        """Method to check if response has error
            Args:
                response(obj)         --  Response Object

            Raises:
                Exception if response was error
        """
        try:
            if response.status_code != 200:
                raise Exception("Error in calling solr URL. Reason %s" % response.reason)
            response = json.loads(response.content)
            if "error" in response:
                raise Exception("Error in the solr URL. Reason %s " % response["error"]["msg"])
        except Exception as excp:
            self.log.exception(excp)
            raise excp

    def check_is_visisble(self, files_list, index_core, application_id, is_visible=True):
        """check for is_visible flag set to given value for files
            Args:
                files_list(list)   -- list of file names for which is_visible flag need
                                      to be check

                index_core(str)     --  NFS index core to query the search

                application_id(int)   --  application id of objectstore

                is_visible (bool)   -- is_visible flag value to be checked
            Returns:
                True - Success
                False - on failure
        """
        status = True
        select_dict = {'ApplicationId': application_id}
        self.log.info("verifying is_visible flag in index server")
        index_details = self.create_url_and_get_response(index_core, select_dict=select_dict)
        for item in index_details:
            if item['FileName'] in files_list and item['IsVisible'] != is_visible:
                self.log.error("IsVisible is not set to %s for file %s" % (is_visible, item['FileName']))
                self.log.error("{%s}" % item)
                status = False

        if not status:
            self.log.exception("IsVisible flag check failed. query results")
        else:
            self.log.info("IsVisible flag to %s verified successfully" % is_visible)
        return status

    def collect_index_details(self, application_id):
        """Helper method to get results from a url
            Args:
             application_id(int)   --  application id of objectstore

            Returns:
                dictionaries of latest and extent core details with
                filename and contentid as key respectively
        """
        latest_core_details = {}
        extent_core_details = {}
        select_dict = {'ApplicationId': application_id}
        result = self.create_url_and_get_response("latest", select_dict=select_dict)
        for item in result:
            latest_core_details[item['FileName']] = item

        result = self.create_url_and_get_response("extent", select_dict=select_dict)
        for item in result:
            extent_core_details[item['contentid']] = item

        return latest_core_details, extent_core_details

    def collect_archfile_details(self, application_id, req_files_list):
        """collects archfile Ids for given list of files
            Args:
                application_id(int)   --  application id of objectstore

            Returns:
                dictionary of archfile details {'filename':[list of archfiles]
        """

        latest_core_details, extent_core_details = self.collect_index_details(application_id)

        self.log.debug("found index details latestcore:%s, extentcore:%s" %
                      (latest_core_details, extent_core_details))

        self.log.info("note down archfileId for given files %s" % req_files_list)
        arch_file_map = {}
        files_intersection = list(set(req_files_list).intersection(list(latest_core_details.keys())))

        # as we cannot sort given file name string we have to compare two list which are unordered
        common_files = [x for x in req_files_list if x in files_intersection]
        self.log.debug("intersection of required files and all files in latest core %s" % files_intersection)
        if len(common_files) != len(req_files_list):
            self.log.exception("latest core index details not found for all given files")
            return

        for file_name in req_files_list:
            content_id_temp = latest_core_details[file_name]['contentid']
            content_ids = [x for x in extent_core_details.keys() if content_id_temp in x]
            if not bool(content_ids):
                self.log.exception("no contentID found for filename %s and contentID %s" %(file_name, content_id_temp))

            arch_file_map[file_name] = []
            for content_id in content_ids:
                arch_file_id = extent_core_details[content_id]['AchiveFileId']
                if arch_file_id not in arch_file_map[file_name]:
                    arch_file_map[file_name].append(arch_file_id)

        return arch_file_map

    def validate_deleted_items_index(self, deleted_files_list, application_id):
        """validates deleted files details are cleared in latest core
            Args:
                deleted_files_list(list)   -- list of file names for which
                                              index details to be cleared

                application_id(int)   --  application id of objectstore
            Returns:
                None
        """
        select_dict = {'ApplicationId': application_id}
        results = self.create_url_and_get_response("latest", select_dict=select_dict)
        file_names = []
        for item in results:
            file_names.append(item['FileName'])

        if bool(set(file_names).intersection(deleted_files_list)):
            self.log.exception("deleted files details are not cleared in latest core"
                               "latest core output %s" % results)
        else:
            self.log.info("deleted files details are cleared in latest core")

    def validate_is_pruned(self, deleted_files, app_id, is_pruned=True):
        """validates is_pruned flag for given file names
            Args:
                deleted_files(list)   -- list of file names for which
                                         index details to be cleared

                app_id(int)   --  application id of objectstore

                is_pruned(bool) -- value of isPruned field
            Returns:
                None
        """
        latest_core, extent_core = self.collect_index_details(app_id)
        status = True
        for file_name in deleted_files:
            if not bool(latest_core.get(file_name)):
                self.log.exception("file details %s not found in latest core")
            if latest_core[file_name]['IsPruned'] != is_pruned:
                self.log.exception("IsPruned is not marked to %s. Item:{%s}" %
                                   (is_pruned, latest_core[file_name]))
                status = False

        if not status:
            self.log.exception("IsPruned flag check failed. query results %s" % latest_core)
        else:
            self.log.info("IsPruned flag verified successfully")

    def validate_afiles_after_synthfull(self,
                                        tc_obj,
                                        afiles_before_synthfull,
                                        afiles_after_synthfull,
                                        deleted_files,
                                        non_deleted_files,
                                        deleted_afiles):
        """validates afiles are prunable and archfile Ids are carried forward correctly
            Args:
                tc_obj (obj)    --  testcase object which contain csdb instance

                afiles_before_synthfull (dict) -- filename and archfile ID
                        details before running synthfull Job

                afiles_after_synthfull (dict) -- filename and archfile ID
                        details after running synthfull Job

                deleted_files (list) -- list of filenames deleted

                non_deleted_files(list) -- list of filenames not deleted

                deleted_afiles (list)   -- afiles which are part of delted files
            Returns:
                None
        """
        # check if old afiles are reflected in ArchFileSpaceReclamation table
        query = "select * from ArchFileSpaceReclamation"
        tc_obj.csdb.execute(query)
        results = tc_obj.csdb.fetch_all_rows()
        self.log.info("ArchFileSpaceReclamation results %s" % results)
        if not bool(results):
            self.log.exception("no prunable afiles found in ArchFileSpaceReclamation table")

        prunable_afiles_from_db = [int(x[0]) for x in results]
        self.log.info("archfileIds from ArchFileSpaceReclamation table {%s}" %
                      prunable_afiles_from_db)
        deleted_afiles = list(set(deleted_afiles))
        afiles_inersection = list(set(prunable_afiles_from_db).intersection(deleted_afiles))
        afiles_inersection.sort()
        deleted_afiles.sort()
        if deleted_afiles == afiles_inersection:
            self.log.info("all expected afiles {%s} found in"
                          "ArchFileSpaceReclamation table" % deleted_afiles)
        else:
            self.log.info("all expected afiles {%s} not found in"
                          "ArchFileSpaceReclamation table" % deleted_afiles)

        self.log.info("validate archFileId is not changed for deleted items")
        for file_name in deleted_files:
            if afiles_before_synthfull[file_name] != afiles_after_synthfull[file_name]:
                self.log.exception("deleted file %s having new afileId" % file_name)
        self.log.info("validation of archFileId for deleted items is successful")

        self.log.info("validate archFileId is changed for non deleted items")
        for file_name in non_deleted_files:
            if afiles_before_synthfull[file_name] in deleted_afiles and \
                    afiles_before_synthfull[file_name] == afiles_after_synthfull[file_name]:
                raise Exception("non deleted file having deleted afileId."
                                "{%s}:{%s}" % (file_name, afiles_before_synthfull[file_name]))
        self.log.info("validation of archFileId for non deleted items is successful")
