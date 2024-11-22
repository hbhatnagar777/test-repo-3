# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case to trigger maintenance failover

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case
"""

from cvpysdk.commcell import Commcell
from cvpysdk.client import Client
from Server.CVFailover import cvfailover
from AutomationUtils.options_selector import CVEntities
from Server.JobManager import jobmanager_helper
from AutomationUtils import idautils
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Test case class for invoking maintenance fail-over"""

    def __init__(self):
        super().__init__()
        self.name = ("Regression test case for CVFailover - Production maintenance")
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.CVFAILOVER
        self.show_to_user = True
        self.tcinputs = {
            "productionSQL": None,
            "webconsole": None,
            "ClientName": None,
            "DRSql": None
        }

    def run(self):
        """ Main function for test case execution.
        This Method creates cvfailover objects to perform cvfailover.
        """
        try:
            # Getting TCInputs from JSON.
            productionsql = self.tcinputs["productionSQL"]
            webconsole = self.tcinputs["webconsole"]
            client_name = self.tcinputs["ClientName"]
            drsql = self.tcinputs["DRSql"]
            cvfailover_client = Client(self.commcell, drsql)

            cvfailoverobj = cvfailover.CVFailoverHelper(
                drsql, op_type='"Production Maintenance"', log=self.log)
            cvfailoverobj.path = cvfailover_client.install_directory

            # Creating Sub-Clients, Library, Storage-Policy for Failover Control MA machine.

            idautil = idautils.CommonUtils(self)
            entities = CVEntities(self)
            all_props = entities.create({
                'target':
                    {
                        'client': client_name,
                        'agent': "File system",
                        'instance': "defaultinstancename",
                        'mediaagent': client_name,
                        'force': True
                    },
                'backupset': {},
                'subclient': {},
                'disklibrary': {},
                'storagepolicy': {}
            })

            # Running First Backup on Fail-over Control MA Machine.

            self.log.info("Running Full Backup before initiating Maintenance Fail-over")
            subclient_content = all_props["subclient"]["content"][0]
            subclient = all_props['subclient']['object']
            backupset = all_props['backupset']['object']
            self.log.info("Generating test data at: {0}".format(subclient_content))
            idautil.subclient_backup(subclient, backup_type="FULL", wait=True)
            idautil.subclient_backup(subclient, backup_type="FULL", wait=False)

            # Launching Maintenance Fail-over:

            cvfailoverobj.run_cvfailover()

            # Connecting to DR Site, and launching Restore Job:

            self.commcell = Commcell(webconsole,
                                     self._inputJSONnode['commcell']["commcellUsername"],
                                     self._inputJSONnode['commcell']["commcellPassword"])
            all_clients = self.commcell.clients
            drclient = all_clients.get(drsql)

            self.log.info("Running a restore job after Maintenance fail-over")

            client = all_clients.get(client_name)
            fsagent = client.agents.get('file system')
            instance = fsagent.instances.get('defaultinstancename')
            backupset = instance.backupsets.get(backupset.backupset_name)
            subclient = backupset.subclients.get(subclient.subclient_name)
            idautil = idautils.CommonUtils(self)

            job = idautil.subclient_restore_in_place([subclient_content], subclient)
            job_manager = jobmanager_helper.JobManager(job.job_id, self.commcell)
            job_manager.wait_for_state("completed")

            # Issue a Maintenance Fail-back to complete a cycle.

            cvfailoverobj = cvfailover.CVFailoverHelper(productionsql, log=self.log)
            cvfailoverobj.path = drclient.install_directory
            self.log.info("Starting Maintenance Fail-back operation")
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
