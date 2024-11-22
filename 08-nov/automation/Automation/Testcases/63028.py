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
from datetime import datetime as dt
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.fshelper import FSHelper
from Server.Network.networkhelper import NetworkHelper

class TestCase(CVTestCase):
    """Testcase for VME to Vmware in a Network Gateway Topology"""

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Virtualize me to VMWare in Network Gateway Topology"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.BMR
        self.helper = None
        self.network = None
        self.time_stamp = None
        self.topology_name = None
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
            "FirewallClientGroup": None,
            "FirewallProxyGroup": None,
            "FirewallProxyClient": None,
            "FirewallHostname": None,
            "ClientName": None,
            "CSClientGroup": None,
            "FirewallDirection": None,
            "FirewallPort": None
        }

    def run(self):
        """Runs System State backup and Virtualize me to VMWare-Clone"""
        try:
            self.helper = FSHelper(self)
            self.network = NetworkHelper(self)
            self.time_stamp = str(dt.now().microsecond)

            FSHelper.populate_tc_inputs(self, mandatory=False)
            backupset_name = "Test_63028"

            self.log.info("Step 1: Checking if Client group, Proxy group and CS group already exist on the CS.")
            if self.commcell.client_groups.has_clientgroup(self.tcinputs['FirewallClientGroup']):
                self.log.info("Deleting Client Group %s as it already exists", self.tcinputs['FirewallClientGroup'])
                self.commcell.client_groups.delete(self.tcinputs['FirewallClientGroup'])
            if self.commcell.client_groups.has_clientgroup(self.tcinputs['FirewallProxyGroup']):
                self.log.info("Deleting Client Group %s as it already exists", self.tcinputs['FirewallProxyGroup'])
                self.commcell.client_groups.delete(self.tcinputs['FirewallProxyGroup'])
            if self.commcell.client_groups.has_clientgroup(self.tcinputs['CSClientGroup']):
                self.log.info("Deleting Client Group %s as it already exists", self.tcinputs['CSClientGroup'])
                self.commcell.client_groups.delete(self.tcinputs['CSClientGroup'])

            self.log.info("Step 2: Creating Client group, Proxy group and CS group")
            self.commcell.client_groups.add(self.tcinputs['FirewallClientGroup'], [self.tcinputs['ClientName']])
            self.commcell.client_groups.add(self.tcinputs['FirewallProxyGroup'], [self.tcinputs['FirewallProxyClient']])
            self.commcell.client_groups.add(self.tcinputs['CSClientGroup'], [self.commcell.commserv_name])

            self.log.info("Step 3: Setting Network Gateway Topology")
            self.topology_name = "63028_gateway_" + self.time_stamp

            self.network.proxy_topology(self.tcinputs['FirewallClientGroup'],
                                        self.tcinputs['CSClientGroup'],
                                        self.tcinputs['FirewallProxyGroup'],
                                        self.topology_name)

            self.log.info("Step 4: Validating Network Gateway Topology")
            self.network.validate_proxy_topology(self.topology_name)

            self.log.info("Step 5: Pushing the network configuration for the topology")
            self.network.push_topology(self.topology_name)

            self.log.info("Step 6: Creating the backupset")
            self.helper.create_backupset(backupset_name, delete=False)
            self.helper.create_subclient("default", self.tcinputs['StoragePolicyName'], ["\\"])
            self.helper.update_subclient(storage_policy=self.tcinputs['StoragePolicyName'],
                                         allow_multiple_readers=True, data_readers=10)

            self.log.info("Step 7: Starting the System state backup")
            self.helper.run_systemstate_backup('Incremental', wait_to_complete=True)

            self.log.info("Step 8: Triggering the Virtualize Me Job")
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

            self.log.info("Step 9: Verifying the Cloned Client")
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

        finally:
            self.log.info("Cleaning up")
            self.network.topologies.delete(self.topology_name)
            self.commcell.client_groups.delete(self.tcinputs['FirewallClientGroup'])
            self.commcell.client_groups.delete(self.tcinputs['FirewallProxyGroup'])
            self.commcell.client_groups.delete(self.tcinputs['CSClientGroup'])
