# -*- coding: utf-8 -*-
# pylint: disable=W1202

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for performing disaster recovery validations.

DRValidator is the only class defined in this file

DRValidator:

    __init__(test_object)                                       --  initialize instance of the DRValidator class.

    validate()                                                  --  entry point for validation

    trigger_dr_full_or_diff_job()                               --  Triggers full or differential dr jobs

    full_dr_job_hash_comparison()                               --  compares hash values of source and destination
                                                                    full dumps

    diff_dr_job_hash_comparison()                               --  compares hash values of source and destination
                                                                    diff dumps

    set_destination_path_based_on_tcinputs()                    --  sets destination path based on tcinputs

    validate_job_type()                                         --  validates job type.

    guid_of_the_commcell()                                      --  gets the guid of the commcell

    validate_dr_backup_metadata()                               --  Validates full and differential set folders by
                                                                    comparing the hash values of set folder with
                                                                    staging folder.

    validate_commserve_recovery()                               --  validates cs recovery with full and
                                                                    differential dumps.


    validate_dr_metadata_restore()                              --  validates dr restore jobs by comparing the hash
                                                                    values of restored folders with set folder

    validate_set_folder_pruning()                               --  validates set folder pruning scenario.

    validate_db_compress()                                      --  validates db compress scenario

    _get_folder_or_file_names()                                 --  gets the file names in a folder

    validate_client_logs()                                      --  checks the existence of log files

    _wait_for_job_completion()                                  --  waits for the completion of the job.

    validate_drbackup_qcommands()                               --  validates dr backup qcommands

    validate_multiple_dr_jobs_initiation()                      --  validates multiple dr jobs initiation sceanrios.
"""

import os
import time
from cvpysdk.commcell import Commcell
from cvpysdk.job import Job
from datetime import datetime
from AutomationUtils import logger, constants
from AutomationUtils.options_selector import OptionsSelector
from Server.DisasterRecovery.drhelper import DRHelper
from AutomationUtils.options_selector import CVEntities
from AutomationUtils.wrapper7z import Wrapper7Z
from AutomationUtils.machine import Machine
from Server.DisasterRecovery.drmanagement_helper import DRCommvaultCloudManagement


class DRValidator(object):
    """DRValidator helper class to perform DR validations"""

    def __init__(self, test_object, cvcloud_cs=None, cvcloud_username=None, cvcloud_password=None):
        """
        Initialize instance of the DRValidator class.

            Args:
                test_object     (object)            --      instance of testcase.

                cvcloud_cs          (str)           --      hostname of the cloudcs

                cvcloud_username    (str)           --      username of the cloudcs

                cvcloud_password     (str)          --      password of the cloudcs

            Note: cvcloud_cs, cvcloud_username and cvcloud_password are required for downloading dumps from cvcloud.
        """
        self.log = logger.get_log()
        self.test_object = test_object
        self._commcell = test_object.commcell
        self._csdb = test_object.csdb
        self._tcinputs = test_object.tcinputs
        self.utility = OptionsSelector(self._commcell)
        self.dr_helper = DRHelper(self._commcell)
        if cvcloud_cs and cvcloud_username and cvcloud_password:
            self.cv_cloud_helper = DRCommvaultCloudManagement(Commcell(webconsole_hostname=cvcloud_cs,
                                                                       commcell_username=cvcloud_username,
                                                                       commcell_password=cvcloud_password))
        self.management = self.dr_helper.management
        self.entities = CVEntities(self._commcell)
        self.fulldrjob = None
        self.diffdrjob = None
        self.dr_helper.delete_dr_folders(self.dr_helper.client_machine)
        if self._tcinputs.get('UncPath', False):
            host_name = self._tcinputs['UncPath'].split('\\')[2]
            self.dr_helper.delete_dr_folders(Machine(host_name,
                                                     username=self._tcinputs['UncUser'],
                                                     password=self._tcinputs['UncPassword']),
                                             dr_path=os.path.dirname(self._tcinputs['UncPath']))

    def validate(self, feature, **parameters):
        """
        Entry point for feature validations

            Args:
                feature        (list)      --      list of features to be validated.

                parameters      (kwargs)   --       required parameters for the corresponding validate method.

        Returns :
            None
        """
        existing_dr_policy = None
        try:
            dr_entities = self.dr_helper.dr_prerequisites()
            existing_dr_policy = self.management.dr_storage_policy
            self.management.dr_storage_policy = dr_entities['storagepolicy']
            self.dr_helper.kill_running_drjobs()
            if feature in ('dr_backup_metadata', 'commserve_recovery', 'dr_metadata_restore', 'set_folder_pruning',
                           'db_compress', 'drbackup_qcommands', 'multiple_dr_jobs_initiation'):
                getattr(self, 'validate_' + feature)(**parameters)
            else:
                raise Exception('please pass the validate feature name')
        except Exception as excp:
            self.log.error('Failed with error:%s ' % str(excp))
            self.test_object.result_string = str(excp)
            self.test_object.status = constants.FAILED
        finally:
            time.sleep(30)
            self.dr_helper.kill_running_drjobs()
            self.management.dr_storage_policy = existing_dr_policy

    def trigger_dr_full_or_diff_job(self, backup_type='full', client_list=None):
        """
        Triggers a one full dr job if backup_type = 'full' or
        Triggers one full dr job followed by one differential dr job if backup_type = 'differential'

            Args:
                 backup_type        (str)       --      type of backup

                client_list         (list)      --      list of client names.

            Returns:
                None
        """
        if backup_type in ('full', 'differential'):
            self.log.info('Triggering a Full dr backup with {0}'
                          ' as a destination path'.format(self.management.backup_metadata_folder))
            # negative testcase: If first DR job is Diff, then convert it to full
            self.fulldrjob = self.dr_helper.trigger_dr_backup(backup_type='differential', client_list=client_list)
            self.validate_job_type(self.fulldrjob, expected_type='full')
            if backup_type.lower() == 'differential':
                self.log.info('Triggering a differential dr backup with {0}'
                              ' as a destination path'.format(self.management.backup_metadata_folder))
                self.diffdrjob = self.dr_helper.trigger_dr_backup(backup_type=backup_type, client_list=client_list)
                self.validate_job_type(self.diffdrjob, expected_type=backup_type)
        else:
            raise Exception('please pass valid backup type')

    def full_dr_job_hash_comparison(self, source_path, destination_path, dumps_on_controller=False):
        """
        compares hash values of dr full dumps

            Args:
                source_path         (str)       --      source path of full dumps

                destination_path    (str)       --      destination path of full dumps

                dumps_on_controller (bool)      --      True/False

            Note:   paths can be staging path or set folder path or restored dumps
        """
        self.log.info('Performing full dumps comparison '
                      'Source = {0}, destination = {1}'.format(source_path, destination_path))
        if destination_path.startswith('\\'):
            # split machine hostname from destination path
            hostname = destination_path.split('\\')[2]
            self.log.info('Destination path is UNC path, hostname = {0}'.format(hostname))
            destination_machine = Machine(hostname,
                                          username=self._tcinputs['UncUser'],
                                          password=self._tcinputs['UncPassword'])
        elif dumps_on_controller:
            destination_machine = Machine()
        else:
            destination_machine = self.dr_helper.client_machine
        self.log.info('destination machine = {0}'.format(destination_machine.machine_name))
        return self.dr_helper.client_machine.compare_folders(
            destination_machine,
            source_path,
            destination_path)

    def diff_dr_job_hash_comparison(self, full_dump_source_path, diff_dump_source_path, destination_path):
        """
        compares hash values of dr differential dumps

            Args:
                full_dump_source_path         (str)       --      source path of full dumps

                diff_dump_source_path         (str)       --      source path of differential dumps

                destination_path              (str)       --      destination path of full and differential dumps

            Note:   destination path should have both full and diff dumps.
        """
        self.log.info('Performing full and diff dumps comparsion'
                      ' full_dump_source_path = {0}, diff_dump_source_path = {1},'
                      ' destination_path = {2}'.format(full_dump_source_path,
                                                       diff_dump_source_path,
                                                       destination_path))
        if destination_path.startswith('\\'):
            # split machine hostname from destination path
            hostname = destination_path.split('\\')[2]
            self.log.info('Destination path is UNC path, hostname = {0}'.format(hostname))
            destination_machine = Machine(hostname, username=self._tcinputs['UncUser'],
                                          password=self._tcinputs['UncPassword'])
        else:
            destination_machine = self.dr_helper.client_machine
        self.log.info('destination machine = {0}'.format(destination_machine.machine_name))

        full_hash = self.dr_helper.client_machine.get_folder_hash(full_dump_source_path)
        diff_hash = self.dr_helper.client_machine.get_folder_hash(diff_dump_source_path)
        set_folder_hash = destination_machine.get_folder_hash(destination_path)
        diff_list = (full_hash | diff_hash) - set_folder_hash
        return diff_list

    def set_destination_path(self, clean_up=False):
        """
        sets the destination path based on tcinputs

            Args:
                clean_up        (bool)      --          deletes the content present in UNC directory.

            Returns:
                None
            Raise:
                Exception:
                    if failed to clean up the directory.
        """
        current_time = time.strftime('%Y%m%d%H%M%S')
        uncPath = nfsServer = local_set_path = None
        uncUser = uncPass = nfsShare = None
        if self._tcinputs.get('UncPath') and self._tcinputs.get('UncUser') and self._tcinputs.get('UncPassword'):
            uncPath, uncUser, uncPass = (self._tcinputs.get('UncPath') + "__" + current_time,
                                         self._tcinputs.get('UncUser'),
                                         self._tcinputs.get('UncPassword'))

        elif self._tcinputs.get('NfsServer') and self._tcinputs.get('NfsShare'):
            nfsServer, nfsShare = self._tcinputs.get('NfsServer') or None, self._tcinputs.get('NfsShare')
        else:
            local_set_path = self.dr_helper.generate_path(self.dr_helper.client_machine, alias='local_path')

        if self.dr_helper.client_machine.os_info == "WINDOWS":
            if uncPath:
                if clean_up:
                    self.log.info('Cleaning up the directory {0}'.format(self._tcinputs.get('UncPath')))
                    try:
                        self.dr_helper.client_machine.remove_directory(self._tcinputs.get('UncPath'),
                                                                       username=uncUser,
                                                                       password=uncPass)
                    except Exception as excp:
                        self.log.error('ignore : {0}'.format(excp))
                self.management.set_network_dr_path(path=uncPath, username=uncUser, password=uncPass)
            else:
                self.management.set_local_dr_path(path=local_set_path)

        elif self.dr_helper.client_machine.os_info == "UNIX":
            if uncPath:  # mount cifs share
                local_set_path = "/Mount/cifs/" + "local_path_{}".format(current_time)
                local_set_path = self.dr_helper.client_machine.mount_network_path(network_path=uncPath,
                                                                                  username=uncUser,
                                                                                  password=uncPass,
                                                                                  cifs_client_mount_dir=local_set_path)
            elif nfsServer:  # mount nfs share
                local_set_path = "/Mount/nfsshare/" + "local_path_{}".format(current_time)
                self.dr_helper.client_machine.mount_nfs_share(nfs_client_mount_dir=local_set_path, server=nfsServer,
                                                              share=nfsShare, cleanup=clean_up)
            self.management.set_local_dr_path(path=local_set_path)

    def guid_of_the_commcell(self):
        """
        gets the guid of the commcell.

            Returns:
                (str)           --      hexadecimal id of the commcell.
        """

        _, result = self.utility.exec_commserv_query('SELECT csGUID '
                                                     'FROM APP_COMMCELL WHERE clientId=2')

        return result[0][0]

    def validate_job_type(self, job_object, expected_type='full', hardcheck=True):
        """
        validates job type(full/differential)

            Args:
                job_object      (object)        --         job object

                expected_type   (str)           --          expected type of the job

                    'full'
                    'differential'

                hardcheck       (bool)          --          True/False

                    if job type doesn't match with expected type and hardcheck is true
                        raises exception
                    if job type doesn't match with expected type and hardcheck is false
                        returns false
            Returns:
                bool
            Raises:
                Exception:
                    when job type doesn't match
        """
        if expected_type in ('full', 'differential'):
            backuplevel = job_object.backup_level
            if backuplevel.lower() != expected_type.lower():
                if hardcheck:
                    error = "DR backup job type is not {0} ," \
                            " please check the type job id {1}," \
                            " current job type is {2}".format(expected_type, str(job_object), backuplevel)
                    self.log.error(error)
                    raise Exception(error)
                return False
            self.log.info('Validated dr job type = {0}'.format(expected_type))
            return True
        raise Exception('Please pass the valid job type')

    def validate_dr_backup_metadata(self, backup_type='full', client_list=None, log_names=None,
                                    upload_to_cvcloud=None, upload_to_third_party_cloud=None,
                                    er_staging_directory=None):
        """
        Validates full and differential set folders by comparing the hash values of set folder with staging folder.

        Below scenarios are handled:
            Set folder with full dumps compared with staging folder.
            Set folder with full and differential dumps compared with staging folder.

        Note:  Based on the tcinputs, set folder destination path will be set.

            Args:

                backup_type (str)   -      type of backup to be triggered.

                    "full"
                    "differential"

                client_list     (list)  -   list of clients to be set.

                log_names       (list)  -   list of log names to be set

                upload_to_cvcloud   (dict)  -   credentials to enable upload to cvcloud option.

                    {
                        "CloudUserName": "",
                        "CloudPassword": "",
                        "CompanyName": "",
                        "DestinationPath": ""
                    }

                upload_to_third_party_cloud     (dict)   -   required key/value pairs to enable the option
                                                             upload to third party cloud and to download dumps fom that
                                                             cloud.

                    {
                        "VendorName": "",
                        "CloudLibraryName": "",
                        "LoginName": "",
                        "Password": "",
                        "MountPath": ""
                    }

                er_staging_directory            (str)   -   path of ERStaging directory

            Returns:
                None

        """
        self.set_destination_path()
        self.log.info('Validating scenario backup type = {0}'
                      ' and path = {1}'.format(backup_type, self.management.backup_metadata_folder))
        if er_staging_directory:
            self.log.info('Setting the additional setting {0} = {1}'.format('ERStagingDirectory',
                                                                            er_staging_directory))
            self._commcell.add_additional_setting(category='CommServe', key_name='ERStagingDirectory',
                                                  data_type='STRING', value=er_staging_directory)
        if log_names:
            self.dr_helper.management.wild_card_settings = log_names
        if upload_to_cvcloud:
            self.management.upload_metdata_to_commvault_cloud(
                flag=True,
                username=upload_to_cvcloud.get('CloudUserName'),
                password=upload_to_cvcloud.get('CloudPassword'))
        if upload_to_third_party_cloud:
            self.dr_helper.check_entity_existence(
                entity_type='library',
                entity_object=upload_to_third_party_cloud.get('CloudLibraryName'))
            self.management.upload_metdata_to_cloud_library(
                flag=True,
                libraryname=upload_to_third_party_cloud.get('CloudLibraryName'))

        self.trigger_dr_full_or_diff_job(backup_type=backup_type, client_list=client_list)
        _, result = self.utility.exec_commserv_query("select dirName, fileName_srm from {0} where jobid = {1}".format(
            "GXDRFULL", self.fulldrjob.job_id))  # pull it out
        destination_path, staging_path = result[0][0], result[0][1]
        sep = "\\"
        if self.dr_helper.client_machine.os_info.lower() == "unix":
            sep = "/"
        set_folder_name = destination_path.split(sep)[-1]

        if client_list:
            self.log.info('Validating logs {0} for clients {1}'.format(log_names, client_list))
            self.validate_client_logs(staging_path, client_list, log_names)

        if upload_to_cvcloud:
            if "DestinationPath" in upload_to_cvcloud and upload_to_cvcloud.get("DestinationPath"):
                Machine().create_directory(upload_to_cvcloud.get("DestinationPath"), force_create=True)
                destination_path = upload_to_cvcloud.get("DestinationPath")
            else:
                destination_path = (self.dr_helper.generate_path(Machine(), alias="cv_cloud") +
                                    Machine().os_sep + set_folder_name)
                Machine().create_directory(destination_path, force_create=True)

            commcell_guid = self.guid_of_the_commcell()

            companyname_companyid_commcellguid_commcellid = (
                self.cv_cloud_helper.get_companyname_companyid_commcellguid_commcellid())

            # find the company id associated with commcell guid and company name
            for index in range(len(companyname_companyid_commcellguid_commcellid)):
                if (companyname_companyid_commcellguid_commcellid[index][0] == upload_to_cvcloud.get("CompanyName") and
                        companyname_companyid_commcellguid_commcellid[index][2] == commcell_guid):
                    (self.cv_cloud_helper.company_name,
                     self.cv_cloud_helper.company_id,
                     self.cv_cloud_helper.commcell_guid,
                     _) = companyname_companyid_commcellguid_commcellid[index]
                    break

            self.log.info(f'commcell_guid {0} is associated with company {1}'.format(commcell_guid,
                                                                                     self.cv_cloud_helper.company_name))
            self.cv_cloud_helper.commcell_guid = commcell_guid

            self.cv_cloud_helper.download_from_cvcloud(set_folder_name=set_folder_name,
                                                       destination_path=destination_path)
            self.log.info('{0} folder downloaded successfully'.format(set_folder_name))
        if upload_to_third_party_cloud:
            destination_path = (self.dr_helper.generate_path(self.dr_helper.client_machine, alias="third_party_cloud") +
                                self.dr_helper.client_machine.os_sep + set_folder_name)
            self.dr_helper.client_machine.create_directory(destination_path, force_create=True)

            source_path = 'DR/{0}/{1}'.format(self._commcell.commserv_name, set_folder_name)
            self.dr_helper.download_from_third_party_cloud(
                upload_to_third_party_cloud.get('VendorName'),
                upload_to_third_party_cloud.get('LoginName'),
                upload_to_third_party_cloud.get('Password'),
                upload_to_third_party_cloud.get('MountPath'),
                source_path,
                destination_path)
            destination_path = self.dr_helper.client_machine.join_path(destination_path,
                                                                       upload_to_third_party_cloud.get('MountPath'),
                                                                       'DR', self._commcell.commserv_name,
                                                                       set_folder_name)
        self.log.info('Comparing hash values...')
        if backup_type == 'full':
            diff_list = self.full_dr_job_hash_comparison(
                staging_path, destination_path,
                dumps_on_controller=upload_to_cvcloud.get("DestinationPath") if upload_to_cvcloud else False)
        else:
            staging_full_path = self.dr_helper.client_machine.join_path(
                self.dr_helper.install_path, 'CommserveDR', 'DR_{}'.format(self.fulldrjob.job_id))

            staging_diff_path = self.dr_helper.client_machine.join_path(
                self.dr_helper.install_path, 'CommserveDR', 'DR_{}'.format(self.diffdrjob.job_id))

            diff_list = self.diff_dr_job_hash_comparison(staging_full_path, staging_diff_path, destination_path)

        self.log.info('Hash values difference list = {0}'.format(diff_list))
        for name in diff_list:
            if name[0].endswith('.dmp'):
                raise Exception('Hash values of staging folder and set folder are not equal')
        self.log.info('Hash values have been compared successfully, diff list = {0}'.format(diff_list))
        self.log.info('Successfully validated scenario backup type = {0}'
                      ' and path = {1}'.format(backup_type, self.management.backup_metadata_folder))
        if upload_to_cvcloud:
            if "DestinationPath" in upload_to_cvcloud:
                Machine().remove_directory(upload_to_cvcloud.get("DestinationPath"))
            self.management.upload_metdata_to_commvault_cloud(flag=False)
        if upload_to_third_party_cloud:
            self.management.upload_metdata_to_cloud_library(flag=False)
        if er_staging_directory:
            self.log.info('Deleting the additional setting {0}'.format('ERStagingDirectory'))
            self._commcell.delete_additional_setting(category='CommServe', key_name='ERStagingDirectory')

    def validate_commserve_recovery(self, backup_type="full"):
        """
        validates cs recovery with full and differential dumps.

        Below scenarios are handled:
            CSRecovery with Full dumps.
            CSRecovery with Full and differential dumps.

            Args:
                backup_type (str)   -      type of backup to be triggered.

                    "full"
                    "differential"

            Returns:
                None
        """
        self.set_destination_path()
        self.log.info('Validating the scenario, CSRecovery with {0} dumps'.format(backup_type))
        if backup_type in ('full', 'differential'):
            if backup_type == 'full':
                entity_properties = self.entities.create(input_entities=['disklibrary', 'storagepolicy'])
                fulldrjob = self.dr_helper.trigger_dr_backup()
                self.validate_job_type(fulldrjob)
            else:
                fulldrjob = self.dr_helper.trigger_dr_backup()
                self.validate_job_type(fulldrjob)
                entity_properties = self.entities.create(input_entities=['disklibrary', 'storagepolicy'])
                diffdrjob = self.dr_helper.trigger_dr_backup(backup_type=backup_type)
                self.validate_job_type(diffdrjob, expected_type=backup_type)
            self.log.info('Cleaning up the created entities {0}'.format(entity_properties))
            self.entities.cleanup()
            _, result = self.utility.exec_commserv_query("select dirName, fileName_srm from {0} where jobid = {1}".format(
                "GXDRFULL", fulldrjob.job_id))
            destination_path, staging_path = result[0][0], result[0][1]
            self.log.info('Launching CSRecoveryAssistant with dbdump location {0}'.format(destination_path))
            self.dr_helper.restore_db_with_csrecovery_assistant(dbdumplocation=destination_path,
                                                                operation='Recovery',
                                                                start_services_after_recovery=True)
            if self.dr_helper.client_machine.os_info == 'WINDOWS':
                self.log.info('Executing iisreset cmd on cs...')
                time.sleep(120)
                output = self.dr_helper.client_machine.execute_command('iisreset')
                self.log.info('iisreset cmd output {0}'.format(output.formatted_output))
                time.sleep(120)
            self.log.info('checking the existence of entities on th commcell {0}'.format(entity_properties))
            self.dr_helper.check_entity_existence('policy', entity_properties['storagepolicy']['object'])
            self.dr_helper.check_entity_existence('library', entity_properties['disklibrary']['object'])
            self.log.info('Recovery of CS is completed successfully')
        else:
            raise Exception('please pass valid backup type')

    def validate_dr_metadata_restore(self, backup_type='full'):
        """
        validates dr restore jobs by comparing the hash values of restored folders with set folder

        Below scenarios are handled:
            Restore of full dr backup by jobid and hash validation
            Restore of full and differential dr backups by jobid and hash validation

            Args:
                backup_type (str)   -      type of backup to be triggered.

                    values:

                    "full"
                    "differential"

            Returns:
                None
        """
        custom_restore_path = self.dr_helper.generate_path(self.dr_helper.client_machine, alias='restore_path')
        self.log.info('Validating restore by job id, Restoring dumps = {0}'.format(backup_type))
        self.set_destination_path()
        self.trigger_dr_full_or_diff_job(backup_type=backup_type)
        restore_jobs = [int(self.fulldrjob.job_id)]
        if backup_type.lower() == 'differential':
            restore_jobs.append(int(self.diffdrjob.job_id))
        self.log.info('Restoring dr jobs = {0}'.format(restore_jobs))
        # restoring to same client(CS) but different location
        restorejob_obj = self.dr_helper.dr.restore_out_of_place(self.dr_helper.csclient,
                                                                custom_restore_path,
                                                                fs_options={'index_free_restore': True},
                                                                restore_jobs=restore_jobs)
        self.dr_helper.job_manager.job = restorejob_obj
        self.dr_helper.job_manager.wait_for_state()
        self.log.info('Comparing hash values...')
        _, result = self.utility.exec_commserv_query("select dirName, fileName_srm from {0} where jobid = {1}".format(
            "GXDRFULL", self.fulldrjob.job_id))
        destination_path, staging_path = result[0][0], result[0][1]
        restore_full_path = self.dr_helper.client_machine.join_path(custom_restore_path,
                                                                    self.dr_helper.install_path.replace(':\\', '\\'),
                                                                    'CommserveDR', 'DR_' + self.fulldrjob.job_id)
        if backup_type == 'full':
            diff_list = self.full_dr_job_hash_comparison(destination_path, restore_full_path)
        else:
            restore_diff_path = self.dr_helper.client_machine.join_path(custom_restore_path,
                                                                        self.dr_helper.install_path.replace(':\\',
                                                                                                            '\\'),
                                                                        'CommserveDR', 'DR_' + self.diffdrjob.job_id)
            diff_list = self.diff_dr_job_hash_comparison(restore_full_path, restore_diff_path, destination_path)
        self.log.info('Hash values difference list = {0}'.format(diff_list))
        for name in diff_list:
            if name[0].endswith('.dmp'):
                raise Exception('Hash values of restore folder and set folder are not equal')
        self.log.info('Hash values have been compared successfully, diff list = {0}'.format(diff_list))
        self.log.info('successfully validated dr restore scenario')

    def validate_set_folder_pruning(self):
        """
        validates set folder pruning scenario.

        Below scenarios are handled:
            validates pruning for local path and unc path

        Note:  Based on the tcinputs, set folder destination path will be set.

        Returns:
            None
        """
        self.set_destination_path()
        self.log.info('Validating set folder pruning with path = {0}'.format(
            self.management.backup_metadata_folder))
        default_value = self.management.number_of_metadata
        self.management.number_of_metadata = 1
        fulljob1 = self.dr_helper.trigger_dr_backup()
        self.validate_job_type(fulljob1)
        _, result = self.utility.exec_commserv_query("select dirName, fileName_srm from {0} where jobid = {1}".format(
            "GXDRFULL", fulljob1.job_id))
        destination_path, staging_path = result[0][0], result[0][1]
        fulljob2 = self.dr_helper.trigger_dr_backup()
        self.validate_job_type(fulljob2)
        if self.dr_helper.client_machine.check_directory_exists(destination_path):
            raise Exception("Set folder didn't pruned successfully")
        self.log.info('Set folder pruned successfully')
        self.log.info('Applying default settings..')
        self.management.number_of_metadata = default_value
        self.log.info('Successfully validated set folder pruning')

    def validate_db_compress(self):
        """
        Validates db compress scenario.

            triggers full and differential dr jobs with compression disabled.

            triggers full and differential dr jobs with compression enabled.

            Compares sizes of above set folders to validate the scenario.

            Returns:
                None
        """
        self.set_destination_path()
        self.dr_helper.management.number_of_metadata = 2
        self.log.info("Validating db compress setting, destination path = {0}".format(
            self.management.backup_metadata_folder))
        fulljob_uncompressed = self.dr_helper.trigger_dr_backup(backup_type='full', compression=False)
        self.dr_helper.trigger_dr_backup(backup_type='differential', compression=False)
        _, uncompressed_result = self.utility.exec_commserv_query(
            "select dirName, fileName_srm from {0} where jobid = {1}".format(
                "GXDRFULL", fulljob_uncompressed.job_id))
        uncompressed_folder_path = uncompressed_result[0][0]
        fulljob_compressed = self.dr_helper.trigger_dr_backup(backup_type='full', compression=True)
        self.dr_helper.trigger_dr_backup(backup_type='differential', compression=True)
        _, compressed_result = self.utility.exec_commserv_query(
            "select dirName, fileName_srm from {0} where jobid = {1}".format(
                "GXDRFULL", fulljob_compressed.job_id))
        compressed_folder_path = compressed_result[0][0]
        compressed_folder_size = self.dr_helper.client_machine.get_folder_size(compressed_folder_path)
        uncompressed_folder_size = self.dr_helper.client_machine.get_folder_size(uncompressed_folder_path)
        if compressed_folder_size >= uncompressed_folder_size:
            raise Exception('Compressed folder size {0} is greater than uncompressed folder size {1}'.format(
                compressed_folder_size, uncompressed_folder_size))
        else:
            self.log.info('Compressed folder size = {0} and uncompressed folder size = {1}'.format(
                compressed_folder_size, uncompressed_folder_size))
        self.log.info('Successfully validated db compress scenario')
        self.log.info('Successfully validated set folder pruning')

    def _get_folder_or_file_names(self, path):
        """
        gets the file names in given directory

            Args:
                 path   (str)   -   directory path

            Returns:
                list    -       list of file names
        """
        self.log.info('getting the file names from directory {0}'.format(path))
        output = self.dr_helper.client_machine.get_folder_or_file_names(path.replace(' ', "' '"), filesonly=True)
        return ' '.join(output.splitlines()).split()[2:]

    def validate_client_logs(self, destination_path, client_list, log_file_names=None):
        """
        Validates the existence of the log files in destination path.

            Args:

                destination_path    (str)   -   path of the archive folder

                client_list         (list)  -   list of client names

                log_file_names      (list)  -   list of log names to be checked.

            Returns:
                None

            Raises:
                Exception:
                    if logs are not found.
        """
        self.log.info('Checking the existence of log files {0}  for clients {1}'.format(log_file_names, client_list))
        if not log_file_names:
            log_file_names = self.management.wild_card_settings
        set_folder_list = self._get_folder_or_file_names(destination_path)
        found_7z = False
        for file in set_folder_list:
            if file.lower().endswith('.7z'):
                found_7z = True
                zipobject = Wrapper7Z(self._commcell, self.dr_helper.csclient,
                                      self.log, zipfilepath=os.path.join(destination_path, file))
                temp_path = self.dr_helper.generate_path(self.dr_helper.client_machine, alias='temp_path')
                self.log.info('Extracting archive {0}'.format(file))
                zipobject.extract(dest=temp_path)
                sendlog_folder_list = self._get_folder_or_file_names(temp_path)
                for client_name in client_list:
                    if client_name.lower() + '.7z' in sendlog_folder_list:
                        client_zip_object = Wrapper7Z(
                            self._commcell, self.dr_helper.csclient, self.log,
                            zipfilepath=os.path.join(temp_path, client_name.lower() + '.7z'))
                        self.log.info('Extracting archive {0}.7z'.format(client_name))
                        client_zip_object.extract()
                        clientlog_folder_list = self._get_folder_or_file_names(
                            os.path.join(temp_path, client_name.lower()))
                        clientlog_folder_list = [x.lower() for x in clientlog_folder_list]
                        for log_name in log_file_names:
                            if log_name.lower() + '.log' not in clientlog_folder_list:
                                raise Exception("Log {0} not found in zip folder for client {1}".format(
                                    log_name, client_name))
                            self.log.info('for client {1}, {0} log found in archive'.format(log_name, client_name))
                    else:
                        raise Exception('client = {0}, 7z is not found in archive'.format(client_name))
        if not found_7z:
            raise Exception('sendlogs_xxxx not found in staging folder')
        self.log.info('Successfully validated client logs...')

    def _wait_for_job_completion(self, job_id, time_limit=60):
        """
        waits for the completion of the job

        Args:
            job_id      (int/str)   --      job id

            time_limit      (int)   --      wait time for the completion of job(minutes)

        Returns:
            job object
        """
        dr_job = Job(self._commcell, job_id=job_id)
        self.log.info('Dr job is triggered with id = {0}'.format(dr_job.job_id))
        self.dr_helper.job_manager.job = dr_job
        self.dr_helper.job_manager.wait_for_state(expected_state=['completed'],
                                                  retry_interval=120, time_limit=time_limit)
        return dr_job

    def validate_drbackup_qcommands(self, backup_type='full'):
        """
        validates dr backup full and differential qcommands.

            Args:
                backup_type         (full)  --     type of backup job to be triggered.

            Returns:
                None

            Raises:
                Exception:
                    if invalid backup_type is passed.
                    if hash values are not same.
        """
        self.set_destination_path()
        if backup_type.lower() in ('full', 'differential'):
            self.log.info('validating dr backup qcommand scenario {0}'.format(backup_type))
            response = self._commcell.execute_qcommand(command='qoperation drbackup -t Q_FULL')
            self.fulldrjob = self._wait_for_job_completion(job_id=int(response.text), time_limit=300)
            self.validate_job_type(self.fulldrjob)
            if backup_type.lower() == 'differential':
                response = self._commcell.execute_qcommand(command='qoperation drbackup -t Q_DIFF')
                self.diffdrjob = self._wait_for_job_completion(job_id=int(response.text), time_limit=300)
                self.validate_job_type(self.diffdrjob, expected_type='differential')
            _, result = self.utility.exec_commserv_query("select dirName, fileName_srm from {0} where jobid = {1}".format(
                "GXDRFULL", self.fulldrjob.job_id))  # pull it out
            destination_path, staging_path = result[0][0], result[0][1]
            self.log.info('Comparing hash values...')
            if backup_type == 'full':
                diff_list = self.full_dr_job_hash_comparison(staging_path, destination_path)
            else:
                staging_full_path = self.dr_helper.client_machine.join_path(self.dr_helper.install_path, 'CommserveDR',
                                                                            'DR_{}'.format(self.fulldrjob.job_id))
                staging_diff_path = self.dr_helper.client_machine.join_path(self.dr_helper.install_path, 'CommserveDR',
                                                                            'DR_{}'.format(self.diffdrjob.job_id))
                diff_list = self.diff_dr_job_hash_comparison(staging_full_path, staging_diff_path, destination_path)
            self.log.info('Hash values difference list = {0}'.format(diff_list))
            for name in diff_list:
                if name[0].endswith('.dmp'):
                    raise Exception('Hash values of staging folder and set folder are not equal')
            self.log.info('Hash values have been compared successfully, diff list = {0}'.format(diff_list))
        else:
            raise Exception('please pass valid backup type')

    def validate_multiple_dr_jobs_initiation(self, backup_types, scenario='full'):
        """
        validates multiple job initiation.

            Args:
                backup_types            (list)  --  list of job types need to be triggered.

                NOTE as of now two major combinations are handled as follows.

                    ['full', 'full', 'full', 'differential', 'full', 'differential']

                    ['differential, 'differential', 'differential', 'full', 'full', 'differential']

                scenario                (str)   --  type of scenario to be validated.

            Returns:
                None

            Raise:
                Exception:
                    if status of job is not matched
        """
        self.set_destination_path()
        self.log.info('validating scenario {0}, sequence of jobs need to triggered {1}'.format(scenario, backup_types))
        if scenario == 'differential':
            self.dr_helper.trigger_dr_backup()
        job_objects = []
        if isinstance(backup_types, list):
            for backup_type in backup_types:
                job_obj = self.dr_helper.trigger_dr_backup(backup_type=backup_type, wait_for_completion=False)
                job_objects.append(job_obj)
                if len(job_objects) in (3, 5, 6):
                    time.sleep(20)
                    if job_obj.status.lower() != 'failed to start':
                        raise Exception('{0} job is not in expected state {1},'
                                        ' it is in {2} state'.format(job_obj, 'failed to start', job_obj.status))
            while job_objects[3].status.lower() not in ('completed', 'completed w/ one or more errors',
                                                        'failed'):
                self.log.info('Status of jobs {0} = {1}, {2} = {3}, {4} = {5}'.format(
                    job_objects[0].job_id, job_objects[0].status,
                    job_objects[1].job_id, job_objects[1].status,
                    job_objects[3].job_id, job_objects[3].status))
                time.sleep(300)
            self.log.info('Multiple dr jobs initiation is validated successfully')
        else:
            raise Exception('please pass the valid parameter type')
