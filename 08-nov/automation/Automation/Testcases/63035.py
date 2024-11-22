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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

"""


from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from FileSystem.FSUtils.fshelper import FSHelper
from Install.sim_call_helper import SimCallHelper


class TestCase(CVTestCase):
    """Testcase for system state backup and Vme to VMware with existing recovery client present"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "VME to Vmware with Clone Client (Existing recovery client in the CS)"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.BMR
        self.show_to_user = False
        self.sim_caller = None
        self.clone_client_obj = None
        self.opt_selector = None
        self.helper = None
        self.recovery_client_name = None
        self.config = None
        self.tcinputs = {
            "VcenterServerName": None,
            "VcenterUsername": None,
            "VcenterPassword": None,
            "IsoPath": None,
            "Datastore": None,
            "VmName": None,
            "StoragePolicyName": None,
            "VirtualizationClient": None,
            "EsxServer": None,
            "NetworkLabel": None,
            "CloneClientName": None,
        }

    def setup(self):
        """Initializes the appropriate items needed for this testcase """
        self.sim_caller = SimCallHelper(self.commcell)
        self.helper = FSHelper(self)
        FSHelper.populate_tc_inputs(self, mandatory=False)
        self.recovery_client_name = self.tcinputs['ClientName'] + "_Recovery"
        self.opt_selector = OptionsSelector(self.commcell)

    def run(self):
        """Runs System State backup and Virtualize me to VMWare-Clone with existing recovery client present"""
        try:
            self.log.info("Going to create a dummy onetouch recovery client...")
            self.log.info("SP Version: {}".format(float(self.commcell.commserv_version)))
            self.sim_caller.install_new_client(client_name=self.recovery_client_name,
                                               client_hostname="dummy_host",
                                               username=self.tcinputs["CommcellUsername"],
                                               password=self.tcinputs['CommcellPasswordEncrypted'],
                                               recovery_client=True)

            self.commcell.clients.refresh()
            if self.commcell.clients.has_client(self.tcinputs["ClientName"] + "_Recovery"):

                # Run query to set 1-Touch Client property on the dummy client
                query = f"insert into " \
                        f"APP_ClientProp(componentNameId, attrName, attrType, attrVal, created, modified, ccpId)" \
                        f" values (((select id from app_client where name like '%{self.recovery_client_name}%') ), " \
                        f"'1-Touch Client', 2, 1, 1669115426, 0, 0)"
                self.opt_selector.update_commserve_db(query)
                self.log.info("Created dummy onetouch recovery client.")
            else:
                raise Exception("Dummy onetouch recovery client could not be created.")

            backupset_name = "Test_63035"
            self.helper.create_backupset(backupset_name, delete=False)
            self.helper.create_subclient("default", self.tcinputs['StoragePolicyName'], ["\\"])
            self.helper.update_subclient(storage_policy=self.tcinputs['StoragePolicyName'],
                                         allow_multiple_readers=True, data_readers=10)
            self.log.info("Starting the System state backup")
            self.helper.run_systemstate_backup('Incremental', wait_to_complete=True)
            self.log.info("Triggering the Virtualize Me Job")
            restore_job = self.backupset.run_bmr_restore(**self.tcinputs)
            self.log.info(
                "Started Virtualize Me to VMWare with Job ID: %s", str(
                    restore_job.job_id))

            if restore_job.wait_for_completion():
                self.log.info("Virtualize Me job ran successfully")
            else:
                raise Exception(
                    "Virtualize me job failed with error: {0}".format(
                        restore_job.delay_reason))

            self.commcell.clients.refresh()

            if self.commcell.clients.has_client(self.tcinputs['CloneClientName']) and \
                    self.commcell.clients.has_client(self.tcinputs['ClientName']):
                self.log.info("The clone client has been created succesfully & original client is intact")
                self.clone_client_obj = self.commcell.clients.get(self.tcinputs['CloneClientName'])

                clone_license = self.clone_client_obj.consumed_licenses

                if 'Server File System - Windows File System' in clone_license:
                    self.log.info("File system is configured for the clone client")

                else:
                    raise Exception("File system license is not consumed by the clone client")

                job_obj = self.clone_client_obj.uninstall_software(force_uninstall=True)

                if job_obj.wait_for_completion():
                    self.log.info("The clone client has been uninstalled.")

            else:
                raise Exception("The clone client has not been created / The original client has been overwritten.")

        except Exception as excp:
            self.log.error(str(excp))
            self.log.error("TEST CASE FAILED")
            self.status = constants.FAILED
            self.result_string = str(excp)
