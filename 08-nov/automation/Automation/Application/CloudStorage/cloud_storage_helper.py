# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing common cloud Storage operations

CloudStorageHelper is the only class defined in this file.

CloudStorageHelper: Helper class to perform common cloud Storage operations

CloudStorageHelper :

    __init__()                                      --      initializes Cloud Storage helper object

    cloud_apps_backup()                             --      method to perform cloudapps
                                                            backup operations

    cloud_apps_restore()                            --      method to perform
                                                            cloudapps restore operations

    restore_validation()                            --      method to perform folder
                                                            comparison and restore
    validation

    cleanup()                                       --      method to delete the test directories

    cross_cloud_restore_with_configured_instance()  --      method to perform cross cloud
                                                            restore with configured instance

    restore_to_file_system()                        --      restore to local file system
                                                            and validation

"""
import socket
import time
from AutomationUtils.machine import Machine
from AutomationUtils.idautils import CommonUtils
from AutomationUtils import constants


class CloudStorageHelper(object):
    """Helper class to perform cloud storage operations"""

    def __init__(self, testcase_object):
        """Initializes cloud storage helper object"""
        self.commcell = testcase_object.commcell
        self.automation_directory = constants.AUTOMATION_DIRECTORY
        self.log = testcase_object.log
        self.commonutils = CommonUtils(testcase_object.commcell)
        self.controller_object = Machine(socket.gethostname())

    def cloud_apps_backup(self, subclient, backup_type):
        """Performs the backup operations on specified cloud apps subclient.

        Args :

            subclient      (obj)    --      subclient object on which the backup needs to be run

            backup_type    (str)    --      level of backup to run
                                            Full / Incremental / Synthetic_full

        Raises :
            Exception :
                if the backup operation fails

                if the backup validation fails

        """

        backup_job = subclient.backup(backup_level=backup_type.lower())
        if backup_job.wait_for_completion() is False:
            raise Exception("Failure occurred during the {} job".format(backup_type))
        self.log.info("Validating the %s backup", backup_type)
        if backup_type.lower() == 'synthetic_full':
            backup_type = 'Synthetic Full'
        return_code = self.commonutils.backup_validation(backup_job.job_id, backup_type)
        if return_code is False:
            self.log.info("%s backup validation failed", backup_type)
            raise Exception("{} backup validation failed".format(backup_type))
        else:
            self.log.info("%s backup validation successful", backup_type)

    def cloud_apps_restore(self,
                           subclient,
                           restore_type,
                           proxy_based=False,
                           overwrite=True,
                           destination_client_name=None,
                           destination_path=None,
                           destination_instance_name=None,
                           proxy_based_credentials=None):
        """Performs the restore operations on cloud apps subclient.

        Args :
            subclient                   (obj)           --        subclient object on which the
                                                                  restore needs to be run

            restore_type                (str)           --        type of restore that needs to be performed
                                                                  values for restore_type:in_place,
                                                                  out_of_place, fs_restore

            proxy_based                 (bool)          --        is out_of_place is proxy based or not

            overwrite                   (bool)          --        unconditional overwrite files during restore
                                                                  default: True

            destination_client_name     (str)           --        name of the destination client

            destination_path            (str)           --        path on the destination client

            destionation_instance_name  (str)           --        name of the destination instance

            proxy_based_credentials     (dict(dict))    --        dict of dict representing
                                                                  cross cloud credentials

            Sample dict(dict) :

            {
                'google_cloud': {
                                    'google_host_url':'storage.googleapis.com',
                                    'google_access_key':'xxxxxx',
                                    'google_secret_key':'yyyyyy'
                                }
            }

            {   'amazon_s3':    {
                                    's3_host_url':'s3.amazonaws.com',
                                    's3_access_key':'xxxxxx',
                                    's3_secret_key':'yyyyyy'
                                }
            }
            {
                'azure_blob':   {
                                    'azure_host_url':'blob.core.windows.net',
                                    'azure_account_name':'xxxxxx',
                                    'azure_access_key':'yyyyyy'
                                }
            }

        Return :

            (object)    -   object of restore job

        Raises :
            Exception :
                if unsupported restore type is mentioned

                if the restore operation fails

        """
        supported_restore_types = ["in_place", "out_of_place", "fs_restore"]
        if restore_type.lower() not in supported_restore_types:
            raise Exception("Unsupported restore type")
        if restore_type.lower() == "in_place":
            restore_job = subclient.restore_in_place(paths=subclient.content, overwrite=overwrite)
            self.log.info('Started in place restore with job id: "%s"',
                          str(restore_job.job_id))
        elif restore_type.lower() == "out_of_place":
            if not proxy_based:
                self.log.info("inside out of place restore")
                restore_job = subclient.restore_out_of_place(paths=subclient.content,
                                                             destination_client=destination_client_name,
                                                             destination_instance_name=destination_instance_name,
                                                             destination_path=destination_path,
                                                             overwrite=overwrite)
            else:
                self.log.info("Proxy based out of place restore")
                restore_job = subclient.restore_using_proxy(paths=subclient.content,
                                                            destination_client_proxy=destination_client_name,
                                                            destination_path=destination_path,
                                                            destination_cloud=proxy_based_credentials,
                                                            overwrite=overwrite)

        elif restore_type.lower() == "fs_restore":
            restore_job = subclient.restore_to_fs(
                subclient.content,
                destination_path,
                destination_client_name)
        if not restore_job.wait_for_completion():
            raise Exception(
                "Failed to run {0} restore job with error: {1}".format(restore_type,
                                                                       restore_job.delay_reason))
        self.log.info("Successfully finished %s restore", restore_job.job_id)
        return restore_job

    def restore_validation(self,
                           controller_obj,
                           original_contents,
                           restored_contents,
                           restore_type):
        """Performs folder comparison and validates the restore.

        Args :
            controller_obj      (obj)    --    object of the controller machine

            original_contents   (str)    --    contents downloaded before restore

            restored_contents   (str)    --    contents downloaded after restore

            restore_type        (str)    --    type of restore that was performed
                values for restore_type :    in_place, out_of_place, fs_restore

        Raises :
            Exception :
                if the folder comparison fails

        """

        if restore_type == 'fs_restore':
            self.log.info("inside validation")
            result = controller_obj.compare_folders(
                controller_obj,
                controller_obj.join_path(self.automation_directory, original_contents),
                restored_contents)
        else:
            result = self.controller_object.compare_folders(
                controller_obj,
                self.controller_object.join_path(self.automation_directory, original_contents),
                self.controller_object.join_path(self.automation_directory, restored_contents))
        if not result:
            self.log.info("restore validated successfully")
        else:
            raise Exception("restore validation unsuccessful")


    def cross_cloud_restore_with_configured_instance(self,
                                                     subclient,
                                                     destination_client_name,
                                                     destination_instance_name,
                                                     destination_path):
        """
        Method to perform cross cloud restore using configured instance

        Args:
            subclient                       (obj)       --      subclient object on which
                                                                the restore needs to be run

            destination_client_name         (str)       --      name of pseudoclient of cross cloud

            destination_instance_name       (str)       --      name of cross cloud instance in commcell

            destination_path                (str)       --      path in cross cloud for restore

        Raises:
            Exception
                if client doesn't exists

                if instance doesn't exists

                if it fails to launch restore job

        """
        client_object = self.commcell.clients.get(destination_client_name)
        agent_object = client_object.agents.get('cloud apps')
        instance_status = agent_object.instances.has_instance(destination_instance_name)
        if not instance_status:
            raise Exception("Given Cross Cloud Instance doesn't exists")

        self.cloud_apps_restore(subclient=subclient,
                                restore_type="out_of_place",
                                destination_client_name=destination_client_name,
                                destination_path=destination_path,
                                destination_instance_name=destination_instance_name)

    def restore_to_file_system(self,
                               subclient,
                               destination_client_name,
                               original_path):
        """
        To restore to local file system and validate the restore

        Args:

            subclient                       (obj)     --    subclient object

            destination_client_name         (str)     --    name of destination client machine

            original_path                   (str)     --    path on controller machine having
                                                            original data downloaded

        Raises
            Exception
                if restore validation fails

        """
        self.log.info("inside file system restore method")
        destination_object = self.commcell.clients.get(destination_client_name)
        destination_machine_object = Machine(destination_object)
        cv_home_path = destination_object.install_directory
        remote_path = destination_machine_object.join_path(cv_home_path,
                                                           "fs_contents")
        destination_machine_object.create_directory(remote_path,
                                                    force_create=True)

        # Restore to Local File System
        self.cloud_apps_restore(subclient=subclient,
                                restore_type='fs_restore',
                                destination_client_name=destination_client_name,
                                destination_path=remote_path)

        original_on_remote = destination_machine_object.join_path(cv_home_path, "original_contents")
        destination_machine_object.create_directory(original_on_remote, force_create=True)

        # copy original contents folder to remote machine for comparison
        # self.controller_object.copy_from_local(original_path, original_on_remote)
        original_path_1 = self.controller_object.join_path(original_path, self.controller_object.os_sep)
        # op = destination_machine_object.join_path(original_path, destination_machine_object.os_sep)
        self.log.info(original_path_1)
        self.log.info(original_on_remote)
        destination_machine_object.copy_from_local(original_path_1, original_on_remote)

        # File System Restore Validation
        self.log.info("validation for file system restore")
        restore_status = destination_machine_object.compare_folders(destination_machine_object,
                                                                    original_on_remote,
                                                                    remote_path)
        self.log.info(restore_status)

        if restore_status is False:
            raise Exception("Restore to Given destination Failed During Validation")

        self.log.info("Restore to Local File System Succeeded")
        destination_machine_object.remove_directory(remote_path)
        destination_machine_object.remove_directory(original_on_remote)

    def cleanup(self,
                machine,
                original_contents,
                inplace_contents,
                outofplace_contents,
                fs_contents):
        """Method to delete test directories as part of cleanup.

        Args :
            machine             (obj)    --    object of the machine used as client for fs restore

            original_contents   (str)    --    original contents downloaded from cloud
            before any backup or restore

            inplace_contents    (str)    --    contents downloaded after in place restore

            outofplace_contents (str)    --    contents downloaded after out of place restore

            fs_contents         (str)    --    contents downloaded as part of fs restore

        """
        if self.controller_object.check_directory_exists(original_contents) is True:
            self.controller_object.remove_directory(original_contents)
        if self.controller_object.check_directory_exists(inplace_contents) is True:
            self.controller_object.remove_directory(inplace_contents)
        if self.controller_object.check_directory_exists(outofplace_contents) is True:
            self.controller_object.remove_directory(outofplace_contents)
        if machine.check_directory_exists(fs_contents) is True:
            machine.remove_directory(fs_contents)
