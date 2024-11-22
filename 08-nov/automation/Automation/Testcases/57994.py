# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

Inputs:

    pool_name           (str)       -- Name of the storage pool to be created

    nodes               (list)      -- Add media agents to configure

"""

import os
import time
from AutomationUtils import constants
from AutomationUtils import idautils
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper


class TestCase(CVTestCase):
    """Class for Basic acceptance Test case to validate hyper-scale reference architecture"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Basic acceptance Test case to validate hyper-scale reference architecture"
        self.ma1 = None
        self.ma2 = None
        self.ma3 = None
        self.server = None
        self.storage_pool = None
        self.sql_password = None
        self.sql_user = None
        self.cleanup = True
        self.sql_password = None
        self.clientmachine = None
        self.idautil = None
        self.entities = None
        self.subclient_content = None
        self.hyperscale = None
        self.shortsleep = 60
        self.longsleep = 300
        self.sp_name = "Hyperscale_sp"
        self.tcinputs = {
            "poolname": None,
            "nodes": None,
            "sqlpassword": None,
            "sqluser": None,
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.storage_pool = self.tcinputs['poolname']
        nodes = self.tcinputs['nodes'].split(",")
        if len(nodes) <= 2:
            raise Exception("three media agents nodes are not provided as input")
        self.ma1 = nodes[0]
        self.ma2 = nodes[1]
        self.ma3 = nodes[2]
        self.sql_password = self.tcinputs['sqlpassword']
        self.sql_user = self.tcinputs['sqluser']
        self.sp_name = "Hyperscale_sp"
        self.cleanup = True
        self.shortsleep = 60
        self.longsleep = 300

    def run(self):
        """Main function for test case execution"""
        try:
            self.commcell.refresh()
            self.hyperscale = HyperScaleHelper(self.commcell, self.csdb, self.log)
            status = self.hyperscale.check_if_storage_pool_is_present(self.storage_pool)
            if status:
                try:
                    self.hyperscale.delete_plan(self.sp_name)
                except Exception as err:
                    self.log.error("failed to delete plan %s" % err)
                self.hyperscale.clean_up_storage_pool(self.storage_pool,
                                                      self.sql_user, self.sql_password,
                                                      self.ma1, self.ma2, self.ma3)
            self.log.info("wait for 5 minutes before or after cleaning libraries/ storagepools")
            time.sleep(self.longsleep)
            status = self.hyperscale.create_storage_pool(self.storage_pool, self.ma1, self.ma2, self.ma3)
            if not status:
                self.log.error("Storagepools creation failed")
                self.cleanup = False
                raise Exception("failed to create storage pool")
            self.log.info('Successfully created a new storage pool: ' + self.storage_pool)
            self.log.info("Wait for 1 minute ")
            time.sleep(self.shortsleep)
            self.hyperscale.create_and_associate_plan(self.sp_name, self.storage_pool)
            self.log.info('Successfully created a plan / storage policy: ' + self.sp_name)
            all_clients = self.commcell.clients
            self.client = all_clients.get(self.commcell.commserv_name)
            self.clientmachine = Machine(self.commcell.commserv_name, self.commcell)
            self.idautil = idautils.CommonUtils(self)
            self.entities = CVEntities(self)
            backupset_props = self.entities.create({'backupset': {
                'name': "Backupset_hscale",
                'client': self.client.client_name,
                'agent': "File system",
                'instance': "defaultinstancename",
                'on_demand_backupset': False,
                'force': True}})
            subclient_props = self.entities.create({'subclient': {
                'name': "subclient_hscale",
                'client': self.client.client_name,
                'agent': "File system",
                'instance': "defaultinstancename",
                'storagepolicy': self.sp_name,
                'backupset': backupset_props['backupset']['name'],
                'content': None,
                'level': 5,
                'size': 20,
                'description': "Automation created subclient",
                'subclient_type': None,
                'force': True}})
            self.subclient_content = subclient_props["subclient"]["content"][0]
            self.log.info("Subclient content is %s" % str(self.subclient_content))
            self.subclient = subclient_props['subclient']['object']
            self.log.info("Generating test data at: {0}".format(self.subclient_content))
            self.idautil.subclient_backup(self.subclient, "FULL", wait=True)
            self.log.info("backup job completed")
            self.log.info("Wait for 1 minute after backup")
            time.sleep(self.shortsleep)
            install_path = self.client.install_directory.split(os.path.sep)[0]
            if not install_path.endswith(os.path.sep):
                install_path += os.path.sep
            restore_location = self.clientmachine.join_path(install_path,
                                                            "Automation_Restore", "Hyperscale")
            try:
                self.clientmachine.remove_directory(restore_location)
            except Exception as err:
                self._log.info(
                    "Failed to delete Destination dir {0}".format(err))
            restore_job = self.idautil.subclient_restore_out_of_place(
                restore_location, [self.subclient_content], self.client.client_name,
                self.subclient)
            restore_job.wait_for_completion()
            self.log.info("Wait for 1 minute after restore job")
            time.sleep(self.shortsleep)
            self.log.info("Restore location is %s" % restore_location)
            comparelocation = self.clientmachine.join_path(restore_location, os.path.basename(self.subclient_content))
            self.log.info("Destiantion location to compare %s" % str(comparelocation))
            difference = self.clientmachine.compare_folders(
                self.clientmachine, self.subclient_content, comparelocation)
            if difference:
                error = ("""difference in source content {} and
                     restored content {}and difference is {} """.format(
                         self.subclient_content, restore_location, difference))
                self.log.error(error)
                self.cleanup = False
                raise Exception(error)
            self.log.info("Compare Source and restore data is successful")
            try:
                self.clientmachine.remove_directory(restore_location)
            except Exception as err:
                self._log.info(
                    "Failed to delete Destination dir {0}".format(err))
            self.log.info("Restore job completed")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.cleanup = False
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function"""
        try:
            try:
                if self.cleanup:
                    self.entities.cleanup()
                    self.idautil.cleanup()
            except Exception as err:
                self.log.error("Exception raised while doing cleanup %s" % err)
            try:
                if self.cleanup:
                    self.hyperscale.delete_plan(self.sp_name)
                    self.hyperscale.clean_up_storage_pool(self.storage_pool,
                                                          self.sql_user, self.sql_password,
                                                          self.ma1, self.ma2, self.ma3)
            except Exception as err:
                self.log.error("Exception raised while doing cleanup %s" % err)

            if self.cleanup:
                self.log.info("Wait for 5 minute before removing clients")
                time.sleep(self.longsleep)
                for mediagent in [self.ma1, self.ma2, self.ma3]:
                    if self.commcell.clients.has_client(mediagent):
                        maclient = self.commcell.clients.get(mediagent)
                    else:
                        continue
                    license_values = maclient.consumed_licenses
                    try:
                        for key in license_values:
                            maclient.release_license(key)
                        if self.commcell.media_agents.has_media_agent(maclient.client_name):
                            self.commcell.media_agents.delete(maclient.client_name, True)
                        maclient.release_license()
                        self.commcell.clients.delete(maclient.client_name)
                        self.log.info("deleted client %s" % maclient.client_name)
                    except Exception as err:
                        self.log.error("Remove mediaagent failed with exception %s" % err)
        except Exception as exep:
            self.log.info("Cleanup failed%s" % exep)

