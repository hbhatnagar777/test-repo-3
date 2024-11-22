"""
Main file for all the utilities of Virtual Sever

Method:

get_utils_path - get the utils path of VSA Automation

get_testdata_path - path where testdata needs to copied
"""

import os
import base64
import ipaddress
import random
import time

import socket

from AutomationUtils import logger
from AutomationUtils.machine import Machine
from AutomationUtils.pyping import ping
from Cryptodome.Cipher import AES
from Cryptodome import Random

from cvpysdk.client import Client

UTILS_PATH = os.path.dirname(os.path.realpath(__file__))
BLOCK_SIZE = 16
key = b'515173A5C402A03398D79B5353B2A080'


def get_testdata_path(machine, timestamp=None, create_folder=True):
    """
    get the test data path provided base directory

    Args:

        machine         (obj)   - Machine object of controller
        timestamp       (str or int) - Timestamp (epoch time). We will get current timestamp by default
        create_folder   (bool)  - Whether to create the testdata folder or not

    returns:
        _test_data_path (str)   - Test data Path where test data can be generated
        False           (bool)  - if testdata path cannot be retreived

    Exception:
        if failed to create directory

    """
    log = logger.get_log()
    try:
        _vserver_path = os.path.dirname(UTILS_PATH)
        import time
        if not timestamp:
            timestamp = str(int(time.time()))
        _testdata_path = os.path.join(_vserver_path, "TestCases", "TestData", timestamp)
        log.info("checking if directory {} exist".format(_testdata_path))
        if not machine.check_directory_exists(_testdata_path) and create_folder:
            machine.create_directory(_testdata_path)
        if machine.os_info.lower() != 'windows':
            return _testdata_path.replace('/', '//')
        return _testdata_path.replace('/', '\\')
    except Exception:
        log.exception("Error: can't find the VirtualServer utils Path")
        return False


def get_version_file_path(machine):
    """
    Get the version file's path in the local machine.

    Args:
        machine         (obj)   - Machine object of controller

    returns:
        _version_file_path (str)   - Test data Path where test data can be generated

        False           (bool)  - if testdata path cannot be retreived

    Raises
        Exception:
            if failed to create the parent directory of versions file.
    """
    log = logger.get_log()
    try:
        _vserver_path = os.path.dirname(UTILS_PATH)
        _version_file_path = os.path.join(_vserver_path, "TestCases", "TestFileVersions")

        log.info("Checking if directory {} exists".format(_version_file_path))
        if not machine.check_directory_exists(_version_file_path):
            machine.create_directory(_version_file_path)

        if machine.os_info.lower() != 'windows':
            return _version_file_path.replace('/', '//')

        return _version_file_path.replace('/', '\\')
    except Exception as exp:
        log.exception(f"Error: can't find the VirtualServer utils Path: {exp}")
        return False


def get_vm_collectfile_path(csdbobj, machinesobj, jobid, subclientid):
    """
    gets vmcollect file path on proxy machine

    Args:
        
        csdbobj- sql object to connect to CS Data base
        
        machineobj (list) - Machine name to get the vmcollect file path
        
        job_id  (list)   -   Backup job id
        
        subclientid -  subclientid
        
    returns:
        job vmcollect path
        
    Exception:
        if failed to get vmcollect file path

    """
    log = logger.get_log()
    try:
        path_list= []
        for eachmachine in machinesobj:
            query = "select jobresultdir from app_client where name = '"+eachmachine.machine_name+"'"
            queryoutput = csdbobj.execute(query)
            path = queryoutput.rows[0]['jobresultdir']+'\\CV_JobResults\\iDataAgent\\VirtualServerAgent\\2\\'+subclientid+''+'\\vmcollect_'+jobid+'.cvf'
            path_list.append(path)
        return path_list
    except Exception:
        log.exception("Error: can't find vmcollect Path")
        return False


def get_content_indexing_path(machine):
    """
    get the content indexing data path provided base directory

    Args:

        machine         (obj)   - Machine object of controller

    returns:
        _test_data_path (str)   - Content Indexing test data path

        False           (bool)  - if testdata path cannot be retreived

    Exception:
        if failed to create directory

    """
    log = logger.get_log()
    try:
        _vserver_path = os.path.dirname(UTILS_PATH)
        _testdata_path = os.path.join(_vserver_path, "TestCases", "ContentIndexing")

        log.info("checking if directory exist %s" % _testdata_path)

        if not machine.check_directory_exists(_testdata_path):
            raise Exception("The content indexing data path is not available")

        return _testdata_path.replace('/', '\\')

    except Exception:
        log.exception("Error: can't find the VirtualServer utils Path")
        return False


def find_live_browse_db_file(machine, db_path):
    """

    :param machine: Machine object of MA machine used for live browse
    :param db_path: DB path where the live browse db is located
    :return:
        db_name :   (str)   : name of the db used in live browse

    Raise:
        Exception if DB file is not found
    """
    log = logger.get_log()
    try:

        file_name = None
        file_in_path = machine.get_files_in_path(db_path)
        if isinstance(file_in_path, str):
            file_in_path = [os.path.basename(file_in_path)]
        for each_file in file_in_path:
            each_file = os.path.basename(each_file)
            if each_file.strip().endswith(".db"):
                file_name = each_file
                break

        if file_name is None:
            raise Exception("no file found with that extension")

        return os.path.join(db_path, file_name)

    except Exception as err:
        log.exception("An error Occurred in getting live browse db path")
        raise err


def encode_password(message):
    """
    :param value: value of the text needed to be encoded
    :return: encoded value of the password
    """

    if not isinstance(message, bytes):
        message = message.encode()
    IV = Random.new().read(BLOCK_SIZE)
    aes = AES.new(key, AES.MODE_CFB, IV)
    return base64.b64encode(IV + aes.encrypt(message)).decode()


def encode_base64(message):
    """

    Encodes password in base 64 format

    Args:
            message                 (string):   String needs to be encoded

    Returns:
                                    (byte):     base 64 encoded password

    """

    if not isinstance(message, bytes):
        message = message.encode()
    return base64.b64encode(message)


def decode_password(message):
    """
        :param value: value of the text needed to be decoded
        :return: decoded value of the password
        """
    encrypted = base64.b64decode(message)
    IV = encrypted[:BLOCK_SIZE]
    aes = AES.new(key, AES.MODE_CFB, IV)
    cipher = aes.decrypt(encrypted[BLOCK_SIZE:])
    return cipher.decode("utf-8")


def bytesto(bytes, to, bsize=1024):
    """

    Args:
        bytes: bytes to convert
        to: format to be converted into
        bsize: unit of byte size

    Returns: Converted value of the bytes in desired format

    """

    available_units = {'KB': 1, 'MB': 2, 'GB': 3, 'TB': 4}
    result = float(bytes)
    for i in range(available_units[to]):
        result = result / bsize
    return result


def get_os_flavor(guest_os_name):
    """

    Args:
        guest_os_name: Name of the guestOs of the VM

    Returns:
        Flavor to which guestOS belongs to

    """
    os_flavor = None
    if "windows" in guest_os_name.lower():
        os_flavor = "Windows"
    else:
        os_flavor = "Unix"
    return os_flavor


def find(lst, key, value):
    """
    Finds the dict based on a key value given in a list of
    dicts
    Args:
        lst:    list of dicts
        key:    Key that should be checked for
        value:  Value that filters the dict

    Returns:
        Dict when the key with given value is found else returns -1

    """
    for i, dict in enumerate(lst):
        if dict[key] == value:
            return i, dict
    return -1, {}


def validate_ip(ip):
    """
    Validates the Ip given
    Args:
        ip:     (str) - Ip to be validated
    Returns:
        True - if valid IP
        False - if invalid IP
    """
    try:
        response = ping(ip)
        return response.ret_code == 0
    except Exception as err:
        return False


def validate_ipv4(ip):
    """
    Validates the Ip given for ipv4
    Args:
        ip:     (str) - Ip to be validated
    Returns:
        True - if valid IPv4
        False - if invalid IPv4
    """
    try:
        if ip.find('169.254') != 0 and ipaddress.IPv4Address(ip):
            return True
        return False
    except Exception as err:
        return False


def decorative_log(msg=""):
    """
    Logs to be printed in a different way
    Args:
            msg                     (string):  Log line to be printed


    """
    if msg != "":
        log = logger.get_log()
        log.info("%(boundary)s %(message)s %(boundary)s",
                 {'boundary': "*" * 25,
                  "message": msg})


def get_details_from_config_file(tag1, tag2=None):
    """
    Get details from config file
    Args:
        tag1                  (string):   first tag to look in the config file

        tag2                  (string):   second tag to look in the config file

    Returns:
        value in config file
    """
    from AutomationUtils import config
    config = config.get_config()
    if tag2:
        return eval('config.Virtualization.{}.{}'.format(tag1, tag2))
    else:
        return eval('config.Virtualization.{}.creds'.format(tag1))


def set_inputs(inputs, source_options):
    """
    Sets the input given in the input

    Args:

        inputs                      (dict):     all the inputs in the input json

        source_options              (object):   source object for restores

    """
    log = logger.get_log()
    for each_key, each_val in inputs.items():
        try:
            log.info(f"Setting attribute {each_key} in object {each_val}")
            setattr(source_options, each_key, each_val)
        except Exception as exp:
            log.error(f"Encountered error while setting attribute. {exp}")


def subclient_initialize(testcase, **kwargs):
    """

    Args:
        testcase                    (obj):  Object of the testcase

    Returns:
        auto_subclient              (obj):  Object of the subclient

    Raises:
            Exception:
                if it fails to create subclient object

    """
    try:
        from . import VirtualServerHelper
        log = logger.get_log()
        if hasattr(testcase,"is_tenant"):
            kwargs["is_tenant"] = testcase.is_tenant
        log.info("Started executing {} testcase".format(testcase.id))
        decorative_log("Initialize helper objects")
        auto_commcell = VirtualServerHelper.AutoVSACommcell(testcase.commcell, testcase.csdb, **kwargs)
        auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, testcase.client)
        auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client,
                                                              testcase.agent, testcase.instance, testcase.tcinputs, **kwargs)
        auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, testcase.backupset)
        auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, testcase.subclient)
        auto_subclient.testcase_id = testcase.id
        log.info("$$$$$$$$$Subclient initialize done successfully")
        if not auto_subclient.vm_list:
            raise Exception("No content found in the subclient")
        return auto_subclient
    except Exception as exp:
        logger.get_log().error('Subclient object created failed with error: {} '.format(str(exp)))
        raise Exception(str(exp))


def destination_subclient_initialize(testcase):
    """

    Args:
        testcase                    (obj):  Object of the testcase

    Returns:
        dest_auto_subclient              (obj):  Object of the destination subclient

    Raises:
            Exception:
                if it fails to create destination subclient object

    """
    try:
        from . import VirtualServerHelper
        decorative_log("Initialize destination helper objects")
        try:
            vcenter_client = testcase.tcinputs["Destination_Virtualization_client"]
        except KeyError:
            vcenter_client = testcase.tcinputs["DestinationClient"]
        testcase.client = testcase.commcell.clients.get(vcenter_client)
        testcase.tcinputs["ClientName"] = vcenter_client
        testcase.agent = testcase.client.agents.get('Virtual Server')
        try:
            testcase.instance = testcase.agent.instances.get(testcase.tcinputs['DestinationInstance'])
        except KeyError:
            instance_keys = next(iter(testcase.agent.instances.all_instances))
            testcase.instance = testcase.agent.instances.get(instance_keys)
        testcase.tcinputs["InstanceName"] = testcase.instance.name
        backupsetkeys = next(iter(testcase.instance.backupsets.all_backupsets))
        testcase.tcinputs["BackupsetName"] = backupsetkeys
        testcase.backupset = testcase.instance.backupsets.get(backupsetkeys)
        sckeys = next(iter(testcase.backupset.subclients.all_subclients))
        testcase.tcinputs["SubclientName"] = sckeys
        testcase.subclient = testcase.backupset.subclients.get(sckeys)

        dest_auto_commcell = VirtualServerHelper.AutoVSACommcell(testcase.commcell, testcase.csdb)
        dest_auto_client = VirtualServerHelper.AutoVSAVSClient(dest_auto_commcell, testcase.client)
        dest_auto_instance = VirtualServerHelper.AutoVSAVSInstance(dest_auto_client,
                                                                   testcase.agent, testcase.instance, testcase.tcinputs)
        dest_auto_backupset = VirtualServerHelper.AutoVSABackupset(dest_auto_instance, testcase.backupset)
        dest_auto_subclient = VirtualServerHelper.AutoVSASubclient(dest_auto_backupset, testcase.subclient)
        return dest_auto_subclient
    except Exception as exp:
        logger.get_log().error('Destination subclient object created failed with error: {} '.format(str(exp)))
        raise exp


def discovered_client_initialize(auto_subclient, vm):
    """
        Initializes objects of discovered client

        Args:
            auto_subclient              (obj):   Object of the subclient

            vm                   (str):   Discovered client name

        Raises:
                Exception:
                    if it fails to create object

        """
    try:
        log = logger.get_log()
        log.info("Initialize helper objects for discovered clients")
        v2client_obj = auto_subclient.auto_commcell.commcell.clients.get(vm)
        vmagent_obj = v2client_obj.agents.get(auto_subclient.vsa_agent.agent_name)
        vminstance_obj = vmagent_obj.instances.get('VMInstance')
        vmbackupset_obj = vminstance_obj.backupsets.get(
            auto_subclient.auto_vsa_backupset.backupset_name)
        vmsub_obj = vmbackupset_obj.subclients.get(auto_subclient.subclient.name)
        auto_subclient.subclient._subClientEntity = vmsub_obj._subClientEntity
        auto_subclient.hvobj.VMs[vm].subclient = vmsub_obj

    except Exception as exp:
        raise Exception('Discovered client object created failed with error: {} '.format(str(exp)))


def cross_client_restore_pre_validation(testcase):
    """
    Validates the checks for cross client restore
    Args:
        testcase                    (obj):  Object of the testcase

    Returns:
                                    (bool): True if successful
                                            False if not successful

    Raises:
            Exception:
                if it fails during validation of clients

    """
    try:
        log = logger.get_log()
        try:
            vcenter_client = testcase.tcinputs["Destination_Virtualization_client"]
        except KeyError:
            vcenter_client = testcase.tcinputs["DestinationClient"]
        dest_client = testcase.commcell.clients.get(vcenter_client)
        dest_agent = dest_client.agents.get('Virtual Server')
        try:
            dest_instance = dest_agent.instances.get(testcase.tcinputs['DestinationInstance'])
        except KeyError:
            instance_keys = next(iter(dest_agent.instances.all_instances))
            dest_instance = dest_agent.instances.get(instance_keys)
        if testcase.client.name != dest_client.name:
            log.info("source and destination client are different")
            from .VirtualServerConstants import on_premise_hypervisor
            if testcase.instance.instance_name == dest_instance.instance_name and on_premise_hypervisor(
                    dest_instance.instance_name) and on_premise_hypervisor(
                testcase.instance.instance_name):
                log.info("Validating the servers")
                if set(testcase.instance.server_host_name) == set(dest_instance.server_host_name):
                    log.error("Servres of source and destination are same")
                    return False
            else:
                log.info("Valdiation of Servers are not needed. Either Cloud hyperviour or conversion")
            return True
        else:
            log.info("Source and destination client are same")
            return False

    except Exception as exp:
        raise Exception('Validation of cross client restore validation has excetion : {} '.format(str(exp)))


def add_test_data(vm, folder_name="Dummy", timestamp=str(int(time.time()))):
    """Adds the test data to the VM object
        Args:
            vm: VM object of the VM on which the data is generated
            folder_name (str): The name of the folder to add test data to
            timestamp (str)  : Timestamp of the test data path
        Returns:
        Raises:
                Exception:
                    if it fails to generate test data or copy it to the virtual machine
    """
    log = logger.get_log()
    controller = Machine(socket.gethostbyname_ex(socket.gethostname())[2][0])

    # Generate test data path on the controller machine, folder will be created in next step
    local_testdata_path = get_testdata_path(controller, timestamp=timestamp, create_folder=False)

    # Delete old directory
    if controller.check_directory_exists(local_testdata_path):
        controller.remove_directory(local_testdata_path)
    controller.create_directory(local_testdata_path)

    # Generate testdata at path
    generate = controller.generate_test_data(local_testdata_path, 3, 5, random.randint(40000, 60000))
    if not generate:
        raise Exception("Could not generate test data locally")

    # Copy test data to the VM's each drive
    for drive in vm.drive_list.values():
        testdata_path = vm.machine.join_path(drive, folder_name)
        if vm.machine.check_directory_exists(testdata_path):
            log.info(f'Cleaning up %s', testdata_path)
            vm.machine.remove_directory(testdata_path)
        log.info('Copying Test data to Drive %s', drive)
        vm.copy_test_data_to_each_volume(drive, folder_name, local_testdata_path)
    log.info("Copy test data completed successfully")


def validate_test_data(vm, folder_name="Dummy", timestamp=None):
    """Validates the test data to the VM object
        Args:
            vm: VM object of the VM on which the data is to be compared
            folder_name (str): The name of the folder to check test data in
            timestamp   (str): The timestamp of the test data path
        Returns:
        Raises:
                Exception:
                    if it fails to validate test data or if the directory doesn't exist
    """
    log = logger.get_log()
    controller = Machine(socket.gethostbyname_ex(socket.gethostname())[2][0])
    if not timestamp:
        timestamp = vm.hvobj.timestamp

    log.info("Performing test data validation")
    for drive in vm.drive_list.values():
        dest_path = vm.machine.join_path(drive, folder_name, "TestData", timestamp)
        # Get the base testdata directory from get_testdata_path and replace timestamp
        # Timestamp is stored in hypervisor object during copying to each drive
        source_path = get_testdata_path(controller, timestamp=timestamp, create_folder=False)
        # Try to attempt testdata validation 5 times before raising exception
        for attempt in range(5):
            try:
                difference = controller.compare_folders(vm.machine, source_path, dest_path)
                break
            except:
                log.info("test data validation attempt %d", attempt)
                log.info("Sleeping for 30 seconds")
                time.sleep(30)
        else:
            difference = controller.compare_folders(vm.machine, source_path, dest_path)

        if difference:
            log.info("checksum mismatched for files {0}".format(difference))
            raise Exception(
                "Folder Comparison Failed for Source: {0} and destination: {1}".format(
                    source_path, dest_path))
    log.info("Validation completed successfully")


def validate_no_test_data(vm, folder_name="Dummy", timestamp=None):
    """Validates the test data doesn't exist on the VM object
        Args:
            vm: VM object of the VM on which the data is to be checked
            folder_name (str): The name of the folder to check test data in
            timestamp   (str): The timestamp of the test data path
        Returns:
        Raises:
                Exception:
                    if test data exists on the VM
    """
    log = logger.get_log()
    if not timestamp:
        timestamp = vm.hvobj.timestamp

    log.info("Performing No test data validation")
    for drive in vm.drive_list.values():
        # Timestamp is stored in hypervisor object during copying to each drive
        dest_path = vm.machine.join_path(drive, folder_name, "TestData", timestamp)
        if vm.machine.check_directory_exists(dest_path):
            raise Exception("Test data exists on the VM when it should not be present")
    log.info("Validation completed successfully")


def cleanup_test_data(vm, folder_name="Dummy", timestamp=None):
    """Cleans up the test data on the VM object
        Args:
            vm: VM object of the VM on which the data is to be checked
            folder_name (str): The name of the folder to clean data from
            timestamp (int or str): The epoch time for uniquely identifying testdata
        Returns:
        Raises:
                Exception:
                    if test data cleanup fails
    """
    log = logger.get_log()
    controller = Machine(socket.gethostbyname_ex(socket.gethostname())[2][0])

    # Get timestamp from hvobj, if not passed as argument
    if not timestamp:
        timestamp = vm.hvobj.timestamp

    log.info("Performing test data cleanup on VM")
    try:
        for drive in vm.drive_list.values():
            testdata_path = vm.machine.join_path(drive, folder_name, "TestData", timestamp)
            if vm.machine.check_directory_exists(testdata_path):
                log.info(f'Cleaning up %s', testdata_path)
                vm.machine.remove_directory(testdata_path)
            else:
                log.info(f"Test data doesn't exist on VM at %s", testdata_path)
    except Exception as exp:
        log.exception(f"Failed to cleanup testdata on VM: %s", str(exp))
    log.info("Performing test data cleanup on controller")
    try:
        local_testdata_path = get_testdata_path(controller, timestamp=timestamp, create_folder=False)
        if controller.check_directory_exists(local_testdata_path):
            controller.remove_directory(local_testdata_path)
    except Exception as exp:
        log.exception(f"Failed to cleanup testdata on controller: %s", str(exp))
    log.info('Cleanup completed successfully')


def wait_for_timer(end_time=60, start_time=0):
    """
    Timer for making job/process wait
    Args:

        end_time                    (int):  wait time

        start_time                  (int): current time

    Returns:

    """
    log = logger.get_log()
    diff_time = end_time - start_time
    log.info("Waiting for {} Seconds".format(diff_time))
    time.sleep(diff_time)
    return True


def find_log_lines(cs, client_name, log_file, search_term, job_id=None):
    """
    Finds if the search term is in the log files

    Args:
        cs                                  (object):   Commcell object

        client_name                         (string):   client name

        log_file                            (string):   Name of the log file

        search_term                         (string):   String needed to be searched

        job_id                              (int):      job id to be searched on

    Returns:
                                            (bool):     True if found else False

                                            (str):      Log line containing the search term
    """
    try:
        from cvpysdk.client import Client
        log = logger.get_log()
        _machine = Machine(machine_name=client_name,
                           commcell_object=cs)
        _client = Client(cs, client_name)
        log_directory = _client.log_directory
        log.info('Navigate to the {} Log Files directory to read {} log'.format(client_name, log_file))
        _log = _machine.join_path(log_directory, log_file)
        log_line = _machine.read_file(_log, search_term=job_id)
        list_of_lines = log_line.split("\n")
        log.info('Looking for the log line that contains: {}'.format(search_term))
        for line in list_of_lines:
            if search_term.lower() \
                    in line.lower():
                log.info("Found {} in: {}".format(search_term, line))
                return True, line
        return False, ''
    except Exception as exp:
        logger.get_log().error('Error occurred during reading log files: {} '.format(str(exp)))


def create_adminconsole_object(testcase_obj, is_destination_client=False):
    """
    Creates an AdminConsoleVirtualServer object for conversion restore and returns it.

    Args:
        testcase_obj      (Object): A testcase object.

        is_destination_client      (bool): Whether the object getting created for a destination client
                                            in a conversion restore

    Returns:
         admin_console_obj  (Object): An object of AdminConsoleVirtualServer.

    Raises:
        Exceptions:
            If an AdminConsoleVirtualServer object could not be created.

        Unexpected Behaviours:
            If the destination object is created before the source object.
    """
    log = logger.get_log()

    try:
        from Web.AdminConsole.Helper.VirtualServerHelper import AdminConsoleVirtualServer
        inputs = testcase_obj.tcinputs
        if is_destination_client:
            log.info("An AdminConsoleVirtualServer object is being made for the destination.")
            try:
                vcenter_client = testcase_obj.tcinputs["Destination_Virtualization_client"]
            except KeyError:
                vcenter_client = testcase_obj.tcinputs["DestinationClient"]
            dest_client = testcase_obj.commcell.clients.get(vcenter_client)
            dest_agent = dest_client.agents.get('Virtual Server')
            try:
                dest_instance = dest_agent.instances.get(testcase_obj.tcinputs['DestinationInstance'])
            except KeyError:
                instance_keys = next(iter(dest_agent.instances.all_instances))
                dest_instance = dest_agent.instances.get(instance_keys)
            backupsetkeys = next(iter(dest_instance.backupsets.all_backupsets))
            backupset = dest_instance.backupsets.get(backupsetkeys)
            sckeys = next(iter(backupset.subclients.all_subclients))
            subclient = backupset.subclients.get(sckeys)

            admin_console_obj = AdminConsoleVirtualServer(dest_instance, testcase_obj.browser, testcase_obj.commcell,
                                                          testcase_obj.csdb)
            admin_console_obj.hypervisor = vcenter_client
            admin_console_obj.instance = dest_instance.name
            admin_console_obj.subclient = subclient.name
            admin_console_obj.conversion_restore = True
            admin_console_obj.auto_vsa_subclient = destination_subclient_initialize(testcase_obj)
        else:
            log.info("An AdminConsoleVirtualServer object is being made.")
            admin_console_obj = AdminConsoleVirtualServer(testcase_obj.instance, testcase_obj.browser,
                                                          testcase_obj.commcell, testcase_obj.csdb)
            admin_console_obj.hypervisor = inputs['ClientName']
            admin_console_obj.instance = inputs['InstanceName']
            admin_console_obj.subclient = inputs['SubclientName']
            admin_console_obj.subclient_obj = testcase_obj.subclient
        admin_console_obj.testcase_obj = testcase_obj
        return admin_console_obj

    except Exception as exp:
        log.exception("An exception occurred while creating an AdminConsoleVirtualServer Object")
        raise exp

#   Following methods (get_restore_channel, get_push_install_attempt, and get_push_job_id are helpers
#   to determine whether the flag restore via cv tools is working as expected.
#   These are run during a VSA Guest File Restore.


def get_restore_channel(restore_job_id=None, destination_vm=None, dest_vm_credentials=None, commcell=None):
    """
    Checks if the restore job went through an agent.

    Args:
        restore_job_id       (str)           -- Restore job id for the guest file restore
        destination_vm      (str)           -- Destination VM for guest file restore
        dest_vm_credentials (str)           -- Credentials for the destination vm
        commcell            (object)        -- Commcell object
    Returns:
        agent_used      (boolean)           -- If the restore happened via the pushed agent.
        description     (str)               -- Description string for the logs.
    """

    # We go to clRestore.log on destination vm, if logs exist for this job, job was agent-based.

    log = logger.get_log()

    default_error_desc = 'The job did not go through a pushed agent. Please check logs for more details.'

    success_desc = 'Restore job went through a pushed agent.'

    try:
        _machine = Machine(machine_name=destination_vm,
                           commcell_object=commcell, username=dest_vm_credentials['username'], password=dest_vm_credentials['password'])

        _client = Client(commcell, destination_vm)
        log_directory = _client.log_directory

        log.info("Navigating to log files to read clRestore logs")
        jobmanager_log = _machine.join_path(log_directory, "clRestore.log")
        log_lines = _machine.read_file(jobmanager_log, search_term=restore_job_id.job_id)
        list_of_lines = log_lines.split("\n")

        if len(list_of_lines) > 0:
            return True, success_desc

        return False, default_error_desc

    except Exception as exp:
        log.info(str(exp))
        return False, str(exp)


def get_push_install_attempt(restore_job_id=None, commcell=None):
    """
    Checks if an attempt was made to push install an agent on the destination VM.

    Args:
        restore_job_id      (int)       - VSA Guest File Restore ID
        commcell            (object)    - Commcell object
    Returns:
        success             (bool)      - If a push agent job was initiated
        description         (str)       - Additional details about the job
    """

    # If attempt made, check state of child job, if not skip checking state.
    # In both cases with the push_expected flag the job channel should be agent based.

    log = logger.get_log()

    default_error_desc = 'FS Agent already present on destination. Push Job wasn\'t initiated'

    success_desc = 'FS Agent push install initiated.'

    try:
        log.info('Creating CS Machine for {}'.format(commcell.commserv_hostname))
        _machine = Machine(machine_name=commcell.commserv_hostname,
                           commcell_object=commcell)
        log.info('Creating CS Client for {}'.format(commcell.commserv_hostname))
        _client = Client(commcell, commcell.commserv_hostname)

        log_directory = _client.log_directory

        log.info("Navigating to log files to read JobManager logs. Directory-[{}]".format(log_directory))
        jobmanager_log = _machine.join_path(log_directory, "JobManager.log")
        log_lines = _machine.read_file(jobmanager_log, search_term=restore_job_id.job_id)
        list_of_lines = log_lines.split("\n")

        log.info('Checking for an attempted Push Install Job.')

        log_line_push_initiated = "Trying to push install FS agent to client".lower()

        for line in list_of_lines:
            if log_line_push_initiated in line.lower():
                log.info(success_desc)
                return True, success_desc

        log.info(default_error_desc)
        return False, default_error_desc

    except Exception as exp:
        raise Exception(str(exp))


def get_push_job_id(restore_job_id=None, csdb=None):
    """
    Gets the Job ID for a push install job initiated by a guest file restore [refer Project 1910]

    Args:
        restore_job_id      (int)              --  parent job in this case a guest file restore
        csdb                (object)           --  CSDB object

    Returns:
        install_job_id      (int | None)       --  The push-install job id | None, if can't be extracted
        error_desc          (str | None)       --  Error description if push-install job id can't be extracted | None, if successful
    """

    log = logger.get_log()

    if not restore_job_id:
        return None, 'Invalid restore_job_id passed to the function.'

    # This query checks the push-install job id for a guest file restore.
    # If the query returns no result it can be due to one of two possible reasons:
    # - The push install job wasn't initiated
    # - The restore job moved out of 'Queued' state

    log.info('Checking push install job associated with restore job {}'.format(restore_job_id))

    error_desc = 'Failed to extract push-install job id for restore job {}.' \
                 ' Either no push install job was initiated for the restore' \
                 ' or the restore job moved out of the queued state. ' \
                 'Check job logs for more information.'.format(restore_job_id.job_id)

    _push_job_query = "select data as 'InstallJobId' from JMFailureReasonMsgParam with (NOLOCK)" \
                      "where msgId = " \
                      "(select id from JMFailureReasonMsg with (NOLOCK)" \
                      "where messageId = 318769646 and jobId = {}) ".format(restore_job_id.job_id)

    try:
        csdb.execute(_push_job_query)
        _results = csdb.fetch_all_rows()

        if not _results[0][0]:
            return None, error_desc

        install_job_id = _results[0][0]

        if not install_job_id:
            return None, error_desc

        log.info('Push Install job id is {}'.format(install_job_id))
        return install_job_id, None
    except Exception as exp:
        raise Exception(str(exp))


def vcloud_df_to_disks(disk_filters=None):
    """
    Returns disk prefixes based on disk filter rules.
    Use to know which disks should be skipped.
    """

    prefix_list = []
    for rule in disk_filters["Rules"]:
        comp = rule.split("-")
        for i in range(int(comp[-2]), int(comp[-1])+1):
            prefix_list.append(f"{comp[0]}{comp[1]}-{i}")

    return prefix_list


def vcloud_df_to_rules(disk_filters=None):
    """
    Converts encoded disk filter string to Rules
        disk_filters    (list(str)) --      [ 'scsi-X-Y-Z' ]
    """
    rule_list = []
    rule_dict = {}
    for rule in disk_filters["Rules"]:
        controller, bus, start, end = rule.split("-")
        rule_list.append({
            "filter_type": "Bus type",
            "props": [
                ["Controller", "dropdown", f"{controller.upper()} Controller ({bus})"],
                ["Enter disk starting number", "text", f"{start}"],
                ["Enter disk ending number", "text", f"{end}"]
            ]
        })

    rule_dict.update({"Rules": rule_list})
    return rule_dict


def get_stored_disks(vm_guid=None, subclient=None):
    """
    Browses VM to get a sanitised list of disk names for attach disk restore

    Args:
        vm_guid     (str)           --      GUID for the VM
        subclient   (obj)           --      Subclient object containing the VM backups.

    Returns:
        vm_disks    (list(str))     --      List of disk names for the VM
    """
    vm_guid = vm_guid.split(":")[-1]  # extract sanitised VM GUID for browse
    vm_disks, _ = subclient.disk_level_browse(vm_path="\\" + vm_guid)
    disk_prefix = ['scsi', 'lsi', 'ide']  # Add prefixes here

    for index, disk in enumerate(vm_disks):
        for prefix in disk_prefix:
            vm_disks[index] = disk.split("\\")[-1][len(prefix) + 5:]  # +5 to account for -<busnumber>-<unitnumber>- add regex later

    return vm_disks

def vcloud_bridge_vm(hvobj, vcloud_vm):
    """
    Utilise this function from the VirtualServerHelper to inject the use of VMware SDK calls. 
    Added initially to allow delete_disks() for vCloud attach disk restores.
    Args:
        hvobj       (VcloudAdminConsole) -       Object which hosts the VM and vCenters.
        vcloud_vm   (VcloudVM)           -       Source VM object hosted on vCloud.
    """
    from VirtualServer.VSAUtils.VMHelpers.VmwareVM import VmwareVM

    vc_client_name = [vc[1] for vc in hvobj.associated_vcenters if vcloud_vm.vcenter_host in vc[1]][0]

    dest_client_obj = hvobj._create_hypervisor_object(vc_client_name)[0]
    return VmwareVM(dest_client_obj, vcloud_vm.vcenter_vm)



