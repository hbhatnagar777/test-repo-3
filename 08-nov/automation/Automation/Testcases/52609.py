# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  initialize TestCase class

    setup()             --  setup function of this test case

    run()               --  run function of this test case
"""
import os
import random
import time
from cvpysdk import storage
from cvpysdk.client import Client
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.windows_machine import WindowsMachine
from Server.DisasterRecovery import drhelper


class TestCase(CVTestCase):
    """Class for executing DR backup test case"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "DR Backup-Restore with local DR path"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.DISASTERRECOVERY
        self.show_to_user = True
        self.tcinputs = {
            "RestoreLocation": None
        }

    def setup(self):
        """Initializes pre-requisites for test case"""
        self._log = logger.get_log()

    def run(self):
        """Execution method for this test case"""
        try:
            self._log.info(
                "Started executing {}test case".format(str(self.id)))
            randomint = str(random.randint(100000, 9999999))
            shortsleep = 30
            full_library_name = "Full_DiskLibrary_{}".format(randomint)
            diff_library_name = "Diff_DiskLibrary_{}".format(randomint)
            full_sp = "Full_SP1_{}".format(randomint)
            diff_sp = "diff_sp1_{}".format(randomint)
            clenup_enties = {"storagepolicy": []}

            self._log.info("Create Machine class object")
            client = Client(self.commcell, self.commcell.commserv_name)
            client_machine = WindowsMachine(client.client_name, self.commcell)
            drhelperobject = drhelper.DRHelper(
                self.commcell, self._log, self.tcinputs, killdrjobs=True)
            drhelperobject.client_machine = client_machine

            if "RestoreLocation" in self.tcinputs and self.tcinputs["RestoreLocation"]:
                drrestorelocation = self.tcinputs["RestoreLocation"]
            else:
                install_path = drhelperobject.csclient.install_directory.split(os.path.sep)[
                    0]
                if not install_path.endswith(os.path.sep):
                    install_path += os.path.sep
                drrestorelocation = os.path.join(install_path, "Automation_test",
                                                 "drrestore_location")
            full_mount_path = os.path.join(
                drrestorelocation, "Full_MountPath_{}".format(randomint))
            diff_mount_path = os.path.join(
                drrestorelocation, "Diff_MountPath_{}".format(randomint))
            drobject = self.commcell.disasterrecovery
            try:
                client_machine.remove_directory(drrestorelocation)
            except Exception as err:
                self._log.info(
                    "Failed to delete Destination dir {0}".format(err))

            self._log.info("Run DR backup before creating any entities")
            drobject.backup_type = 'full'
            fulldrjob = drobject.disaster_recovery_backup()

            if not fulldrjob.wait_for_completion():
                raise Exception(
                    "Failed to run {0} backup job with error: {1}".format(
                        drobject.backup_type, fulldrjob.delay_reason
                    )
                )

            drhelperobject.drjob = fulldrjob
            drhelperobject.validate = False
            drhelperobject.validateset_folder()
            self._log.info(
                "Creating Library and Storage Policy for full DR backup")
            self._log.info(
                "Creating Library with name {}".format(full_library_name))
            mediaagent = storage.MediaAgent(self.commcell, client.client_name)
            disklibraries = storage.DiskLibraries(self.commcell)

            if not disklibraries.has_library(full_library_name):
                fulldisklibrary = disklibraries.add(
                    full_library_name, mediaagent, full_mount_path)
            else:
                fulldisklibrary = disklibraries.get(full_library_name)

            storageobj = storage.StoragePolicies(self.commcell)
            self._log.info(
                "Creating Storage Policy with name {}".format(full_sp))

            if not storageobj.has_policy(full_sp):
                full_sp = storageobj.add(
                    full_sp,
                    fulldisklibrary,
                    mediaagent,
                    retention_period=5)
            else:
                self._log.info(
                    "SP already exists, so creating SP object {}".format(full_sp))
                full_sp = storage.StoragePolicy(self.commcell, full_sp)

            clenup_enties["storagepolicy"].append(full_sp.storage_policy_name)
            self._log.info("Running FUll backup job after creating Lib/SP")
            drobject.backup_type = 'full'
            fulldrjob = drobject.disaster_recovery_backup()
            self._log.info("Full DR Job {}".format(str(fulldrjob)))

            if not fulldrjob.wait_for_completion():
                raise Exception(
                    "Failed to run {0} backup job with error: {1}".format(
                        drobject.backup_type, fulldrjob.delay_reason
                    )
                )

            fulldrjob.summary
            backuplevel = fulldrjob.backup_level

            if not backuplevel.lower().find("full") >= 0:
                error = "DR backup job type is not full , \
                please check the type job id {}, current job type is {} \
                ".format(str(fulldrjob), backuplevel)
                self._log.error(error)
                raise Exception(error)

            fulldrrestorelocation = os.path.join(drrestorelocation, "Full")
            restore_job = drobject.restore_out_of_place(
                client,
                fulldrrestorelocation,
                overwrite=True,
                restore_data_and_acl=True,
                copy_precedence=None,
                from_time=fulldrjob.start_time,
                to_time=fulldrjob.end_time,
                fs_options=None)
            self._log.info(
                "Running DR restore job {} for full backup ".format(
                    str(restore_job)))

            if not restore_job.wait_for_completion():
                raise Exception(
                    "Failed to run {0} Restore job with error: {1}".format(
                        drobject.backup_type, restore_job.delay_reason
                    )
                )

            self._log.info(
                "Removing SP and library before restore of Full dump")

            if not storageobj.delete(full_sp.storage_policy_name):
                error = "Failed to delete SP {}".format(
                    full_sp.storage_policy_name)
                self._log.error(error)
                raise Exception(error)

            self._log.info("Run Full DB restore with CS recovery tool")
            drhelperobject.db_dumplocation = os.path.join(
                fulldrrestorelocation, "CommserveDR", "DR_" + fulldrjob.job_id)
            drhelperobject.restore_db_with_cvmigrationtool()
            self._log.info(
                "Full DB restore is successful with CS recovery tool")
            self._log.info("Start services with DRrestore.exe")
            time.sleep(shortsleep)
            drhelperobject.startservices()
            time.sleep(shortsleep * 6)

            self._log.info("Verifying Full DB SP/Lib")
            storageobj = storage.StoragePolicies(self.commcell)
            disklibraries = storage.DiskLibraries(self.commcell)

            if storageobj.has_policy(full_sp.storage_policy_name):
                self._log.info(
                    "Storage policy created for Full DR is available after DR restore {}".format(
                        full_sp.storage_policy_name))
            else:
                error = "Storage policy created for Full DR is not available \
                after DR restore {}".format(full_sp.storage_policy_name)
                self._log.error(error)
                raise Exception(error)

            if disklibraries.has_library(full_library_name):
                self._log.info("full_library_name created for Full DR is available\
                 after DR restore {}".format(full_library_name))
            else:
                error = "full_library_name created for Full DR is not available\
                 after DR restore {}".format(full_library_name)
                self._log.error(error)
                raise Exception(error)

            self._log.info("Running one more Full DR backup after DB restore before\
             creating Differential DB entities")
            drobject.backup_type = 'full'
            fulldrjob = drobject.disaster_recovery_backup()

            if not fulldrjob.wait_for_completion():
                raise Exception(
                    "Failed to run {0} backup job with error: {1}".format(
                        drobject.backup_type, fulldrjob.delay_reason
                    )
                )

            self._log.info("Creating differential backup entities (Lib / SP)")
            disklibraries = storage.DiskLibraries(self.commcell)

            if not disklibraries.has_library(diff_library_name):
                self._log.info(
                    "Creating differential Disk Library with name {}".format(
                        str(diff_library_name)))
                disklibraries.add(
                    diff_library_name,
                    mediaagent,
                    diff_mount_path)
            else:
                self._log.info(
                    "Differential Disk Library with name {} already exist".format(
                        str(diff_library_name)))
                disklibraries.get(diff_library_name)
            storageobj = storage.StoragePolicies(self.commcell)
            self._log.info(
                "Creating differential Storage Policy with name {}".format(diff_sp))

            if not storageobj.has_policy(diff_sp):
                diff_sp = storageobj.add(
                    diff_sp,
                    diff_library_name,
                    mediaagent,
                    retention_period=5)
                self._log.info(
                    "Created differential Storage Policy with name {}".format(diff_sp))
            else:
                self._log.info(
                    "SP already exists, so creating SP object {}".format(diff_sp))
                diff_sp = storage.StoragePolicy(self.commcell, diff_sp)

            clenup_enties["storagepolicy"].append(diff_sp.storage_policy_name)
            drobject.backup_type = "differential"
            self._log.info("Running Differential DR backup")
            diffdrjob = drobject.disaster_recovery_backup()
            self._log.info("Differential DR backup job id : {}".format(
                str(diffdrjob)))

            if not diffdrjob.wait_for_completion():
                raise Exception(
                    "Failed to run {0} backup job with error: {1}".format(
                        drobject.backup_type, diffdrjob.delay_reason
                    )
                )

            diffdrjob.summary
            backuplevel = diffdrjob.backup_level

            if not backuplevel.lower().find("differential") >= 0:
                error = "DR backup job type is not differential , please check \
                the type job id {}, current job type is {} \
                ".format(str(diffdrjob), backuplevel)
                self._log.error(error)
                raise Exception(error)

            diffdrrestorelocation = os.path.join(drrestorelocation, "Diff")
            diff_restore_job = drobject.restore_out_of_place(
                client,
                diffdrrestorelocation,
                overwrite=True,
                restore_data_and_acl=True,
                copy_precedence=None,
                from_time=diffdrjob.start_time,
                to_time=diffdrjob.end_time,
                fs_options=None)
            self._log.info(
                "Differential DR restore job id : {}".format(
                    str(diff_restore_job)))

            if not diff_restore_job.wait_for_completion():
                raise Exception(
                    "Failed to run Restore job with error: {1}".format(
                        diff_restore_job.delay_reason
                    )
                )

            client_machine.copy_folder(
                os.path.join(diffdrrestorelocation, "CommserveDR", "DR_" +
                             diffdrjob.job_id + os.path.sep + "*.*"),
                os.path.join(diffdrrestorelocation, "CommserveDR", "DR_" +
                             fulldrjob.job_id))
            drhelperobject.db_dumplocation = os.path.join(
                diffdrrestorelocation, "CommserveDR", "DR_" + fulldrjob.job_id)

            self._log.info(
                "Run Differential DR DB restore with CS recovery tool")
            drhelperobject.restore_db_with_cvmigrationtool()
            time.sleep(shortsleep)
            drhelperobject.startservices()
            time.sleep(shortsleep * 6)
            self._log.info("Verify Differential DR SP/LIB")
            storageobj = storage.StoragePolicies(self.commcell)
            disklibraries = storage.DiskLibraries(self.commcell)

            if not disklibraries.has_library(diff_library_name):
                error = "Storage policy created for Differential DR \
                is not available after Differential DR restore {}\
                ".format(diff_library_name)
                self._log.error(error)
                raise Exception(error)

            if not storageobj.has_policy(diff_sp.storage_policy_name):
                error = "Differential SP is not available after \
                differential DR restore {}".format(diff_sp.storage_policy_name)
                self._log.error(error)
                raise Exception(error)

            if storageobj.has_policy(full_sp.storage_policy_name):
                self._log.info(
                    "Storage policy created for Full DR is available after DR restore {}".format(
                        full_sp.storage_policy_name))
            else:
                error = "Storage policy created for Full DR is not available \
                after DR restore {}".format(full_sp.storage_policy_name)
                self._log.error(error)
                raise Exception(error)

            if disklibraries.has_library(full_library_name):
                self._log.info("full_library_name created for Full DR is available\
                 after DR restore {}".format(full_library_name))
            else:
                error = "full_library_name created for Full DR is not available \
                 after DR restore {}".format(full_library_name)
                self._log.error(error)
                raise Exception(error)

            self._log.info("Restoring from SET_Folder to verify Restore")
            drhelperobject.db_dumplocation = drhelperobject.set_folder
            drhelperobject.restore_db_with_cvmigrationtool()
            time.sleep(shortsleep)
            drhelperobject.startservices()
            time.sleep(shortsleep * 6)
            storageobj = storage.StoragePolicies(self.commcell)

            if storageobj.has_policy(full_sp.storage_policy_name):
                error = "Storage policy created for Full DR is available after \
                DR restore {}".format(full_sp.storage_policy_name)
                self._log.error(error)
                raise Exception(error)
            time.sleep(shortsleep)

            try:
                client_machine.remove_directory(full_mount_path)
            except Exception as err:
                self._log.info(
                    "Failed to delete library mount path dir {0}".format(err))
            try:
                client_machine.remove_directory(diff_mount_path)
            except Exception as err:
                self._log.info(
                    "Failed to delete library mount path  dir {0}".format(err))
            try:
                client_machine.remove_directory(drrestorelocation)
            except Exception as err:
                self._log.info("Failed to restore location {0}".format(err))
            self._log.info("Testcase execution completed")
        except Exception as exp:
            self._log.error('Failed with error:%s ' % str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            try:
                drhelperobject.startservices()
                drhelperobject.cleanup_entities(clenup_enties)
            except Exception:
                self._log.error("Failed to start services")
