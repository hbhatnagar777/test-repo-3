
'''
    To access the OVF zip file from a shared network path, copy the file, unzip and send the folder to VM_from_OVF.py

    get_args()      -   Get CLI arguments

    copy_OVF()      -   Copy the OVF zip file from the shared network path to a given destination

        source_folder       -   Location of the folder where the zipped file is present
        destination_folder  -   Location of the local path where the zipped file is to be copied
        zip_file            -   Name of the zip file in the source path

    unzip_file()    -   Unzip the zipped OVF file

        destination_folder  -   Location of the local path where the file is to be unzipped
        file_path           -   Location of the file where the file to be zipped is present
'''

import os
import shutil
import time
import zipfile
import logging
import json
from VM_from_OVF import main
from argparse import ArgumentParser
from getpass import getpass


def get_args():
    '''
        Get CLI arguments
    '''

    parser = ArgumentParser(description='Arguments for talking to cloning an OVF template')

    parser.add_argument('--commserver_host_name',
                        required=True,
                        action='store',
                        help='Host name of Commserver to connect the client to.')

    parser.add_argument('--commserver_name',
                        required=True,
                        action='store',
                        help='Name of Commserver Computer to connect the client to.')

    parser.add_argument('--commcell_user_name',
                        required=True,
                        action='store',
                        help='User name of Commcell Console.')

    parser.add_argument('--commcell_password',
                        required=False,
                        action='store',
                        default=None,
                        help='Password of Commcell Console.')

    parser.add_argument('--destination_folder_name',
                        required=True,
                        action='store',
                        help='Location of the local path where the OVF zipped file is to be copied.')

    parser.add_argument('--json_path',
                        required=True,
                        action='store',
                        help='path of json file containing the VM configuration details.')

    args = parser.parse_args()

    if not args.commcell_password:
        args.commcell_password = getpass(prompt='Enter password: ')

    return args


def copy_OVF(source_folder, destination_folder, zip_file):
    '''
        Copy the OVF zip file from the shared network path to a given destination
    '''

    if zip_file in os.listdir(source_folder) and zip_file.endswith(".zip"):
        try:
            log.info("Started copying OVF template to local path")
            shutil.copy(os.path.join(source_folder, zip_file), destination_folder)
            time.sleep(10)
            log.info("Copied ---- {} ---- to ---- {} ---- ".format(zip_file, destination_folder))
            print("Copied ---- {} ---- to ---- {} ----".format(zip_file, destination_folder))
        except Exception as e:
            log.info("Exception occurred while copying the file to destination {}".format(e))
            print("Exception occurred while copying the file to destination {}".format(e))
    else:
        log.info("{} bundle doesn\'t exist in {} ".format(zip_file, source_folder))
        raise Exception("{} bundle doesn\'t exist in {} ".format(zip_file, source_folder))


def unzip_file(destination_folder, file_path):
    '''
        Unzip the zipped OVF file
    '''

    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        log.info("Started unzipping OVF zip file locally")
        zip_ref.extractall(destination_folder)
        log.info("Finished unzipping OVF zip file locally")


log = None
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', filename="VM_from_OVF.log",
                            level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S')
log = logging.getLogger()

log.info("---------------------Initializing cloning of VM from OVF---------------------- ")

args = get_args()

# Location of the folder where the zipped file is present
source = "\\\\#####\\E$\\templates"

# Location of the local path where the zipped file is to be copied
destination = args.destination_folder_name

# Name of the zip file for backup windows VM in the source path
Bfile = "AutoBackup.zip"
# Name of the zip file for controller windows VM in the source path
Cfile = "AutoController.zip"
# Name of the zip file for backup linux VM in the source path
BLfile = "AutoBackupLinux.zip"
# Name of the zip file for controller linux VM in the source path
CLfile = "AutoControllerLinux.zip"

# json file containing the VM configuration details
json_file = args.json_path

# Opening JSON file
f = open(json_file, 'r')
log.info("Opened json file with Backup and Controller VM details")

# returns JSON object as a dictionary
data = json.load(f)

to_be_deleted = False

# Iterating through the json list
for i in data['vcenter']:

    host = i['host']
    user = i['user']
    password = i['password']
    datacenter_name = i['datacenter_name']
    resource_pool_name = i['resource_pool_name']
    datastore_name = i['datastore_name']

# Iterating through the json list
for idx, i in enumerate(data['templates']):

    log.info("Creating {}".format(i))

    VM_Name = i['VM Name']
    CPU = i['CPU']
    Cores = i['Cores']
    Memory = i['Memory']
    Hard_Disk = i['Hard disk']
    Hard_Disk_Cap = i['Hard disk Capacity']
    Network = i['Network adapter 1']
    Op_Type = i['Operating System']
    isBackupVM = i['isBackupVM']

    if str(isBackupVM) == "True" and str(Op_Type) == "Windows":
        log.info("VM {} is a Windows Backup VM".format(idx+1))
        file = Bfile
        core = 1

        if not os.path.exists(os.path.join(destination, Bfile)):
            log.info("Windows Backup VM template not already present")

            # Copy the OVF zip file
            copy_OVF(source, destination, Bfile)

            # Unzip the zipped OVF file
            unzip_file(destination, os.path.join(destination, Bfile))
            to_be_deleted = True
            break

        log.info("Windows Backup VM template already present")

    elif str(isBackupVM) == "False" and str(Op_Type) == "Windows":
        log.info("VM {} is a Windows Controller VM".format(idx+1))
        file = Cfile
        core = 3

        if not os.path.exists(os.path.join(destination, Cfile)):
            log.info("Windows Controller VM template not already present")

            # Copy the OVF zip file
            copy_OVF(source, destination, Cfile)

            # Unzip the zipped OVF file
            unzip_file(destination, os.path.join(destination, Cfile))
            to_be_deleted = True
            break

        log.info("Windows Controller VM template already present")

    elif str(isBackupVM) == "True" and str(Op_Type) == "Linux":
        log.info("VM {} is a Linux Backup VM".format(idx+1))
        file = BLfile
        core = 1

        if not os.path.exists(os.path.join(destination, BLfile)):
            log.info("Linux Backup VM template not already present")

            # Copy the OVF zip file
            copy_OVF(source, destination, BLfile)

            # Unzip the zipped OVF file
            unzip_file(destination, os.path.join(destination, BLfile))
            to_be_deleted = True
            break

        log.info("Linux Backup VM template already present")

    elif str(isBackupVM) == "False" and str(Op_Type) == "Linux":
        log.info("VM {} is a Linux Controller VM".format(idx+1))
        file = CLfile
        core = 3

        if not os.path.exists(os.path.join(destination, CLfile)):
            log.info("Linux Controller VM template not already present")

            # Copy the OVF zip file
            copy_OVF(source, destination, CLfile)

            # Unzip the zipped OVF file
            unzip_file(destination, os.path.join(destination, CLfile))
            to_be_deleted = True
            break

        log.info("Linux Controller VM template already present")

    # Call VM_from_OVF.py
    main_obj = main(destination, file, VM_Name, CPU, Cores, Memory, Hard_Disk, Network, Hard_Disk_Cap, Op_Type, idx+1,
                    isBackupVM, i, host, user, password, datacenter_name,
                    resource_pool_name, datastore_name, args.commserver_host_name,
                    args.commserver_name, args.commcell_user_name, args.commcell_password)
    main_obj.start()

    log.info("Cloned {}".format(VM_Name))

    if to_be_deleted == True:
        log.info("Deleting the templates from destination")

        if str(isBackupVM) == "True" and str(Op_Type) == "Windows":
            os.remove(os.path.join(destination, Bfile))
            os.remove(os.path.join(destination, Bfile.split(".")[0]))

        if str(isBackupVM) == "False" and str(Op_Type) == "Windows":
            os.remove(os.path.join(destination, Cfile))
            os.remove(os.path.join(destination, Cfile.split(".")[0]))

        if str(isBackupVM) == "True" and str(Op_Type) == "Linux":
            os.remove(os.path.join(destination, BLfile))
            os.remove(os.path.join(destination, BLfile.split(".")[0]))

        if str(isBackupVM) == "False" and str(Op_Type) == "Linux":
            os.remove(os.path.join(destination, CLfile))
            os.remove(os.path.join(destination, CLfile.split(".")[0]))


# Closing file
log.info("Closing json file")
f.close()

log.info("Successfully cloned all the VMs")
log.info("-------------------------------------------------------------------------------------------------")