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
import time
import datetime as dt
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.machine import Machine
from VirtualServer.VSAUtils import VirtualServerUtils

class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test to check Nutanix snap Meditech Quiesce time """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Meditech snap backup check for quiesce and unquiesce"
    def run(self):
        """Main function for test case execution"""
        try:
            VirtualServerUtils.decorative_log("Started executing {0} testcase".format(self.id))
            VirtualServerUtils.decorative_log(
                "-" * 25 + " Initialize helper objects " + "-" * 25)
            client_name = self.tcinputs.get('ClientName')
            agent = self.tcinputs.get('AgentName')
            subclient_name = self.tcinputs.get('SubclientName')
            backupset = self.tcinputs.get('BackupsetName')
            subclient_obj = CommonUtils(self.commcell).get_subclient(
                client_name, agent, backupset, subclient_name)
            VirtualServerUtils.decorative_log('-----Triggering backup job-----')
            job_obj = subclient_obj.backup("Incremental")
            job_obj._initialize_job_properties()
            if not job_obj.wait_for_completion():
                self.log.exception("Failed to run Incremental backup with error: {0}"
                            .format(job_obj.delay_reason))
                raise Exception
            self._log.info("Backup job {0} completed".format(job_obj.job_id))
            vmobj = Machine(self.subclient.subclient_proxy[0], self.commcell)
            search_term = ['MediTech UnQuiesce successful',
                           'MediTech Quiesce successful', ("vsbkp.log")]
            unquiesce = vmobj.get_logs_for_job_from_file(job_obj.job_id,
                                                                            search_term[2],
                                                                            search_term[0])
            quiesce = vmobj.get_logs_for_job_from_file(job_obj.job_id,
                                                                          search_term[2],
                                                                          search_term[1])
            self.log.info(quiesce+","+unquiesce)
            unquiesce_split = unquiesce.split(job_obj.job_id)
            quiesce_slipt = quiesce.split(job_obj.job_id)
            time1 = unquiesce_split[0]
            time2 = quiesce_slipt[0]
            ft_unquiesce = time1[-9:]
            ft_unquiesce = ft_unquiesce[:-1]
            ft_quiesce = time2[-9:]
            ft_quiesce = ft_quiesce[:-1]
            start_dt = dt.datetime.strptime(ft_quiesce, '%H:%M:%S')
            end_dt = dt.datetime.strptime(ft_unquiesce, '%H:%M:%S')
            diff = (end_dt - start_dt)
            diff = diff.total_seconds()
            time.sleep(5)
            if diff > 30.0:
                self.log.error("Quiesce took more time than expected")
                raise Exception
            VirtualServerUtils.decorative_log("Quiesce happened in expected time")
        except Exception as exp:
            self.log.error('Failed with error: '+str(exp))
