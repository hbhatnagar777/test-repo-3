# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the functions to validate software cache/ remote cache media

CommServeCache_Validation -- Class to validate software cache media
RemoteCache_Validation    -- Class to validate remote cache media
Download_Validation       -- Class to validate downloaded media

CommServeCache_Validation
=========================

    __init__()                          -- initialize instance of the CommServeCache_Validation class
    get_files_in_cache()                -- returns list of files in the given cache path
    _get_name_from_osid()                -- returns os name for the given os id
    compute_windows_third_party_packages_to_sync()      -- compute Third Party Packages to Sync based on the available
                                                           packages on CS's cache and those configured for RC
    get_binary_info_dict()              -- converts BinaryInfo.xml to dict
    list_from_binary_info_dict()        -- returns list of cab files and MSIs from Binaryinfo.xml dictionary
    get_os_in_cs_cache()                -- returns list of os ids present in cs cache
    expected_package_list()             -- returns all Packages to be synced


RemoteCache_Validation
=========================

     __init__()                                       --  initialize instance of the RemoteCache_Validation class
     get_media_from_remotecache()                     --  returns list of media present in remote cache
     validate_remote_cache()                          -- validate remote cache media
     validate_cu_pack_in_remotecache()                -- validates cu pack present in media
     set_os_for_sync_all                              -- returns dictionary of os and packages present in cs cache
     get_files_to_be_present_in_remote_cache()        -- computes list of files to be present in the remote cache
     get_os_configured_on_remote_cache()              -- returns list of oses to be synced to remote cache

DownloadValidation
==========================

    __init__()                            --  Initialize instance of the DownloadedSoftwareValidation Class
    get_simos_patchos_dict()              --  Creates a dictionary of Simbinarysetid to PatchUpdateOS
    download_validation()                 --  Validates download by going through the files
    set_updates_path()                    --  This sets the looseupdates folder path for every flavor of OS
    download_xml()                        --  downloads xml files from server
    parse_cu_xml()                        --  Downloads and parses the files needed from the server
    get_cu_pack_files_from_cache()        --  gets the CU pack file list from CS software cache/ remote cache
    generate_cu_configuration_url()       --  generates cu configuration URL in the HTTP server
    get_cu_pack_details()   --  returns the transaction id of a particular CU
    get_latest_cu_pack()                  --  returns latest CU pack for a service pack
    validate_files_downloaded_for_cu_pack()   --  Validates files in CU Pack downloaded
    check_for_checksumfile()              --  Checks if UpdatesChecksum.txt file is present in the loose updates folder
    get_os_updates_dict_in_cache()        --  Gets the dict having Os and Loose updates
    get_latest_dvd_path()                 --  gets the latest path of CVMedia
    get_sp_info()                         --  Returns the transaction  id, revision id, and sp major
    validate_media()                      --  Validates CV Media in software cache
    get_bi_wp_xml()                       --  downloads BinaryInfo and WinPackages
    get_packages()                        --  Returns a list of package after parsing through WinPackages.xml
    filter_binary_dict()                  --  Filters the binaries_dict dictionary based on packages provided
    filter_skipped_files()                --  Filters through the file list and keeps files not included in the ignoreList
    validate_count_of_files()             --  validates the count of files downloaded and count of files to be downloaded
    get_cu_path()                         --  Returns the path to CumulativeUpdatePackInstallPack.xml
    compare_ftp_cache_updates()           --  Compares updates in xml downloaded and Cache
    compare_ftp_cache_hotfix_xml()        --  Compares UpdatesInfo.xml present in cache and FTP and check if correct XMl is placed in cache
    get_hotfix_xml_os_updates_dict()      --  From parsed UpdatesInfo gets the  OS:Updates dict to compare
    get_hotfix_xml()                      --  return the path for UpdatesInfo xml
    parse_hotfix_xml()                    --  parses file in hotfix path and returns its content in a dict
    validate_hotfixes()                   --  validates hotfixes downloaded
"""
from xml.etree import ElementTree as ET
import os.path
import os
import urllib3
import xmltodict
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils import database_helper, logger
from AutomationUtils import cvhelper
from AutomationUtils import commonutils
from AutomationUtils import config
from AutomationUtils.machine import Machine
from Install import installer_constants
from Install.softwarecache_helper import SoftwareCache
from Install import installer_utils
from Web.AdminConsole.Helper import adminconsoleconstants
from cvpysdk.deployment import deploymentconstants


class CommServeCache:
    """Download validator class to validate commserve cache"""

    def __init__(self, client_obj, commcell, machine_obj=None):
        """
        Initialize instance of the CommServeCache class.

        Args:
            commcell_obj -- commcell object

            client_obj   -- client object


        """

        self.commcell = commcell
        self.csdb = database_helper.get_csdb()
        self.log = logger.get_log()
        self.client_obj = client_obj
        self.config_json = config.get_config()
        self.machine_obj = machine_obj if machine_obj else Machine(self.client_obj)
        self.software_cache_obj = SoftwareCache(self.commcell, self.client_obj)
        self.cs_client = Machine(self.commcell.commserv_client)
        self.cs_cache_path = self.software_cache_obj.get_cs_cache_path()
        self.ignore_list = installer_constants.IGNORE_LIST
        self.trans_id = None
        self.revision_id = None
        self.filtered_dict = {}
        self.local_machine = Machine()
        self.options_selector = OptionsSelector(self.commcell)
        self.sample_folder = OptionsSelector.get_drive(self.local_machine) + 'SWTestFolder'
        if not self.local_machine.check_directory_exists(self.sample_folder):
            self.local_machine.create_directory(self.sample_folder)
    def execute_sp(self, query):
        """
        executes stored procedure
        """
        try:
            encrypted_password = self.cs_client.get_registry_value(r"Database", "pAccess")
            sql_password = cvhelper.format_string(self.commcell, encrypted_password).split("_cv")[1]
            sql_instancename = self.commcell.commserv_hostname.lower()
            if not self.commcell.is_linux_commserv:
                sql_instancename += "\\commvault"
            db = database_helper.MSSQL(
                server=sql_instancename,
                user='sqladmin_cv',
                password=sql_password,
                database='commserv',
                as_dict=False
            )
            return db.execute(query)

        except Exception as exp:
            raise Exception("Failed to execute stored procedure - %s, exp")

    def get_files_in_cache(self, cache_machine_obj=None, media=None):
        """
        Returns list of files in the given cache path.
        Args:
            cache_machine_obj (object) - machine obj for the machine where the cache is present
            media (str) - media to check E.g. SP19_2482227_R737

        Returns:
            list of files in the cache path

        Raises:
            exception if unable to find path
        """
        folder_path = None
        try:
            if not cache_machine_obj:
                cache_machine = self.cs_client
                if media:
                    folder_path = cache_machine.join_path(self.cs_cache_path,
                                                          installer_constants.DOWNLOAD_SOFTWARE_DEFAULT_MEDIA,
                                                          self.software_cache_obj.get_version(), media)
                else:
                    folder_path = self.cs_cache_path
            else:
                cache_machine = cache_machine_obj
                folder_path = self.software_cache_obj.get_remote_cache_path_to_validate(media)
            files_in_cache = set()
            files = cache_machine.get_files_in_path(folder_path=folder_path)

            for each_file in files:
                is_found = False
                for each in self.ignore_list:
                    if each in each_file:
                        is_found = True
                        break
                if not is_found and "11.0.0" in each_file:
                    if 'windows' in cache_machine.os_info.lower():
                        files_in_cache.add(each_file.split("11.0.0\\")[1])
                    else:
                        files_in_cache.add(each_file.split("11.0.0/")[1].replace("/", "\\"))
            return list(files_in_cache)

        except Exception as exp:
            raise Exception("Exception while getting list of files from cache path %s - %s", folder_path, exp)

    def get_name_from_osid(self, os_id):
        """
        Returns os name for the given os id
        Args:
            os_id (int) - os id

        Returns:
            os name for the given os id
        """

        if os_id != 0:
            query = (f"select simBinarySet.processorName,simBinarySet.name from PatchUpdateOS,simBinarySet where "
                     f"PatchUpdateOS.BinarySetID = simBinarySet.id and PatchUpdateOS.NewUpdateOSID = {os_id}")
            self.csdb.execute(query)
            os_name = self.csdb.fetch_one_row()
        else:
            os_name = installer_constants.OSNAME_LIST[os_id]
        base_os = "Windows" if ("win" in os_name[0]) else "Unix"
        return os_name[0], base_os, os_name[1]

    def compute_windows_third_party_packages_to_sync(self, media):
        """
        Compute Third Party Packages to Sync based on the available packages on CS's cache and those configured for RC

        Raises:
            exception if unable to parse/get winpackages.xml

        """
        try:
            _feature_release = installer_utils.get_latest_recut_from_xml(self.commcell.commserv_version)
            url = installer_constants.DEFAULT_PACKAGE_INSTALL_PATH_WINDOWS.format(_feature_release)
            win_package_xml_path = installer_utils.download_file_from_http_server(url)
            third_party_list = []

            for key, value in self.filtered_dict.items():
                if int(key) == 1:
                    third_party_list = third_party_list + self.software_cache_obj.get_third_party_packages(
                        win_package_xml_path, 1, value)
                elif int(key) == 3:
                    third_party_list = third_party_list + self.software_cache_obj.get_third_party_packages(
                        win_package_xml_path, 3, value)
            computed_third_party_list = list(set(third_party_list))
            self.filtered_dict[0] = computed_third_party_list
            self.log.info("Third party package id are %s", computed_third_party_list)

        except Exception as exp:
            self.log.exception("Exception in Computing ThirdParty Packages to sync - %s", exp)

    def get_binary_info_dict(self, binary_info_xml_path):
        """
        Converts BinaryInfo.xml to dict
        Args:
           binary_info_xml_path - xml path of binaryinfo.xml
        returns:
            binary info dictionary
        """

        tree = ET.parse(binary_info_xml_path)
        root = tree.getroot()
        binary_info_dict = self.software_cache_obj.binary_info_xml_to_dict(root)
        return binary_info_dict

    def list_from_binary_info_dict(self, binary_info_dict, binary_set_id, packages):
        """
        Create list of cab files and MSIs from Binaryinfo.xml dictionary
        Args:
           binary_info_dict -- binary info dict
           binary_set_id    -- binary set id found in the xml
           packages         -- list of package ids
        returns:
            filtered list with only required cab files and MSIs
        """

        final_list = []
        os_dict = binary_info_dict[str(binary_set_id)]
        for key, value in os_dict.items():
            try:
                if int(key) in packages:
                    package_dict = os_dict[key]
                    for k, v in package_dict.items():
                        if "Common\\OEM" in k:
                            found = False
                            for each in installer_constants.EXCLUDE_OEM:
                                if each in k:
                                    found = True
                                    break
                            if not found:
                                file = k
                        else:
                            file = k
                        if file:
                            listval = file
                            final_list.append(listval)
            except Exception as exp:
                self.log.exception("Exception in getting package id and retrieving list of files %s", exp)
        return final_list

    def get_os_in_cs_cache(self, service_pack=None):
        """
        returns list of oses present in cs cache
        Args:
            service_pack (str) -- Service pack E.g. 19

        Returns:
            returns list of os ids present in cs cache (list)

        """
        if not service_pack:
            service_pack = self.commcell.commserv_client.service_pack
        cs_os_list = []
        query = f"select OSId from PatchMultiCache where ClientId = 2 and HighestSP = {service_pack}"
        self.csdb.execute(query)
        data = self.csdb.fetch_all_rows()
        for each in data:
            cs_os_list.append(each[0])
        return cs_os_list

    def expected_package_list(self, package_list, optype=0,
                              client_type=0, client_id=2, prev_rel_id=16, new_rel_id=16, os_id=3):
        """
        returns all Packages to be synced
        Args:
            package_list (list)     - packages list to be installed
            optype (int)            - sync =0 install/update/upgrade = 1
            client_type (int)       - remote cache = 0 client = 1
            client_id (int)         - client id
            prev_rel_id (int)       - V11=16, V10=15, V9=14
            new_rel_id (int)        - current release id
            os_id (int)             - patchupdateos id of the os involved in sync/install
        returns:
            new packages list(integer list)
        raises:
            exception if unable to execute stored procedure
        """

        try:

            for os, packages in package_list.items():
                self.log.info(
                    "Adjusting input package list %s for client ID %s and OS %s", packages, client_id, os_id)
                parameters = "'%s', %d, %d, %d, %d, %d, %d" % (', '.join(
                    map(str, packages)), optype, client_type, int(client_id), prev_rel_id, new_rel_id, int(os))
                query = f'exec simAdjustPkgListForRemoteOperation {parameters}'
                expected_packages = self.execute_sp(query)
                expected_packages = expected_packages.rows[0][0].split(",")
                package_list[os] = [int(package) for package in expected_packages]
            return package_list

        except Exception as exp:
            raise Exception("Failed to obtain adjusted package list - %s", exp)


class RemoteCache(CommServeCache):
    """
    Class to validate Remote cache media
    """

    def __init__(self, client_obj, commcell, machine_obj=None, **kwargs):
        """
        Initialize instance of the RemoteCache class.

        Args:
            commcell_obj -- commcell object

            client_obj   -- client object

        **kwargs: (dict) -- Key value pairs for supporting conditional initializations
            Supported -
            os_ids (list of integers) -- osids to be synced for lower sp media
        """
        super(RemoteCache, self).__init__(client_obj, commcell, machine_obj, **kwargs)
        self.os_ids = kwargs.get('os_ids')
        self.media = None

    def get_media_from_remotecache(self, rcname):
        """
        returns list of media present in remote cache

        Args:
            rcname - name of the remote cache client
        """
        try:
            media_in_cache = []
            feature_release = []
            folder = None
            self.log.info("Since Commserver is not selected we pick the same media installed on CS")
            query = f"select HighestSP from PatchMultiCache where ClientId = " \
                    f"(select id from APP_CLient WITH (NOLOCK) where name like '{rcname}')"
            self.csdb.execute(query)
            data = self.csdb.fetch_all_rows()
            for value in data:
                feature_release.append(int(value[0]))
            feature_release = list(set(feature_release))
            for sp in feature_release:
                query = "select top 1 Release,SPMajor,TransactionID,RevisionID from PatchSPVersion where SPMajor=%d order by RevisionID DESC" % int(
                    sp)
                self.csdb.execute(query)
                sp_data = self.csdb.fetch_all_rows()
                folder = "SP" + str(sp_data[0][1]) + "_" + str(sp_data[0][2]) + "_R" + str(sp_data[0][3])
                media_in_cache.append(folder)
            return media_in_cache

        except Exception as err:
            self.log.exception("Failed to get media from Remote Cache - %s", err)

    def validate_cu_pack_in_remotecache(self):
        """
        validates cu pack present in media in remote cache
        """
        try:
            self.log.info("Validating CU pack files for media :%s", self.media)
            self.download_validator = DownloadValidation(self.commcell, self.client_obj,
                                                         media=self.media, machine_obj=self.machine_obj)
            for _eachos, _packages in self.filtered_dict.items():
                _eachos = int(_eachos)
                if _eachos != 0:
                    # Taking list of CU packs available in CS software cache
                    self.log.info("Validating CU pack for OS [%s]", installer_constants.OSNAME_LIST[_eachos][2])
                    try:
                        os_xml_name, self.base_os, os_binary_info_name = self.get_name_from_osid(int(_eachos))
                        self.cu = installer_utils.get_latest_cu_from_media(
                            self.commcell.commserv_cache.get_cs_cache_path(),
                            self.cs_client)
                        self.download_validator.validate_files_downloaded_for_cu_pack(
                            _eachos, self.cu, selected_packages=list(_packages))
                        if not self.download_validator.status:
                            self.status = False
                    except Exception as err:
                        self.log.exception("Exception occured in validating CU pack for OS [%s] %s" % (
                            installer_constants.OSNAME_LIST[_eachos][2], str(err)))
        except Exception as err:
            self.log.exception("exception occured in validating CU pack under Remote cache %s" % str(err))

    def set_os_for_sync_all(self):
        """
        returns dictionary of os and packages present in cs cache

        returns:
                dictionary of os-packages in cs cache
        """

        current_sp = self.media.split('_')[0].strip('SP')
        cs_os_list = self.get_os_in_cs_cache(current_sp)
        for each in cs_os_list:
            if each in ["1", "3"]:
                url = installer_constants.DEFAULT_PACKAGE_INSTALL_PATH_WINDOWS.format(self.media)
            else:
                url = installer_constants.DEFAULT_PACKAGE_INSTALL_PATH_UNIX.format(self.media)
            pkg_xml_path = installer_utils.download_file_from_http_server(url)
            self.filtered_dict[each] = map(int, installer_utils.get_packages_to_download(
                pkg_xml_path))

    def validate_remote_cache(self, configured_os_pkg_list, sync_all=False):
        """
        Validates remote cache media
        Args:
            configured_os_pkg_list(dict) -  Configured list of oses and packages
            sync_all (boolean)           -  If RC is configured to sync all oses

        Raises:
            exception if unable to get the list of files in the cache
        """
        media_in_cache = self.get_media_from_remotecache(self.client_obj.client_name)
        for media in media_in_cache:
            self.media = media
            self.base_path = self.cs_client.join_path(self.cs_cache_path,
                                                      installer_constants.DOWNLOAD_SOFTWARE_DEFAULT_MEDIA,
                                                      self.software_cache_obj.get_version(), self.media)
            self.log.info("Media to check: %s", self.media)
            self.filtered_dict = {}
            self.status = True
            if sync_all:
                files_in_remote_cache = self.get_files_in_cache(self.machine_obj, media=self.media)
                self.log.info(
                    "Files in %s remote cache:%s", self.client_obj.client_name, files_in_remote_cache)
                files_in_cs_cache = self.get_files_in_cache(media=self.media)
                self.log.info("Files in CS cache:%s", files_in_cs_cache)
                ret, _ = self.machine_obj.compare_lists(files_in_cs_cache, files_in_remote_cache, sort_list=True)
                if not ret:
                    self.log.error("Client side Remote cache media validation failed")
                    self.status = False
                self.set_os_for_sync_all()
                self.validate_cu_pack_in_remotecache()
            else:
                self.configured_os_pkg_list = configured_os_pkg_list
                files_in_remote_cache = self.get_files_in_cache(self.machine_obj, media=self.media)
                self.log.info(
                    "Files in %s remote cache:%s", self.client_obj.client_name,
                    files_in_remote_cache)
                files_to_be_present_in_remote_cache = self.get_files_to_be_present_in_remote_cache()
                self.log.info("Files to be present in RC:%s", files_to_be_present_in_remote_cache)
                ret, _ = self.machine_obj.compare_lists(
                    list(
                        set(files_to_be_present_in_remote_cache)), list(
                        set(files_in_remote_cache)), sort_list=True)
                if not ret:
                    self.log.error("Client side Remote cache media validation failed")
                    self.status = False
                self.validate_cu_pack_in_remotecache()
            if not self.status:
                raise Exception("Remote Cache Validation failed. Please check logs")

    def get_files_to_be_present_in_remote_cache(self):
        """
        Computes list of files to be present in the remote cache.
        Returns:
            list of files to be present in the remote cache
        Raises:
            exception if unable to compute list of files
        """

        files_to_be_present = []
        to_delete = []
        self.log.info("Filtering based on OS present in CS cache")
        cs_os_id = list(map(int, self.get_os_in_cs_cache(self.media.split("_")[0].lower().split("sp")[1])))
        rc_configured_os = self.get_os_configured_on_remote_cache()
        for key, value in rc_configured_os.items():
            if int(key) in cs_os_id:
                self.filtered_dict[key] = rc_configured_os[key]
        self.log.info("Computing Windows Third party packages to sync")
        self.compute_windows_third_party_packages_to_sync(self.media)
        remote_cache_path = self.software_cache_obj.get_remote_cache_path_to_validate(self.media)
        for key, value in self.filtered_dict.items():
            os_xml_name, base_os, os_binary_info_name = self.get_name_from_osid(int(key))
            self.log.info("OS Name for int(key) is %s", os_xml_name)
            if base_os == "Windows":
                url = installer_constants.BINARYINFO_PATH_WINDOWS.format(self.media)
            else:
                url =installer_constants.BINARYINFO_PATH_UNIX.format(self.media, os_xml_name)
            binary_info_xml_path = installer_utils.download_file_from_http_server(url)
            binary_info_dict = self.get_binary_info_dict(binary_info_xml_path)
            if int(key) != 0:
                query = f"select max(BinarySetID) from PatchUpdateOS where NewUpdateOSID = {key}"
                self.csdb.execute(query)
                binary_set_id = self.csdb.fetch_one_row()[0]
            else:
                binary_set_id = 0
            filtered_binary_info_dict = self.list_from_binary_info_dict(binary_info_dict, binary_set_id, value)
            for each in filtered_binary_info_dict:
                fullpath = each.replace("/", "\\")
                mediapath = f"{remote_cache_path}\\{base_os}\\{os_xml_name}" \
                    if (base_os == "Unix") else f"{remote_cache_path}\\{base_os}"
                fullpath = mediapath + "\\" + fullpath
                files_to_be_present.append(fullpath)
        win_root_list, unix_root_list = self.software_cache_obj.get_root_files(remote_cache_path)
        if self.machine_obj.os_info.upper() == "WINDOWS":
            if any(int(key) not in [1, 3, 0] for key in self.filtered_dict):
                files_to_be_present = files_to_be_present + unix_root_list
            files_to_be_present = files_to_be_present + win_root_list
        else:
            if any(int(key) in self.filtered_dict for key in [1, 3]):
                files_to_be_present = files_to_be_present + win_root_list
            files_to_be_present = files_to_be_present + unix_root_list
        _client_prop = self.client_obj.properties.get('clientProps')
        force_client_side_download = _client_prop.get('forceClientSideDownload')
        if force_client_side_download==2:
            query = "declare @inxml XML  = '<App_IsForceClientSideDownloadSetReq clientId=\"{0}\" option=\"0\" " \
                    "/>';exec IsForceClientSideDownloadSet @inxml".format(self.client_obj.client_id)
            output = self.options_selector.update_commserve_db(query)
            xml_msg = output.get_column(output.rows[0], output.columns[0])
            force_client_side_download = int(ET.fromstring(xml_msg).attrib["forceClientSideDownload"])
        if force_client_side_download==1:
            for key, value in self.filtered_dict.items():
                os_xml_name, base_os, os_binary_info_name = self.get_name_from_osid(int(key))
                if key != deploymentconstants.OSNameIDMapping.WINDOWS_32.value and \
                        key != deploymentconstants.OSNameIDMapping.WINDOWS_64.value and key != 0:
                    for pkg in installer_constants.SYNC_UNIX_CU_SKIP_LIST:
                        full_path = f"{remote_cache_path}\\{base_os}\\{os_xml_name}\\{os_binary_info_name}" \
                                    f"\\BinaryPayLoad\\{pkg}"
                        files_to_be_present.append(full_path)
        for count, element in enumerate(files_to_be_present):
            files_to_be_present[count] = element.replace("/", '\\')
        for count, element in enumerate(files_to_be_present):
            for each in self.ignore_list:
                if each in str(element):
                    to_delete.append(count)
                    break
                else:
                    corrpath = element.split("11.0.0\\")[1]
                    files_to_be_present[count] = corrpath

        for file in sorted(to_delete, reverse=True):
            del files_to_be_present[file]

        return files_to_be_present

    def get_os_configured_on_remote_cache(self):
        """
        returns list of oses to be synced

        Returns:
            returns dictionary of list of oses and packages to be synced to the remote cache
        raises:
            exception if unable to compute list of oses to be synced

        """
        try:

            final_dict = {}
            client_list = []
            client_os_pkg_dict = {}
            self.log.info("Getting clients associated to RC")
            query = f"select componentNameId from App_clientprop WITH (NOLOCK) " \
                    f"where attrname = 'UPDATE CACHE AGENT ID' and " \
                    f"attrVal = (select id from PatchUpdateAgentInfo where clientid = {self.client_obj.client_id})"
            self.csdb.execute(query)
            data = self.csdb.fetch_all_rows()
            for each in data:
                client_list.append(each[0])
            for client in client_list:
                query = f"select NewUpdateOSID from PatchUpdateOS where BinarySetID = (select attrVal " \
                        f"from APP_ClientProp WITH (NOLOCK) " \
                        f"where (attrName = 'Binary Set ID' AND componentNameId ={client}))"
                self.csdb.execute(query)
                client_os_id = int(self.csdb.fetch_one_row()[0])
                client_package = self.software_cache_obj.get_packages(client)
                client_os_pkg_dict[client_os_id] = client_package
            self.log.info("Combining the OS and packages dict required for sync")
            feature_release = []
            query = f"select HighestSP from PatchMultiCache where ClientId = " \
                    f"(select id from APP_CLient WITH (NOLOCK) where name like '{self.client_obj.client_name}')"
            self.csdb.execute(query)
            data = self.csdb.fetch_all_rows()
            for value in data:
                feature_release.append(int(value[0]))
            feature_release = list(set(feature_release))
            feature_release = str(feature_release[0])
            for key, value in self.configured_os_pkg_list.items():
                osid = key
                pkg_list = list(value)
                hard_dependent_packages = installer_utils.get_packages_to_install(pkg_list, osid, feature_release,
                                                                                  only_hard_dependent_packages=True)
                for pkg in hard_dependent_packages.keys():
                    self.configured_os_pkg_list[key].append(int(pkg))
            for key, value in self.configured_os_pkg_list.items():
                if int(key) in list(client_os_pkg_dict.keys()):
                    final_dict[key] = list(set(self.configured_os_pkg_list[key] + client_os_pkg_dict[int(key)]))
                else:
                    final_dict[key] = self.configured_os_pkg_list[key]
            for key, value in client_os_pkg_dict.items():
                if int(key) in list(final_dict.keys()):
                    final_dict[key] = list(set(final_dict[key] + client_os_pkg_dict[key]))
                else:
                    final_dict[key] = client_os_pkg_dict[key]
            final_dict = self.expected_package_list(
                package_list=final_dict,
                client_id=self.client_obj.client_id)
            for key, value in final_dict.items():
                self.log.info("The package selected for OS %s is %s", key, value)
            if self.media != self.software_cache_obj.get_cs_installed_media():
                self.log.info("filtering the os ids based on side by side cache logic")
                final_dict = dict([(key, final_dict[key]) for key in final_dict if key in self.os_ids])
            return final_dict

        except Exception as exp:
            raise Exception(exp)


class DownloadValidation:
    def __init__(self, commcell=None, client_obj=None, **kwargs):
        """
                Initialize instance of the DownloadedSoftwareValidation class.

                Args:
                    commcell    --  Commcell object

                    client_obj  --  remote cache client object

                Optional:

                    download_option:    option for latest SP, latest hotfix for current SP, or specified SP and CU
                                        (maintenance release)

                    os_download:        list of Unix flavours / windows

                    cu_pack:            CU pack number

                    service_pack:       service pack to download

                    media:              downloaded/synced media to check
        """
        self.download_option = kwargs.get('download_option')
        self.service_pack = kwargs.get('service_pack')
        self.cu_pack = kwargs.get('cu_pack')
        if type(self.cu_pack) == int:
            self.cu_pack = "CU" + str(self.cu_pack)
        self.os_to_download = kwargs.get('os_to_download')
        self.bootstrapper_validation = False
        self.config_json = config.get_config()
        self.job_id = kwargs.get('job_id')
        self.commcell = commcell
        self.machine_obj = kwargs.get('machine_obj' , Machine(self.commcell.commserv_client))
        self.transaction_id = None
        self.revision_id = None
        self.base_path = None
        self.csdb = database_helper.get_csdb()
        self.sp_major = None
        self.local_machine = Machine()
        self.get_simos_patchos_dict()
        self.release = installer_constants.CURRENT_RELEASE_VERSION
        self.build = installer_constants.CURRENT_BUILD_VERSION
        self._server_url = None
        self.log = logger.get_log()
        self.commserv_cache = CommServeCache(self.commcell.commserv_client, self.commcell)
        self.media = kwargs.get('media')
        self.options_selector = OptionsSelector(self.commcell)
        if self.media:
            self.transaction_id = self.media.split('_')[1]
            self.revision_id = self.media.split('_')[2][1:]
            self.service_pack = self.media.split('_')[0][2:]
        self.os_src_path = None
        self.client_obj = None
        if client_obj:
            self.remote_cache_obj = self.commcell.get_remote_cache(client_name=client_obj.client_name)
            self.remote_cache_path = self.remote_cache_obj.get_remote_cache_path()
            self.cache_path = self.remote_cache_path
            self.client_obj = client_obj
        else:
            self.client_machine = Machine(self.commcell.commserv_client)
            self.client_obj = self.commcell.commserv_client
            self.cache_path = self.commserv_cache.cs_cache_path
        self.check_latest_updates = True
        self.status = True
        self.status_msg = ''
        self.sample_folder = OptionsSelector.get_drive(self.local_machine) + 'SWTestFolder'
        if not self.local_machine.check_directory_exists(OptionsSelector.get_drive(self.local_machine)
                                                         + 'SWTestFolder'):
            self.local_machine.create_directory(
                OptionsSelector.get_drive(self.local_machine) + 'SWTestFolder')
    @property
    def get_server_url(self):
        """
        returns url of server: https://eng-updates.gp.cv.commvault.com

        returns:
                url -- server url
        """
        if not self._server_url:
            self.log.info("Getting server URL")
            query = "select * from GXGlobalParam where name = 'Patch Config URL Prefix'"
            self.csdb.execute(query)
            db_response = self.csdb.fetch_one_row()
            self._server_url = db_response[2]

        return self._server_url
    def frame_path(self, *args):
        path = os.path.join(*args)
        if self.commcell.is_linux_commserv:
            return path.replace("\\", "/")
        return path

    def get_simos_patchos_dict(self):
        """
        Creates a dictionary of Simbinarysetid to PatchUpdateOS Eg: for linuxx8664{'18':'16'}

        """
        try:
            self.simos_patchos_dict = {}
            query = "select BinarySetID,NewUpdateOSID from patchupdateos"
            self.csdb.execute(query)
            data = self.csdb.fetch_all_rows()
            for each in data:
                self.simos_patchos_dict[int(each[0])] = int(each[1])

        except Exception as err:
            raise Exception(
                "Exception occured in creating the simbinaryset and patchupdate os mapping - %s", str(err))

    def set_updates_path(self, os_id, os_src_path):
        """
        This sets the looseupdates folder path for every flavor of OS

        Args:
            os id - os id of the os in cache
            os_src_path - media part of the os

        returns:
        loose updates folder path
        """
        updates_path = ''
        base_os = "Windows" if os_id in [1, 3] else "Unix"
        if base_os == "Windows":
            if os_id == 3:
                updates_path = str(installer_utils.get_windows_looseupdates_path(os_src_path))
            else:
                updates_path = str(installer_utils.get_windows_looseupdates_path(os_src_path, x64=False))

        elif base_os == "Unix":
            _flavour = installer_constants.OSNAME_LIST[int(os_id)][1]
            updates_path = str(installer_utils.get_linux_looseupdates_path(os_src_path, _flavour))

        return updates_path

    def download_xml(self, url, write_to_folder=False):
        """
        downloads xml files from server

        args:
            url - url path of the configuration xml
            write_to_folder - if needs to be downloaded or written to a folder

        returns:
            path/response - path of the file or http response

        Raises:
            exception if unable to find file
            exception if unable to download file
        """
        try:
            self.log.info("Downloading XML files")
            http = urllib3.PoolManager()
            response = http.request('GET', url)
            response = response.data.decode('utf-8')
            self.log.info("Downloading xml from %s", url)
            if write_to_folder:
                basename = os.path.basename(url)
                path = os.path.join(self.sample_folder, basename)
                file = open(path, 'w')
                file.write(response)
                file.close()
                return path
            return response

        except Exception as exp:
            self.log.warning(f'Failed to download xml: {exp}')
            self.log.info("Retrying with http instead of https")
            http_url = url.replace('https', 'http')
            try:
                self.log.info("Downloading XML files")
                http = urllib3.PoolManager()
                response = http.request('GET', http_url)
                response = response.data.decode('utf-8')
                self.log.info("Downloading xml from %s", http_url)
                if write_to_folder:
                    basename = os.path.basename(http_url)
                    path = os.path.join(self.sample_folder, basename)
                    file = open(path, 'w')
                    file.write(response)
                    file.close()
                    return path
                return response
            except Exception as err:
                raise Exception(f'Failed to download xml: {err}') from exp

    def parse_cu_xml(self, os_downloaded, cu_num, selected_packages=[]):
        """
            Downloads and parses the files needed from the server

            args:
                os_downloaded       -- os id to set the xml path of CU
                cu_num              -- cu number
                selected_packages   --  selected packages

            returns:
                list of files to be present

        """
        try:
            self.log.info("Parsing CU config file")
            _osname = installer_constants.OSNAME_LIST[os_downloaded][1]
            cu_path = self.get_cu_path(_osname, cu_num)
            file = self.download_xml(cu_path)
            cu_install_map_dict = xmltodict.parse(file)
            add_root_files_patching_packages = False
            if not self.bootstrapper_validation:
                akamai_enabled = self.client_obj.properties['clientProps']['forceClientSideDownload']
                if akamai_enabled == 2:
                    query = "declare @inxml XML  = '<App_IsForceClientSideDownloadSetReq clientId=\"{0}\" option=\"0\" " \
                            "/>';exec IsForceClientSideDownloadSet @inxml".format(self.client_obj.client_id)
                    output = self.options_selector.update_commserve_db(query)
                    xml_msg = output.get_column(output.rows[0], output.columns[0])
                    akamai_enabled = int(ET.fromstring(xml_msg).attrib["forceClientSideDownload"])
                add_root_files_patching_packages = akamai_enabled == 1
            files_to_download = []

            def get_updates():
                def parse_update():
                    def get_files():
                        if each_file['@InstallFlag'] != "Stub":
                            file_path = each_file['@SourcePath']
                            files_to_download.append(file_path)

                    if int(each_package["@ID"]) in selected_packages or selected_packages == []:
                        if 'UpdBinary' in each_package.keys():
                            if not isinstance(each_package['UpdBinary'], list):
                                each_file = each_package['UpdBinary']
                                get_files()
                            else:
                                for each_file in each_package['UpdBinary']:
                                    get_files()
                        files_to_download.append(each_update['UpdConfigs']['UpdConfigFile']['@Name'])
                    elif int(each_package["@ID"]) == installer_constants.ROOT_FILES_PATCHING_ID and \
                             add_root_files_patching_packages:
                        if not isinstance(each_package['UpdBinary'], list):
                            each_file = each_package['UpdBinary']
                            get_files()
                        else:
                            for each_file in each_package['UpdBinary']:
                                get_files()
                        files_to_download.append(each_update['UpdConfigs']['UpdConfigFile']['@Name'])

                if not isinstance(each_update['UpdBinarySet']['UpdPackage'], list):
                    each_package = each_update['UpdBinarySet']['UpdPackage']
                    parse_update()
                else:
                    for each_package in each_update['UpdBinarySet']['UpdPackage']:
                        parse_update()

            if not isinstance(cu_install_map_dict['UpdatePatches_CumulativeUpdatePack']['UPUpdate'], list):
                each_update = cu_install_map_dict['UpdatePatches_CumulativeUpdatePack']['UPUpdate']
                get_updates()
            else:
                for each_update in cu_install_map_dict['UpdatePatches_CumulativeUpdatePack']['UPUpdate']:
                    get_updates()
            for each_config_file in \
                    cu_install_map_dict['UpdatePatches_CumulativeUpdatePack']['UPConfigs']['UPConfigFile']:
                files_to_download.append(each_config_file['@Name'])
            extra_files = [r'Config/CumulativeUpdatePackInstallMap.xml',
                           r'Config/CumulativeUpdatePackInstallMap.xml.description']
            files_to_download.extend(extra_files)
            final_files = []
            for file in files_to_download:
                if self.machine_obj:
                    if self.machine_obj.os_info.lower() == 'windows':
                        file = file.replace("/", "\\")
                    else:
                        file = file.replace("\\", "/")
                else:
                    if not self.commcell.is_linux_commserv:
                        file = file.replace("/", "\\")
                    else:
                        file = file.replace("\\", "/")
                final_files.append(file)
            return list(set(final_files))

        except Exception as err:
            raise Exception(f'Failed to parse CU xml : {err}') from err

    def get_cu_pack_files_from_cache(self, os_id, cu_num, cache_machine_obj):
        """
        gets the CU pack file list from CS software cache/ remote cache

        args:
            os_id - os id to set the xml path of CU
            cu_num - cu number

        returns:
            list of files from cache

        """
        try:

            os_xml_name, self.base_os, os_binary_info_name = self.commserv_cache.get_name_from_osid(os_id)

            self.os_src_path = self.frame_path(self.cache_path,
                                               installer_constants.DOWNLOAD_SOFTWARE_DEFAULT_MEDIA,
                                               installer_constants.CURRENT_RELEASE_VERSION,
                                               self.media,
                                               self.base_os)
            cu_path = self.frame_path(self.set_updates_path(os_id, self.os_src_path), "CU" + str(cu_num))

            self.log.info(cu_path)
            exclude_list = installer_constants.EXCLUDE_LIST
            exclude_list.append('Updates')
            if 'ThirdParty' in exclude_list:
                exclude_list.remove(installer_constants.THIRDPARTY_FOLDER)
            if 'LooseUpdates' in exclude_list:
                exclude_list.remove(installer_constants.LOOSEUPDATES_FOLDER)
            filelist = []
            if 'windows' in self.client_machine.os_info.lower():
                files = cache_machine_obj.get_files_in_path(folder_path=cu_path)
                all_files = [item.split(',') for item in files]
                all_files_copy = all_files.copy()
                for file in all_files_copy:
                    file_path = [item.split('\\') for item in file]
                    for each_file in file_path:
                        for exclude_file in each_file:
                            if exclude_file in exclude_list:
                                all_files.remove(file)
                req_files = [j for i in all_files for j in i]
                filelist = [item.split(f'CU{cu_num}\\')[1] for item in req_files]
            else:
                cu_folder_path = cu_path.replace('\\', '/') + '/'
                files = cache_machine_obj.get_files_in_path(folder_path=cu_folder_path)
                all_files = [item.split(',') for item in files]
                all_files_copy = all_files.copy()
                for file in all_files_copy:
                    file_path = [item.split('/') for item in file]
                    for each_file in file_path:
                        for exclude_file in each_file:
                            if exclude_file in exclude_list:
                                all_files.remove(file)
                req_files = [j for i in all_files for j in i]
                filelist = [item.split(f'CU{cu_num}/')[1] for item in req_files]
            return filelist

        except Exception as err:
            self.log.exception("Failed to get list of files in CU folder - %s", err)

    def get_cu_pack_files_from_downloaded_location(self, os_id, cu_num):
        """
        gets the CU pack file list from CS software cache/ remote cache

        args:
            os_id - os id to set the xml path of CU
            cu_num - cu number

        returns:
            list of files from cache

        """
        try:
            cu_path = self.machine_obj.join_path(self.set_updates_path(os_id, self.os_src_path), 'CU' + str(cu_num))
            if self.machine_obj.os_info.lower() == 'unix':
                cu_path = cu_path.replace('\\', '/')
            self.log.info(cu_path)
            exclude_list = installer_constants.EXCLUDE_LIST
            exclude_list.append('Updates')
            if 'ThirdParty' in exclude_list:
                exclude_list.remove(installer_constants.THIRDPARTY_FOLDER)
            if 'LooseUpdates' in exclude_list:
                exclude_list.remove(installer_constants.LOOSEUPDATES_FOLDER)
            filelist = []
            if 'windows' in self.machine_obj.os_info.lower():
                files = self.machine_obj.get_files_in_path(folder_path=cu_path)
                all_files = [item.split(',') for item in files]
                for file in all_files:
                    file_path = [item.split('\\') for item in file]
                    for each_file in file_path:
                        for exclude_file in each_file:
                            if exclude_file in exclude_list:
                                all_files.remove(file)
                req_files = [j for i in all_files for j in i]
                filelist = [item.split(f'CU{cu_num}\\')[1] for item in req_files]
            else:
                cu_folder_path = cu_path.replace('\\', '/') + '/'
                files = self.machine_obj.get_files_in_path(folder_path=cu_folder_path)
                all_files = [item.split(',') for item in files]
                all_files_copy = all_files.copy()
                for file in all_files_copy:
                    if '/Updates/' not in file[0]:
                        file_path = [item.split('/') for item in file]
                        for each_file in file_path:
                            for exclude_file in each_file:
                                if exclude_file in exclude_list:
                                    all_files.remove(file)
                    else:
                        all_files.remove(file)
                req_files = [j for i in all_files for j in i]
                filelist = [item.split(f'CU{cu_num}/')[1] for item in req_files]
            return filelist
        except Exception as err:
            self.log.exception("Failed to get list of files in CU folder - %s", err)

    def generate_cu_configuration_url(self):
        """
        generates cu configuration URL in the HTTP server

        returns:
                CU configuration URL
        """
        self.log.info("generating default URL")
        if self.transaction_id and self.revision_id and int(self.revision_id) > 952:
            self.url = r'https://{0}/CVUpdates/{1}/{2}/SP{3}_{4}_R{5}/MaintenanceReleasesInfo.xml'.format(
                self.config_json.Install.download_server, installer_constants.CURRENT_RELEASE_VERSION,
                installer_constants.CURRENT_BUILD_VERSION, self.service_pack, self.transaction_id, self.revision_id)
        else:
            self.url = r'https://{0}/CVUpdates/{1}/{2}/SP{3}/CUConfiguration.xml'.format(
                self.config_json.Install.download_server,
                installer_constants.CURRENT_RELEASE_VERSION,
                installer_constants.CURRENT_BUILD_VERSION,
                self.service_pack)

        self.log.info("URL generated for identifying the configuration files is %s", format(self.url))
        return self.url

    def validate_files_downloaded_for_cu_pack(self, os_downloaded, cu_num, selected_packages=[]):
        """
            Validates files in CU Pack downloaded

            args:
                os_downloaded - os ids downloaded
                cu_num - CU number
                selected_packages - list of packages selected for download
        """
        try:
            files_to_be_present = self.parse_cu_xml(os_downloaded, cu_num, selected_packages)
            final_list_from_xml = []
            for each_file in files_to_be_present:
                if 'Base32' not in files_to_be_present:
                    final_list_from_xml.append(each_file)
            files_to_be_present = list(set(files_to_be_present))
            ignore_list = installer_constants.DOWNLOAD_UNIX_SKIP_LIST + installer_constants.DOWNLOAD_WIN_IGNORE_LIST
            final_list_from_xml = [eachfile for eachfile in files_to_be_present if
                                   not any(x in eachfile for x in ignore_list)]
            self.log.info("Files to be downloaded are %s", final_list_from_xml)

            if self.bootstrapper_validation:
                files_present = list(set(self.get_cu_pack_files_from_downloaded_location(os_downloaded, cu_num)))
            else:
                files_present = list(set(self.get_cu_pack_files_from_cache(os_downloaded, cu_num, self.machine_obj)))
            files_present = [eachfile for eachfile in files_present if not any(x in eachfile for x in ignore_list)]
            self.log.info("Files present in cache are-  %s", files_present)

            match_list, only_in_media, only_in_xml = commonutils.compare_list(files_present,
                                                                              final_list_from_xml)
            if len(only_in_xml) == 0 and len(only_in_media) == 0:
                self.log.info("CU pack validation PASSED for OS [%s]",
                              installer_constants.OSNAME_LIST[os_downloaded][2])

            else:
                err_msg = ''
                if len(only_in_media) > 0:
                    err_msg += f'\nFiles present in client media but not in xml are: {only_in_media}'
                    self.log.error(f"Files present in client media but not in xml are: {only_in_media}")

                if len(only_in_xml) > 0:
                    err_msg += f'\nFiles in XML but not in Client media are: {only_in_xml}'
                    self.log.error(f"Files in XML but not in Client media are: {only_in_xml}")
                raise Exception(err_msg)

        except Exception as exp:
            error_msg = f'CU Pack validation failed for ' \
                        f'OS {installer_constants.OSNAME_LIST[int(os_downloaded)][2]} with error {exp}'
            self.log.exception(self.status_msg)
            self.status_msg += '\n' + error_msg
            self.status = False
    def check_for_checksumfile(self, updateslist, updatespath):
        """
        Checks if UpdatesChecksum.txt file is present in the loose updates folder to ensure the update is not corrupt and make a list of updates if file not present
        args:
            updateslist - list of loose updates
            updatespath - looseupdates path
        returns:
            list of updates missing checksum file
        """
        try:
            updates_missing_checksum = []
            for each in updateslist:
                for root, dirs, files in os.walk(os.path.join(updatespath, each)):
                    if "updatesChecksum.txt" in files:
                        break
                    else:
                        # list of updates missing the checksum file
                        updates_missing_checksum.append(each)
                        break
            return updates_missing_checksum
        except Exception as err:
            raise Exception(
                "Exception occured in checking if updatesChecksum.txt file is present in folder - %s", str(err))

    def get_os_updates_dict_in_cache(self, os_id):
        """
        Gets the dict having Os and Loose updates/hotfixes downloaded for that OS
        args:
            os_id - os id in the cache
        """
        try:
            updates_list = []
            corrupt_updates_list = []
            os_dict = {}
            updates_path = f"{self.set_updates_path(os_id, self.os_src_path)}\\{self.cu_pack}\\Updates"
            self.looseupdates_path = installer_utils.convert_unc(self.commcell.commserv_hostname, updates_path)
            patchinstaller_path = installer_utils.convert_unc(
                self.commcell.commserv_hostname, self.set_updates_path(
                    os_id, self.os_src_path))
            for root, dirs, files in os.walk(self.looseupdates_path):
                updates_list = dirs
                break
            if (updates_list):
                self.cache_os_updates_dict[os_id] = updates_list
            # Checking updatesChecksum.txt file is present for each update
            corrupt_updates_list = self.check_for_checksumfile(updates_list, self.looseupdates_path)
            if (corrupt_updates_list):
                self.cache_corrupt_os_updates_dict[os_id] = corrupt_updates_list
            # Get installer files checksum for PatchInstaller validation
            for root, dirs, files in os.walk(patchinstaller_path):
                for each_file in files:
                    checksum = int(commonutils.crc(patchinstaller_path + "\\" + each_file), 16)
                    os_dict[each_file] = checksum
                break
            self.patchinstaller_checksum_dict[os_id] = os_dict
        except Exception as err:
            raise Exception("Exception occured in getting the Os-Updates dict - %s", str(err))

    # download software validation
    def download_validation(self):
        """
            Validates download by going through the files

        """
        try:
            self.log.info("Starting Validation")

            # creating a sample folder to keep track of config files
            if self.local_machine.create_directory(
                    OptionsSelector.get_drive(self.local_machine) + 'SWTestFolder', force_create=True):
                self.sample_folder = OptionsSelector.get_drive(self.local_machine) + 'SWTestFolder'

            # upgrade to the latest release
            if (self.download_option == adminconsoleconstants.DownloadOptions.LATEST_SP.value
                    or self.download_option == deploymentconstants.DownloadOptions.LATEST_SERVICEPACK.value
                    or self.download_option is None):
                self.log.info("Download option : Latest service pack")
                query = f"SET NOCOUNT ON; exec GetFTPServicePackInfo a"
                ftp_sp_xml = self.commserv_cache.execute_sp(query)
                ftp_sp_dict = xmltodict.parse(ftp_sp_xml.rows[0][0])
                self.service_pack = ftp_sp_dict['EVGui_GetFTPServicePackInfoResp']['@MainstreamSP'].split('.')[1]
                self.revision_id, self.transaction_id, self.service_pack = self.get_sp_info(sp_major=self.service_pack)
                self.cu_pack = \
                    f"CU{int(ftp_sp_dict['EVGui_GetFTPServicePackInfoResp']['@MainstreamSP'].split('.')[2])}"

            # latest hotfixes for current release
            elif (self.download_option == adminconsoleconstants.DownloadOptions.LATEST_HF_FOR_INSTALLED_SP.value
                  or self.download_option == deploymentconstants.DownloadOptions.LATEST_HOTFIXES.value):
                self.log.info("Download option : Latest hotfix for installed service pack")
                cs_sp_version = self.commcell.commserv_version
                self.revision_id, self.transaction_id, self.service_pack = self.get_sp_info(cs_sp_version)
                self.cu_pack = installer_utils.get_latest_cu_from_xml(f'SP{self.service_pack}_{self.transaction_id}'
                                                                      f'_R{self.revision_id}')

            # feature release, maintenance release (cu pack)
            elif ((self.download_option == adminconsoleconstants.DownloadOptions.GIVEN_SP_AND_HF.value or
                  self.download_option == deploymentconstants.DownloadOptions.SERVICEPACK_AND_HOTFIXES.value) and
                  self.service_pack is not None):
                self.log.info("Download option : Given SP and hotfix")

                self.revision_id, self.transaction_id, self.service_pack = self.get_sp_info(self.service_pack)

            else:
                raise Exception('Please specify Service Pack version')

            self.log.info('Revision ID: {0}, Transaction ID: {1}, SP Major: {2}, CU Pack: {3}'.format(
                self.revision_id, self.transaction_id, self.service_pack, self.cu_pack))
            self.media = f'SP{self.service_pack}_{self.transaction_id}_R{self.revision_id}'
            self.base_path = self.frame_path(self.commserv_cache.cs_cache_path,
                                             installer_constants.DOWNLOAD_SOFTWARE_DEFAULT_MEDIA,
                                             self.commserv_cache.software_cache_obj.get_version(),
                                             self.media)

            for each_os in self.os_to_download:
                self.os_xml_name, self.base_os, self.os_binary_info_name = self.commserv_cache.get_name_from_osid(
                    int(each_os))
                self.os_src_path = self.frame_path(self.base_path, self.base_os)
                self.log.info("Source path to search %s", self.os_src_path)
                self.log.info("*************Validating CVMedia****************")
                self.validate_media(each_os)
                self.log.info(
                    "*************Validating CU pack for OS [%s]****************",
                    installer_constants.OSNAME_LIST[each_os][2])
                self.validate_files_downloaded_for_cu_pack(each_os, self.cu_pack[2:])
                if self.download_option not in [adminconsoleconstants.DownloadOptions.GIVEN_SP_AND_HF.value,
                                            deploymentconstants.DownloadOptions.SERVICEPACK_AND_HOTFIXES.value]:
                    self.log.info("*************Validating hotfixes***************")
                    self.validate_hotfixes(each_os)
                self.log.info("**************Validating setup.exe patching***************")
                self.validate_setupexe_patching()
                if self.download_option in [adminconsoleconstants.DownloadOptions.GIVEN_SP_AND_HF.value,
                                        deploymentconstants.DownloadOptions.SERVICEPACK_AND_HOTFIXES.value]:
                    self.log.info("*************Validating quickfixes***************")
                    self.validate_hotfixes(each_os, only_qf=True)
                if not self.commcell.is_linux_commserv and each_os in [deploymentconstants.OSNameIDMapping.WINDOWS_64.value,
                                                                       deploymentconstants.OSNameIDMapping.WINDOWS_32.value]:
                    self.log.info("**************Validating OEM***************")
                    self.validate_oem()
            self.log.info("**************Validating count of files***************")
            self.validate_count_of_files(self.job_id)

            if not self.status:
                self.log.info("Download Validation failed. Check logs for more details")
                raise Exception("Download Software Validation failed")

        except Exception as exp:
            raise Exception(exp)

    def bootstrapper_download_validation(self, media_path, package_dict=None):
        """
            Validates download by going through the files

        """
        self.bootstrapper_validation = True
        try:
            self.log.info("Starting Validation")
            # creating a sample folder to keep track of config files
            if self.local_machine.create_directory(
                    OptionsSelector.get_drive(self.local_machine) + 'SWTestFolder', force_create=True):
                self.sample_folder = OptionsSelector.get_drive(self.local_machine) + 'SWTestFolder'

            if self.cu_pack is None:
                self.cu_pack = f"CU{installer_utils.get_latest_cu_from_xml(self.media)}"
            self.log.info(f'Revision ID: {self.revision_id}, Transaction ID: {self.transaction_id}, '
                          f'SP Major: {self.service_pack}, CU Pack: {self.cu_pack}')
            self.base_path = media_path

            for each_os in self.os_to_download:
                final_pkg_list = []
                if package_dict:
                    package_list = list(package_dict[each_os])
                    hard_dependent_packages = installer_utils.get_packages_to_install(
                        package_list, each_os, self.media, only_hard_dependent_packages=False)
                    for pkg in hard_dependent_packages.keys():
                        final_pkg_list.append(int(pkg))
                    final_pkg_list = list(set(final_pkg_list + package_list))
                    self.log.info(f"Final list of packages {final_pkg_list}")

                self.os_xml_name, self.base_os, self.os_binary_info_name = self.commserv_cache.get_name_from_osid(
                    int(each_os))
                self.os_src_path = media_path
                self.log.info("Downloaded media location %s", self.os_src_path)
                self.log.info(f"*************Validating DVD Media for OS"
                              f" [{installer_constants.OSNAME_LIST[each_os][2]}]****************")
                self.validate_media(each_os, final_pkg_list)
                self.log.info(f"*************Validating CU pack for OS "
                              f"[{installer_constants.OSNAME_LIST[each_os][2]}]****************")
                self.validate_files_downloaded_for_cu_pack(each_os, self.cu_pack[2:], final_pkg_list)
                if not package_dict:
                    self.log.info(f"*************Validating hotfixes for OS "
                                  f"[{installer_constants.OSNAME_LIST[each_os][2]}]***************")
                    self.validate_hotfixes(each_os)
            if not self.status:
                self.log.info(f"Download Validation Failed!! \n {self.status_msg}")
                raise Exception("Download Validation failed. Check logs for more details")

        except Exception as exp:
            raise Exception(exp)

    def get_latest_dvd_path(self):
        """
            Gets the latest path of CVMedia
            ex: CVMedia/11.0.0/BUILD80/SP25DVD/Windows

            returns:
                path -- latest dvd path
        """

        self.log.info("Getting latest path of CVMedia")

        path = 'CVMedia/{0}/{1}/SP{2}_{3}_R{4}/{5}'.format(self.release, self.build, self.service_pack,
                                                           self.transaction_id, self.revision_id, self.base_os)
        return path

    def get_sp_info(self, sp_major):
        """
            Returns the transaction  id, revision id, and sp major depending on the given sp major

            args:
                sp_major - service pack number
        """
        try:
            self.log.info("Querying DB to get SP info")
            if sp_major:
                trans_id = "select max(TransactionID) from PatchSPVersion where SPMajor = %s" % sp_major
                query = "select SPMajor, RevisionID, TransactionID " \
                        "from PatchSPVersion where TransactionID =( %s )" % trans_id
            else:
                trans_id = "select max(TransactionID) from PatchSPVersion where SPMajor = (select max(SPMajor) " \
                           "from PatchSPVersion) "
                query = "select SPMajor, RevisionID, TransactionID " \
                        "from PatchSPVersion where TransactionID = ( %s )" % trans_id
            self.csdb.execute(query)
            response = self.csdb.fetch_one_row()

            self.log.info("Querying DB to collect Release and Build info")
            query = 'select * from PatchSPVersion where TransactionID = 0 and SPMajor = {0}'.format(sp_major)
            self.csdb.execute(query)
            db_response = self.csdb.fetch_one_row()
            self.release = db_response[1]
            self.build = db_response[2]

            return response[1], response[2], response[0]

        except Exception as exp:
            raise Exception("Unable to fetch major sp details - %s", exp)

    def validate_media(self, os_id, package_list=None, server_url=installer_constants.DEFAULT_CONFIG_URL_PREFIX):
        """'
            Validates CV Media in software cache

            args:
                os_id: os id to validate in cache

        """

        try:
            binary_set_id = \
                installer_constants.BinarySetIDMapping[deploymentconstants.OSNameIDMapping(int(os_id)).name].value
            path_of_server = self.get_latest_dvd_path()
            server_dvd_path = server_url + "/" + path_of_server
            if not self.bootstrapper_validation:
                binary_set_id = [key for key, value in self.simos_patchos_dict.items() if value == os_id][0]
                server_dvd_path = self.get_server_url + "/" + path_of_server
            self.log.info("Binary set ID: %s", format(binary_set_id))
            self.log.info("CVMedia path: %s", format(server_dvd_path))

            # Download WinPackages.xml and BinaryInfo.xml to a new directory
            binary_info_path, package_xml_path = self.get_binaryinfo_winpackages_xml(server_dvd_path)

            # Gather data on packages and corresponding binaries from WinPackages.xml and BinaryInfo.xml
            packages = self.get_packages(package_xml_path)
            if package_list:
                packages = [str(x) for x in package_list]
            binaries_dict = self.commserv_cache.get_binary_info_dict(binary_info_path)
            filtered_binaries_dict = self.filter_binary_dict(binaries_dict, packages)[str(binary_set_id)]
            self.log.info("Filtered binaries dict: %s", format(filtered_binaries_dict))

            # Gather ThirdParty packages
            third_party_packages = self.commserv_cache.software_cache_obj.get_third_party_packages(
                package_xml_path, binary_set_id, packages)

            if third_party_packages:
                self.log.info("Third party packages exist")
                third_party_dict = self.filter_binary_dict(binaries_dict, list(map(str, third_party_packages)))['0']
                filtered_binaries_dict.update(third_party_dict)

            binary_files = self.process_binary_files(filtered_binaries_dict)
            files_in_xml = self.filter_skipped_files(binary_files)

            ignore_list = installer_constants.DOWNLOAD_WIN_IGNORE_LIST + installer_constants.DOWNLOAD_UNIX_SKIP_LIST
            loc = self.os_src_path
            if os_id == 1:
                ignore_list.append('BinaryPayload')
            elif os_id == 3:
                ignore_list.extend(installer_constants.WIN32_IGNORE_LIST)
            else:
                loc = self.machine_obj.join_path(self.os_src_path, self.os_xml_name)
            if self.machine_obj.os_info.lower() != 'windows':
                ignore_list[:] = [f.replace('\\', '/') for f in ignore_list]
            files_in_cache = []
            self.log.info("Ignored List {0}".format(ignore_list))

            temp = self.machine_obj.get_files_in_path(loc)
            for f_temp in temp:
                temp_file = f_temp.split(loc)[-1][1:]
                if not any(
                        ignored_file in temp_file for ignored_file in ignore_list) and 'LooseUpdates' not in temp_file:
                    files_in_cache.append(temp_file)

            in_both, only_in_media, only_in_xml = commonutils.compare_list(files_in_cache, files_in_xml)

            if len(only_in_xml):
                raise Exception("Files missing in media: %s.", only_in_xml)

            if len(only_in_xml) == 0 and len(only_in_media) == 0:
                self.log.info("DVD Media validation PASSED for OS [%s]",
                              installer_constants.OSNAME_LIST[int(os_id)][2])
            else:
                self.log.info("DVD Media validation FAILED for OS [%s]",
                              installer_constants.OSNAME_LIST[int(os_id)][2])
                raise Exception(f"Files missing in XML {only_in_media}")

        except Exception as exp:
            error_msg = f'DVD Media validation failed for OS {installer_constants.OSNAME_LIST[int(os_id)][2]} with error {exp}'
            self.log.exception(error_msg)
            self.status_msg += '\n' + error_msg
            self.status = False

    def validate_cvappliance_media(self, validate_rc=True):
        """
            Validates CV Appliance Media
        """
        try:
            versions_xml_dict = self.get_cvappliance_config_xml()

            self.log.info("Starting CVAppliance Validation for CS cache")
            mssql_versions_to_download = self.check_cvappliance_for_sql_versions()
            windows_versions_to_download = self.check_cvappliance_for_windows_versions()
            files_to_download = []

            for each_version in mssql_versions_to_download:
                files_to_download.extend(versions_xml_dict[each_version])

            for each_version in windows_versions_to_download:
                files_to_download.extend(versions_xml_dict[each_version])

            cv_appliance_media_path = self.frame_path(self.commserv_cache.cs_cache_path,
                                                      installer_constants.DOWNLOAD_SOFTWARE_DEFAULT_CVAPPLIANCE_MEDIA)

            temp = self.machine_obj.get_files_in_path(folder_path=cv_appliance_media_path)
            files_present = [str(x.split(cv_appliance_media_path)[-1])[1:] for x in temp]
            self.log.info("Files present in location are-  %s", files_present)

            _, only_in_media, only_in_xml = commonutils.compare_list(files_present, files_to_download)

            if len(only_in_xml) == 0 and len(only_in_media) == 0:
                self.log.info("CV Appliance validation PASSED for CS cache")
            else:
                err_msg = ''
                if len(only_in_media) > 0:
                    err_msg += f'\nFiles present in media but not in xml are: {only_in_media}'
                    self.log.error(f"Files present in media but not in xml are: {only_in_media}")

                if len(only_in_xml) > 0:
                    err_msg += f'\nFiles in XML but not in media are: {only_in_xml}'
                    self.log.error(f"Files in XML but not in media are: {only_in_xml}")
                raise Exception(err_msg)

            if validate_rc:
                rc_obj_list = self.get_appliance_media_synced_rc_list()
                _status_msg = ''
                _status = True
                for rc_obj in rc_obj_list:
                    try:
                        mssql_versions_to_download = self.check_cvappliance_for_sql_versions(rc_obj.client_id)
                        windows_versions_to_download = self.check_cvappliance_for_windows_versions(rc_obj.client_id)
                        files_to_download = []
                        for each_version in mssql_versions_to_download:
                            files_to_download.extend(versions_xml_dict[each_version])
                        for each_version in windows_versions_to_download:
                            files_to_download.extend(versions_xml_dict[each_version])

                        remote_cache_obj = self.commcell.get_remote_cache(rc_obj.client_name)
                        cv_appliance_media_path = f"{remote_cache_obj.get_remote_cache_path()}\\" \
                                                  f"{installer_constants.DOWNLOAD_SOFTWARE_DEFAULT_CVAPPLIANCE_MEDIA}"

                        temp = self.machine_obj.get_files_in_path(folder_path=cv_appliance_media_path)
                        files_present = [str(x.split(cv_appliance_media_path)[-1])[1:] for x in temp]
                        self.log.info("Files present in location are-  %s", files_present)

                        _, only_in_media, only_in_xml = commonutils.compare_list(files_present, files_to_download)

                        if len(only_in_xml) == 0 and len(only_in_media) == 0:
                            self.log.info(f"CV Appliance validation PASSED for RC {rc_obj.client_name}")
                        else:
                            err_msg = ''
                            if len(only_in_media) > 0:
                                err_msg += f'\nFiles present in client media but not in xml for RC ' \
                                           f'{rc_obj.client_name} are: {only_in_media}'
                                self.log.error(f"Files present in client media but not in xml for RC "
                                               f"{rc_obj.client_name} are: {only_in_media}")

                            if len(only_in_xml) > 0:
                                err_msg += f'\nFiles in XML but not in Client media for RC ' \
                                           f'{rc_obj.client_name} are: {only_in_xml}'
                                self.log.error(f"Files in XML but not in Client media for RC "
                                               f"{rc_obj.client_name} are: {only_in_xml}")
                            raise Exception(err_msg)

                    except Exception as exp:
                        error_msg = f'CV Appliance Media validation failed for RC {rc_obj.client_name} with error {exp}'
                        _status_msg += '\n' + error_msg
                        _status = False
                if not _status:
                    raise Exception(_status_msg)
        except Exception as exp:
            error_msg = f'CV Appliance Media validation failed with error {exp}'
            self.log.exception(error_msg)
            self.status_msg += '\n' + error_msg
            self.status = False

    def get_cvappliance_config_xml(self):
        """
            Fetches the cvappliance dict from XML
        """
        try:
            xml_server_location = self.get_server_url + \
                                  "/" + \
                                  installer_constants.DOWNLOAD_SOFTWARE_DEFAULT_CVAPPLIANCE_MEDIA + \
                                  "/" + \
                                  "CVApplianceConfig_Windows.xml"
            cvappliance_xml = self.download_xml(xml_server_location, write_to_folder=True)
            if os.path.isfile(cvappliance_xml):
                with open(cvappliance_xml) as fd:
                    pkgdict = xmltodict.parse(fd.read())
                    fd.close()
            else:
                pkgdict = xmltodict.parse(cvappliance_xml)

            cvappliance_dict = self.convert_cvappliance_xml_to_dict(pkgdict)
            return cvappliance_dict

        except Exception as exp:
            raise Exception(exp)

    def convert_cvappliance_xml_to_dict(self, xml_dict):
        """
            Converts cv appliance xml element to python dict
        """
        try:
            cvappliance_dict = {}

            def get_patches():
                def add_files():
                    cvappliance_dict[each_sub_os['@name']].append(eachpatch['@SourcePath'])

                if type(each_sub_os['updateBundle']['patchFile']) is list:
                    for eachpatch in each_sub_os['updateBundle']['patchFile']:
                        add_files()
                else:
                    eachpatch = each_sub_os['updateBundle']['patchFile']
                    add_files()

            for each_os_patch in xml_dict['UpdatePatches_CVApplianceOSPatches']['OSPatches']:
                if type(each_os_patch['subOS']) is list:
                    for each_sub_os in each_os_patch['subOS']:
                        if not each_sub_os['@name'] in cvappliance_dict.keys():
                            cvappliance_dict[each_sub_os['@name']] = []
                        get_patches()
                else:
                    each_sub_os = each_os_patch['subOS']
                    if not each_sub_os['@name'] in cvappliance_dict.keys():
                        cvappliance_dict[each_sub_os['@name']] = []
                    get_patches()
            return cvappliance_dict

        except Exception as exp:
            raise Exception(exp)

    def check_cvappliance_for_sql_versions(self, rc_client_id=None):
        """
            Queries the DB to fetch mssql versions to download
        """
        try:
            mssql_versions = []
            query = "select version from simInstalledThirdPartyCU where enabled = 1 and type = 1"
            if rc_client_id:
                query = f"select name from patchApplianceOS where clientid = {str(rc_client_id)} and type = 1"
            self.csdb.execute(query)
            db_response = self.csdb.fetch_all_rows()
            for count in range(len(db_response)):
                if db_response[count][0] != "":
                    mssql_versions.append(db_response[count][0])

            return mssql_versions

        except Exception as exp:
            raise Exception(exp)

    def check_cvappliance_for_windows_versions(self, rc_client_id=None):
        """
            Queries the DB to fetch Windows versions to download
        """
        try:
            windows_versions = []
            query = "select version from simInstalledThirdPartyCU where enabled = 1 and type = 2"
            if rc_client_id:
                query = f"select name from patchApplianceOS where clientid = {str(rc_client_id)} and type = 1"
            self.csdb.execute(query)
            db_response = self.csdb.fetch_all_rows()
            for count in range(len(db_response)):
                if db_response[count][0] != "":
                    windows_versions.append(db_response[count][0])

            return windows_versions

        except Exception as exp:
            raise Exception(exp)

    def get_appliance_media_synced_rc_list(self):
        """

        """
        query = "select clientId from patchApplianceOS where clientId !=2"
        self.csdb.execute(query)
        db_response = self.csdb.fetch_all_rows()
        rc_list = []
        for _, res in enumerate(db_response):
            if res[0]:
                query = f"select net_hostname from APP_Client where id = {str(res[0])}"
                self.csdb.execute(query)
                if self.csdb.fetch_one_row()[0]:
                    rc_list.append(self.commcell.clients.get(self.csdb.fetch_one_row()[0]))
        return rc_list

    def validate_cv_appliance_media_for_bootstrapper(self, appliance_list, media_path):
        """
            Validates appliance media downloaded

            args:
                os_id: os id to validate in cache

        """
        cv_appliance_dict = {}
        if "UNIX_APPLIANCE" in appliance_list:
            xml_path = self.config_json.Install.rpm_configfile
            with open(xml_path) as xml:
                xml_dict = xmltodict.parse(xml.read())

            for each_os_patch in xml_dict['UpdatePatches_UnixCVApplianceOSPatches']['OS']['patches']:
                if not each_os_patch['@Name'] in cv_appliance_dict.keys():
                    cv_appliance_dict[each_os_patch['@Name']] = []
                cv_appliance_dict[each_os_patch['@Name']].append(each_os_patch['@SourcePath'])
        else:
            xml_url = installer_constants.DEFAULT_CV_APPLIANCE_XML_WINDOWS
            xml_path = self.download_xml(xml_url, write_to_folder=True)
            with open(xml_path) as xml:
                xml_dict = xmltodict.parse(xml.read())

            def get_patches():
                def add_files():
                    cv_appliance_dict[each_sub_os['@name']].append(eachpatch['@SourcePath'])
                if type(each_sub_os['updateBundle']['patchFile']) is list:
                    for eachpatch in each_sub_os['updateBundle']['patchFile']:
                        add_files()
                else:
                    eachpatch = each_sub_os['updateBundle']['patchFile']
                    add_files()
            for each_os_patch in xml_dict['UpdatePatches_CVApplianceOSPatches']['OSPatches']:
                if type(each_os_patch['subOS']) is list:
                    for each_sub_os in each_os_patch['subOS']:
                        if not each_sub_os['@name'] in cv_appliance_dict.keys():
                            cv_appliance_dict[each_sub_os['@name']] = []
                        get_patches()
                else:
                    each_sub_os = each_os_patch['subOS']
                    if not each_sub_os['@name'] in cv_appliance_dict.keys():
                        cv_appliance_dict[each_sub_os['@name']] = []
                    get_patches()

        files_to_download = []
        for each_version in cv_appliance_dict.keys():
            files_to_download.extend(cv_appliance_dict[each_version])
        files_to_download[:] = [f.replace('/', self.machine_obj.os_sep) for f in files_to_download.copy()]
        files_to_download[:] = [f.replace('\\', self.machine_obj.os_sep) for f in files_to_download.copy()]
        self.log.info("Files to be present in location are-  %s", files_to_download)

        temp = self.machine_obj.get_files_in_path(folder_path=media_path)
        files_present = [str(x.split(media_path)[-1])[1:] for x in temp]
        xml_name = str(xml_path.split(self.machine_obj.os_sep)[-1])
        if xml_name in files_present:
            files_present.remove(xml_name)
        self.log.info("Files present in location are-  %s", files_present)

        match_list, only_in_media, only_in_xml = commonutils.compare_list(files_present, files_to_download)

        if len(only_in_xml) == 0 and len(only_in_media) == 0:
            self.log.info(f"CV Appliance validation PASSED for windows")

        else:
            err_msg = ''
            if len(only_in_media) > 0:
                err_msg += f'\nFiles present in client media but not in xml are: {only_in_media}'
                self.log.error(f"Files present in client media but not in xml are: {only_in_media}")

            if len(only_in_xml) > 0:
                err_msg += f'\nFiles in XML but not in Client media are: {only_in_xml}'
                self.log.error(f"Files in XML but not in Client media are: {only_in_xml}")
            raise Exception(err_msg)

    def get_binaryinfo_winpackages_xml(self, server_url):
        """
            downloads BinaryInfo and WinPackages
            args:
                server_url - url path of the xmls
            returns:
                binaryinfo.xml path
                winpackages.xml path
        """
        try:
            if self.base_os == 'Unix':
                bi_path = '{0}/{1}/BinaryInfo.xml'.format(server_url, self.os_xml_name)
                wp_xml = '{0}/pkg.xml'.format(server_url)
            else:
                bi_path = '{0}/BinaryInfo.xml'.format(server_url)
                wp_xml = '{0}/WinPackages.xml'.format(server_url)

            self.log.info("BinaryInfo path: %s", format(bi_path))
            self.log.info("WinPackages/Pkg xml path: %s", format(wp_xml))

            bi_xml_file = self.download_xml(bi_path, write_to_folder=True)
            wp_xml_file = self.download_xml(wp_xml, write_to_folder=True)
            return bi_xml_file, wp_xml_file

        except Exception as exp:
            self.log.exception('Failed to download BinaryInfo.xml and WinPackages.xml(Pkg.xml) with error: %s', exp)
            raise Exception('Exception occurred while downloading xml files')

    def get_packages(self, path):
        """
            Returns a list of package names after parsing through WinPackages.xml

            args:
                path - path of winpackages.xml

            returns:
                list of packge ids from winpackages.xml
        """
        try:
            self.log.info("Getting a list of packages")
            with open(path) as package_xml:
                # parsing xml to dict to convert to list
                doc = xmltodict.parse(package_xml.read())

            packages_list = []
            for package in doc['UpdatePatches_PackageDetails']['PkgList']['pkg']:
                if package['@id'] not in installer_constants.DOWNLOAD_IGNORE_PACKAGE_LIST:
                    packages_list.append(package['@id'])

            self.log.info("Packages list: %s", format(packages_list))
            return packages_list

        except Exception as exp:
            self.log.exception('Error while getting package names in WinPackage.xml: %s', format(exp))
            raise Exception('Unable to parse WinPackages.xml')

    def filter_binary_dict(self, binaries_dict, packages):
        """
            Filters the binaries_dict dictionary based on packages provided

            args:
                binaries_dict - binary dict
                packages - packages to filter

            returns:
                filterd dictionary
        """

        try:
            self.log.info("Filtering binary dictionary")

            copy_dict = binaries_dict.copy()
            for os_id, package_id in copy_dict.items():
                filtered_binaries = {}
                for (pkg_id, deets) in package_id.items():
                    if pkg_id in packages:
                        filtered_binaries[pkg_id] = deets
                copy_dict[os_id] = filtered_binaries

            self.log.info("Filtered dict: %s", format(copy_dict))
            return copy_dict

        except Exception as exp:
            self.log.exception('Failed to filter binary dictionary with error: {0}'.format(exp))

    def process_binary_files(self, binaries_dict):
        """
            Goes through binary dictionary to identify file paths
            Returns a list of file paths

            args:
                binaries_dict - binary dict
        """
        try:
            self.log.info("Processing binary files with binary dict: %s", format(binaries_dict))

            file_paths = []
            for pkg_id, path in binaries_dict.items():
                for file in binaries_dict[pkg_id].keys():
                    file_paths.append(file)

            if self.machine_obj:
                if self.machine_obj.os_info.lower() == 'windows':
                    file_paths[:] = [f.replace('/', '\\') for f in file_paths]
                else:
                    file_paths[:] = [f.replace('\\', '/') for f in file_paths]
            else:
                if not self.commcell.is_linux_commserv:
                    file_paths[:] = [f.replace('/', '\\') for f in file_paths]
                else:
                    file_paths[:] = [f.replace('\\', '/') for f in file_paths]

            self.log.info("File paths of binaries: %s", format(file_paths))
            return file_paths

        except Exception as exp:
            self.log.exception('Failed to to process binary info dict: %s', format(exp))

    def filter_skipped_files(self, binary_files):
        """
            Filters through the file list and keeps files not includes in the ignoreList

            args:
                binary_files - list of files

            returns:
                Returns new file list
        """
        try:
            self.log.info("Filtering binary files list")
            filtered_files = []
            ignore_list = installer_constants.DOWNLOAD_WIN_IGNORE_LIST + installer_constants.DOWNLOAD_UNIX_SKIP_LIST
            if self.machine_obj.os_info.lower() != 'windows':
                ignore_list[:] = [f.replace('\\', '/') for f in ignore_list]
            for file in binary_files:
                if not any(ignored_file in file for ignored_file in ignore_list):
                    filtered_files.append(file)

            self.log.info("List of filtered files: %s", format(filtered_files))
            return filtered_files

        except Exception as exp:
            self.log.exception('Failed to filter binary files properly: {0}'.format(exp))

    def validate_count_of_files(self, job_id=None):
        """
            validates the count of files downloaded and count of files to be downloaded

            args:
                job_id -- download job id
        """
        try:
            self.log.info("Validating Count of Files")
            if not job_id:
                self.log.info("No job id provided. skipping file count validation")
            else:
                query = 'select EX_TotalMedia, EX_TotalSuccess from JMAdminJobStatsTable where jobId={0}'.format(
                    job_id)
                self.csdb.execute(query)
                db_response = self.csdb.fetch_one_row()
                self.log.info("DB response: %s", format(db_response))
                if db_response[0] == db_response[1]:
                    self.log.info("Validated count of files downloaded. RESULT - SUCCESS")
                else:
                    self.log.info("Validated count of files downloaded. RESULT - FAIL")
                    self.status = False

        except Exception as exp:
            self.log.exception('Failed to validate count of files, with exception: %s', format(exp))
            self.status = False

    def get_cu_path(self, os_name, pack_num):
        """
            Returns the path to CumulativeUpdatePackInstallPack.xml

            args:
                os_name - os name in the cache
                pack_num - cu pack number
        """
        cu_url = f'{self.get_server_url}/CVUpdates/{self.release}/{self.build}/' \
                 f'SP{self.service_pack}_{self.transaction_id}_R{self.revision_id}'
        cu_path = f'{cu_url}/{os_name}/CumulativeUpdatePacks/CU{pack_num}/Config/CumulativeUpdatePackInstallMap.xml'
        self.log.info("cu_path = %s", format(cu_path))
        return cu_path

    def get_hotfix_xml_os_updates_dict(self, hotfix_xml_dict):
        """
        From parsed UpdatesInfo gets the  OS:Updates dict to compare

        args:
            hotfix_xml_dict - hotfix xml dict

        returns:
            dict of os-updates from UpdatesInfo.xml
        """
        try:
            hotfixxml_os_updates_dict = {}
            for key, value in hotfix_xml_dict.items():
                mod_value = self.simos_patchos_dict[int(key)]
                if mod_value in self.os_to_download:
                    update_list = []
                    for each in value:
                        update_list.append(list(each.keys())[0].rstrip('.exe'))
                    if update_list:
                        hotfixxml_os_updates_dict[mod_value] = update_list
            return hotfixxml_os_updates_dict
        except Exception as err:
            self.log.exception(
                "Exception occured in preparing OS-updates dict from UpdatesInfo.xml - %s", str(err))

    def get_hotfix_xml(self):
        """
        return the path for UpdatesInfo xml
        """
        if self.bootstrapper_validation:
            self.log.info("Getting hotfix XML")
            path = f"{self.get_server_url}/CVUpdates/{self.release}/{self.build}/" \
                   f"SP{self.service_pack}_{self.transaction_id}_R{self.revision_id}/UpdatesInfo.xml"
            self.log.info("UpdatesInfo file path: %s", format(path))
            hotfix_xml = self.download_xml(path)
            return hotfix_xml
        else:
            path = self.frame_path(self.base_path, "UpdatesInfo.xml")
            self.log.info("UpdatesInfo file path: %s", format(path))
            if self.machine_obj.check_file_exists(path):
                file_content = self.machine_obj.read_file(file_path=path)
                return file_content
            else:
                raise Exception("Hotfix Validation Failed")

    def parse_hotfix_xml(self, hotfix_path, per_package=False, only_qf=False):
        """
        parses file in hotfix path and returns its content in a dict

        args:
            hotfix_path - UpdatesInfo xml path

            only_qf - Validates only quick fixes but not loose updates if passed as True
        """
        try:
            self.log.info("Parsing hotfix XML")

            if os.path.isfile(hotfix_path):
                tree = ET.parse(hotfix_path)
                root = tree.getroot()
            else:
                root = ET.fromstring(hotfix_path)

            cu_config_xml_path = self.download_xml(self.generate_cu_configuration_url(), True)
            cu_transactionid = installer_utils.get_cu_pack_details_from_xml(self.cu_pack,
                                                                            cu_config_xml_path)["TransactionId"]
            hotfix_dict = {}
            if not per_package:
                for child in root:
                    hotfix_info = {child.attrib['hotfixName']: child.attrib}
                    if int(child.attrib['TransactionId']) > int(cu_transactionid):
                        if int(child.attrib['binarySetId']) not in hotfix_dict.keys():
                            hotfix_dict[int(child.attrib['binarySetId'])] = []
                        if (not only_qf or
                                (only_qf and f"SP{self.service_pack}-{self.cu_pack}" in child.attrib['hotfixName'])):
                            hotfix_dict[int(child.attrib['binarySetId'])].append(hotfix_info)
                return hotfix_dict
            else:
                for child in root:
                    if int(child.attrib['TransactionId']) > int(cu_transactionid):
                        package_id = child.attrib['pkgList'].split(',')
                        for each in package_id:
                            if each.strip():
                                if int(child.attrib['binarySetId']) not in hotfix_dict.keys():
                                    hotfix_dict[int(child.attrib['binarySetId'])] = {}
                                if int(each) not in hotfix_dict[int(child.attrib['binarySetId'])].keys():
                                    hotfix_dict[int(child.attrib['binarySetId'])][int(each)] = []
                                hotfix_dict[int(child.attrib['binarySetId'])][int(each)].append(
                                    (child.attrib['hotfixName']).strip('.exe'))
                return hotfix_dict

        except Exception as err:
            self.log.exception('Hotfix xml parsing failed with path %s', hotfix_path)
            raise err

    def validate_hotfixes(self, os_id=None, only_qf=False):
        """
            Validates hotfixes downloaded
        """
        try:
            ftp_hotfix_xml_path = self.get_hotfix_xml()
            ftp_hotfix_dict = self.parse_hotfix_xml(ftp_hotfix_xml_path, only_qf=only_qf)
            self.log.info("Hotfix files: %s", ftp_hotfix_dict)

            binaryset_id = \
                installer_constants.BinarySetIDMapping[deploymentconstants.OSNameIDMapping(int(os_id)).name].value
            updates_path = self.machine_obj.join_path(
                self.set_updates_path(os_id, self.os_src_path), self.cu_pack, 'Updates')
            if self.machine_obj.os_info.lower() == 'unix':
                updates_path = updates_path.replace('\\', '/')
            if not self.machine_obj.check_directory_exists(updates_path):
                self.log.info("No Hotfixes to validate")
                return
            files_present = self.machine_obj.get_folders_in_path(updates_path, recurse=False)
            files_present = [str(x.split(updates_path)[-1])[1:] for x in files_present]

            missing_updates = []
            for updates in ftp_hotfix_dict[binaryset_id]:
                if list(updates.keys())[0].split('.exe')[0] not in files_present:
                    missing_updates.append(list(updates.keys())[0])

            if missing_updates:
                raise Exception(f"Updates missing in media: {missing_updates}")
            else:
                self.log.info("Hotfix validation PASSED for OS [%s]",
                              installer_constants.OSNAME_LIST[int(os_id)][2])

        except Exception as exp:
            error_msg = f'Hotfix validation failed for OS ' \
                        f'{installer_constants.OSNAME_LIST[int(os_id)][2]} with error {exp}'
            self.log.exception(self.status_msg)
            self.status_msg += '\n' + error_msg
            self.status = False

    def validate_setupexe_patching(self):
        """
            This Method determines if a Setup.exe Update is issued and if it is -> then make sure check sum of the
            latest setup.exe present in the cache and the setup.exe present in the root Folder Matches

        """
        try:
            updates_path = self.frame_path(self.set_updates_path(3, self.os_src_path),
                                           self.cu_pack, "Updates")
            _win_oslist = []
            ftp_hotfix_xml_path = self.get_hotfix_xml()
            per_package_cache_hotfix_config_dict = self.parse_hotfix_xml(ftp_hotfix_xml_path, True)
            for each_os in self.os_to_download:
                if each_os in installer_constants.WINDOWS_BOOTSTRAPPER_DOWNLOAD_OSID:
                    _win_oslist.append(each_os)
            if _win_oslist:
                for each_flavor in _win_oslist:
                    if int(each_flavor) in per_package_cache_hotfix_config_dict.keys() and \
                            installer_constants.ROOT_FILES_PATCHING_ID in \
                            per_package_cache_hotfix_config_dict[int(each_flavor)].keys():
                        latest_update_number = sorted(per_package_cache_hotfix_config_dict[int(
                            each_flavor)][installer_constants.ROOT_FILES_PATCHING_ID])[-1].strip('.exe')
                        self.log.info("Latest Hotfix on Setup.exe that has to be patched is %s", latest_update_number)
                        update_path = self.machine_obj.join_path(updates_path, latest_update_number)
                        update_path = self.machine_obj.join_path(
                            update_path,
                            "BinaryPayload",
                            f"{installer_constants.WINDOWS_DEFAULT_INSTALLER_EXECUTABLE}.zip")
                        if self.machine_obj.check_file_exists(update_path):
                            cmd = f"python -m zipfile -e  {update_path} {self.sample_folder}"
                            checksum_setupexe_looseupdate = commonutils.crc(self.machine_obj.join_path(
                                self.sample_folder, installer_constants.WINDOWS_DEFAULT_INSTALLER_EXECUTABLE))
                            checksum_setupexe_rootdir = commonutils.crc(self.machine_obj.join_path(
                                self.os_src_path, installer_constants.WINDOWS_DEFAULT_INSTALLER_EXECUTABLE))
                            if checksum_setupexe_looseupdate != checksum_setupexe_rootdir:
                                self.log.info("Checksum of setup.exe in root path : %s ; "
                                              "Checksum of setup.exe Update computed :"
                                              " %s",(checksum_setupexe_rootdir, checksum_setupexe_looseupdate))
                                self.log.error("Setup.exe is not properly patched with the latest HotFix")
                                self.status = False

                            else:
                                self.log.info("Setup.exe is patched successfully with the latest Hotfix")
                        else:
                            raise Exception("Failed to Extract Setup.exe Update to compute the checksum")
                    else:
                        self.log.error("Setup.exe.zip is not present")
            else:
                self.log.info("There are no root files for patching")

        except Exception as exp:
            self.log.exception(f"Exception raised at setupexe patching {exp}")

    def validate_oem(self):
        """
        Validates the OEM downloaded in cache and checks if EULA for OEM 1 is also present for all non Commvault OEMS

        """
        try:
            # Get the OEM of CS from registry
            oem_id = self.commserv_cache.cs_client.get_registry_value('', value="nCurrentOEMId")
            oem_folder_path = f"{self.os_src_path}\\Common\\OEM\\{oem_id}"
            eula_file_path = self.machine_obj.join_path(oem_folder_path, "EULAs", "EULAtext.pdf")
            self.log.info(f"Checking path {eula_file_path}")
            if self.machine_obj.check_file_exists(eula_file_path):
                self.log.info("OEM folder and EULA files are present for the corresponding OEM %s", oem_id)
                oem_status = True
            else:
                self.log.info(f"{eula_file_path} path does not exists. "
                              f"OEM folder for ID {oem_id} has not been downloaded/copied")
                oem_status = False

            # check if EULA is downloaded for OEM 1- commvault
            cv_oem_folder_path = f"{self.os_src_path}\\Common\\OEM\\1"
            eula_file_path = self.machine_obj.join_path(cv_oem_folder_path, "EULAs", "EULAtext.pdf")
            self.log.info(f"Checking path {eula_file_path}")
            if self.machine_obj.check_file_exists(eula_file_path):
                self.log.info("EULAtext.pdf is downloaded for the OEM-1")
                default_oem_status = True
            else:
                self.log.info(f"{eula_file_path} path does not exists. "
                              f"OEM folder for ID {oem_id} has not been downloaded/copied")
                default_oem_status = False

            if oem_status and default_oem_status:
                self.log.info("Validation on download of OEM  folder is successful")
            else:
                self.status = False

        except Exception as err:
            self.log.exception("Exception raised in validating the OEM downloaded/copied - %s", str(err))
            self.status = False
