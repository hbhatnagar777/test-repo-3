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
import time
from AutomationUtils import constants
from AutomationUtils import idautils
from AutomationUtils.options_selector import CVEntities
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils.mahelper import CloudLibrary
from MediaAgents.MAUtils.mahelper import MMHelper


class TestCase(CVTestCase):
    """Class for executing HPStore Library operations"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "HP Library - Acceptence"
        self.show_to_user = True
        self.tcinputs = {
            "mountpath1": None,
            "mountpath2": None,
            "loginname": None,
            "password": None,
            "server": None

        }

    def run(self):
        """Execution method for this test case"""
        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            randomint = str(random.randint(100000, 9999999))
            hp_library_name = "hp_library_{}".format(randomint)
            disk_library_name = "disk_library_{}".format(randomint)
            self.log.info("Create Machine class object")
            client_machine = Machine(self.client.client_name, self.commcell)
            copy_name = "sp_copy_{}".format(randomint)
            hp_libraries = []
            mediaagent = self.commcell.media_agents.get(self.client.client_name)
            clenup_enties = {'storagepolicy': [], 'library': []}
            install_path = self.client.install_directory.split(os.path.sep)[0]
            if not install_path.endswith(os.path.sep):
                install_path += os.path.sep
            restore_location = client_machine.join_path(install_path, "Automation_test",
                                                        "Hp_restore")
            disk_mountpath = client_machine.join_path(install_path, "Automation_test")
            disklibraries = self.commcell.disk_libraries

            for iter in range(2):
                if iter == 0:
                    mountpath = self.tcinputs["mountpath1"]
                else:
                    mountpath = self.tcinputs["mountpath2"]
                values = {
                    "mountPath": mountpath,
                    "serverType": 59,
                    "loginName": self.tcinputs["server"] + r"//" + self.tcinputs["loginname"],
                    "password": self.tcinputs["password"]}
                library_obj = CloudLibrary(hp_library_name + "%s" % str(iter), values)

                if not disklibraries.has_library(library_obj.libraryname):
                    library_obj.cloud_library_name = disklibraries.add(
                        library_obj.libraryname,
                        mediaagent,
                        library_obj.mountpath,
                        library_obj.loginname,
                        library_obj.secret_accesskey,
                        library_obj.servertype)
                    self.log.info(
                        "Created cloud library {} for cloud type {} ".format(
                            library_obj.cloud_library_name, hp_library_name))
                else:
                    library_obj.cloud_library_name = disklibraries.get(
                        library_obj.cloud_library_name)
                    self.log.info(
                        "HP library {}  already exist ".format(
                            library_obj.cloud_library_name))

                clenup_enties["library"].append(library_obj.cloud_library_name.library_name)
                hp_libraries.append(library_obj.cloud_library_name)

            if not disklibraries.has_library(disk_library_name):
                disk_library_name = disklibraries.add(
                    disk_library_name,
                    mediaagent,
                    disk_mountpath)
                self.log.info(
                    "Created disk library {} ".format(
                        disk_library_name))
            else:
                disk_library_name = disklibraries.get(
                    disk_library_name)
                self.log.info(
                    "disk library {} ".format(
                        disk_library_name))

            clenup_enties["library"].append(disk_library_name.library_name)
            idautil = idautils.CommonUtils(self)
            entities = CVEntities(self)

            for i in range(3):
                self.log.info("Iteration {}".format(str(i)))
                if i == 0:
                    lib_first = hp_libraries[0].library_name
                    lib_second = hp_libraries[1].library_name
                elif i == 1:
                    lib_first = disk_library_name.library_name
                    lib_second = hp_libraries[1].library_name
                else:
                    lib_first = hp_libraries[0].library_name
                    lib_second = disk_library_name.library_name

                all_props = entities.create({
                    'target':
                        {
                            'client': self.client.client_name,
                            'agent': "File system",
                            'instance': "defaultinstancename",
                            'mediaagent': self.client.client_name,
                            'force': True
                        },
                    'backupset': {},
                    'subclient': {},
                    'storagepolicy': {'library': lib_first}
                })

                self.log.info("Library name is {}".format(lib_first))
                sp_obj = all_props['storagepolicy']['object']

                if sp_obj.has_copy(copy_name):
                    self.log.info("Storage policy copy exists!")
                else:
                    self.log.info("Creating dedupe copy")
                    sp_obj.create_secondary_copy(copy_name,
                                                 lib_second, self.client.client_name)
                    self.log.info("secondary copy creation completed ")

                self._log.info("setting retention to: 0 day, 1 cycle")
                primary_copy = sp_obj.get_copy('Primary')
                primary_copy.copy_retention = (0, 1, 1)
                subclient_content = all_props["subclient"]["content"][0]
                self.subclient = all_props['subclient']['object']
                self.log.info("Generating test data at: {0}".format(subclient_content))
                backup_jobs = []

                for itera in range(3):
                    jobid = idautil.subclient_backup(self.subclient, "FULL", wait=True)
                    backup_jobs.append(jobid)
                    client_machine.generate_test_data(subclient_content, 1, 1)
                    jobid = idautil.subclient_backup(self.subclient, "INCREMENTAL", wait=True)
                    backup_jobs.append(jobid)
                try:
                    client_machine.remove_directory(restore_location)
                    client_machine.remove_directory(disk_mountpath)
                except Exception as err:
                    self._log.info(
                        "Failed to delete Destination dir {0}".format(err))

                restore_job = idautil.subclient_restore_out_of_place(
                    restore_location, [subclient_content], self.client.client_name, self.subclient)
                restore_job.wait_for_completion()
                difference = client_machine.compare_folders(
                    client_machine, subclient_content, restore_location)
                if difference:
                    error = ("""difference in source content {}
                        f" and restored content {}"
                        f" and difference is {} """.format(subclient_content,
                                                           restore_location, difference))

                    self.log.error(error)

                self.log.info("Running auxcopy with job limit set to 10")
                aux_job = sp_obj.run_aux_copy("", self.client.client_name, use_scale=True,
                                              total_jobs_to_process=1)
                self.log.info("Auxcopyjob {0} launched.".format(str(aux_job.job_id)))

                if not aux_job.wait_for_completion():
                    raise Exception(
                        "Failed to run auxcopy with error: {0}".format(aux_job.delay_reason)
                    )

                if i == 0:
                    files_tranfred = aux_job.details['jobDetail']['progressInfo'][
                        'dataCopiedInfo'][0]['BytesXferred']
                    data_tocopy = aux_job.details['jobDetail']['progressInfo'][
                        'dataCopiedInfo'][0]['dataToCopy']
                    actualfiles = aux_job.details['jobDetail']['progressInfo'][
                        'numOfFilesTransferred']
                    if files_tranfred <= data_tocopy and files_tranfred <= actualfiles:
                        self.log.info("data transferred is less compared to Actual data")
                    else:
                        raise Exception(
                            ("""data transferred {}is more compared to Actual data{} for.
                            auxcopy job {}""").format(str(files_tranfred), str(data_tocopy),
                                                      aux_job)
                        )

                try:
                    client_machine.remove_directory(restore_location)
                except Exception as err:
                    self._log.info(
                        "Failed to delete Destination dir {0}".format(err))
                self.log.info(
                    "Auxcopy job completed, now try restore from precedence 2 and compare")
                restore_job = idautil.subclient_restore_out_of_place(
                    restore_location, [subclient_content],
                    self.client.client_name, self.subclient, copy_precedence=2)
                difference = client_machine.compare_folders(
                    client_machine, subclient_content, restore_location)
                if difference:
                    error = ("""difference in source content {}
                        f" and restored content {}"
                        f" and difference is {} """.format(subclient_content,
                                                           restore_location, difference))
                self._log.info("wait for 10 min, before data aging job")
                time.sleep(10 * 60)
                self._log.info("Running Data aging...")
                da_job = self.commcell.run_data_aging('Primary', sp_obj.storage_policy_name)
                self._log.info("data aging job: {0}".format(da_job.job_id))

                if not da_job.wait_for_completion():
                    raise Exception(
                        "Failed to run data aging with error: {0}".format(da_job.delay_reason)
                    )
                self._log.info("Data aging job completed. wait for 10 min")
                time.sleep(6 * 60)
                # Validate - J1 and J2 are aged
                self._log.info("VALIDATION: all but last Day 1 jobs are aged")
                # initialize MMHelper class
                mmhelper = MMHelper(self)
                count = 0
                self.log.info("All Jobs to verify %s" % (backup_jobs))

                for job in backup_jobs:
                    self.log.info("Jobs to verify %s" % (job))
                    retcode = mmhelper.validate_job_prune(job.job_id, primary_copy.copy_id)
                    if count > 3:
                        retcode = not retcode
                    if retcode:
                        self.log.info("Validation success")
                    else:
                        self.log.error("Jobs to verify %s , count %s" % (job, str(count)))
                        raise Exception(
                            "Prunning is not happening for job id {0}".format(job)
                        )
                    count = count + 1
            self.log.info("Testcase execution completed")
        except Exception as exp:
            self.log.error('Failed with error:%s ' % str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            try:
                self.log.info("Running cleanup code")
                try:
                    client_machine.remove_directory(subclient_content)
                except Exception as err:
                    self._log.info(
                        "Failed to delete subclient dir {0}".format(err))
                try:
                    idautil.cleanup()
                    entities.cleanup()
                except Exception as exep:
                    self.log.info("Cleanup failed%s" % exep)
                CloudLibrary.cleanup_entities(self.commcell, self.log, clenup_enties)
            except Exception as err:
                self.log.info("failed to clean test case entities, exception {}".format(err))
