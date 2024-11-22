# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test to check GCP snap Meditech Quiesce time """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Meditech GCP snap backup check for quiesce and unquiesce"
        self.ind_status = True
        self.failure_msg = ''
        self.tcinputs = {"searchterm1": None,
                         "searchterm2": None,
                         "time": None}

    def run(self):
        """Main function for test case execution"""
        try:
            VirtualServerUtils.decorative_log("Started executing {0} testcase".format(self.id))
            VirtualServerUtils.decorative_log("Initialize helper objects")
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            try:
                backup_options = OptionsHelper.BackupOptions(auto_subclient)
                backup_options.backup_type = "FULL"
                VirtualServerUtils.decorative_log("Starting Backup Job")
                _backup_job = self.subclient.backup(backup_options.backup_type)
                if _backup_job.wait_for_completion():
                    VirtualServerUtils.decorative_log(
                        "Backup job {0} completed".format(_backup_job.job_id))
            except Exception as err:
                self.log.error("Backup job Failed %s", str(err))
                raise Exception
            search_term = [self.tcinputs.get('searchterm1'),
                           self.tcinputs.get('searchterm2')]
            auto_subclient.meditech_quiece_unquiece(
                _backup_job.job_id, search_term,
                self.tcinputs.get('time'))
        except Exception as exp:
            self.log.error("Failed with error %s", str(exp))
            self.failure_msg = str(exp)
            self.ind_status = False
        finally:
            if not self.ind_status:
                self.result_string = self.failure_msg
