# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  initialize TestCase class

    setup()             --  setup function of this test case

    run()               --  run function of this test case
"""

import os
import random
import threading
import time
from cvpysdk import storage
from cvpysdk.backupset import Backupsets
from cvpysdk.subclient import Subclients
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from MediaAgents import mediaagentconstants
from MediaAgents.MAUtils.mahelper import CloudLibrary


class TestCase(CVTestCase):
    """Class for executing Advanced DiskLibrary operations"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "Cloud Library - Acceptence"
        self.product = self.products_list.MEDIAAGENT
        self.feature = self.features_list.MEDIAMANAGEMENT
        self.show_to_user = True
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "RestoreLocation": None,
            "subClientContent": None
        }

    def _run_backup(self, backup_type):
        """Initiates backup job and waits for completion"""

        self.log.info("*" * 10 + " Starting Subclient {0} Backup ".format(backup_type) + "*" * 10)
        job = self.subclient.backup(backup_type)
        self.log.info("{}:Started {} backup with Job ID: {}".format(
            threading.currentThread().getName(), backup_type, str(job.job_id)))

        if not job.wait_for_completion():
            raise Exception(
                "{}:Failed to run {} backup job with error: {}".format(
                    threading.currentThread().getName(), backup_type,
                    job.delay_reason
                )
            )
        self.log.info("Successfully finished {0} backup job".format(backup_type))
        return job

    def setup(self):
        """Initializes pre-requisites for test case"""
        if self.log is None:
            self.log = logger.get_log()

    def run(self):
        """Execution method for this test case"""
        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            randomint = str(random.randint(100000, 9999999))
            shortsleep = 60
            sleeptime = 4 * 60 * 60
            cloud_library_name = "cloud_library_{}".format(randomint)
            non_dedupsp = ("non_dedupsp_{}".format(randomint))
            mediaagent = storage.MediaAgent(self.commcell, self.client.client_name)
            backupset_name = "cloud_backupset"
            subclient_name = "cloud_subclient_{}".format(randomint)
            lock = threading.Lock()
            install_path = self.client.install_directory.split(os.path.sep)[0]
            clean_subclient_content = []

            if not install_path.endswith(os.path.sep):
                install_path += os.path.sep

            if "RestoreLocation" in self.tcinputs and self.tcinputs["RestoreLocation"]:
                restore_location = self.tcinputs["RestoreLocation"]
            else:
                restore_location = os.path.join(install_path, "Automation_test",
                                                "restore_location_" + randomint)

            if "subClientContent" in self.tcinputs:
                subclient_content = self.tcinputs["subClientContent"]
            else:
                subclient_content = os.path.join(
                    install_path, "Automation", "subclient_content_" + randomint)

            failed_thread = {}
            clenup_enties = {'storagepolicy': [], 'library': []}
            self.log.info("Create Machine class object")
            client_machine = Machine(self.client.client_name, self.commcell)

            def library_operations(vendor, values):
                '''
                performs cloud library operations
                '''
                self.log.info("Cloud library operations {}{}".format(vendor, values))
                try:
                    libraryobj = CloudLibrary(vendor, values)
                    vendor = vendor.replace(" ", "")
                    kwargs = {"restore_location": restore_location + os.path.sep + vendor,
                              "non_dedupsp": (non_dedupsp + "_" + vendor).lower(),
                              "subclient_name": (subclient_name + "_" + vendor).lower(),
                              "subclient_content": subclient_content + "_" + vendor,
                              "cloud_library_name": (cloud_library_name + "_" + vendor).lower()}

                    for key, value in kwargs.items():
                        setattr(libraryobj, key, value)
                    with lock:
                        self.log.info("Libblock {}".format(threading.currentThread().getName()))
                        disklibraries = storage.DiskLibraries(self.commcell)

                        if not disklibraries.has_library(libraryobj.cloud_library_name):
                            libraryobj.cloud_library_name = disklibraries.add(
                                libraryobj.cloud_library_name,
                                mediaagent,
                                libraryobj.mountpath,
                                libraryobj.loginname,
                                libraryobj.secret_accesskey,
                                libraryobj.servertype)
                            self.log.info(
                                "Created cloud library {} for cloud type {} ".format(
                                    libraryobj.cloud_library_name, vendor))
                        else:
                            libraryobj.cloud_library_name = disklibraries.get(
                                libraryobj.cloud_library_name)
                            self.log.info(
                                "cloud library {} for cloud type {} already exist ".format(
                                    libraryobj.cloud_library_name, vendor))
                        clenup_enties["library"].append(libraryobj.cloud_library_name.library_name)
                        storage_obj = storage.StoragePolicies(self.commcell)

                        if not storage_obj.has_policy(libraryobj.non_dedupsp):
                            libraryobj.non_dedupsp = storage_obj.add(
                                libraryobj.non_dedupsp,
                                libraryobj.cloud_library_name,
                                mediaagent,
                                retention_period=0,
                                retention_cycles=1)
                            self.log.info(
                                "Created Non dedup Storage Policy with name {}".format(
                                    libraryobj.non_dedupsp))
                        else:
                            self.log.info(
                                "SP already exists, so creating SP object {}".format(
                                    libraryobj.non_dedupsp))
                            libraryobj.non_dedupsp = storage.StoragePolicy(
                                self.commcell, libraryobj.non_dedupsp)
                        clenup_enties["storagepolicy"].append(
                            libraryobj.non_dedupsp.storage_policy_name)
                        self.log.info(
                            "Creating BackupSet with name {}".format(backupset_name))
                        self.commcell.refresh()
                        libraryobj.backupset = Backupsets(self.agent)

                        if not libraryobj.backupset.has_backupset(backupset_name):
                            libraryobj.backupset_name = libraryobj.backupset.add(
                                backupset_name)
                        else:
                            libraryobj.backupset_name = libraryobj.backupset.get(
                                backupset_name)

                        libraryobj.subclients = Subclients(libraryobj.backupset_name)
                        self.log.info(
                            "Creating subclient with name {}".format(libraryobj.subclient_name))
                        if not libraryobj.subclients.has_subclient(libraryobj.subclient_name):
                            libraryobj.subclient_name = libraryobj.subclients.add(
                                libraryobj.subclient_name,
                                libraryobj.non_dedupsp.storage_policy_name)
                        else:
                            libraryobj.subclient_name = libraryobj.subclients.get(
                                libraryobj.subclient_name)

                    self.log.info(
                        "{} :wait for 8 minutes after library creation".format(
                            threading.currentThread().getName()))
                    time.sleep(shortsleep * 8)

                    with lock:
                        self.log.info(
                            "job running block {}".format(
                                threading.currentThread().getName()))
                        libraryobj.subclient_name.content = [libraryobj.subclient_content]
                        self.log.info("Subclient Content: {0}".format(
                            libraryobj.subclient_name.content))
                        self.subclient = libraryobj.subclient_name
                        self.log.info("Generating test data at: {0}".format(subclient_content))
                        client_machine.generate_test_data(libraryobj.subclient_content, 1, 1)
                        clean_subclient_content.append(libraryobj.subclient_content)
                        self._run_backup('FULL')
                        self.log.info(
                            "Generating test data at: {0}".format(
                                libraryobj.subclient_content))
                        # client_machine.generate_test_data(libraryobj.subclient_content)
                        self._run_backup('INCREMENTAL')

                        libraryobj.restore_job = self.subclient.restore_out_of_place(
                            mediaagent.media_agent_name,
                            libraryobj.restore_location,
                            libraryobj.subclient_name.content
                        )
                        self.log.info("{} :started restore job {}".format(
                            libraryobj.restore_job, threading.currentThread().getName()))
                    self.log.info(
                        "{}Wait for 5 minutes after triggering the restore job {}".format(
                            threading.currentThread().getName(), libraryobj.restore_job))
                    time.sleep(shortsleep * 5)
                    with lock:
                        self.log.info(
                            "restore block {}".format(
                                threading.currentThread().getName()))
                        if libraryobj.restore_job.status.lower().find("pending") >= 0:
                            self.log.info(
                                "Restore job {} is in pending state".format(
                                    str(libraryobj.restore_job)))
                        else:
                            error = ("{} Restore job {} is not in pending state,"
                                     " job status is {}").format(
                                         threading.currentThread().getName(),
                                         libraryobj.restore_job,
                                         str(libraryobj.restore_job.status))
                            self.log.error(error)

                        if libraryobj.restore_job.pending_reason is not None:
                            if libraryobj.restore_job.pending_reason.find(
                                    "Error occurred in Cloud Storage Library Path") >= 0:
                                self.log.info(
                                    "Job is in pending state with valid reason {}".format(
                                        libraryobj.restore_job.pending_reason))
                            else:
                                error = ("{}Job is not in pending state or not"
                                         " failed with valid reason{} ").format(
                                             threading.currentThread().getName(),
                                             libraryobj.restore_job.pending_reason)
                                self.log.error(error)
                                failed_thread[threading.currentThread().getName()] = error

                    self.log.info(
                        "{}:Wait for 4 hours after triggering the restore job".format(
                            threading.currentThread().getName()))
                    time.sleep(sleeptime)
                    with lock:
                        self.log.info(
                            "thread {} execution completed".format(
                                threading.currentThread().getName()))
                        if not libraryobj.restore_job.wait_for_completion():
                            raise Exception(
                                "{0} Failed to run {1} restore job with error: {2}".format(
                                    threading.currentThread().getName(),
                                    libraryobj.restore_job,
                                    libraryobj.restore_job.delay_reason))
                        libraryobj.sourcehash = client_machine._get_folder_hash(
                            libraryobj.subclient_content)
                        actualrestored_path = os.path.join(libraryobj.restore_location,
                                                           os.path.basename(os.path.normpath(
                                                               libraryobj.subclient_content)))
                        self.log.info("Actual restored path {}".format(actualrestored_path))
                        libraryobj.destinationhash = client_machine._get_folder_hash(
                            libraryobj.restore_location)
                        libraryobj.difference = client_machine.compare_folders(
                            client_machine, libraryobj.subclient_content, actualrestored_path
                        )
                        if libraryobj.difference:
                            error = (
                                f"{threading.currentThread().getName()}:There is a"
                                f" difference in source content {libraryobj.subclient_content} "
                                f" and restored content {libraryobj.restore_location}"
                                f" and difference is {libraryobj.difference} ")

                            self.log.error(error)
                            failed_thread[threading.currentThread().getName()] = error
                        else:
                            self.log.info(
                                "thread {} execution completed".format(
                                    threading.currentThread().getName()))
                except Exception as err:
                    with lock:
                        self.log.error(
                            "Exiting thread {} :Exception raised with error {}".format(
                                threading.currentThread().getName(), err))
                        failed_thread[threading.currentThread().getName()] = err

            thread_list = []
            for library in mediaagentconstants.CLOUD_LIBRARIES.keys():
                lib_thread = threading.Thread(target=library_operations, name=library, args=(
                    library, mediaagentconstants.CLOUD_LIBRARIES[library],))
                lib_thread.daemon = False
                lib_thread.start()
                thread_list.append(lib_thread)
                time.sleep(20)

            for threadobj in thread_list:
                self.log.info("waiting for thread {}".format(threadobj.getName()))
                threadobj.join()
                self.log.info("Completed processing thread {}".format(
                    threadobj.getName()))

            self.log.info("Failed items in test case {}".format(str(failed_thread)))
            if len(failed_thread) > 0:
                self.log.error('Failed in one of the test step, please check logs')
                self.result_string = str(failed_thread)
                self.status = constants.FAILED
                return

            self.log.info("Testcase execution completed")
        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            try:
                self.log.info("Running cleanup code")

                for content in clean_subclient_content:
                    try:
                        client_machine.remove_directory(content)
                    except Exception:
                        self.log.error("Failed to delete content{}".format(content))
                try:
                    backupset = Backupsets(self.agent)
                    if backupset.has_backupset(backupset_name):
                        subclientobj = Subclients(backupset.get(backupset_name))
                        subclients = subclientobj.all_subclients
                        for subclient in subclients:
                            if subclient != "default":
                                subclientobj.delete(subclient)
                except Exception as err:
                    self.log.info("failed to clean test case subclients, exception {}".format(err))
                CloudLibrary.cleanup_entities(self.commcell, self.log, clenup_enties)

            except Exception as err:
                self.log.info("failed to clean test case entities, exception {}".format(err))
