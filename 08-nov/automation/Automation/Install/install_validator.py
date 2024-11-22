# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Helper file for performing Install validation

InstallValidator
================

    __new__()                                   --      based on the OS details Windows / UNIX,
                                                        initialize the class instance accordingly

    __init__()                                  --      initializes Install validator helper object

    validate_services()                         --      to validate services installed on client

    check_feature_release_version_installed     --      to validate FR version of client

    validate_baseline()                         --      to validate if baseline is correct

    validate_sp_info_in_db()                    --      to validate if package sp version matches that of commserve

    validate_oem()                              --      to validate the OEM properties of client

    validate_company()                          --      to validate if the client is registered to the correct company

    get_list_of_hotfixes_from_installation_media--      to get list of hotfixes from media

    get_additional_path_info_from_db()          --      to get list of hotfixes from DB

    validate_install()                          --      to validate install of client

    get_looseupdates_fromcache()                --      to get loose updates from cache

    get_latestfolder_touse()                    --      to get the latest folder to use from the cache folders

    get_media_path()                            --      to get the media path for the installation


WindowsValidator
================

    __init__()                                  --      initializes Install validator helper object

    check_if_installer_key_exists()             --      to validate installer keys in registry

    validate_installed_packages()               --      to validate packages installed

    validate_services()                         --      to validate services in a windows client

    console_name_validation()                   --      to validate console name

    validate_loose_updates_install()            --      to validate install loose updates

    validate_install()                          --      to validate install of windows client

UnixValidator
================

    __init__()                                  --      initializes Install validator helper object

    check_if_installer_key_exists()             --      to validate installer keys in registry

    validate_installed_packages()               --      to validate packages installed

    validate_services()                         --      to validate services in a unix client

    validate_installed_directory()              --      to validate installed directories

    check_service_status()                      --      to validate a single service in a unix client

    validate_loose_updates_install()            --      to validate install loose updates

    validate_nonroot_install()                  --      to verify if the installer honored the non-root flag

    validate_nonroot_services()                 --      to verify if services are running as non-root

    validate_install()                          --      to validate install of unix client

Attributes
----------

    **package_id**      --  returns the package id list based on the package names

"""
from abc import ABCMeta
import xmltodict
import urllib3
from AutomationUtils import logger,config
from AutomationUtils.machine import Machine
from AutomationUtils.constants import AUTOMATION_DIRECTORY
from AutomationUtils.database_helper import CommServDatabase
from Install import installer_constants, installer_utils
from cvpysdk.deployment.deploymentconstants import OSNameIDMapping
from Server.Security.securityhelper import OrganizationHelper
from Server import mongodb_helper

class InstallValidator:
    """Install validator for windows and unix machines"""
    __metaclass__ = ABCMeta

    def __new__(cls, machine_name, testcase_object=None, commcell_object=None, **kwargs):
        """
        Returns the instance of one of the Subclasses WindowsValidator / UnixValidator,
        based on the OS details of the remote client.

        """
        if testcase_object:
            machine = Machine(machine_name, testcase_object.commcell)
        else:
            machine = Machine(machine_name, commcell_object)
        if 'windows' in machine.os_info.lower():
            instance = object.__new__(WindowsValidator)
        elif 'unix' in machine.os_info.lower():
            instance = object.__new__(UnixValidator)
        else:
            raise Exception("Validation is not implemented for this os")

        instance.machine = machine
        return instance

    def __init__(self, machine_name, testcase_object=None, commcell_object=None, **kwargs):
        """
        Initializes instance of the InstallValidator class.

        Args:
            machine_name    (str)           -- machine to validate install on

            testcase_object    (object)     -- object of TestCase class

            commcell_object    (object)     -- object of Commcell class

            **kwargs: (dict)                -- Key value pairs for supporting conditional initializations
            Mandatory-

            package_list (list)                -- List of packages selected for install. Eg: ['20']

                default : [1]

            Supported -

            machine_object (object)         -- Machine class object of client

                default : Machine(machine_name, self.commcell)

            is_push_job (bool)              -- Whether installation is through a push job

                default : False

            oem_id (int)                    -- OEM ID of installer

                default : 1

            feature_release (str)                  -- Service Pack

                default : self.commcell.commserv_version

            cu_version (str)                  -- CU pack

                default : None

            media_path (str)                   -- Path of installer used instead of Bootstrapper

                default : None

            unix_flavour (str)              -- Unix flavour

                default : linux-x8664

            is_32_on_64_bit (bool)           -- Whether 32-bit installer is used on a 64-bit Machine

                default : False

        """
        self.security_helper = None
        self.machine_name = machine_name
        self._server_url = None
        if commcell_object:
            self.log = logger.get_log()
            self.commcell = commcell_object
            self.csdb = CommServDatabase(self.commcell)
        else:
            self.log = testcase_object.log
            self.commcell = testcase_object.commcell
            self.csdb = CommServDatabase(
                testcase_object.commcell) if testcase_object.csdb is None else testcase_object.csdb
        self.client_id = self.commcell.clients.get(machine_name).client_id
        self.machine = kwargs.get('machine_object', Machine(machine_name, self.commcell))
        self.os_info = None
        self.status_flag = True
        self.status_msg = "\n"
        self.installed_packages = kwargs.get('package_list', [])
        self.is_push_job = kwargs.get('is_push_job', False)
        self.oem_id = str(kwargs.get('oem_id', 1))
        self.is_32_on_64_bit = kwargs.get('is_32_on_64_bit', False)
        self.installation_path = self.machine.get_registry_value(commvault_key='Base', value='dGALAXYHOME')
        self.feature_release = kwargs.get('feature_release', str(self.commcell.commserv_version))
        if '_' in self.feature_release:
            self.feature_release = self.feature_release.split('_')[0].lower().split('sp')[1]
        self.media_path = kwargs.get('media_path', None)
        _latest_recut = installer_utils.get_latest_recut_from_xml(self.feature_release)
        self.cs_machine = Machine(self.commcell.commserv_client)
        path = self.commcell.commserv_cache.get_cs_cache_path()
        default_cu = str(installer_utils.get_latest_cu_from_media(self.media_path, self.machine)) if self.media_path \
            else str(installer_utils.get_latest_cu_from_media(path, self.cs_machine)) if self.is_push_job \
            else str(installer_utils.get_latest_cu_from_xml(_latest_recut))
        self.cu_version = kwargs.get('cu_version', default_cu)

    def __repr__(self):
        """
        String representation of the instance of this class.

        Returns:
            str - string about the details of the Machine class instance

        """
        return f"InstallValidator class instance of Host {self.machine_name}"

    def __del__(self):
        """
        destructor of the class InstallValidator

        """
        del self.machine_name
        del self.log
        del self.csdb
        del self.commcell
        del self.client_id

    def validate_services(self):
        """
        To validate if services are running on the client machine or not

        Raises:
             Exception:

                if service is not running

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def check_feature_release_version_installed(self):
        """
                To validate FR version of client

                Raises:
                     Exception:
                        if FR version is wrong
        """
        req_version = f"{installer_constants.CURRENT_RELEASE_VERSION.split('.')[0]}." \
                      f"{self.feature_release}.{self.cu_version}"
        self.log.info(f"Required feature release version : {req_version}")
        result = self.machine.get_registry_value(commvault_key='', value='sProductVersion')
        self.log.info(f"Feature release version from registry: {result}")
        if req_version == result:
            self.log.info("Feature release version validation successful")
        else:
            self.log.error("Feature release version installed is different from the expected value")
            self.status_flag = False
            self.status_msg += "Feature release version validation failed\n"

    def validate_baseline(self):
        """
        To validate if baseline for the installed packages is 1 or not

        Raises:
             Exception:

                if baseline of the package is not 1
        """
        packages = self.req_pkg_dict.keys()
        status = True
        if self.is_push_job:
            expected_baseline = str(installer_constants.BaselineStatus.UP_TO_DATE.value)
            for package in packages:
                query = f"select  baseline from simInstalledPackages where " \
                        f"ClientId={self.client_id} and simPackageID={package}"
                self.csdb.execute(query)
                if self.csdb.fetch_one_row()[0] != expected_baseline:
                    status = False
                    try:
                        baseline = installer_constants.BaselineStatus(int(self.csdb.fetch_one_row()[0])).name
                    except Exception:
                        baseline = 'N/A'
                    self.log.error(f'Baseline of package {package} is {baseline} not '
                                   f'{expected_baseline} on client {self.machine_name}')
            if status:
                self.log.info("Baseline validation successful")
            else:
                self.status_flag = False
                self.status_msg += "Baseline validation failed\n"
        else:
            self.log.info("Skipping baseline validation as the installation is not marked as push installation")

    def validate_sp_info_in_db(self):
        """
        To validate if sp version for the installed packages matches the commserv version or not

        Raises:
             Exception:

                if sp version is not same as commserv version

        """
        sp_flag = True
        packages = self.req_pkg_dict.keys()
        query = f"select HighestSP,UPNumber,simPackageID from simInstalledPackages where ClientId = {self.client_id}"
        self.csdb.execute(query)
        if isinstance(self.csdb.fetch_all_rows(), list):
            for row in self.csdb.fetch_all_rows():
                highest_sp = row[0]
                cu_version = row[1]
                package_id = row[2]
                if package_id in packages:
                    if highest_sp != str(self.feature_release):
                        self.log.error(f'SP version of package {self.req_pkg_dict[package_id]} on '
                                       f'client {self.machine_name} is not same as DB value')
                        sp_flag = False
                    if cu_version != str(self.cu_version):
                        self.log.error(f'CU version (CU{self.cu_version}) of package {self.req_pkg_dict[package_id]} '
                                       f'on client {self.machine_name} is not same as DB value (CU{cu_version})')
                        sp_flag = False
        else:
            self.log.error(f"Value returned from DB : {self.csdb.fetch_all_rows()}")
            sp_flag = False

        if sp_flag:
            self.log.info("SP info validation in DB successful")
        else:
            self.status_flag = False
            self.status_msg += "SP info validation in DB failed\n"

    def validate_oem(self):
        """
                 To validate OEM value selected during install and ContentStore is created with the correct OEMid folder
        """
        output1 = self.machine.get_registry_value(commvault_key='', value='nCurrentOEMId')
        output2 = self.machine.get_registry_value(commvault_key='Base', value='dBASEHOME')
        if self.is_32_on_64_bit:
            reg_key = installer_constants.COMMVAULT_REGISTRY_ROOT_32BIT_WINDOWS + "\\Instance001"
            output1 = self.machine.get_registry_value(commvault_key='', value='nCurrentOEMId', win_key=reg_key)
            output2 = self.machine.get_registry_value(commvault_key='Base', value='dBASEHOME',
                                                      win_key=reg_key + "\\Base")

        brand_name = installer_constants.oemid_edition_name(self.oem_id)
        if output1 == str(self.oem_id) and brand_name.lower() in output2.lower():
            self.log.info("OEM validation successful")
        else:
            self.log.error("OEM validation failed")
            self.status_flag = False
            self.status_msg += "OEM validation failed\n"

    def get_list_of_hotfixes_from_installation_media(self, updates_path):
        """
                To get a list of loose updates(hotfixes) for each package from the installation media in dicitionary form
        """
        try:
            loose_updates_dict = {}
            machine_obj = Machine(self.commcell.commserv_client) if self.is_push_job else self.machine
            if machine_obj.check_directory_exists(updates_path):
                for each in machine_obj.get_folders_in_path(updates_path, recurse=False):
                    if each != updates_path:
                        config_path = machine_obj.join_path(each, "Config", "update.ini")
                        for section in machine_obj.read_file(config_path, search_term='\\[[0-9][0-9]*:.').split('\n'):
                            if ':' in section:
                                package_name = section.replace('[', '').split(':')[0]
                                if package_name in loose_updates_dict.keys():
                                    loose_updates_dict[package_name].append(each.split('_')[-1])
                                else:
                                    loose_updates_dict[package_name] = []
                                    loose_updates_dict[package_name].append(each.split('_')[-1])
            return loose_updates_dict
        except Exception as exp:
            self.log.error(f"Exception in get_list_of_hotfixes_from_installation_media: {exp}")
            return {}

    def get_additional_path_info_from_db(self):
        """
                To get list of hotfixes from DB
        """
        query = f"select simPackageID,AdditionalPatches,MissingPatches " \
                f"from simInstalledPackages where ClientId = {self.client_id}"
        self.csdb.execute(query)
        response = self.csdb.fetch_all_rows()
        additional_patches_dict = {}
        for each in response:
            if str(each[1].upper()) != "NONE":
                update_list = each[1].split(",")
            else:
                update_list = []
            update_list = [x for x in update_list if x != '']
            additional_patches_dict[int(each[0])] = update_list
        return additional_patches_dict

    def check_if_installation_dir_empty(self):
        """"
            To validate installation directory after uninstallation
        """
        if self.machine.check_directory_exists(self.installation_path):
            self.log.error("Installation directory still exists even after successful uninstallation")
            self.status_flag = False
            self.status_msg += "Installation directory still exists even after successful uninstallation\n"
        else:
            self.log.info("Installation path validation successful")

    def check_if_registry_entries_exists(self, reg_key):
        """"
            To validate registry entries after uninstallation
        """
        self.log.info(f"Validating if registry entries are removed under {reg_key}")
        result = self.machine.check_registry_exists(reg_key)
        if result:
            self.log.error("Registry entries still exists even after successful uninstallation")
            self.status_flag = False
            self.status_msg += "Registry entries still exists even after successful uninstallation\n"
        else:
            self.log.info("Registry key validation successful")

    def validate_client_company(self, company=None):
        """
            To validate if the client was installed to a particular company
        """
        self.security_helper = OrganizationHelper(self.commcell, company)
        clients = self.security_helper.get_company_clients()
        client_name = self.commcell.clients.get(self.machine_name).client_name
        if client_name in clients:
            self.log.info(f"Client registered successfully to the company {company}")
        else:
            self.status_flag = False
            self.log.info(f"Client failed to register to the company {company}")

    def validate_mongodb(self):
        """
            To validate MongoDB during installation
        """
        try:
            self.mongoDB_Helper = mongodb_helper.MongoDBHelper(self.commcell, self.machine_name)
            self.config_json = config.get_config()

            self.mongoDB_Helper.validate_service_status()
            self.mongoDB_Helper.validate_installed_mongodb_version()
            self.mongoDB_Helper.validate_cc_login(self.commcell.commcell_username, self.config_json.Install.cs_password)
            self.mongoDB_Helper.validate_check_readiness()

            self.log.info("Completed MongoDB validation for the CS")
        except Exception as e:
            self.log.error(f"Error in MongoDB validation : {e}")
            self.status_flag= False
            self.status_msg += "MongoDB validation failed\n"

     
    def get_latestfolder_touse(self, cache_folders, cupack=False):
        """
        Get the latest folder to use from the cache folders.

        Args:
            cache_folders (list): List of cache folders.
            cupack (bool, optional): If True, find the latest CU folder. Defaults to False.

        Returns:
            str: The latest folder to use.

        Raises:
            Exception: If failed to get the CS cache path to use.

        """
        try:
            found = False
            latestFolder = ""
            for folder in cache_folders:
                if (not cupack and folder.find("SP") >= 0) or (cupack and folder.find("CU") >= 0):
                    found = True
                    if latestFolder == "":
                        latestFolder = folder
                    else:
                        if not cupack:
                            latestFolderSplit = latestFolder.split("_")
                            currentFoldrSplit = folder.split("_")
                            if (
                                latestFolderSplit[0] >= currentFoldrSplit[0]
                                and latestFolderSplit[1] >= currentFoldrSplit[1]
                                and latestFolderSplit[2] >= currentFoldrSplit[2]
                            ):
                                latestFolder = latestFolder
                            else:
                                latestFolder = folder
                        else:
                            if int(latestFolder.replace("CU", "")) >= int(folder.replace("CU", "")):
                                latestFolder = latestFolder
                            else:
                                latestFolder = folder
            if not found and not cupack:
                self.log.error("Failed to get CS cache path to use [%s]." % (str(cache_folders)))
                raise Exception("Failed to get CS cache path to use.")

            self.log.info("CS cache version path to use [%s]." % (str(latestFolder)))
            return latestFolder

        except Exception as err:
            raise Exception("Exception occurred while processing CS cache: %s" % err)
        
    def get_media_path(self, media_path=False, media_version_folder=False, all_folders=False, cupack=False, all=False):
        """
        Get the media path for the installation.

        Args:
            media_path (bool, optional): If True, return the media path. Defaults to False.
            media_version_folder (bool, optional): If True, return the latest media version folder. Defaults to False.
            all_folders (bool, optional): If True, return a list of all folders in the media path. Defaults to False.
            cupack (bool, optional): If True, return the latest CU folder. Defaults to False.
            all (bool, optional): If True, return both the media path and the latest CU folder. Defaults to False.

        Returns:
            str or list: The requested media path or folder(s).

        """
        machine_obj = Machine(self.commcell.commserv_client) if self.is_push_job else self.machine
        latest_folder = ""
        updates_path = machine_obj.join_path(
            self.commcell.commserv_cache.get_cs_cache_path(),
            installer_constants.DOWNLOAD_SOFTWARE_DEFAULT_MEDIA,
            installer_constants.CURRENT_RELEASE_VERSION)
        foldervalues = []
        folder_list = machine_obj.get_folder_or_file_names('"' + updates_path + '"', False)
        # find the folder_list type
        if type(folder_list) is not list:
            for val in folder_list.splitlines():
                if val.find("SP") >= 0:
                    foldervalues.append(val)
            folder_list = foldervalues
            
        latest_folder = self.get_latestfolder_touse(folder_list)
        if media_path or all:
            mediapath = machine_obj.join_path(updates_path, latest_folder)
            if media_path:
                return mediapath
        elif media_version_folder:
            return latest_folder
        if all_folders:
            folder_list = machine_obj.get_folder_or_file_names(updates_path, False)
            folder_list = ' '.join(folder_list.splitlines()).split()[2:]
            return folder_list
        latest_cu_folder = ""
        latest_cu_folder_path = ""
        if cupack or all:
            if machine_obj.os_info == (installer_constants.WINDOWS).upper():
                flavor = installer_constants.WINDOWS
                cupath = machine_obj.join_path(updates_path, latest_folder,
                                               flavor, installer_constants.BINARY_PAYLOAD,
                                               installer_constants.LOOSEUPDATES_FOLDER)
            else:
                flavor = installer_constants.UNIX_PATH
                cupath = machine_obj.join_path(updates_path, latest_folder,
                                               flavor, installer_constants.LOOSEUPDATES_FOLDER)
            if machine_obj.check_directory_exists(cupath):
                folder_list = machine_obj.get_folder_or_file_names('"' + cupath + '"', False)
                if type(folder_list) is not list:
                    folder_list = ' '.join(folder_list.splitlines()).split()[2:]
                latest_cu_folder = self.get_latestfolder_touse(folder_list, cupack=True)
                latest_cu_folder_path = machine_obj.join_path(cupath, latest_cu_folder)
                if cupack:
                    return latest_cu_folder

        return mediapath, latest_cu_folder_path, latest_cu_folder
    
    def get_looseupdates_fromcache(self):
        """
        Get the loose updates from the cache.

        Returns:
            list: The list of cache update numbers.
            string: The latest CU folder.

        """
        mediapath, latest_cu_folder_path, latest_cu_folder = self.get_media_path(all=True)
        self.csobj = Machine(self.commcell.commserv_client)
        loose_updates_exist = False
        if latest_cu_folder_path:
            cu_folders = self.csobj.get_folder_or_file_names('"' + latest_cu_folder_path + '"', False)
            if type(cu_folders) is not list:
                cu_folders = ' '.join(cu_folders.splitlines()).split()[2:]
            if installer_constants.UPDATES in cu_folders:
                loose_updates_exist = True
        cacheupdate_numbers = []

        if loose_updates_exist:
            media_folder_list = self.csobj.get_folder_or_file_names('"' + mediapath + '"', False)
            if type(media_folder_list) is not list:
                media_folder_list = ' '.join(media_folder_list.splitlines()).split()[2:]
            unixosfolderlist = []
            unixfoldername = ""
            for folder in media_folder_list:
                if folder.lower() != installer_constants.WINDOWS.lower():
                    unixfoldername = folder
                    newfolder_list = self.csobj.get_folder_or_file_names(
                        '"' + self.csobj.join_path(mediapath, folder) + '"', False
                    )
                    if type(newfolder_list) is not list:
                        newfolder_list = ' '.join(newfolder_list.splitlines()).split()[2:]
                    unixosfolderlist = newfolder_list

            for folder in unixosfolderlist:
                unixosfolders = self.csobj.get_folder_or_file_names(
                    '"' + self.csobj.join_path(mediapath, unixfoldername, folder,
                                                installer_constants.LOOSEUPDATES_FOLDER, latest_cu_folder) + '"', False
                )
                if type(unixosfolders) is not list:
                    unixosfolders = ' '.join(unixosfolders.splitlines()).split()[2:]

                if installer_constants.UPDATES in unixosfolders:
                    folder_list = self.csobj.get_folder_or_file_names(
                        '"' + self.csobj.join_path(mediapath, unixfoldername, folder,
                                                    installer_constants.LOOSEUPDATES_FOLDER, latest_cu_folder, installer_constants.UPDATES) + '"', False
                    )
                    if type(folder_list) is not list:
                        folder_list = ' '.join(folder_list.splitlines()).split()[2:]
                    cacheupdate_numbers.extend(folder_list)

            folder_list = self.csobj.get_folder_or_file_names(
                '"' + self.csobj.join_path(mediapath, installer_constants.WINDOWS, installer_constants.BINARY_PAYLOAD,
                                            installer_constants.LOOSEUPDATES_FOLDER, latest_cu_folder, installer_constants.UPDATES) + '"', False
            )
            if type(folder_list) is not list:
                folder_list = ' '.join(folder_list.splitlines()).split()[2:]
            cacheupdate_numbers.extend(folder_list)

            winosfolders = self.csobj.get_folder_or_file_names(
                '"' + self.csobj.join_path(mediapath, installer_constants.WINDOWS, installer_constants.BINARY_PAYLOAD_32,
                                            installer_constants.LOOSEUPDATES_FOLDER, latest_cu_folder) + '"', False
            )
            if type(winosfolders) is not list:
                winosfolders = ' '.join(winosfolders.splitlines()).split()[2:]

            if installer_constants.UPDATES in winosfolders:
                folder_list = self.csobj.get_folder_or_file_names(
                    '"' + self.csobj.join_path(mediapath, installer_constants.WINDOWS, installer_constants.BINARY_PAYLOAD_32,
                                                installer_constants.LOOSEUPDATES_FOLDER, latest_cu_folder, installer_constants.UPDATES) + '"', False
                )
                if type(folder_list) is not list:
                    folder_list = ' '.join(folder_list.splitlines()).split()[2:]
                cacheupdate_numbers.extend(folder_list)

            self.log.info(f"Cache update numbers : {cacheupdate_numbers}")
        return cacheupdate_numbers, latest_cu_folder

    def validate_install(self, **kwargs):
        """
        To validate install of client machine

        Raises:
             Exception:

                if service is not running
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def check_service_status(self, service=None):
        """
        To validate status of a particular service

        Returns:

             0: If service is running
             1: If service is down

        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def validate_uninstall(self):
        """
            To validate uninstall of unix client
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def validate_nonroot_install(self):
        """
            To verify if the installer honored the non-root flag
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def validate_nonroot_services(self):
        """
            To verify if services are running as non-root
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')


class WindowsValidator(InstallValidator):
    """Class for performing validation on the Windows machine"""

    def __init__(self, machine_name, testcase_object=None, commcell_object=None, **kwargs):
        """
        Initializes instance of the InstallValidator class

        Args:
            machine_name    (str)           -- machine to validate install on

            testcase_object    (object)     -- object of TestCase class

            commcell_object    (object)     -- object of Commcell class

        """
        self.os_info = OSNameIDMapping.WINDOWS_64.value
        super(WindowsValidator, self).__init__(machine_name, testcase_object, commcell_object, **kwargs)
        if not self.installed_packages:
            self.installed_packages = [702]
            self.log.warning(f"Package list not provided, "
                             f"using default package 'File System : {self.installed_packages}'")
        self.req_pkg_dict = installer_utils.get_packages_to_install(
            packages_list=self.installed_packages, osid=self.os_info,
            feature_release=self.feature_release, only_hard_dependent_packages=self.is_push_job)

    def check_if_installer_key_exists(self):
        """"
                To validate installer keys in registry
        """
        reg_key = installer_constants.COMMVAULT_REGISTRY_ROOT_WINDOWS
        if self.is_32_on_64_bit:
            reg_key = installer_constants.COMMVAULT_REGISTRY_ROOT_32BIT_WINDOWS
        self.log.info(f"Validating If installer key is removed under {reg_key}")
        result1 = self.machine.check_registry_exists(reg_key + "\\Installer")
        self.log.info(f"Validating If installer key is removed under {reg_key}\\InstanceXXX")
        result2 = self.machine.check_registry_exists("\\Installer")
        if result1 or result2:
            self.log.error("Installer registry key still exists even after successful installation")
            self.status_flag = False
            self.status_msg += "Installer registry key still exists even after successful installation\n"
        else:
            self.log.info("Installer registry key validation successful")

    def validate_installed_packages(self):
        """
                To validate packages installed
        """
        try:
            reg_value = "InstalledPackages"
            reg_key = f"{installer_constants.COMMVAULT_REGISTRY_ROOT_WINDOWS}\\{self.machine.instance}\\{reg_value}"
            pkg_list = []
            pkg_flag = True
            self.log.info(f"Packages required: {str(self.req_pkg_dict)}")
            output = self.machine.execute_command(f"Get-ChildItem -Path '{reg_key}'"
                                                  f" | Select-Object Name | Format-List")
            sub_keys = output.output.split('\r\n')
            for keys in sub_keys:
                if reg_value in keys:
                    pkg_list.append(keys.split(f'\\{reg_value}\\')[1].split()[0])
            self.log.info(f"Packages already installed: {pkg_list}")
            for pid, name in self.req_pkg_dict.items():
                if pid not in pkg_list:
                    self.log.error(f"Package '{name}' is missing from installed packages on the client registry")
                    pkg_flag = False
            if pkg_flag:
                self.log.info("Package install validation successful")
            else:
                self.log.error("Package install validation failed")
                self.status_flag = False
                self.status_msg += "Package install validation failed\n"
        except Exception as exp:
            self.log.error(f"Package install validation failed with error {exp}")
            self.status_flag = False
            self.status_msg += "Package install validation failed\n"

    def validate_services(self):
        """
        To validate if services are running on the client machine or not

        Raises:
             Exception:

                if service is not running

        """
        services = []
        missing_services = []
        windows_services = installer_constants.WINDOWS_SERVICES
        _packages = self.req_pkg_dict.keys()

        [services.append(f'{service}({self.machine.instance})')
         for package in _packages if int(package) in windows_services.keys()
         for service in windows_services[int(package)] if service not in services]

        machine_services = self.machine.execute_command('Get-Service | Where Status'
                                                        ' -eq "Running" | select Name')
        running_services = [service[0] for service in machine_services.formatted_output]

        for service in services:
            if service not in running_services:
                missing_services.append(service)
        if missing_services:
            self.log.error(f'Services {missing_services} for machine {self.machine_name} are down')
            self.status_flag = False
            self.status_msg += "Service validation failed\n"
        else:
            self.log.info("Service validation successful")

    def check_service_status(self, service=None):
        """
        To validate if a service are running on the client machine or not

        Raises:
             Exception:

                if service is not running

        """

        machine_services = self.machine.execute_command('Get-Service | Where Status'
                                                        ' -eq "Running" | select Name')
        running_services = [service[0] for service in machine_services.formatted_output]

        if service in running_services:
            self.log.info(f"Service {service} is running")
            return 0
        else:
            self.log.info(f"Service {service} is down")
            return 1

    def console_name_validation(self):
        """
                To validate console name
        """
        _brand_name = installer_constants.oemid_edition_name(self.oem_id)
        start_menu_path = "C:\\ProgramData\\Microsoft\\Windows\\Start Menu\\Programs"
        if self.machine.check_directory_exists(self.machine.join_path(start_menu_path,
                                                                      _brand_name, self.machine.instance)):
            console = [f for f in self.machine.get_files_in_path(start_menu_path)
                       if (f.endswith('.lnk') and (f.split('\\')[-1].startswith(_brand_name)))]
        else:
            if self.machine.check_directory_exists(self.machine.join_path(start_menu_path,
                                                                          "Commvault", self.machine.instance)):
                console = [f for f in self.machine.get_files_in_path(start_menu_path)
                           if (f.endswith('.lnk') and (f.split('\\')[-1].startswith(_brand_name)))]
            else:
                self.log.error("Could not find console name")
                self.status_flag = False
                self.status_msg += "Console name validation failed\n"
                return 0
        if len(console) > 0:
            self.log.info("The Console is added to Start menu")
        else:
            self.log.error("Could not find console name")
            self.status_flag = False
            self.status_msg += "Console name validation failed\n"

    def validate_loose_updates_install(self):
        """
                To validate loose updates installed
        """
        try:
            updates_flag = True
            machine_obj = Machine(self.commcell.commserv_client) if self.is_push_job else self.machine
            if self.is_push_job:
                updates_path = machine_obj.join_path(
                    self.commcell.commserv_cache.get_cs_cache_path(),
                    installer_constants.DOWNLOAD_SOFTWARE_DEFAULT_MEDIA,
                    installer_constants.CURRENT_RELEASE_VERSION,
                    installer_utils.get_latest_recut_from_xml(self.feature_release), "Windows")
            else:
                updates_path = machine_obj.join_path(installer_constants.DEFAULT_DRIVE_LETTER,
                                                     installer_constants.BOOTSTRAPPER_EXECUTABLE_EXTRACTPATH)
            updates_path = machine_obj.join_path(
                installer_utils.get_windows_looseupdates_path(updates_path), f"CU{self.cu_version}", "Updates")
            loose_updates_dict = self.get_list_of_hotfixes_from_installation_media(updates_path)
            additional_patches_dict = self.get_additional_path_info_from_db()
            if additional_patches_dict and loose_updates_dict:
                for pkg_id, name in self.req_pkg_dict.items():
                    if pkg_id in loose_updates_dict.keys():
                        if sorted(loose_updates_dict[pkg_id]) != sorted(additional_patches_dict[int(pkg_id)]):
                            self.log.error(f"Some updates are missing for {self.req_pkg_dict[pkg_id]}")
                            temp_set = set(loose_updates_dict[pkg_id]).difference(
                                set(additional_patches_dict[int(pkg_id)]))
                            self.log.error(f"Updates present in Media but missing in DB "
                                           f"for package {name} are {str(temp_set)}")
                            temp_set = set(additional_patches_dict[int(pkg_id)]).difference(
                                set(loose_updates_dict[pkg_id]))
                            self.log.error(f"Updates missing in Media but present in DB "
                                           f"for package {name} are {str(temp_set)}")
                            updates_flag = False
            if loose_updates_dict == {}:
                self.log.info("No loose updates found in Media")
            if updates_flag:
                self.log.info("Loose updates install validation successful")
            else:
                self.status_flag = False
                self.status_msg += "Loose updates install validation failed\n"
        except Exception as exp:
            self.log.error(f"Error in Loose updates install validation: {exp}")
            self.status_flag = False
            self.status_msg += "Loose updates install validation failed\n"

    def validate_bundle_present(self):
        """
            To validate bundle present in AddorRemove programs
        """
        try:
            _brand_name = installer_constants.oemid_edition_name(self.oem_id)
            script_path = self.machine.join_path(
                AUTOMATION_DIRECTORY, "AutomationUtils", "Scripts", "Windows", "GetInstalledPrograms.ps1")
            output = self.machine.execute_script(script_path)
            result = output.output.split('\n')
            status = False
            for line in result:
                if line.strip():
                    line = line.strip()
                    if line.find(':') != -1:
                        key = line.split(':')[1]
                        for k in key:
                            if _brand_name.lower() in k.lower():
                                status = True
            if status:
                self.log.error("Bundle key is still present in ADD\\Remove programs")
                self.status_flag = False
                self.status_msg += "Bundle validation failed\n"
        except Exception as exp:
            self.log.error("Error in bundle validation")
            self.status_flag = False
            self.status_msg += "Bundle validation failed\n"

    def validate_install(self, **kwargs):
        """
                To validate install of windows client

        """
        self.log.info(f"Starting Install Validation of Client {self.machine_name}")
        if kwargs.get('check_if_installer_key_exists', True):
            self.log.info(f"Starting Registry key validation of Client {self.machine_name}")
            self.check_if_installer_key_exists()
        if kwargs.get('validate_installed_packages', True):
            self.log.info(f"Starting Installed packages validation of Client {self.machine_name}")
            self.validate_installed_packages()
        if kwargs.get('validate_services', True):
            self.log.info(f"Starting Service validation of Client {self.machine_name}")
            self.validate_services()
        if kwargs.get('check_feature_release_version_installed', False):
            self.log.info(f"Starting Feature release version validation of Client {self.machine_name}")
            self.check_feature_release_version_installed()
        if kwargs.get('validate_baseline', True):
            self.log.info(f"Starting Baseline validation of Client {self.machine_name}")
            self.validate_baseline()
        if kwargs.get('validate_sp_info_in_db', True):
            self.log.info(f"Starting SP info validation of Client {self.machine_name}")
            self.validate_sp_info_in_db()
        if kwargs.get('validate_loose_updates_install', True):
            if not self.media_path:
                self.log.info(f"Starting Loose updates validation of Client {self.machine_name}")
                self.validate_loose_updates_install()
            else:
                self.log.warning(f"Skipping Loose updates validation of Client {self.machine_name} "
                                 f"since Media path is used for Installation")
        if kwargs.get('console_name_validation', True):
            self.log.info(f"Starting Console name validation of Client {self.machine_name}")
            self.console_name_validation()
        if kwargs.get('validate_oem', True):
            self.log.info(f"Starting OEM validation of Client {self.machine_name}")
            self.validate_oem()
        if kwargs.get('validate_company', False):
            company = kwargs.get("company")
            self.log.info(f"Starting Company validation of Client {self.machine_name}")
            self.validate_client_company(company)
        if kwargs.get('validate_mongodb',False):
            self.log.info("Starting MongoDB validation for the CS")
            self.validate_mongodb()

        if self.status_flag:
            self.log.info(f"Install Validation of Client {self.machine_name} Successful")
        else:
            raise Exception(f"Install Validation of Client {self.machine_name} Failed with error: {self.status_msg}")

    def validate_uninstall(self):
        """
            To validate uninstall of windows client
        """
        self.log.info(f"Starting Uninstall Validation of Client {self.machine_name}")
        reg_key = installer_constants.COMMVAULT_REGISTRY_ROOT_32BIT_WINDOWS \
            if self.is_32_on_64_bit else installer_constants.COMMVAULT_REGISTRY_ROOT_WINDOWS
        self.check_if_registry_entries_exists(reg_key)
        self.check_if_installation_dir_empty()
        if self.status_flag:
            self.log.info(f"Uninstall Validation of Client {self.machine_name} Successful")
        else:
            self.log.info(
                f"Uninstall Validation of Client {self.machine_name} Failed with error: {self.status_msg}")

    def validate_mssql_patches(self):
        """
            To validate mssql patches installed on the Windows machine
        """
        try:
            cvappliance_config_dict = self._get_windows_and_mssql_kb_updates()
            query = "SELECT simInstalledThirdPartyCU.version " \
                    "FROM simInstalledThirdPartyCU " \
                    "INNER JOIN APP_Client ON simInstalledThirdPartyCU.ClientId = APP_Client.id " \
                    "WHERE simInstalledThirdPartyCU.type=1 " \
                    "AND simInstalledThirdPartyCU.enabled=1 AND " \
                    f"APP_Client.net_hostname='{self.machine.machine_name}';"

            self.csdb.execute(query)
            db_response = self.csdb.fetch_one_row()

            if not db_response[0]:
                self.log.info("Client not eligible for CV Appliance Patching.")
                raise Exception("Check if the OS Patching is enabled on the client")

            else:
                version = db_response[0]

            updates_to_be_present = []
            for each in cvappliance_config_dict[version]:
                updates_to_be_present.append(each)

            updates_to_be_present.sort(reverse=True)
            latest_mssql_patch = updates_to_be_present[0]

            reg_path = "HKLM:\\SOFTWARE\\Microsoft\\Microsoft SQL Server\\COMMVAULT\\" \
                       "MSSQLServer\\CurrentVersion"
            installed_version = self.machine.get_registry_value(win_key=reg_path, value="CurrentVersion")

            if installed_version == "":
                raise Exception("Failed to retrieve installed MSSQL version from the System")

            if installed_version in latest_mssql_patch:
                self.log.info("MSSQL Patch is successfully installed on the machine")

            else:
                self.log.error("Failed to install the latest MSSQL patch on the Machine")
                raise Exception("MSSQL updates were not installed on the machine.")

        except Exception as exp:
            error_msg = f'Failed with the error: {exp}'
            self.log.error(error_msg)
            raise Exception("Failed Validating the Windows OS Patches")

    def validate_installed_windows_kb_updates(self):
        """
            To validate kb updates installed on the Windows machine
        """
        try:
            installed_kb_updates = self._get_list_of_kb_updates_installed()
            cvappliance_config_dict = self._get_windows_and_mssql_kb_updates()

            query = "SELECT simInstalledThirdPartyCU.version " \
                    "FROM simInstalledThirdPartyCU " \
                    "INNER JOIN APP_Client ON simInstalledThirdPartyCU.ClientId = APP_Client.id " \
                    "WHERE simInstalledThirdPartyCU.type=2 " \
                    "AND simInstalledThirdPartyCU.enabled=1 AND " \
                    f"APP_Client.net_hostname='{self.machine.machine_name}';"

            self.csdb.execute(query)
            db_response = self.csdb.fetch_one_row()

            if not db_response[0]:
                self.log.info("Client not eligible for CV Appliance Patching.")
                raise Exception("Check if the OS Patching is enabled on the client")

            else:
                version = db_response[0]

            updates_to_be_present = []
            for each in cvappliance_config_dict[version]:
                updates_to_be_present.append(each)

            def check_elements_missing(list1, list2):
                missing_elements = [item for item in list1 if item not in list2]
                return missing_elements

            if check_elements_missing(updates_to_be_present, installed_kb_updates):
                raise Exception("Windows Updates missing on the machine")

            else:
                self.log.info("The KB Updates were installed successfully.")

        except Exception as exp:
            error_msg = f'Failed with the error: {exp}'
            self.log.error(error_msg)
            raise Exception("Failed Validating the Windows OS Patches")

    def _get_windows_and_mssql_kb_updates(self):
        """
            To fetch the list of applicable windows and mssql updates
            :return: dictionary
            Example: {"MSSQL_12":["12.3.6214.1",
                                "12.3.6024.0"]}
        """
        xml_server_loc = self.get_server_url + "/" + installer_constants.DOWNLOAD_SOFTWARE_DEFAULT_CVAPPLIANCE_MEDIA \
                         + "/" + "CVApplianceConfig_Windows.xml"
        try:
            http = urllib3.PoolManager()
            response = http.request('GET', xml_server_loc)
            response = response.data.decode('utf-8')
            cvappliance_xml = response
        except Exception as err:
            raise Exception(f'Failed to download xml: {err}') from err
        pkgdict = xmltodict.parse(cvappliance_xml)
        cvappliance_dict = self._convert_cvappliance_xml_to_dict(pkgdict)
        return cvappliance_dict

    def _convert_cvappliance_xml_to_dict(self, xml_dict):
        try:
            cvappliance_dict = {}

            def get_patches():
                def add_files():
                    cvappliance_dict[each_sub_os['@name']].append(eachpatch['@Name'])

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

    def _get_list_of_kb_updates_installed(self):
        """

        :return:
        """
        kb_updates = self.machine.execute_command("wmic qfe get HotFixID").formatted_output
        kb_list = []
        for each_row in kb_updates.split('\n'):
            if each_row.strip():
                each_row = each_row.strip()
                kb_list.append(each_row)

        return kb_list[1:]

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


class UnixValidator(InstallValidator):
    """Class for performing validation on the Unix machine"""

    def __init__(self, machine_name, testcase_object=None, commcell_object=None, **kwargs):
        """
        Initializes instance of the InstallValidator class

        Args:
            machine_name    (str)           -- machine to validate install on

            testcase_object    (object)     -- object of TestCase class

            commcell_object    (object)     -- object of Commcell class

        """
        self.os_info = OSNameIDMapping.UNIX_LINUX64.value
        super(UnixValidator, self).__init__(machine_name, testcase_object, commcell_object, **kwargs)
        if not self.installed_packages:
            self.installed_packages = [1101]
            self.log.warning(f"Package list not provided, "
                             f"using default package 'File System : {self.installed_packages}'")
        self.unix_flavor = kwargs.get('unix_flavour',
                                      installer_constants.OSNAME_LIST[OSNameIDMapping.UNIX_LINUX64.value][1])
        self.req_pkg_dict = installer_utils.get_packages_to_install(
            packages_list=self.installed_packages, osid=self.os_info,
            feature_release=self.feature_release, only_hard_dependent_packages=self.is_push_job)

    def check_if_installer_key_exists(self):
        """
                To validate installer keys
        """
        reg_key = installer_constants.COMMVAULT_REGISTRY_ROOT_UNIX
        self.log.info(f"Validating If installer key is removed under {reg_key}")
        result = self.machine.check_registry_exists(reg_key + "/Installer")
        if result:
            self.log.error("Installer registry key still exists even after successful installation")
            self.status_flag = False
            self.status_msg += "Installer registry key still exists even after successful installation\n"
        else:
            self.log.info("Installer registry key validation successful")

    def validate_installed_packages(self):
        """
                To validate installed packages
        """
        reg_key = f"{installer_constants.COMMVAULT_REGISTRY_ROOT_UNIX}/{self.machine.instance}/Installer/Subsystems/"
        pkg_list = []
        self.log.info(f"Packages required: {str(self.req_pkg_dict)}")
        for keys in self.machine.get_folders_in_path(reg_key):
            if keys.split(reg_key)[-1].isdigit():
                pkg_list.append(keys.split(reg_key)[-1])
        self.log.info(f"Packages already installed: {pkg_list}")
        for pid, name in self.req_pkg_dict.items():
            if pid not in pkg_list:
                self.log.error(f"Package '{name}' is missing from Installed packages")
                self.status_flag = False
                self.status_msg += "Package install validation failed\n"
        if 'Package install validation failed' not in self.status_msg:
            self.log.info("Package validation successful")

    def validate_services(self):
        """
        To validate if services are running on the client machine or not

        Raises:
             Exception:

                if service is not running

        """
        services = []
        unix_services = installer_constants.UNIX_SERVICES
        packages = self.req_pkg_dict.keys()
        [services.append(service) for package in packages if int(package) in unix_services.keys()
         for service in unix_services[int(package)] if service not in services]
        for service in services:
            cmd = 'ps -A | grep ' + service
            output = self.machine.execute_command(cmd)
            if str(output.output).find(service) > 0:
                self.log.info("Service created successfully for %s" % service)
            else:
                raise Exception(f'Unix services for machine {self.machine_name} are down')

    def check_service_status(self, service=""):
        """
        To validate status of a particular service

        Returns:

             0: If service is running
             1: If service is down

        """
        cmd = 'ps -A | grep ' + service
        output = self.machine.execute_command(cmd)
        if str(output.output).find(service) > 0:
            self.log.info(f"Service {service} is running")
            return 0
        else:
            self.log.info(f"Service {service} is down")
            return 1

    def validate_nonroot_services(self):
        """
            To validate if services are running as non-root
        """

        services = [
            "cvd",
            "cvlaunchd",
            "AppMgrSvc",
            "cvfwd",
            "ClMgrS",
            "EvMgrS",
            "JobMgr",
            "MediaManager"]
        status = True
        for service in services:
            cmd = f'ps -elf | grep /opt/commvault/Base/{service}'
            output = self.machine.execute_command(cmd)
            if str(output.output.split('\n')[0]).find('commvau') == -1:
                status = False
                self.status_msg += "Non-root service validation failed\n"

        if status:
            self.log.info("All services are running as non-root")
        else:
            self.status_flag = False
            self.log.info("Services are not running as non-root")

    def validate_nonroot_install(self):
        """
            To verify if the installer honored the non-root flag
        """
        output = self.machine.get_registry_value(commvault_key='', value='nNonrootType')
        if str(output) != "1":
            self.status_flag = False
            self.status_msg += "Non root install validation failed\n"

    def validate_installed_directory(self):
        """
                To validate installed directories
        """
        status = True
        brand_name = installer_constants.oemid_edition_name(self.oem_id)
        output = self.machine.execute_command(f"{brand_name.lower()} status")
        if output.output != '':
            for each in output.output.split('\n'):
                if "Home Directory" in str(each):
                    if brand_name.lower() not in str(each).split(" ")[-1].strip('\n'):
                        self.log.error("Home Directory is not as per the Brand")
                        status = False
                if "Log Directory" in str(each):
                    if brand_name.lower() not in str(each).split(" ")[-1].strip('\n'):
                        self.log.error("Log Directory is not as per the Brand")
                        status = False
                if "Core Directory" in str(each):
                    if brand_name.lower() not in str(each).split(" ")[-1].strip('\n'):
                        self.log.error("Core Directory is not as per the Brand")
                        status = False
                if "Temp Directory" in str(each):
                    if brand_name.lower() not in str(each).split(" ")[-1].strip('\n'):
                        self.log.error("Temp Directory is not as per the Brand")
                        status = False
        else:
            status = False
        if status:
            self.log.info("Install directory validation successful")
        else:
            self.status_flag = False
            self.status_msg += "Install directory validation failed\n"

    def validate_loose_updates_install(self):
        """
                To validate loose updates installed
        """
        try:
            updates_flag = True
            machine_obj = Machine(self.commcell.commserv_client) if self.is_push_job else self.machine
            if self.is_push_job:
                updates_path = machine_obj.join_path(
                    self.commcell.commserv_cache.get_cs_cache_path(),
                    installer_constants.DOWNLOAD_SOFTWARE_DEFAULT_MEDIA,
                    installer_constants.CURRENT_RELEASE_VERSION,
                    installer_utils.get_latest_recut_from_xml(self.feature_release), "Unix")
            else:
                updates_path = machine_obj.join_path(
                    installer_constants.UNIX_DEFAULT_DRIVE_LETTER,
                    installer_constants.BOOTSTRAPPER_EXECUTABLE_EXTRACTPATH)

            updates_path = machine_obj.join_path(
                installer_utils.get_linux_looseupdates_path(updates_path, self.unix_flavor),
                f"CU{self.cu_version}", "Updates")
            loose_updates_dict = self.get_list_of_hotfixes_from_installation_media(updates_path)
            additional_patches_dict = self.get_additional_path_info_from_db()
            if additional_patches_dict and loose_updates_dict:
                for pkg_id, name in self.req_pkg_dict.items():
                    if pkg_id in loose_updates_dict.keys():
                        if sorted(loose_updates_dict[pkg_id]) != sorted(additional_patches_dict[int(pkg_id)]):
                            self.log.error(f"Some updates are missing for {self.req_pkg_dict[pkg_id]}")
                            temp_set = set(loose_updates_dict[pkg_id]).difference(
                                set(additional_patches_dict[int(pkg_id)]))
                            self.log.error(f"Updates present in Media but missing in DB "
                                           f"for package {name} are {str(temp_set)}")
                            temp_set = set(additional_patches_dict[int(pkg_id)]).difference(
                                set(loose_updates_dict[pkg_id]))
                            self.log.error(f"Updates missing in Media but present in DB "
                                           f"for package {name} are {str(temp_set)}")
                            updates_flag = False
            if loose_updates_dict == {}:
                self.log.info("No loose updates found in Media")
            if updates_flag:
                self.log.info("Loose updates install validation successful")
            else:
                self.status_flag = False
                self.status_msg += "Loose updates install validation failed\n"
        except Exception as exp:
            self.log.error(f"Error in Loose updates install validation: {exp}")
            self.status_flag = False
            self.status_msg += "Loose updates install validation failed\n"

    def validate_install(self, **kwargs):
        """
            To validate install of windows client
        """
        self.log.info(f"Starting Install Validation of Client {self.machine_name}")
        if kwargs.get('check_if_installer_key_exists', True):
            self.log.info(f"Starting Registry key validation of Client {self.machine_name}")
            self.check_if_installer_key_exists()
        if kwargs.get('validate_installed_packages', True):
            self.log.info(f"Starting Installed packages validation of Client {self.machine_name}")
            self.validate_installed_packages()
        if kwargs.get('validate_services', True):
            self.log.info(f"Starting Service validation of Client {self.machine_name}")
            self.validate_services()
        if kwargs.get('check_feature_release_version_installed', False):
            self.log.info(f"Starting Feature release version validation of Client {self.machine_name}")
            self.check_feature_release_version_installed()
        if kwargs.get('validate_baseline', True):
            self.log.info(f"Starting Baseline validation of Client {self.machine_name}")
            self.validate_baseline()
        if kwargs.get('validate_sp_info_in_db', True):
            self.log.info(f"Starting SP info validation of Client {self.machine_name}")
            self.validate_sp_info_in_db()
        if kwargs.get('validate_loose_updates_install', True):
            if not self.media_path:
                self.log.info(f"Starting Loose updates validation of Client {self.machine_name}")
                self.validate_loose_updates_install()
            else:
                self.log.warning(f"Skipping Loose updates validation of Client {self.machine_name} "
                                 f"since Media path is used for Installation")
        if kwargs.get('validate_installed_directory', True):
            self.log.info(f"Starting Install directory validation of Client {self.machine_name}")
            self.validate_installed_directory()
        if kwargs.get('validate_oem', True):
            self.log.info(f"Starting OEM validation of Client {self.machine_name}")
            self.validate_oem()
        if kwargs.get('validate_company', False):
            company = kwargs.get("company")
            self.log.info(f"Starting Company validation of Client {self.machine_name}")
            self.validate_client_company(company)
        if kwargs.get('validate_nonroot_services', False):
            self.log.info(f"Starting non root services validation of Client {self.machine_name}")
            self.validate_nonroot_services()
        if kwargs.get('validate_nonroot_install', False):
            self.log.info(f"Starting non root install validation of Client {self.machine_name}")
            self.validate_nonroot_install()
        if kwargs.get('validate_mongodb', False):
            self.log.info("Starting MongoDB validation for the CS")
            self.validate_mongodb()

        if self.status_flag:
            self.log.info(f"Install Validation of Client {self.machine_name} Successful")
        else:
            raise Exception(f"Install Validation of Client {self.machine_name} Failed with error: {self.status_msg}")

    def validate_uninstall(self):
        """
            To validate uninstall of unix client
        """
        self.log.info(f"Starting Uninstall Validation of Client {self.machine_name}")
        self.check_if_registry_entries_exists(installer_constants.COMMVAULT_REGISTRY_ROOT_UNIX)
        self.check_if_installation_dir_empty()
        if self.status_flag:
            self.log.info(f"Uninstall Validation of Client {self.machine_name} Successful")
        else:
            self.log.info(f"Uninstall Validation of Client {self.machine_name} Failed with error: {self.status_msg}")
