# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case to trigger Test Failover

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case
"""

from cvpysdk.commcell import Commcell
from cvpysdk.client import Client
from Server.CVFailover import cvfailover
from Server.JobManager import jobmanager_helper
from AutomationUtils.options_selector import CVEntities
from AutomationUtils import idautils
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Test case class for invoking Test Failover"""

    def __init__(self):
        super().__init__()
        self.name = ("Regression test case for CVFailover - Test Failover")
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.CVFAILOVER
        self.show_to_user = True
        self.tcinputs = {
            "webconsole": None,
            "TestClient": None,
            "TestMA": None,
            "DRSql": None,
            "ProdSql": None
        }

    def run(self):
        """ Main function for test case execution.
        This Method creates cvfailover objects to perform cvfailover.
        """
        try:
            # Getting TCInputs from JSON.

            webconsole = self.tcinputs["webconsole"]
            testclient = self.tcinputs["TestClient"]
            testma = self.tcinputs["TestMA"]
            drsql = self.tcinputs["DRSql"]
            prodsql = self.tcinputs["ProdSql"]
            cvfailover_client = Client(self.commcell, drsql)
            cvfailoverobj = cvfailover.CVFailoverHelper(drsql, op_type="Test", log=self.log)
            cvfailoverobj.path = cvfailover_client.install_directory

            # Creating Sub-Clients, Library, Storage-Policy for Test Clients to carry
            # out recovery operations.

            idautil = idautils.CommonUtils(self)
            entities = CVEntities(self)
            all_props = entities.create({
                'target':
                    {
                        'client': testclient,
                        'agent': "File system",
                        'instance': "defaultinstancename",
                        'mediaagent': testma,
                        'force': True
                    },
                'backupset': {},
                'subclient': {},
                'disklibrary': {},
                'storagepolicy': {}
            })

            # Running First Backup on Test Failover Client Machine:
            self.log.info("Running Backup on test client before initiating Test Fail-over")
            subclient_content = all_props["subclient"]["content"][0]
            self.log.info("The name of sub client is %s:", subclient_content)
            subclient = all_props['subclient']['object']
            backupset = all_props['backupset']['object']
            self.log.info("Generating test data at: {0}".format(subclient_content))
            idautil.subclient_backup(subclient, backup_type="FULL", wait=True)
            idautil.subclient_backup(subclient, backup_type="FULL", wait=False)
            # Launching Test Fail-over

            cvfailoverobj.run_cvfailover()

            # Connecting to DR Site, and launching Restore Job:

            self.commcell = Commcell(webconsole,
                                     self._inputJSONnode['commcell']["commcellUsername"],
                                     self._inputJSONnode['commcell']["commcellPassword"])

            all_clients = self.commcell.clients
            client = all_clients.get(testclient)
            drclient = all_clients.get(drsql)
            fsagent = client.agents.get('file system')
            instance = fsagent.instances.get('defaultinstancename')
            backupset = instance.backupsets.get(backupset.backupset_name)
            subclient = backupset.subclients.get(subclient.subclient_name)
            idautil = idautils.CommonUtils(self)

            self.log.info("Running a restore job, post Test Fail-over on DR")

            job = idautil.subclient_restore_in_place([subclient_content], subclient)
            job_manager = jobmanager_helper.JobManager(job.job_id, self.commcell)
            job_manager.wait_for_state("completed")

            # Issue a Test-Fail_back.

            cvfailoverobj = cvfailover.CVFailoverHelper(
                prodsql, op_type='"Test Failback"', log=self.log)
            cvfailoverobj.path = drclient.install_directory
            self.log.info("starting test Fail-back operation")
            cvfailoverobj.run_cvfailover()

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

        # Connecting to original active node to clean up entities configured
            # during this test case.
        finally:
            self.commcell = Commcell(self._inputJSONnode['commcell']["webconsoleHostname"],
                                     self._inputJSONnode['commcell']["commcellUsername"],
                                     self._inputJSONnode['commcell']["commcellPassword"])
            idautil.cleanup()
            entities.cleanup()
