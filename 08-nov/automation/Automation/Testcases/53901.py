# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for uploading package to Download Center, and removing existing package with same name

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""


import threading
import time
from cvpysdk.commcell import Commcell
from cvpysdk.client import Client
from cvpysdk.job import Job
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities
from AutomationUtils import idautils
from Server.CVFailover import cvfailover


class TestCase(CVTestCase):
    """Test case class for testing cvfailover operations."""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ("CV Failover Basic acceptance test case")
        super(TestCase, self).__init__()
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.CVFAILOVER
        self.show_to_user = True
        self.tcinputs = {
            "productionSQL": None,
            "standalonecs": None,
            "ClientName": None,
            "webconsole": None
        }

    def setup(self):
        """Initializes pre-requisites for test case"""
        self.log.info("We are in setup function")

    def restart(self, standalonecs, restart_flag):
        """
        Restart standalone machine if it is not controller
        """
        if restart_flag:
            standalone_machine = Machine(standalonecs, self.commcell)
            standalone_machine.reboot_client()
            self.log.info("Rebooted client")
        else:
            self.log.info("Not Rebooting the client")

    def run(self):
        """ Main function for test case execution.
        This Method creates cvfailover objects to perofrm cvfailover.

        Raises:
            SDKException:
                if it fails to execute any one of the test case step
        """
        try:
            self.log.info("we are in test case run method")
            self.log.info("Started executing %s testcase", self.id)
            restart_flag = False

            if "standalonecs" in self.tcinputs and self.tcinputs["standalonecs"]:
                standalonecs = self.tcinputs["standalonecs"]
            if "productionSQL" in self.tcinputs and self.tcinputs["productionSQL"]:
                prodction_sql = self.tcinputs["productionSQL"]
            if "webconsole" in self.tcinputs and self.tcinputs["webconsole"]:
                webconsole = self.tcinputs["webconsole"]

            cvfailover_client = Client(self.commcell, prodction_sql)
            cvfailoverobj = cvfailover.CVFailoverHelper(standalonecs, log=self.log)
            cvfailoverobj.path = cvfailover_client.install_directory
            client_name = self.client.client_name
            idautil = idautils.CommonUtils(self)
            entities = CVEntities(self)
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
                'disklibrary': {},
                'storagepolicy': {}
            })

            subclient_content = all_props["subclient"]["content"][0]
            subclient = all_props['subclient']['object']
            backupset = all_props['backupset']['object']
            client_machine = Machine(self.client.client_name, self.commcell)
            self.log.info("Generating test data at: {0}".format(subclient_content))
            idautil.subclient_backup(subclient, "FULL", wait=True)
            restart_job = idautil.subclient_backup(subclient, "FULL", wait=False)
            thread_list = []

            for newthread in range(2):
                if newthread == 1:
                    lib_thread = threading.Thread(
                        target=cvfailoverobj.run_cvfailover, name="failover")
                else:
                    lib_thread = threading.Thread(
                        target=self.restart, name="restart", args=(
                            standalonecs, restart_flag,))
                lib_thread.daemon = False
                lib_thread.start()
                thread_list.append(lib_thread)
                time.sleep(2)

            for threadobj in thread_list:
                self.log.info("waiting for thread {}".format(threadobj.getName()))
                threadobj.join()
                self.log.info("Completed processing thread {}".format(
                    threadobj.getName()))

            self.commcell = Commcell(webconsole,
                                     self._inputJSONnode['commcell']["commcellUsername"],
                                     self._inputJSONnode['commcell']["commcellPassword"])
            all_clients = self.commcell.clients
            client = all_clients.get(client_name)
            fsagent = client.agents.get('file system')
            instance = fsagent.instances.get('defaultinstancename')
            backupset = instance.backupsets.get(backupset.backupset_name)
            subclient = backupset.subclients.get(subclient.subclient_name)
            idautil = idautils.CommonUtils(self)
            job = idautil.subclient_restore_in_place([subclient_content], subclient)
            restart_job = Job(self.commcell, restart_job.job_id)
            restart_job.wait_for_completion()
        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            try:
                idautil.cleanup()
                entities.cleanup()
            except Exception as excp:
                self.log.info("Cleanup failed")
