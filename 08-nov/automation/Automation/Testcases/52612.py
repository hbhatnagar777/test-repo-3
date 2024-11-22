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
        self.name = "DR backup with invalid path and registry key"
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
            self._log.info("Started executing %s testcase" % self.id)
            regroot = r"Database"
            regkey = "nSkipDumpCopyFlag"
            self._log.info("Create Machine class object")
            invalidpath = "\\\\invalidpath"
            shortsleep = 30
            client = Client(self.commcell, self.commcell.commserv_name)
            client_machine = WindowsMachine(client.client_name, self.commcell)
            try:
                retcode = client_machine.remove_registry(regroot, regkey)
            except BaseException:
                self._log.info("Failed to delete registry key")
            self._log.info(
                "Verifying DR backup with invalid path with Registry key %s with value %s" %
                (regkey, str(1)))
            retcode = client_machine.create_registry(
                regroot, regkey, 1, reg_type="DWord")

            if retcode:
                self._log.info(
                    "Created Registry key {0} with value {1}".format(
                        regkey, str(1)))
            else:
                self._log.error(
                    "Failed to create Registry key %s with value %s" %
                    (regkey, str(1)))
                self.status = constants.FAILED
                return

            drobject = self.commcell.disasterrecovery
            drhelperobject = drhelper.DRHelper(
                self.commcell, self._log, self.tcinputs, killdrjobs=True)
            initialdrpath = drhelperobject.drpath

            if drhelperobject.drpath is not None:
                validpath = drhelperobject.drpath
            else:
                validpath = os.path.join(
                    client.install_directory, "Automation", "DR")

            try:
                client_machine.remove_directory(validpath)
            except BaseException:
                self._log.info(
                    "failed to delete content from drive %s" %
                    str(validpath))
            drobject.client_machine = client
            drhelperobject.drpath = invalidpath
            exception = False
            try:
                drhelperobject.changedrsettings()
            except Exception as err:
                if str(err).find("Failed to set") >= 0:
                    self._log.info(
                        "DR setting failed with correct error for invalid path")
                    exception = True
                else:
                    self._log.error(
                        "DR setting failed with incorrect error {} for invalid path".format(err))
                    exception = True

            if not exception:
                raise Exception(
                    "DR setting failed with incorrect error for invalid path")

            drhelperobject.changedrpath()
            self._log.info("check DR backup jobs with invalid DR path")
            drobject.backup_type = 'full'
            fulldrjob = drobject.disaster_recovery_backup()
            time.sleep(shortsleep)
            fulldrjob.wait_for_completion()

            if fulldrjob.status.find("Completed w/ one or more errors") >= 0:
                self._log.info(
                    "Job {} Completed with one or more errors".format(
                        str(fulldrjob)))
            else:
                self._log.error(
                    "Job {} not completed with one or more errors, job status is {}".format(
                        str(fulldrjob), str(
                            fulldrjob.status)))
                self.status = constants.FAILED
                return

            if fulldrjob.pending_reason is not None:
                if fulldrjob.pending_reason.find(
                        "does not exist or is inaccessible") >= 0:
                    self._log.info("Job is in pending state with valid reason\
                     {}".format(fulldrjob.pending_reason))
                else:
                    self._log.error("Job is not in pending state or not failed with\
                     valid reason {}".format(fulldrjob.pending_reason))
                self.status = constants.FAILED
                return

            self._log.info(
                "Verifying DR backup with invalid path with  Registry key {0}\
                 with value {1}".format(regkey, str(0)))
            retcode = client_machine.create_registry(
                regroot, regkey, 0, reg_type="DWord")

            if retcode:
                self._log.info(
                    "Created Registry key {0} with value {1}".format(
                        regkey, str(0)))
            else:
                self._log.error(
                    "Failed to create Registry key {0} with value {1}".format(
                        regkey, str(0)))
                self.status = constants.FAILED
                return

            drhelperobject.client_machine = client_machine
            drhelperobject.drpath = invalidpath
            drhelperobject.changedrpath()
            drobject.backup_type = 'full'
            fulldrjob = drobject.disaster_recovery_backup()
            time.sleep(shortsleep)

            if fulldrjob.status.lower().find("pending") >= 0:
                self._log.info(
                    "Job {} is in pending state".format(
                        str(fulldrjob)))
            else:
                self._log.error(
                    "Job {} is not in pending state, job status is {}".format(
                        str(fulldrjob), str(
                            fulldrjob.status)))
                self.status = constants.FAILED
                return

            if fulldrjob.pending_reason.find(
                    "does not exist or is inaccessible") >= 0:
                self._log.info(
                    "Job is in pending state with valid reason {}".format(
                        fulldrjob.pending_reason))
            else:
                self._log.error(
                    "Job is not in pending state or not failed with valid reason {}".format(
                        fulldrjob.pending_reason))
                self.status = constants.FAILED
                return

            self._log.info("Kill the pending job and continue")
            fulldrjob.kill(True)

            self._log.info(
                "Verifying DR backup with valid path without any registry keys")
            try:
                if client_machine.remove_registry(regroot, regkey):
                    self._log.info("Removed registry key")
                else:
                    self._log.error(
                        "Failed to remove registry key, but continuing DR backup with valid path")
            except BaseException:
                self._log.error(
                    "Failed to remove registry key, but continuing DR backup with valid path")

            drhelperobject.drpath = validpath
            drhelperobject.changedrsettings()

            drobject.backup_type = 'full'
            fulldrjob = drobject.disaster_recovery_backup()

            if not fulldrjob.wait_for_completion():
                raise Exception(
                    "Failed to run {0} backup job with error: {1}".format(
                        drobject.backup_type, fulldrjob.delay_reason
                    )
                )

            self._log.info("Test case execution completed")
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
