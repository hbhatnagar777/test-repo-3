# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for software cache related operations on the commcell.

This file has all the classes related to software cache operations.

SoftwareCache: Class for software cache related operations

WindowsCacheConfig: Class for software cache related operations for Windows

UnixCacheConfig: Class for software cache related operations for Unix

SoftwareCache:

    __new__()                           --  returns the respective class object based on the os_info

    __init__()                          --  initializes instance of SoftwareCache class

    get_cs_cache_path()                 --  returns commserve cache path

    get_packages()                      --  returns list of packages installed on the client

    is_packages_installed()             --  check if package with given id is installed or not

    get_binary_info_path()              --  returns the binaryinfo.xml path based on operating system

    get_remote_cache_path()             --  returns remote cache path

    get_remote_cache_path_to_validate() --  returns media path under remote cache to validate

    configure_remotecache()             --  configures client as remote cache

    get_cs_installed_media()            --  returns the media installed on CS

    get_media_in_cs_cache()             --  returns list of media present in CS cache

    get_media_to_sync()                 --  returns list of media to sync to remote cache

    configure_packages_to_sync()        --  configures packages to sync for the remote cache

    binary_info_xml_to_dict()           --  convert BinaryInfo.xml into dictionary

    get_binary_info()                   --  returns binary details if 'Binary' tag exists

    get_package_id()                    --  returns package id if tag 'Package' exists

    _get_third_party_packages()         --  returns dictionary of third party packages required

    get_root_files()                    --  returns tuple of list of all the root files

    delete_remote_cache_contents()      --  deletes remote cache contents

    point_to_internal()                 --  points the CS to internal FTP

    get_download_job_obj_from_schedule  --  returns download job id from scheduled task

    update_client_gateway_details_in_cs --

WindowsCacheConfig:

    __init__()                          --  initializes instance of WindowsCacheConfig class

    configure_remotecache()             --  configures client as remote cache

    get_remote_cache_path_to_validate() --  returns media path under remote cache to validate

    get_root_files()                    --  returns list of all the root files

UnixCacheConfig:

    __init__()                          --  initializes instance of UnixCacheConfig class

    configure_remotecache()             --  configures client as remote cache

    get_remote_cache_path_to_validate() --  returns media path under remote cache to validate

    get_root_files()                    --  returns list of all the root files

"""
import time
import inspect
import collections
from xml.etree.ElementTree import Element
from abc import ABCMeta, abstractmethod
import xmltodict
from lxml import etree
from AutomationUtils.machine import Machine
from AutomationUtils import database_helper, logger, cvhelper, config
from Install import installer_constants
from cvpysdk.job import Job


class SoftwareCache:
    """Class for software cache related operations"""

    __metaclass__ = ABCMeta

    def __new__(cls, commcell, client_obj=None):
        """
        Returns the respective class object based on the client_obj

        Args:
           commcell   -- commcell object

           client_obj -- client object

        Returns (obj) -- Return the class object based on the client_obj

        """
        if cls is not __class__:
            return super().__new__(cls)

        _os_info = client_obj.os_info if client_obj else commcell.commserv_client.os_info
        if 'unix' in _os_info.lower():
            return UnixCacheConfig(commcell, client_obj)
        else:
            return WindowsCacheConfig(commcell, client_obj)

    def __init__(self, commcell, client_obj=None):
        """
        Initialize instance of the SoftwareCache class.

        Args:
            commcell_obj -- commcell object

            client_obj   -- client object
        """
        self.commcell = commcell
        self.config_json = config.get_config()
        try:
            self.csdb = database_helper.get_csdb()
        except Exception:
            self.csdb = database_helper.CommServDatabase(self.commcell)
            database_helper.set_csdb(self.csdb)
        self.log = logger.get_log()
        self.client_obj = client_obj
        self.current_release_version = self.get_version()
        self.current_cs_media = self.get_cs_installed_media()
        self.cs_client = Machine(self.commcell.commserv_client)
        if client_obj:
            self.remote_cache_obj = self.commcell.get_remote_cache(client_name=self.client_obj.client_name)
        else:
            if self.config_json.Install.use_internal_media:
                self.point_to_internal()

    def get_cs_cache_path(self):
        """
        Returns CS cache path

        Returns:
            CS cache path (str)
        """
        return self.commcell.commserv_cache.get_cs_cache_path()

    def get_package_id(self, element):
        """
        Return package id if tag 'Package' exists
        Args:
            element -- xml element to check
        Returns:
            Return package id if tag 'Package' exists (tuple)
            (is_package -- True if the tag 'Package' exists,
            package    -- package ID if tag exists)
        """
        if not isinstance(element, Element):
            raise TypeError("Invalid Element type passed")
        else:
            is_package = False

            if element.tag == 'Package':
                is_package = True

            if is_package:
                return is_package, element.attrib['pkgID']
            else:
                return is_package, None

    def get_binary_info(self, element):
        """
        returns binary details if "Binary" tag exists
        Args:
            element -- xml element to check
        Returns:
            returns binary details if "Binary" tag exists (tuple)
            (is_binary   -- True if the tag 'Binary' exists,
            name        -- name of the binary,
            checksum    -- checksum of the binary,
            source_path -- source path of the binary,
            size        -- size of the binary)
        """
        if not isinstance(element, Element):
            raise TypeError("Invalid Element type passed")
        else:
            is_binary = False

            if element.tag == 'Binary':
                is_binary = True
            if is_binary:
                name = element.attrib['Name']
                checksum = element.attrib['CheckSum']
                source_path = element.attrib['SourcePath']
                size = element.attrib['SizeInBytes']
                return is_binary, name, checksum, source_path, size
            else:
                return is_binary, None, None, None, None

    def binary_info_xml_to_dict(self, parent_element):
        """
        Convert BinaryInfo.xml into dict
        Args:
            parent_element -- parent element
        Returns:
            dictionary
        """
        if not isinstance(parent_element, Element):
            raise TypeError("Invalid Element Type passed")
        else:
            xml_dict = {}
            children_names = []
            self.log.info("The root node received for parsing is %s", parent_element.tag)

            for child_node in parent_element.iter():
                for each_attribute in child_node.attrib.keys():
                    if each_attribute == 'binarySetId':
                        xml_dict.fromkeys(child_node.attrib[each_attribute])
                        children_names.append(child_node)

            for each_child in children_names:
                base_key = each_child.attrib['binarySetId']
                self.log.info("Enumerating the OS Name is %s", base_key)
                xml_dict.update({base_key: {}})
                for os_child_node in each_child.iter():
                    is_package, package = self.get_package_id(os_child_node)
                    if is_package:
                        if package not in (xml_dict[base_key]).keys():
                            xml_dict[base_key].update({package: {}})
                        for each_child_package in os_child_node.iter():
                            is_binary, name, checksum, source_path, size = self.get_binary_info(each_child_package)
                            if is_binary:
                                if name not in (xml_dict[base_key][package]).keys():
                                    xml_dict[base_key][package].update({source_path: {}})
                                    xml_dict[base_key][package][source_path].update(
                                        {'Name': name, 'Sourcepath': source_path, 'checksum': checksum, 'size': size})
                            else:
                                continue
                    else:
                        continue
            return xml_dict

    def get_packages(self, client_id=2):
        """
        returns list of packages installed on the client
        Args:
            client_id -- client id. Default is 2

        Returns:
            returns list of package ids installed on the client

        """

        packages = []
        query = f"select simPackageID from simInstalledPackages where ClientId = {client_id}"
        self.csdb.execute(query)
        data = self.csdb.fetch_all_rows()
        for package in data:
            packages.append(int(package[0]))
        return packages

    def is_package_installed(self, clientid, package_id, retry_interval=20, time_limit=7, hardcheck=True):
        """ Check if package with given id is installed or not

            Args:

                clientid (int)             -- Client object

                package_id (int)           -- Package id

                retry_interval    (int)    -- Interval (in seconds), checked in a loop. Default = 20

                time_limit        (int)    -- Time limit to check for. Default (in minutes) = 7

                hardcheck         (bool)   -- If True, function will exception out in case package is not installed
                                              If False, function will return with non-truthy value. Default: True

            Returns:
                True/False        (bool)   -- In case package is/(is not) installed or not

            Raises:
                Exception if :

                    - failed during execution of module
                    - package is not installed in given time limit
        """
        try:

            self.log.info("Checking if package id %s is installed on client %s", str(package_id), str(clientid))
            packages = self.get_packages(clientid)

            time_limit = time.time() + time_limit * 60
            while True:
                if (package_id in packages) or (time.time() >= time_limit):
                    break
                else:
                    self.log.info(
                        "Waiting for %s seconds. Package id [%s] not installed on client.",
                        str(retry_interval),
                        str(package_id)
                    )
                    time.sleep(retry_interval)
                    packages = self.get_packages(clientid)

            if package_id not in packages:
                if not hardcheck:
                    return False

                raise Exception("Package [%s] not installed on client with id [%s]", str(package_id), str(clientid))

            self.log.info("Package id [%s] installed on client [%s]", str(package_id), str(clientid))
            return True

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def get_version(self):
        """
        returns current release version

        Returns:
            returns current release version. E.g "11.0.0"
        """

        return f"{self.commcell.version[:2]}.0.0"

    def get_third_party_packages(self, xmlpath, os_id, package_list):
        """
        returns dictionary of third party packages required
        Args:
            xml_path        -- Winpackages.xml path
            os_id           -- os id
            package_list    -- list of packages for the os

        Returns:
            returns list of dictionary of third party packages required

        Raises:
            exception if unable to parse winpackages.xml/pkg.xml
        """
        try:
            package_list_int = [int(x) for x in package_list]
            with open(xmlpath) as fd:
                windows_pkg_dict = xmltodict.parse(fd.read())
            third_party_list = set()
            for each in windows_pkg_dict['UpdatePatches_PackageDetails']['PackageInfoList']['pkginfo']:
                if (int(each['@pkgID']) in package_list_int) and (each['@binarySetId'] == str(os_id)):
                    if 'ThirdPartyPackage' in each:
                        if isinstance(each['ThirdPartyPackage'], list):
                            for every in each['ThirdPartyPackage']:
                                third_party_list.add(int(every['@ID']))
                        elif isinstance(each['ThirdPartyPackage'], dict):
                            third_party_list.add(int(each['ThirdPartyPackage']['@ID']))

            return list(third_party_list)

        except Exception as exp:
            raise Exception("Exception in getting third party package id - %s", exp)

    def configure_packages_to_sync(self, win_os=None, win_package_list=None, unix_os=None,
                                   unix_package_list=None):
        """
        Configures packages to sync for the remote cache

        Args:
            win_os 		(list)	 	-- list of windows oses to sync
            win_package_list  (list)-- list of windows packages to sync
            unix_os (list) 		  	-- list of unix oses to sync
            unix_package_list (list)-- list of unix packages to sync

        Raises:
            SDKException:
            - Failed to execute the api

            - Response is incorrect

            - Incorrect input
        """
        try:
            self.log.info("Configuring packages to remote cache %s", self.client_obj.client_name)
            self.remote_cache_obj.configure_packages_to_sync(
                win_os=win_os,
                win_package_list=win_package_list,
                unix_os=unix_os,
                unix_package_list=unix_package_list)

        except Exception as exp:
            raise Exception("Failed to configure packages to Remote cache with error - %s", exp)

    def get_remote_cache_path(self):
        """
        Returns remote cache path
        """
        return self.remote_cache_obj.get_remote_cache_path()

    def get_cs_installed_media(self):
        """
        Returns media installed in CS

        Returns:
            Service pack (str) -- service pack installed on the CS E.g. SP20_2564690_R751
        """
        query = f"select top 1 Release,SPMajor,TransactionID,RevisionID from PatchSPVersion where TransactionID = " \
            f"(select TransactionID from PatchDBSPInfo) and SPMajor = (select SPNumber from PatchDBSPInfo) " \
            f"order by RevisionID DESC"
        self.csdb.execute(query)
        data = self.csdb.fetch_one_row()
        return f"SP{data[1]}_{data[2]}_R{data[3]}"

    def get_media_in_cs_cache(self):
        """
        Returns a list of media present in CS cache
        E.g. ['SP18_2357765_R713', 'SP19_2548879_R747']
        """
        feature_release = []
        query = f"""select concat('SP',SPMajor,'_',TransactionID,'_R',RevisionID) from PatchSPVersion where id in
        (select distinct spversionid from patchMulticache WHERE ReleaseId = 16 and clientid =2)"""
        self.csdb.execute(query)
        data = self.csdb.fetch_all_rows()
        for fp in data:
            feature_release.append(fp[0])
        return feature_release

    def get_latest_maintenance_release(self, service_pack=None):
        """
        returns the lastest maintenance release number available for download
        Args:
            service_pack (str) -- Service pack E.g. 19
        """
        if not service_pack:
            service_pack = self.commcell.commserv_client.service_pack
        query = f"select max(UPNumber) from patchupversion where SPVersionID = " \
                f"(select top 1 id from PatchSPVersion where SPMajor = {service_pack}" \
                f"  order by TransactionID desc) and bIsAvailableForDownload = 1 and bShowInGUI = 1"
        self.csdb.execute(query)
        data = int(self.csdb.fetch_one_row()[0]) if self.csdb.fetch_one_row()[0] != 'Null' else 0
        return data

    def get_media_to_sync(self):
        """
        Returns list of media to sync to RC

        raises:
            exception if unable to execute stored procedure
        """
        try:
            encrypted_password = self.cs_client.get_registry_value(r"Database", "pAccess")
            sql_password = cvhelper.format_string(self.commcell, encrypted_password).split("_cv")[1]
            sql_instancename = "{0}\\commvault".format(self.commcell.commserv_hostname.lower())
            db = database_helper.MSSQL(
                server=sql_instancename,
                user='sqladmin_cv',
                password=sql_password,
                database='commserv',
                as_dict=False
            )
            xml_op = db.execute(
                f'SET NOCOUNT ON;exec SimGetRCConfiguredSPs {self.client_obj.client_id};'
                f'SET NOCOUNT OFF')
            root = etree.fromstring(xml_op.rows[0][0])
            sp_os_list = {}
            for fr in root.findall(".//verOs/fullVersion/spVersion"):
                os_list = []
                feature_release = f"SP{fr.get('Major')}_{fr.get('TransactionId')}_R{fr.get('RevisionID')}"
                for os in fr.getparent().getparent().findall("OSId"):
                    os_list.append(int(os.get('updateOSId')))
                sp_os_list[feature_release] = os_list
            sp_os_list[self.current_cs_media] = None
            final_sp_os_list = dict([(key, sp_os_list[key])
                                     for key in sp_os_list if key in self.get_media_in_cs_cache()])
            return final_sp_os_list

        except Exception as exp:
            raise Exception("Exception occurred while getting media to sync - %s", exp)

    def get_binary_info_path(self, base_os, base_path, os_flavour=None):
        """
        Returns the binaryinfo.xml path based on os
        Args:
            base_os    -- Base OS. E.g. Windows, Unix
            base_path  -- base path of the os in the cache
            os_flavour -- os flavour for Unix. Default is None

        Returns:
            Returns the binaryinfo.xml path based on os

        Raise:
            exception if unable to form path

        """
        try:
            self.log.info("Base path provided is %s", base_path)
            if base_os == "Windows":
                xml_path = self.cs_client.join_path(base_path, base_os, "BinaryInfo.xml")

            else:
                xml_path = self.cs_client.join_path(base_path, base_os, os_flavour, "BinaryInfo.xml")

            return xml_path

        except Exception as exp:
            raise Exception("Exception occurred while getting BinaryInfo XML Path - %s", exp)

    def delete_remote_cache_contents(self):
        """
        Delete remote cache contents
        """
        self.log.info("Deleting remote cache contents of %s", self.client_obj.client_name)
        self.remote_cache_obj.delete_remote_cache_contents()

    def point_to_internal(self, **kwargs):
        """
            Points the CS to the internal server
        """
        self.log.info("Pointing CS to internal server")
        self.commcell.add_additional_setting(category="CommServDB.GxGlobalParam", key_name="Patch HTTP Use Token",
                                             data_type="INTEGER", value=str(kwargs.get('use_patch_http_token', 0)))
        self.commcell.add_additional_setting(category="CommServDB.GxGlobalParam", key_name="Patch HTTP Site",
                                             data_type="STRING",
                                             value=str(kwargs.get('http_site', installer_constants.DEFAULT_HTTP_SITE)))
        self.commcell.add_additional_setting(category="CommServDB.GxGlobalParam", key_name="Patch Config URL Prefix",
                                             data_type="STRING",
                                             value=str(kwargs.get('config_url_prefix',
                                                                  installer_constants.DEFAULT_CONFIG_URL_PREFIX)))
        self.commcell.add_additional_setting(category="CommServDB.GxGlobalParam",
                                             key_name="PatchSPAdditionalDelayDays", data_type="INTEGER",
                                             value=str(kwargs.get('sp_additional_delay_days', 0)))
        self.commcell.add_additional_setting(category="CommServDB.GxGlobalParam", key_name="nUsePreReleaseFRInfo",
                                             data_type="INTEGER", value=str(kwargs.get('use_pre_release_info', 1)))
        try:
            visibility_level = eval(f"installer_constants.DefaultVisibilityLevels.{self.config_json.Install.visibility_flag}.value")
        except:
            visibility_level = installer_constants.DefaultVisibilityLevels.LAB_USERS.value
        self.log.info(f"Setting the visibility level as : {visibility_level}")
        self.commcell.add_additional_setting(
            category="CommServDB.GxGlobalParam", key_name="Patch Visibility Level", data_type="INTEGER",
            value=str(kwargs.get('visibility_level', visibility_level)))

    def get_download_job_obj_from_schedule(self, schedule_obj):
        """
            Get Job object from Scheduled Task
        """
        task_id = schedule_obj.task_id
        query = f"select jobId from tm_jobs where jobRequestId = (select jobRequestId from TM_JobRequest " \
                f"where taskId = {task_id} and subtaskId in (select subTaskId from TM_SubTask where taskId={task_id}))"
        self.csdb.execute(query)
        response = self.csdb.fetch_one_row()
        if not response[0]:
            self.log.info(f"Failed to get job id from scheduled task, the output is {response}")
            raise Exception("Failed to get job id from scheduled task")
        return Job(self.commcell, response[0])

    def update_client_gateway_details_in_cs(self, client_gateway=None, reset=False):
        """
            set client gateway details
        """
        try:
            if reset:
                self.commcell.add_additional_setting(category="CommServDB.GxGlobalParam",
                                                     key_name="DownloadInternetGtwyEnabled",
                                                     data_type="INTEGER", value=str(0))
            elif client_gateway:
                client_id = self.commcell.clients.get(client_gateway).client_id
                self.commcell.add_additional_setting(category="CommServDB.GxGlobalParam",
                                                     key_name="DownloadInternetGtwyEnabled",
                                                     data_type="INTEGER", value=str(1))
                self.commcell.add_additional_setting(category="CommServDB.GxGlobalParam",
                                                     key_name="CommservSurveyCollectionProxy",
                                                     data_type="INTEGER", value=str(client_id))
                self.commcell.add_additional_setting(category="CommServDB.GxGlobalParam",
                                                     key_name="CommservSurveyProxyClientEnabled",
                                                     data_type="INTEGER", value=str(1))
                self.commcell.add_additional_setting(category="CommServDB.GxGlobalParam",
                                                     key_name="CommservSurveyPrivateProxyClientEnabled",
                                                     data_type="INTEGER", value=str(1))
        except Exception as exp:
            self.log.error(exp)
            raise Exception("Failed to update client gateway details in CS")

    def update_http_proxy_details_in_cs(self, proxy_name=None, proxy_port=None, reset=False):
        """
            Set http proxy details
        """
        try:
            if reset:
                self.commcell.add_additional_setting(category="CommServDB.GxGlobalParam",
                                                     key_name="SendLogsUseHTTPProxy",
                                                     data_type="INTEGER", value=str(0))
            else:
                self.commcell.add_additional_setting(category="CommServDB.GxGlobalParam",
                                                     key_name="SendLogsHTTPProxyPort",
                                                     data_type="INTEGER", value=str(proxy_port))
                self.commcell.add_additional_setting(category="CommServDB.GxGlobalParam",
                                                     key_name="SendLogsHTTPProxySite",
                                                     data_type="STRING", value=str(proxy_name))
                self.commcell.add_additional_setting(category="CommServDB.GxGlobalParam",
                                                     key_name="SendLogsUseHTTPProxy",
                                                     data_type="INTEGER", value=str(1))
        except Exception as exp:
            self.log.error(exp)
            raise Exception("Failed to set http details in DB")

    def set_protocol_type(self, protocol):
        """
            Sets the protocol like FTP, Http, Https
        """
        try:
            self.log.info(f"Setting the protocol type as {protocol}")
            self.commcell.add_additional_setting(category="CommServDB.GxGlobalParam",
                                                 key_name="Patch Download Protocol",
                                                 data_type="STRING", value=str(protocol))
        except Exception as exp:
            self.log.error(exp)
            raise Exception("Failed to Set Protocol type in DB")

    @abstractmethod
    def get_remote_cache_path_to_validate(self, media):
        """
        Returns media path under remote cache to validate

        Args:
            media to validate in remote cache

        Returns:
            media path in remote cache(str)
        """

    @abstractmethod
    def configure_remotecache(self, cache_path=None):
        """
        Configures client as remote cache
        Args:
            cache_path - Remote cache path
        Raises:
            exception if qoperation fails
        """

    @abstractmethod
    def get_root_files(self, cache_path):
        """
        Returns list of all the root files
        Args:
            cache_path      -- cache path
        Returns:
            tuple of list of all the root files
        Raises:
            exception if unable to compute list of files
        """


class WindowsCacheConfig(SoftwareCache):
    """Class for software cache related operations for Windows"""

    def __init__(self, commcell, client_obj=None):
        """
        Initialises the WindowsCacheConfig class

        Args:

            commcell   -- commcell object

            client_obj -- client object
        """
        super().__init__(commcell, client_obj)

    def configure_remotecache(self, cache_path=None):
        """
        Configures client as remote cache

        Args:
            cache_path - Remote cache path
        Raises:
            exception if qoperation fails
        """
        try:
            if not cache_path:
                cache_path = f"{self.client_obj.install_directory}\\SoftwareCache"
            self.log.info("Configuring client %s as remote cache", self.client_obj.client_name)
            self.remote_cache_obj.configure_remotecache(cache_path=cache_path)

        except Exception as exp:
            self.log.exception("Failed to configure Remote cache with error - %s", exp)

    def get_remote_cache_path_to_validate(self, media):
        """
        Returns media path under remote cache to validate

        Args:
            media to validate in remote cache

        Returns:
            media path in remote cache(str)
        """
        remote_cache_path = f"{self.get_remote_cache_path()}\\{installer_constants.DOWNLOAD_SOFTWARE_DEFAULT_MEDIA}" \
            f"\\{self.current_release_version}\\{media}"
        return remote_cache_path

    def get_root_files(self, cache_path):
        """
        Returns list of all the root files
        Args:
            cache_path      -- cache path
        Returns:
            tuple of list of all the root files
        Raises:
            exception if unable to compute list of files
        """
        try:

            win_root_list = []
            unix_root_list = []
            for each in installer_constants.UNIX_ROOT_LIST:
                unix_root_list.append(cache_path + each)
            for each in installer_constants.WIN_ROOT_LIST:
                win_root_list.append(cache_path + each)
            return win_root_list, unix_root_list

        except Exception as exp:
            self.log.exception("Exception in getting root files- %s", exp)


class UnixCacheConfig(SoftwareCache):
    """Class for software cache related operations for Unix"""

    def __init__(self, commcell, client_obj=None):
        """
        Initialises the WindowsCacheConfig class

        Args:

            commcell   -- commcell object

            client_obj -- client object
        """
        super().__init__(commcell, client_obj)

    def configure_remotecache(self, cache_path=None):
        """
        Configures client as remote cache

        Args:
            cache_path - Remote cache path
        Raises:
            exception if qoperation fails
        """
        try:
            if not cache_path:
                cache_path = f"{self.client_obj.install_directory}/SoftwareCache"
            self.log.info("Configuring client %s as remote cache", self.client_obj.client_name)
            self.remote_cache_obj.configure_remotecache(cache_path=cache_path)

        except Exception as exp:
            self.log.exception("Failed to configure Remote cache with error - %s", exp)

    def get_remote_cache_path_to_validate(self, media):
        """
        Returns media path under remote cache

        Args:
            media to validate in remote cache

        Returns:
            media path in remote cache(str)
        """
        remote_cache_path = (f"{self.get_remote_cache_path()}/{installer_constants.DOWNLOAD_SOFTWARE_DEFAULT_MEDIA}/"
                             f"{self.current_release_version}/{media}")
        return remote_cache_path

    def get_root_files(self, cache_path):
        """
        Returns list of all the root files
        Args:
            cache_path      -- cache path
        Returns:
            tuple of list of all the root files
        Raises:
            exception if unable to compute list of files
        """
        try:

            win_root_list = []
            unix_root_list = []
            for each in installer_constants.UNIX_ROOT_LIST:
                unix_root_list.append(cache_path + each.replace("\\", "/"))
            for each in installer_constants.WIN_ROOT_LIST:
                win_root_list.append(cache_path + each.replace("\\", "/"))
            return win_root_list, unix_root_list

        except Exception as exp:
            self.log.exception("Exception in getting root files- %s", exp)
