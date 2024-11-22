# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
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
import time
from cvpysdk.client import Client
from Server.DisasterRecovery import drhelper
from AutomationUtils.windows_machine import WindowsMachine
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Class for executing Advanced DR backup test case"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "DR backup settings validation"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.DISASTERRECOVERY
        self.show_to_user = False
        self.tcinputs = {
            "SqlSaPassword": None
        }

    def setup(self):
        """Initializes pre-requisites for test case"""
        self._log = logger.get_log()

    def run(self):
        """Execution method for this test case"""
        try:
            self._log.info("Started executing {0} testcase".format(self.id))
            shortsleep = 10
            self._log.info("Create Machine class object")
            client = Client(self.commcell, self.commcell.commserv_name)
            client_machine = WindowsMachine(client.client_name, self.commcell)
            drobject = self.commcell.disasterrecovery
            drhelperobject = drhelper.DRHelper(
                self.commcell, self._log, self.tcinputs, killdrjobs=True)
            initialdrpath = drhelperobject.drpath
            drobj_path = drhelperobject.path.split(os.path.sep)[0]

            if not drobj_path.endswith(os.path.sep):
                drobj_path += os.path.sep

            file_path = os.path.join(drobj_path, "Automation", "Scripts")
            validatefile = os.path.join(file_path, "drfile.txt")
            scriptfile = os.path.join(file_path, "scriptfile.bat")
            self._log.info(
                "Verifying Pre/post scripts with DR full/differential backup")
            drhelperobject.client_machine = client_machine
            drhelperobject.runscripts = scriptfile
            drhelperobject.changedrsettings()

            for i in range(2):
                try:
                    client_machine.remove_directory(file_path)
                except:
                    self._log.error("failed to remove directory")
                client_machine.create_file(validatefile, "")
                client_machine.create_file(
                    scriptfile, "ECHO precommand>>%s" %
                    validatefile)

                if i == 0:
                    drobject.backup_type = "full"
                else:
                    drobject.backup_type = "differential"

                fulldrjob = drobject.disaster_recovery_backup()
                time.sleep(2)

                if not fulldrjob.wait_for_completion():
                    raise Exception(
                        "Failed to run {0} backup job with error: {1}".format(
                            fulldrjob, fulldrjob.delay_reason
                        )
                    )

                lines = []

                with open(validatefile) as file:
                    lines = file.readlines()

                if len(lines) < 4:
                    raise Exception(
                        "failed in DR backup pre/post validation, check line from\
                         validation file{0}for job id {1}".format(validatefile, str(fulldrjob)))

            self._log.info("Pre/post scripts validation for  DR full/differential\
                         backup completed")
            self._log.info("Run Full / differential jobs and check differential job is in\
             queued state and moved to running state once full job completed backuptodisk phase")
            drhelperobject.runscripts = None
            drhelperobject.changedrsettings()
            self._log.info("Removed Pre/post scripts from DR backup")

            drobject.backup_type = "full"
            fulldrjob = drobject.disaster_recovery_backup()
            time.sleep(2)
            drobject.backup_type = "differential"
            diffdrjob = drobject.disaster_recovery_backup()
            time.sleep(2)
            status = diffdrjob.status.lower()

            if status != "queued":
                raise Exception("second job {0} is not in queued state,\
                 job status is {1}".format(diffdrjob, status))
            else:
                self._log.info("Second DR backup job is in queued state")

            count = 0

            while count <= 30:
                if fulldrjob.phase == "Backup" or \
                        fulldrjob.phase.lower().replace(" ", "") != "backuptodisk":
                    self._log.info(
                        "First job completed backuptotape phase")
                    time.sleep(30)
                    break
                else:
                    time.sleep(30)
                count = count + 1

            status = diffdrjob.status.lower()
            count = 0

            while count <= 3:

                if status == "queued":

                    if count == 3:
                        phase = fulldrjob.phase
                        if phase.lower().replace(" ", "") != "backuptodisk":
                            self._log.info(
                                "Second job started and completed backuptodisk phase")
                            break
                        else:
                            raise Exception("second job {0} is still in queued state even \
                            first job status is backup".format(diffdrjob))
                    else:
                        time.sleep(30)

                else:
                    self._log.info(
                        "second job started after first job moved to backup phase")
                    break

                count = count + 1
            time.sleep(30)

            backuplevel = diffdrjob.backup_level

            if not backuplevel.lower().find("differential") >= 0:
                self._log.error("DR backup job type is not differential , \
                please check the type job id {0}, current job type is {1}\
                 ".format(str(diffdrjob), backuplevel))
                self.status = constants.FAILED
                return

            if not fulldrjob.wait_for_completion():
                raise Exception(
                    "Failed to run {0} backup job with error: {1}".format(
                        fulldrjob.backup_type, fulldrjob.delay_reason
                    )
                )

            if not diffdrjob.wait_for_completion():
                raise Exception(
                    "Failed to run {0} backup job with error: {1}".format(
                        diffdrjob.backup_type, diffdrjob.delay_reason
                    )
                )

            self._log.info(
                "Completed validation for Full / differential jobs with queue / start run phases.")
            jobids = []
            self._log.info("Run four jobs and check 4th job status and 3rd job\
             (differential) job should run as differential")

            for i in range(4):

                if i == 2:
                    drobject.backup_type = 'differential'
                else:
                    drobject.backup_type = 'full'

                fulldrjob = drobject.disaster_recovery_backup()
                time.sleep(2)

                if i != 3:
                    jobids.append(fulldrjob)

                status = fulldrjob.status.lower()

                if i == 0:

                    if status.lower().replace(" ", "") == "failedtostart":
                        raise Exception("Fourth job {0} started, job {1} status\
                         is not failed to start ".format(fulldrjob, status))

                elif i == 1 or i == 2:

                    while True:
                        if status == 'waiting':
                            self._log.info(" Job is in waiting state. Wait for 30 seconds\
                             for job to move to queued state.")
                            time.sleep(30)
                            status = fulldrjob.status.lower()
                        else:
                            break

                    if status != "queued":
                        raise Exception(
                            "second or third job{0} not in queue state, job status is {1}".format(
                                fulldrjob, status))

                elif i == 3:
                    if fulldrjob.status.lower().replace(" ", "") != "failedtostart":
                        raise Exception("Fourth job{0} status is not failed to start,\
                         job status is {1}".format(fulldrjob, status))

            for job in jobids:
                if not job.wait_for_completion():
                    raise Exception(
                        "Failed to run {0} backup job with error: {1}".format(
                            job.backup_type, job.delay_reason
                        )
                    )

            backuplevel = jobids[len(jobids) - 1].backup_level

            if not backuplevel.lower().find("differential") >= 0:
                self._log.error("DR backup job type is not differential , \
                please check the type job id {0}, current job type is {1}\
                 ".format(str(diffdrjob), backuplevel))
                raise Exception("3rd differential job not ran as differential, please\
                 check logs and job id {0} ".format(str(diffdrjob)))

            self._log.info("validation completed for four jobs case")
            self._log.info("Validate Commserv folder for DR_JOBID folders")
            drobject.backup_type = "full"
            fulldrjob = drobject.disaster_recovery_backup()

            if not fulldrjob.wait_for_completion():
                raise Exception(
                    "Failed to run {0} backup job with error: {1}".format(
                        fulldrjob.backup_type, fulldrjob.delay_reason
                    )
                )

            backuplevel = fulldrjob.backup_level

            if not backuplevel.lower().find("full") >= 0:
                self._log.error("DR backup job type is not differential , please check the\
                 type job id {0}, current job type is {1} ".format(str(fulldrjob), backuplevel))
                self.status = constants.FAILED
                return

            drhelperobject.validate = False
            drhelperobject.drjob = fulldrjob
            drhelperobject.validateset_folder()
            self._log.info("set_folder is " + drhelperobject.set_folder)
            drdir = os.path.split(drhelperobject.set_folder)[0]
            set_folderlist = client_machine.get_folder_or_file_names(
                drdir, False)
            set_folderlist = ' '.join(set_folderlist.splitlines()).split()[2:]
            self._log.info("Validate Set_ folder as well after running 4 jobs")
            self._log.info("Set_folder folders after running more than 4 jobs\
             with number of version =3 {0}".format(str(set_folderlist)))

            if len(set_folderlist) >= 4:
                raise Exception("Number of versions are more than 3 even number \
                 of version is set to 3 ")
            else:
                self._log.info("Number of version validation is successful")

            self._log.info("Validation completed for Set_ folder")
            path = os.path.join(
                drobject.path, "CommserveDR").replace(" ", "' '")
            commservdr = client_machine.get_folder_or_file_names(path, False)
            commservdr = ' '.join(commservdr.splitlines()).split()[2:]
            self._log.info(
                "Folders available in commserv dir are {0}".format(
                    str(commservdr)))
            self._log.info("Job ids {0}to versify ".format(str(jobids)))

            for job in jobids:
                path = "DR_" + job.job_id
                if path in commservdr:
                    raise Exception(
                        "Job id folder {0} is still in Commserv".format(path))
                else:
                    self._log.info(
                        "Job id folder is removed from Commserv folder")

            self._log.info(
                "Validation completed for  Commserv folder for DR_JOBID folders")

            self._log.info(
                "Suspend resume DR backup job afetr backuptodisk phase completed")
            jobs = []

            for i in range(3):
                drobject.backup_type = "full"
                fulldrjob = drobject.disaster_recovery_backup()
                time.sleep(2)
                count = 0

                while count <= 30:
                    phase = fulldrjob.phase

                    if phase == "Backup" or phase.lower().replace(" ", "") != "backuptodisk":
                        self._log.info(
                            "First job completed backuptotape phase")
                        try:
                            fulldrjob.pause(True)
                            jobs.append(fulldrjob)
                        except BaseException:
                            self._log.info("Failed to suspend job")
                        time.sleep(30)
                        break
                    else:
                        time.sleep(30)
                count = count + 1

            for job in jobs:
                job.resume(True)

            for job in jobs:

                if not job.wait_for_completion():
                    raise Exception(
                        "Failed to run {0} backup job with error: {1}".format(
                            job.backup_type, job.delay_reason
                        )
                    )

            self._log.info("Validation completed for Suspend / resume DR backup\
             after DR backuptodisk phase completed")

            self._log.info(
                "Validate Set_ folder size with DR compression as False / true")
            setfoldersize = []

            for i in range(2):

                if i == 0:
                    drobject.iscompression_enabled = False
                else:
                    drobject.iscompression_enabled = True

                drobject.backup_type = 'full'
                drobject.advbackup = True
                fulldrjob = drobject.disaster_recovery_backup()
                time.sleep(shortsleep)
                fulldrjob.summary
                backuplevel = fulldrjob.backup_level

                if not backuplevel.lower().find("full") >= 0:
                    self._log.error("DR backup job type is not full , please check the type\
                     job id {0},current job type is {1} ".format(str(fulldrjob), backuplevel))
                    self.status = constants.FAILED
                    return

                if not fulldrjob.wait_for_completion():
                    raise Exception(
                        "Failed to run {0} backup job with error: {1}".format(
                            drobject.backup_type, fulldrjob.delay_reason
                        )
                    )

                drhelperobject.validate = False
                drhelperobject.drjob = fulldrjob
                drhelperobject.validateset_folder()
                self._log.info("set_folder is " + drhelperobject.set_folder)
                setfoldersize.append(
                    int(client_machine.get_folder_size(drhelperobject.set_folder)))

            if setfoldersize[0] >= setfoldersize[1]:
                self._log.info(
                    "Compression folder size is greatorthan non compressed folder size" +
                    str(setfoldersize))
            else:
                self._log.error(
                    "Compression folder size is lessthan non compressed folder size" +
                    str(setfoldersize))
                raise Exception(
                    "Compression folder size is lessthan non compressed folder size")
            self._log.info(
                "Validation completed for Set_ folder size with DR compression as False / true")
            self._log.info("Test case execution completed successfully")
        except Exception as exp:
            self._log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            try:
                drhelperobject.drpath = initialdrpath
                drhelperobject.changedrsettings()
            except BaseException:
                self._log.error("Exception while updating DR path")
