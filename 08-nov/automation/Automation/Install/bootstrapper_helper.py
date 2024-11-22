# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations for bootstrapper download

BootstrapperHelper
===================

    __init__()                          --  initialize instance of the BootstrapperHelper class
    local_machine_drive                 --  Returns local machine drive
    remote_machine_drive                --  Returns remote machine drive
    cleanup                             --  cleans up testcase results
    bootstrapper_download_url           --  returns download server path of the bootstrapper installer
    download_bootstrapper               --  downloads bootstrapper installer file file
    download_payload_from_bootstrapper  --  downloads payload from bootstrapper
    extract_bootstrapper                --  extracts and downloads payload from bootstrapper
    launch_bootstrapper                 --  launches bootstrapper executable

WindowsBootstrapperHelper
===================

    __init__()                          --  initialize instance of the BootstrapperHelper class
    cleanup                             --  cleans up testcase results
    bootstrapper_download_url           --  returns download server path of the bootstrapper installer
    download_bootstrapper               --  downloads bootstrapper installer file file
    download_payload_from_bootstrapper  --  downloads payload from bootstrapper
    extract_bootstrapper                --  extracts and downloads payload from bootstrapper

UnixBootstrapperHelper
===================

    __init__()                          --  initialize instance of the BootstrapperHelper class
    cleanup                             --  cleans up testcase results
    bootstrapper_download_url           --  returns download server path of the bootstrapper installer
    download_bootstrapper               --  downloads bootstrapper installer file file
    download_payload_from_bootstrapper  --  downloads payload from bootstrapper
    extract_bootstrapper                --  extracts and downloads payload from bootstrapper
    launch_bootstrapper                 --  launches bootstrapper executable

"""
import re
import shutil
import urllib3
from bs4 import BeautifulSoup as bs
from AutomationUtils import logger
from AutomationUtils import config
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from Install import installer_constants, installer_utils
from cvpysdk.deployment.deploymentconstants import OSNameIDMapping


class BootstrapperHelper:
    """BootstrapperHelper helper class to perform bootstrapper related operations"""

    def __new__(cls, feature_release, machine_obj, **kwargs):
        """
            Returns the instance of one of the Subclasses WindowsBootstrapperHelper / UnixBootstrapperHelper,
            based on the OS details of the remote client.
        """
        if cls is not __class__ or machine_obj is None:
            return super().__new__(cls)

        if 'windows' in machine_obj.os_info.lower():
            return object.__new__(WindowsBootstrapperHelper)

        elif 'unix' in machine_obj.os_info.lower():
            return object.__new__(UnixBootstrapperHelper)

    def __init__(self, feature_release, machine_obj, **kwargs):
        """
        Initialize instance of the BootstrapperHelper class.

        Args:
            feature_release                 --  feature release of the bootstrapper

            machine_obj                     --  machine object of the machine where
                                                the bootstrapper is copied and executed

            **kwargs: (dict) -- Key value pairs for supporting conditional initializations
            Supported -

            download_server (str)           --  download server from which bootstrapper .exe file will be downloaded

            bootstrapper_download_os (str)  --  Oses to download E.g. bootstrapper_download_os="Windows,Unix"

            visibility_level (int)          --  Value of visibility flag to be set. Default 16

            oem_id (str)                    --  OEM ID to be used for the bootstrapper
        """
        self.log = logger.get_log()
        self.config_json = config.get_config()
        self.exe_name = None
        self.machine_obj = machine_obj
        self.local_machine = Machine()
        self.feature_release = feature_release
        self.oem_id = int(kwargs.get('oem_id', 1))
        self.download_server = kwargs.get('download_server', installer_constants.DEFAULT_CONFIG_URL_PREFIX)
        self.bootstrapper_download_os = kwargs.get('bootstrapper_download_os', 'Windows').split(",")
        self.windows_os_to_download = ",".join(str(bit)
                                               for bit in installer_constants.WINDOWS_BOOTSTRAPPER_DOWNLOAD_OSID)
        self.unix_os_to_download = ",".join(str(bit) for bit in installer_constants.UNIX_BOOTSTRAPPER_DOWNLOAD_OSID)
        self.local_drive = None
        self.remote_drive = None
        self.local_file_copy_loc = None
        self.remote_file_copy_loc = None
        self.http_export_string = None
        self.download_string = None
        self.visibility_level = kwargs.get('visibility_level',
                                           installer_constants.DefaultVisibilityLevels.LAB_USERS.value)
        if '_' in feature_release:
            self.feature_release_format = feature_release
            self.feature_release = feature_release.split('_')[0]
        else:
            self.feature_release_format = installer_utils.get_latest_recut_from_xml(feature_release)
        if not self.config_json.Install.use_internal_media:
            self.use_internal_http(reset=True)
        else:
            self.use_internal_http()
        if (self.feature_release.isdigit() and len(self.feature_release) == 4) or len(self.feature_release) == 6:
            self.visibility_level = installer_constants.DefaultVisibilityLevels.METALLIC_LAB.value
        self.set_visibility_level()

    @property
    def local_machine_drive(self):
        """
        Returns local machine drive
        """
        if not self.local_drive:
            self.local_drive = OptionsSelector.get_drive(self.local_machine)
        return self.local_drive

    @property
    def remote_machine_drive(self):
        """
        Returns remote machine drive
        """
        if not self.remote_drive:
            self.remote_drive = OptionsSelector.get_drive(self.machine_obj)
        return self.remote_drive

    def set_visibility_level(self, level=None):
        """
            Set the visibility level for Bootstrapper
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def use_internal_http(self, reset=False):
        """
            Set internal http by default for Bootstrapper
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def bootstrapper_download_url(self):
        """
        returns download server path of the bootstrapper installer
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def download_bootstrapper(self):
        """
        Downloads bootstrapper installer .exe file

        Raises:
            exception if unable to find exe
            exception if unable to download exe
        """
        try:
            http = urllib3.PoolManager(cert_reqs='CERT_NONE')
            url = self.bootstrapper_download_url()
            response = http.request('GET', url)
            soup = bs(response.data)
            link = soup.findAll('a', attrs={'href': re.compile(self.download_string)})
            self.exe_name = link[0].attrs["href"]
            self.log.info("Downloading %s from %s", self.exe_name, url)
            if not self.local_machine.check_directory_exists(self.local_file_copy_loc):
                self.local_machine.create_directory(self.local_file_copy_loc)
            with http.request('GET', f"{url}{self.exe_name}", preload_content=False) as resp, \
                    open(f"{self.local_file_copy_loc}{self.exe_name}", 'wb') as out_file:
                shutil.copyfileobj(resp, out_file)

        except Exception as exp:
            self.log.exception(exp)
            raise Exception("Unable to download the exe file")

    def download_payload_from_bootstrapper(self, **kwargs):
        """
        download Payload from Bootstrapper
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')

    def extract_bootstrapper(self):
        """
        Extracts bootstrapper
        """
        self.local_file_copy_loc = self.local_machine.join_path(self.local_machine_drive,
                                                                installer_constants.REMOTE_FILE_COPY_FOLDER, "")
        if 'windows' in self.machine_obj.os_info.lower():
            self.remote_file_copy_loc = installer_constants.REMOTE_FILE_COPY_LOC + "\\"
            self.log.info("Downloading Bootstrapper executable for Windows")
        else:
            self.remote_file_copy_loc = installer_constants.UNIX_REMOTE_FILE_COPY_LOC + "/"
            self.log.info("Downloading Bootstrapper executable for Unix")
        self.download_bootstrapper()
        self.log.info("Extracting Bootstrapper")
        if self.machine_obj.ip_address != self.local_machine.ip_address:
            self.log.info("Copying to remote machine")
            self.machine_obj.copy_from_local(
                f"{self.local_file_copy_loc}{self.exe_name}", self.remote_file_copy_loc, raise_exception="True")
            self.log.info("File copied successfully")
            _machine_obj = self.machine_obj
            file_copy_loc = self.remote_file_copy_loc
        else:
            _machine_obj = self.local_machine
            file_copy_loc = self.local_file_copy_loc

        if 'windows' not in self.machine_obj.os_info.lower():
            cmd = f"rm -r {installer_constants.UNIX_DEFAULT_DRIVE_LETTER}" \
                  f"{installer_constants.BOOTSTRAPPER_EXECUTABLE_EXTRACTPATH}; " \
                  f"mkdir {installer_constants.UNIX_DEFAULT_DRIVE_LETTER}" \
                  f"{installer_constants.BOOTSTRAPPER_EXECUTABLE_EXTRACTPATH} && " \
                  f"cp {file_copy_loc}{self.exe_name} {installer_constants.UNIX_DEFAULT_DRIVE_LETTER}" \
                  f"{installer_constants.BOOTSTRAPPER_EXECUTABLE_EXTRACTPATH}/ && " \
                  f"chmod u+x {installer_constants.UNIX_DEFAULT_DRIVE_LETTER}" \
                  f"{installer_constants.BOOTSTRAPPER_EXECUTABLE_EXTRACTPATH}/{self.exe_name}"
            output = _machine_obj.execute_command(cmd)
        else:
            cmd = f"Remove-Item -LiteralPath {self.remote_machine_drive}" \
                  f"{installer_constants.BOOTSTRAPPER_EXECUTABLE_EXTRACTPATH}" \
                  f" -Force -Recurse -ErrorAction Ignore;" \
                  f"New-Item -ItemType Directory -Force -Path {self.remote_machine_drive}" \
                  f"{installer_constants.BOOTSTRAPPER_EXECUTABLE_EXTRACTPATH};" \
                  f"$app = \"{file_copy_loc}{self.exe_name}\";" \
                  f"$arg = \"/d {self.remote_machine_drive}" \
                  f"{installer_constants.BOOTSTRAPPER_EXECUTABLE_EXTRACTPATH} /silent /noinstall\";" \
                  f"Start-Process $app $arg -Wait"
            output = _machine_obj.execute_command(cmd)
        self.log.info(f"Output from command {output.formatted_output}")

    def launch_bootstrapper(self, media_path, cmdl=''):
        """
            launches bootstrapper executable
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')


class WindowsBootstrapperHelper(BootstrapperHelper):
    """BootstrapperHelper helper class to perform windows bootstrapper related operations"""

    def __init__(self, feature_release, machine_obj, **kwargs):
        """
        Initialize instance of the BootstrapperHelper class.

        Args:
            feature_release -- feature release of the bootstrapper
            machine_obj -- machine object of the machine where the bootstrapper is copied and executed

            **kwargs: (dict) -- Key value pairs for supporting conditional initializations
            Supported -
            download_server (str) - download server from which bootstrapper .exe file will be downloaded
            bootstrapper_download_os (str) - Oses to download E.g. bootstrapper_download_os="Windows,Unix"
        """
        super(WindowsBootstrapperHelper, self).__init__(feature_release, machine_obj, **kwargs)
        self.download_string = ".exe"

    def set_visibility_level(self, level=None):
        """
            Set the visibility level for Bootstrapper
        """
        if level:
            self.visibility_level = level
        self.machine_obj.create_registry(installer_constants.COMMVAULT_REGISTRY_GALAXY_INSTALLER_FLAGS, "nVisibility",
                                         int(self.visibility_level), "DWord")
        self.log.info(f"nVisibility flag set to {int(self.visibility_level)} in registry")

    def use_internal_http(self, reset=False):
        """
            Set internal http by default for Bootstrapper
        """
        sz_internal_download_url = '' if reset else self.download_server
        self.machine_obj.create_registry(installer_constants.COMMVAULT_REGISTRY_GALAXY_INSTALLER_FLAGS,
                                         "szInternalDownloadURL", sz_internal_download_url, "String")
        self.log.info(f"szDownloadURL set to {sz_internal_download_url} in registry")

    def bootstrapper_download_url(self):
        """
        returns download server path of the bootstrapper installer
        """
        _brand_name = installer_constants.BRANDING_DICT[self.oem_id].replace(" ", '') + "-" + str(self.oem_id)
        return f"{self.download_server}/CVMedia/{installer_constants.CURRENT_RELEASE_VERSION}/" \
               f"{installer_constants.CURRENT_BUILD_VERSION}/{self.feature_release_format}/BootStrapper/{_brand_name}/"

    def download_payload_from_bootstrapper(self, **kwargs):
        """
        download Payload from Bootstrapper
        """
        try:
            self.log.info("Downloading from Bootstrapper")
            download_os_path = f"{self.remote_machine_drive}{installer_constants.WINDOWS_BOOTSTRAPPER_DOWNLOADPATH}"
            _download_inputs = kwargs.get('download_inputs', {})
            cmd, download_end_path, extract_cmd = '', '', ''
            _download_type = _download_inputs['download_type'] \
                if 'download_type' in _download_inputs.keys() else ["windows"]
            _download_type = [_download_type] if isinstance(_download_type, str) else _download_type
            for d_type in _download_type:
                cmd += f" /download{d_type.lower()}"
                if d_type.lower() in ['windows', 'unix']:
                    download_end_path = download_os_path + d_type.capitalize()
                elif 'unixospatches' in d_type.lower():
                    download_end_path = download_os_path + 'CVAppliance'
                    cmd += f" {_download_inputs['unix_rpm_config_file']}"
                    extract_cmd = f'\n$app = \"{self.remote_machine_drive}' \
                                  f'{installer_constants.BOOTSTRAPPER_EXECUTABLE_EXTRACTPATH}\\cv7z.exe\"\n ' \
                                  f'$arg = \"x {download_os_path}\\CVAppliance_Unix.tar -o{download_os_path} -r -y\"' \
                                  f'\nStart-Process $app $arg -Wait'
                elif d_type.lower() in ['windowsospatches', 'mssqlpatches']:
                    download_end_path = download_os_path + 'CVAppliance'

            if 'packages' in _download_inputs.keys():
                extra_cmd = f" /packagelist {''.join(str(_download_inputs['packages']))[1:-1]}" \
                    if list(_download_inputs['packages']) else ""
                cmd += extra_cmd
            if 'os_list' in _download_inputs.keys():
                extra_cmd = f" /oslist {''.join([str(x) + ' ' for x in _download_inputs['os_list']])}" \
                    if list(_download_inputs['os_list']) else ""
                cmd += extra_cmd

            cmd += f' /outputpath {download_os_path}'
            if self.machine_obj.check_directory_exists(download_os_path):
                self.machine_obj.clear_folder_content(download_os_path)
            self.log.info("Going to Download at %s", download_os_path)
            final_cmd = f"Remove-Item -LiteralPath \"{download_os_path}\" -Force -Recurse -ErrorAction Ignore\n" \
                        f"ping 127.0.0.1 -n 16\n$app = \"{self.remote_machine_drive}" \
                        f"{installer_constants.BOOTSTRAPPER_EXECUTABLE_EXTRACTPATH}\\Setup.exe\"\n" \
                        f"$arg = \"/silent {cmd}\"\nStart-Process $app $arg -Wait"
            if extract_cmd:
                final_cmd += extract_cmd
            output = self.machine_obj.execute_command(final_cmd)
            self.log.info(output.formatted_output)

            return download_end_path
        except Exception as exp:
            raise Exception(f"Downloading payload failed with error {exp}")

    def cleanup(self):
        """
        Cleans up testcase results
        """
        cmd = f"Remove-Item -LiteralPath {self.remote_file_copy_loc}" \
              f" -Force -Recurse -ErrorAction Ignore;" \
              f"Remove-Item -LiteralPath {self.remote_machine_drive}" \
              f"{installer_constants.BOOTSTRAPPER_EXECUTABLE_EXTRACTPATH}" \
              f" -Force -Recurse -ErrorAction Ignore;"
        if 'windows' in self.local_machine.os_info.lower():
            output = self.local_machine.execute_command(cmd)
        else:
            output = self.machine_obj.execute_command(cmd)
        self.log.info(output.formatted_output)

    def launch_bootstrapper(self, media_path, cmdl=''):
        """
            Launches bootstrapper executable
        """
        raise NotImplementedError('Method Not Implemented by the Child Class')


class UnixBootstrapperHelper(BootstrapperHelper):
    """BootstrapperHelper helper class to perform linux bootstrapper related operations"""

    def __init__(self, feature_release, machine_obj, **kwargs):
        """
        Initialize instance of the BootstrapperHelper class.

        Args:
            feature_release -- feature release of the bootstrapper
            machine_obj -- machine object of the machine where the bootstrapper is copied and executed

            **kwargs: (dict) -- Key value pairs for supporting conditional initializations
            Supported -
            download_server (str) - download server from which bootstrapper .exe file will be downloaded
            bootstrapper_download_os (str) - Oses to download E.g. bootstrapper_download_os="Windows,Unix"
        """
        super(UnixBootstrapperHelper, self).__init__(feature_release, machine_obj, **kwargs)
        self.unix_flavor = kwargs.get('unix_flavour',
                                      installer_constants.OSNAME_LIST[OSNameIDMapping.UNIX_LINUX64.value][1])
        _brand_name = installer_constants.BRANDING_DICT[self.oem_id].replace(" ", '')
        self.download_string = f"{_brand_name}_{self.unix_flavor}_Media"

    def set_visibility_level(self, level=None):
        """
            Set the visibility level for Bootstrapper
        """
        if level:
            self.visibility_level = level
        self.log.info(f"nVisibility flag set to {self.visibility_level}")

    def use_internal_http(self, reset=False):
        """
            Set internal http by default for Bootstrapper
        """
        self.http_export_string = "unset USE_HTTP_CV" if reset else f"export USE_HTTP_CV={self.download_server}"

    def bootstrapper_download_url(self):
        """
            Returns download server path of the bootstrapper installer
        """
        _brand_name = installer_constants.BRANDING_DICT[self.oem_id].replace(" ", '') + "-" + str(self.oem_id)
        return f"{self.download_server}/CVMedia/{installer_constants.CURRENT_RELEASE_VERSION}/" \
               f"{installer_constants.CURRENT_BUILD_VERSION}/{self.feature_release_format}/BootStrapper_Unix/" \
               f"{self.unix_flavor}/{_brand_name}/"

    def download_payload_from_bootstrapper(self, **kwargs):
        """
        Download Payload from Bootstrapper

        Args:
            **kwargs: (dict) -- Key value pairs for supporting conditional initializations
            Supported -

            download_inputs (dict) -    Dictionary for download inputs

                Supported -

                download_type   (str) - unix for unix packages, windows for windows packages

                download_full_kit (bool) - For downloading full media

                packages        (list)  -   List of packages for downloading

                bainary_set_id  (list)  -   List of bainary set ids for downloading

                download_extra  (str) - Extra arguments for download

                                        eg: [2,3]

                                        DOWNLOAD_APPLIANCE_OS_UPDATES    = 2

                                        DOWNLOAD_APPLIANCE_MSSQL_UPDATES = 3

                                        DOWNLOAD_MSSQL_SERVER            = 4

                                        DOWNLOAD_MSSQL_SERVER_UPGRADE    = 5

                                        DOWNLOAD_3RD_PARTY_PACKAGES      = 6

                                        DOWNLOAD_DOTNET40                = 7

        """
        self.log.info("Downloading from Bootstrapper")
        try:
            _download_inputs = kwargs.get('download_inputs', {})
            cmd = f" -download{_download_inputs['download_type'].lower()}" if 'download_type' in _download_inputs.keys() \
                else "-downloadunix"
            downloaded_os = 'Unix' if 'unix' in cmd else 'Windows'
            if 'packages' in _download_inputs.keys():
                extra_cmd = f" -pkgids {''.join([str(x) + ' ' for x in _download_inputs['packages']])}" \
                    if list(_download_inputs['packages']) else ""
                cmd += extra_cmd
            if 'download_extra' in _download_inputs.keys():
                extra_cmd = f" -download-extra {''.join([str(x) + ' ' for x in _download_inputs['download_extra']])}" \
                    if list(_download_inputs['download_extra']) else ""
                cmd += extra_cmd
            if 'binary_set_id' in _download_inputs.keys():
                extra_cmd = f" -binarysetids {''.join([str(x) + ' ' for x in _download_inputs['binary_set_id']])}" \
                    if list(_download_inputs['binary_set_id']) else ""
                cmd += extra_cmd
            if 'download_full_kit' in _download_inputs.keys():
                cmd += " -full" if _download_inputs['download_full_kit'] else ""
            cmd += f' -outputpath {self.remote_file_copy_loc}'
            self.machine_obj.clear_folder_content(self.remote_file_copy_loc +
                                                  installer_constants.UNIX_BOOTSTRAPPER_DOWNLOAD_LOC)
            path = \
                installer_constants.UNIX_DEFAULT_DRIVE_LETTER + installer_constants.BOOTSTRAPPER_EXECUTABLE_EXTRACTPATH
            launch_cmd = self.launch_bootstrapper(path, cmd)
            self.log.info(f"Command to be executed: {launch_cmd}")
            output = self.machine_obj.execute_command(launch_cmd)
            self.log.info(f"Output is {output.formatted_output}")
            return self.remote_file_copy_loc + installer_constants.UNIX_BOOTSTRAPPER_DOWNLOAD_LOC + downloaded_os
        except Exception as exp:
            raise Exception(f"Downloading payload Failed with error {exp}")

    def launch_bootstrapper(self, media_path, cmdl=''):
        """
            Launches bootstrapper executable

        Args:
            media_path -- bootstrapper location
            cmdl -- command line arguments for bootstrapper
        """
        launch_cmd = f"{self.http_export_string} && {media_path}/{self.exe_name} "
        launch_cmd += cmdl
        if self.visibility_level:
            launch_cmd += f" -vf {self.visibility_level} -cr"
        return launch_cmd
