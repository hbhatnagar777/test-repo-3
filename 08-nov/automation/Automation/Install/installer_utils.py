# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""File for the Utils that Support Install Automation

get_current_time()              --  Returns the current time in UnixTime Format
get_batch_working_directory()   --  Returns the Directory where Batch File is Copied
get_batch_output_file()         --  Returns the Path where Output of the Batch file is Printed
output_pipe_path_inside_batch() --  Appends the Path where output of batch file is Printed
create_batch_file_for_remote()  --  This method creates a batch file with the list of commands given
run_batch_file()                --  This Method Runs the Batch File on the current machine
is_path_local()                 --  This Method check if the Path given is Remote or on Local Machine
convert_unc()                   --  Convert a file path on a host to a UNC path.
get_windows_looseupdates_path()   --  returns windows looseupdates path
get_linux_looseupdates_path()     --  returns unix looseupdates path
get_pkg_xml_path()                --  returns xml path of pkg.xml/winpkg.xml
get_packages_to_download()        --  parses winpackages.xml and get list of packages
get_latest_recut_from_xml()       --  Returns the latest recut for the service pack provided
get_latest_cu_from_xml()          --  Returns the latest Maintenance Releaase available for a feature release
collect_logs_after_install()      --  Copies the logs files to an Automation dir
download_file_from_http_server()      --  This method is used to download configuration xml files from server.
_get_hard_dependent_packages()        --  Get the hard depenedent packages for selected package
_get_soft_dependent_packages()        --  Get the list of soft dependent packages for any package
get_pkg_displayname()                --  Frame dictionary of names of hard and soft depenedent package
get_packages_to_install()            --  Dictionary of packages(packages id : package name) to be installed
"""

import os
import time
import subprocess
import requests, urllib
from xml.etree.ElementTree import Element
import xmltodict
import urllib3
from Install import installer_constants
from AutomationUtils import logger, constants, config
from cvpysdk.deployment import deploymentconstants


def get_current_time():
    """Returns the current time in UnixTime Format"""
    return str(int(round(time.time(), 0)))


def get_batch_working_directory():
    """Returns the Directory where Batch File is Copied """
    return installer_constants.REMOTE_FILE_COPY_LOC


def get_batch_output_file():
    """ Returns the Path where Output of the Batch file is Printed"""
    return get_batch_working_directory() + "\\AllOutputFile.txt"


def output_pipe_path_inside_batch():
    """Appends the Path where output of batch file is Printed"""
    return " >> " + get_batch_output_file()


def create_batch_file_for_remote(commands=None, file_name="tempremoteexec.bat"):
    """
        This method creates a batch file with the list of commands given

            Args:
                commands     (list)  --  List of commands to be present in batch file
                    default: None

                file_name    (str)   --  Name of the Batch File
                    default: tempremoteexec.bat

            Returns:
                The File Path where Batch file is created.

    """
    log = logger.get_log()
    try:
        _path = constants.TEMP_DIR
        if file_name:
            _filepath = os.path.join(_path, file_name)
        _filehandle = open(_filepath, "w")
        if commands:
            for command in commands:
                _filehandle.write(command + "\n")
        _filehandle.close()

        log.info("Created batch file [{0}]".format(_filepath))

        return _filepath
    except Exception as err:
        log.exception("Exception raised at createBatchFileForRemoteExec: %s", str(err))
        raise err


def run_batch_file(file_path):
    """
    This Method Runs the Batch File on the current machine
        Args:
            file_path     (str)  --  File Path of the Batch File to be Triggered

        Returns:
            (Str) Output Obtained from the Batch File

        Raises:
            SDKException:
                if it fails to trigger the Batch File
    """
    log = logger.get_log()
    try:
        log.info("Executing batch file [{0}]".format(file_path))

        result = subprocess.call(file_path, shell=True)
        return result

    except Exception as err:
        log.exception("Exception in run_batch_file: %s" % str(err))
        raise err


def is_path_local(path):
    """
    This Method check if the Path given is Remote or on Local Machine
        Args:
            path     (str)  --  Path to check if it is local or Remote

        Returns:
            True            --  If the Path is Local
            False           --  If the Path is Remote

        Raises:
            SDKException:
                if it is unable to determine the Path Format
    """
    if path.startswith("\\"):
        return False

    return True

def is_visibility_acceptable(visibilityFlag):
    """
    Checks if the input visibilityFlag can be considered to download/install.

    Args:
        visibilityFlag - visibility Flag to check if it can be considered

    Returns:
        True, if visibilityFlag can be considered to download/install else False
    """
    vf=int(visibilityFlag)
    if vf==0:
        return True

    log = logger.get_log()
    config_json = config.get_config()

    try:
        accepted_visibility = eval(
            f"installer_constants.DefaultVisibilityLevels.{config_json.Install.visibility_flag}.value")
        log.info(f"Fetched visibility flag {accepted_visibility} from config")

    except Exception as exp:
        log.warning("Failed to fetch visibility flag from config, taking LAB_USERS as visibility")
        accepted_visibility = installer_constants.DefaultVisibilityLevels.LAB_USERS.value

    return (vf & accepted_visibility) > 0

def convert_unc(hostname, path):
    """
    Convert a file path on a host to a UNC path.

    Args:
        hostname - hostname where the file exists
        path - path of file\folder

    Returns:
        returns converted path
    """
    try:
        return ''.join(['\\\\', hostname, '\\', path.replace(':', '$')])
    except Exception as exp:
        raise Exception("Exception raised at convert_unc")


def get_windows_looseupdates_path(path, x64=True):
    """
    returns windows looseupdates path

    args:
        path - cache path
    """
    if x64:
        return path + "\\BinaryPayload" + "\\LooseUpdates"
    return path + "\\BinaryPayload32" + "\\LooseUpdates"


def get_linux_looseupdates_path(path, flavour="linux-x8664"):
    """
    returns unix looseupdates path

    args:
        path - cache path
        flavour - unix flavour
    """
    return path + "\\" + flavour + "\\LooseUpdates"


def get_pkg_xml_path(path, os_id):
    """
    return winpackages.xml path in case of windows, pkg.xml path in case of unix
    args:
        path: path of the server
        os_id: os id

    returns:
        xml path of pkg.xml/winpkg.xml
    """
    if int(os_id) == 3 or int(os_id) == 1:
        return path + "\\Windows\\Winpackages.xml"
    return path + "\\Unix\\pkg.xml"


def get_packages_to_download(xml_path):
    """
    parses winpackages.xml and get list of packages

    args:
        xml_path - winpackages.xml path

    returns:
        list of packages to download

    """
    try:
        with open(xml_path) as fd:
            winpkgdict = xmltodict.parse(fd.read())
        download_package_list = []
        for each in winpkgdict['UpdatePatches_PackageDetails']['PkgList']['pkg']:
            if '@SkipDownload' in each.keys() and each['@SkipDownload'] == 'True':
                continue
            download_package_list.append(each['@id'])
        download_package_list = map(str, download_package_list)

        return download_package_list

    except Exception as err:
        raise Exception("Exception occured in getting files that are marked skipped %s", str(err))


def get_latest_recut_from_xml(sp_number, xml_url=installer_constants.DEFAULT_FEATURE_RELEASE_XML):
    """
        Returns integer value of latest recut for given SP
        Returns:
            latest_recut: String recut number of the the service pack
            trans_id    : String Transaction ID of the recut
    """
    trans_id = 0
    latest_recut = 0
    if not isinstance(sp_number, int):
        if 'sp' in sp_number.lower():
            sp_number = sp_number.lower().split('sp')[1]
    try:
        file_request = requests.get(xml_url)
    except urllib.error.HTTPError as e:
        return None
    xml_dict = xmltodict.parse(file_request.content)
    for sps in xml_dict['UpdatePatches_AvailableMedia']['MediaSet']:
        if (int(sps['SPVersion']['@Major']) == int(sp_number) and int(sps['SPVersion']['@TransactionId']) > trans_id
                and is_visibility_acceptable(sps['SPVersion']['@VisibilityFlag'])):
            trans_id = int(sps['SPVersion']['@TransactionId'])
            latest_recut = int(sps['SPVersion']['@RevisionId'])
    if latest_recut == 0:
        raise Exception("Unable to find latest recut")
    return 'SP' + str(sp_number) + '_' + str(trans_id) + '_R' + str(latest_recut)


def get_latest_cu_from_xml(sp_transaction_recut, xml_url=installer_constants.DEFAULT_MAINTENANCE_RELEASE_XML):
    """
        Returns integer value of latest CU pack for given SP

        Returns:
            int:   latest cu_pack released for that SP
    """
    try:
        if int(sp_transaction_recut.split('_R')[-1]) <= 952:
            xml_url = installer_constants.DEFAULT_CU_CONFIGURATION_XML
            file_request = requests.get(xml_url.format(sp_transaction_recut.split('_')[0]))
        else:
            file_request = requests.get(xml_url.format(sp_transaction_recut))
    except urllib.error.HTTPError as e:
        return None

    available_cu_packs = []
    cu_configuration_dict = xmltodict.parse(file_request.content)
    if not isinstance(cu_configuration_dict[
                          'UpdatePatches_AvailableCumulativeUpdatePacks']['AvailableCUs']['CUPackEntries'], list):
        cu_pack_entries = cu_configuration_dict[
            'UpdatePatches_AvailableCumulativeUpdatePacks']['AvailableCUs']['CUPackEntries']
        available_cu_packs.append(int(cu_pack_entries['@Number']))
    else:
        for each_cu_pack in \
                cu_configuration_dict['UpdatePatches_AvailableCumulativeUpdatePacks']['AvailableCUs']['CUPackEntries']:
            if is_visibility_acceptable(each_cu_pack["@VisibilityFlag"]):
                available_cu_packs.append(int(each_cu_pack['@Number']))
    if not available_cu_packs:
        raise Exception("Unable to find latest CU pack")
    return list(sorted(available_cu_packs))[-1]


def get_cu_trans_id_from_xml(sp_transaction_recut, cu_number):
    """
            Returns integer value of latest CU pack for given SP

            Returns:
                int:   latest cu_pack released for that SP
    """
    try:
        xml_url = installer_constants.DEFAULT_MAINTENANCE_RELEASE_XML
        file_request = requests.get(xml_url.format(sp_transaction_recut))
    except urllib.error.HTTPError as e:
        return None
    cu_configuration_dict = xmltodict.parse(file_request.content)
    if not isinstance(cu_configuration_dict[
                          'UpdatePatches_AvailableCumulativeUpdatePacks']['AvailableCUs']['CUPackEntries'], list):
        cu_pack_entries = cu_configuration_dict[
            'UpdatePatches_AvailableCumulativeUpdatePacks']['AvailableCUs']['CUPackEntries']
        if int(cu_pack_entries['@Number']) == int(cu_number):
            return cu_pack_entries['@TransactionId']
    else:
        for each_cu_pack in \
                cu_configuration_dict['UpdatePatches_AvailableCumulativeUpdatePacks']['AvailableCUs']['CUPackEntries']:
            if int(each_cu_pack['@Number']) == int(cu_number):
                return each_cu_pack['@TransactionId']
    return None


def get_installer_path_from_dvd(media_path, machine_obj, is_windows=True):
    """
        Returns installer path from the given DVD path

        Returns:
            str
    """
    exe_name = "Setup" if is_windows else "cvpkgadd"
    if is_windows:
        files_list = machine_obj.get_files_and_directory_path(media_path)
        for files in files_list:
            if files.split('\\')[-1] == exe_name:
                return files.split('\\')[:-1].join('\\')


def get_latest_cu_from_media(media_path, machine_obj):
    """
        Returns integer value of the CU pack for given DVD

        args:

            media_path - location of media

            machine_obj - machine object

        Returns:
            int:  cu_pack
    """
    if 'windows' in machine_obj.os_info.lower():
        _path = machine_obj.execute_command("Get-PSDrive | where displayroot -like '\\*'").formatted_output[0][0] + ":\\" \
            if media_path[:2] == r'\\' else media_path
        res = machine_obj.execute_command(f"Get-ChildItem \"{_path}\" -filter \"CU*\" -Directory -Recurse | select Name")
    else:
        res = machine_obj.execute_command(f"find {media_path} -type d -iname \"CU*\"")
    return int(res.formatted_output[0][0].split('CU')[-1]) if res.exception == '' else 1


def list_hotfixes_in_cu_pack(cu_media_path, machine_obj):
    update_file = machine_obj.join_path(cu_media_path, 'Config', 'Updates.txt')
    return machine_obj.read_file(update_file).split('\n')


def get_cu_from_cs_version(commcell):
    """
        Returns integer value of the CU pack from commcell version

        Returns:
            int:  cu_pack
    """
    return int(commcell.version.split('.')[-1])


def get_cu_pack_details_from_xml(cu_num, xml_path):
    """
    returns the transaction id of a particular CU

    args:
        cu_num - cu number E.g CU1

    returns:
        dict of CU details(TransactionId and FriendlyName)
    """
    try:
        if 'CU' in cu_num:
            cu_num = cu_num.split("CU")[1]
        cu_pack_dict = {}
        with open(xml_path) as package_xml:
            cu_configuration_dict = xmltodict.parse(package_xml.read())
        cu_pack_entries = cu_configuration_dict['UpdatePatches_AvailableCumulativeUpdatePacks']['AvailableCUs'][
            'CUPackEntries']
        if not isinstance(cu_pack_entries, list):
            if not cu_num == cu_pack_entries['@Number']:
                raise Exception(f"CU pack {cu_num} is not found in internal site eng-updates server")

            cu_pack_dict["TransactionId"] = cu_pack_entries['@TransactionId']
            cu_pack_dict["FriendlyName"] = cu_pack_entries['@FriendlyName']
        else:
            for each_cu_pack in cu_pack_entries:
                if each_cu_pack['@Number'] == cu_num:
                    cu_pack_dict["TransactionId"] = each_cu_pack['@TransactionId']
                    cu_pack_dict["FriendlyName"] = each_cu_pack['@FriendlyName']
        return cu_pack_dict

    except Exception as e:
        raise Exception("Exception occured in setting CU pack number value downloaded %s", str(e))


def _get_package_id(element):
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


def _get_binary_info(element):
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
    is_binary = False
    if element.tag == 'Binary':
        is_binary = True
    if is_binary:
        name = element.attrib['Name']
        checksum = element.attrib['CheckSum']
        source_path = element.attrib['SourcePath']
        size = element.attrib['SizeInBytes']
        return is_binary, name, checksum, source_path, size
    return is_binary, None, None, None, None


def binary_info_xml_to_dict(parent_element):
    """
    Convert BinaryInfo.xml into dict
    Args:
        parent_element -- parent element
    Returns:
        dictionary
    """
    if not isinstance(parent_element, Element):
        raise TypeError("Invalid Element Type passed")
    xml_dict = {}
    children_names = []
    for child_node in parent_element.iter():
        for each_attribute in child_node.attrib.keys():
            if each_attribute == 'binarySetId':
                xml_dict.fromkeys(child_node.attrib[each_attribute])
                children_names.append(child_node)

    for each_child in children_names:
        base_key = each_child.attrib['binarySetId']
        xml_dict.update({base_key: {}})
        for os_child_node in each_child.iter():
            is_package, package = _get_package_id(os_child_node)
            if is_package:
                if package not in (xml_dict[base_key]).keys():
                    xml_dict[base_key].update({package: {}})
                for each_child_package in os_child_node.iter():
                    is_binary, name, checksum, source_path, size = _get_binary_info(each_child_package)
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


def collect_logs_after_install(tc, machine_obj):
    """
    This Method can be called from each testcase to collect the logs if there is a failure while installaiton/
    validation
    Args:
        tc: testcase object
        machine_obj: machine object of the client

    Returns: None

    """
    try:
        if 'windows' in machine_obj.os_info.lower():
            log_dir = installer_constants.DEFAULT_LOG_DIRECTORY_WINDOWS
            destination_folder = installer_constants.REMOTE_FILE_COPY_LOC
            log_name = "Log Files"
        else:
            log_dir = installer_constants.DEFAULT_LOG_DIRECTORY_UNIX
            destination_folder = installer_constants.UNIX_REMOTE_FILE_COPY_LOC
            log_name = "Log_Files"
        if machine_obj.check_directory_exists(log_dir):
            machine_obj.copy_folder(log_dir, destination_folder)
            debug_logs_here = machine_obj.join_path(destination_folder, "TC" + tc.id + "_Logs")
            if machine_obj.check_directory_exists(debug_logs_here):
                machine_obj.remove_directory(debug_logs_here)
            machine_obj.rename_file_or_folder(
                machine_obj.join_path(destination_folder, log_name), debug_logs_here)
    except Exception as exp:
        tc.log.error(f"Exception in tear down function {exp}")


def download_file_from_http_server(file_path):
    """
        This method is used to download configuration xml files from server.
        Args:
            file_path    (str)   --   URL path to download the file
        Returns:
             str  --   returns the file path of configuration xml
    """
    try:
        req = requests.get(file_path)
        _base_filename = os.path.basename(file_path)
        _test_results_path = constants.TEMP_DIR
        base_filepath = os.path.join(_test_results_path, _base_filename)
        if not (os.path.exists(_test_results_path)):
            os.mkdir(_test_results_path)
        fp = open(base_filepath, "wb")
        fp.write(req.content)
        fp.close()
        return base_filepath
    except Exception as exp:
        raise Exception(f"Exception occurred in Downloading the file from http server {exp}")


def _get_hard_dependent_packages(pkgdict, packages_list):
    """
        Get the list of hard dependent packages for selected package
        Args:
             pkgdict        (dict)   --  Xml of packages info convereted to Dict
             packages_list  (list)   --  List of package ID's selected by the user
        Returns:
            List  --   List of hard dependent package ids
    """
    try:
        _hard_list = []
        for each in pkgdict['UpdatePatches_PackageDetails']['PackageInfoList']['pkginfo']:
            if (int(each['@pkgID']) in packages_list) and (each['@binarySetId'] != "1"):
                if 'RequiresHard' in each:
                    if len(each['RequiresHard']) == 1:
                        _hard_list.append(int(each['RequiresHard']['@pkgID']))
                    elif len(each['RequiresHard']) > 1:
                        for every in each['RequiresHard']:
                            if int(every['@pkgID']) not in packages_list:
                                _hard_list.append(int(every['@pkgID']))
        return _hard_list
    except Exception as err:
        raise Exception(f"An exception occurred in getting hard dependent packages. {err}")


def _get_soft_dependent_packages(pkgdict, packages_list):
    """
        Get the list of soft dependent packages for any package
        Args:
             pkgdict        (dict)   --  Xml of packages info convereted to Dict
             packages_list  (list)   --  List of package ID's selected by the user
        Returns:
            List  --   List of soft dependent package ids
    """
    try:
        _soft_list = []
        for each in pkgdict['UpdatePatches_PackageDetails']['PackageInfoList']['pkginfo']:
            if (int(each['@pkgID']) in packages_list) and (each['@binarySetId'] != "1"):
                if 'RequiresSoft' in each:
                    if len(each['RequiresSoft']) == 1:
                        _soft_list.append(int(each['RequiresSoft']['@pkgID']))
                    elif len(each['RequiresSoft']) > 1:
                        for every in each['RequiresSoft']:
                            if int(every['@pkgID']) not in packages_list:
                                _soft_list.append(int(every['@pkgID']))
        return _soft_list
    except Exception as err:
        raise Exception(f"An exception occurred in getting soft dependent packages. {err}")


def get_pkg_displayname(pkgdict, pkg_list):
    """
           frame dictionary of hard and soft dependent package
           Args:
             pkgdict   (dict)   --  Xml of packages info convereted to Dict
             pkg_list  (list)   --  List of packages selected by the user
           Returns:
                Dict   -- dict of packages id with package names
    """
    try:
        packages_info = {}
        for each in pkgdict['UpdatePatches_PackageDetails']['PkgList']['pkg']:
            if int(each['@id']) in pkg_list:
                packages_info[each['@id']] = each['@DisplayName']
        return packages_info
    except Exception as err:
        raise Exception(f"An Exception occurred while getting dictionary of name and package id. {err}")


def get_packages_to_install(packages_list, osid, feature_release, only_hard_dependent_packages=False):
    """
        Get the dictionary of packages(packages id : package name)
        Args:
                packages_list     (list)  --  List of packages selected by the user
                osid              (int)   --  Id of the Operating System
                feature_release   (str)   --  feature release of the bootstrapper
                only_hard_dependent_packages    (bool)  --  Select only hard dependent packages
                                                            :Default False
        Returns:
            Dict  -   dict of packages id with package names
    """
    try:
        _feature_release = feature_release if '_' in feature_release else get_latest_recut_from_xml(feature_release)
        if osid == deploymentconstants.OSNameIDMapping.WINDOWS_32.value or \
                osid == deploymentconstants.OSNameIDMapping.WINDOWS_64.value:
            _xml_path = installer_constants.DEFAULT_PACKAGE_INSTALL_PATH_WINDOWS.format(_feature_release)
        else:
            _xml_path = installer_constants.DEFAULT_PACKAGE_INSTALL_PATH_UNIX.format(_feature_release)
        _pkg_xml_path = download_file_from_http_server(_xml_path)
        with open(_pkg_xml_path) as fd:
            pkgdict = xmltodict.parse(fd.read())
        if not only_hard_dependent_packages:
            hard_packages = _get_hard_dependent_packages(pkgdict, packages_list)
            initial_soft_packages = _get_soft_dependent_packages(pkgdict, packages_list)
            packages_list = list(set(packages_list) | set(initial_soft_packages) | set(hard_packages))
            final_soft_packages = _get_hard_dependent_packages(pkgdict, packages_list)
        else:
            hard_packages = _get_hard_dependent_packages(pkgdict, packages_list)
            final_soft_packages = []
        final_pkg_list = list(set(packages_list) | set(hard_packages) | set(final_soft_packages))
        final_pkg_dict = get_pkg_displayname(pkgdict, final_pkg_list)
        return final_pkg_dict
    except Exception as err:
        raise Exception(f"An error occurred while getting list of packages to be installed. {err}")


def get_details_from_friendly(client_machine_obj, friendly_path):
    update_ini_file = client_machine_obj.join_path(friendly_path, "Config", "update.ini")
    config_details = client_machine_obj.read_file(update_ini_file).split('\n')
    config_dict = {}
    for params in config_details:
        if params:
            val = params.split('=')
            key = val[0].translate({ord(i): None for i in '[]'})
            config_dict[key] = val[1]
    return config_dict


def mount_network_path(media_path, machine_obj, tc_object, local_mount_path=None):

    if 'windows' not in machine_obj.os_info.lower():
        local_path = installer_constants.UNIX_DEFAULT_MOUNT_PATH if local_mount_path is None else local_mount_path
        mount_flag = True

        if machine_obj.check_directory_exists(local_path):
            output = machine_obj.execute_command(
                rf"if df -h {local_path} | grep -q '{media_path}'; then echo 'found'; fi")
            if output.output.strip() == 'found':
                tc_object.log.info(f"{media_path} already mounted on {local_path}")
                mount_flag = False
            else:
                machine_obj.execute_command(f"umount {local_path}")
        else:
            machine_obj.create_directory(directory_name=local_path, force_create=True)

        tc_object.log.info(f"Mounting Network Path:{media_path}")
        if "sunos" in machine_obj.os_flavour.lower():
            media_list = media_path.strip("//").split("/", 2)
            server_info = media_list[0]
            share_path = media_list[1]
            mount_path = f" //{server_info}/{share_path}/"

            # Solaris Machine Does not support cifs | smbfs command is used for mounting
            command_to_mount = "echo " + tc_object.config_json.Install.dvd_password + " | mount -F smbfs -o " + \
                               "user=" + tc_object.config_json.Install.dvd_username.split("\\")[1] + \
                               ",domain=" + tc_object.config_json.Install.dvd_username.split("\\")[0] + \
                               mount_path + f" {local_path}"
            if mount_flag:
                mount_op = machine_obj.execute_command(command_to_mount)
                if mount_op.exit_code != 0:
                    raise Exception("Mount failed.. Check network path and credentials")
            return f"{local_path}/{media_list[2]}"

        if mount_flag:
            mount_op = machine_obj.execute_command(
                "mount -t cifs " + media_path + " -o username=" +
                tc_object.config_json.Install.dvd_username.split("\\")[1] + ",password=" +
                tc_object.config_json.Install.dvd_password + ",vers=2.0" + ",domain=" +
                tc_object.config_json.Install.dvd_username.split("\\")[0] + f" {local_path}")

            if mount_op.exit_code != 0:
                raise Exception("Mount failed.. Check network path and credentials")
        return f"{local_path}"
