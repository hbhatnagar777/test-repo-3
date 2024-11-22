# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  initial settings for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.Network.networkhelper import NetworkHelper
from AutomationUtils.machine import Machine

import time


class TestCase(CVTestCase):

    """Class for executing Validation of incorrect additional setting sBindToInterface on the client

        Setup requirements to run this test case:
        1 client -- can be any client in the commcell
        make sure client connectivity with machine credentials from controller machine

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = ("[Negative scenario] : Validation of incorrect additional "
                     "setting sBindToInterface on the client")
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NETWORK
        self.tcinputs = {
            "FirewallClient1": None,
            "username": None,
            "password": None
        }
        self._network = None
        self.machine_obj = None
        self.client_obj = None
        self.additional_setting_cache_file = None

    def setup(self):
        """Setup function of this test case"""
        self._network = NetworkHelper(self)

    def run(self):
        """Run function """
        non_existing_interface = '192.168.20.42'

        try:
            self.log.info("Started executing testcase")
            self._network.serverbase.check_client_readiness([self.tcinputs['FirewallClient1']])
            self.log.info("creating machine instance for client %s",
                          self.tcinputs['FirewallClient1'])
            self.machine_obj = Machine(machine_name=self.tcinputs['FirewallClient1'],
                                                 username=self.tcinputs['username'],
                                                 password=self.tcinputs['password'])

            self.log.info("creating client instance")
            self.client_obj = self.commcell.clients.get(self.tcinputs['FirewallClient1'])

            self.additional_setting_cache_file = \
                self.machine_obj.join_path(self.client_obj.install_directory,
                                           "Base",
                                           "AdditionalSettingsCache.xml")

            gxadmin_path = self.machine_obj.join_path(self.client_obj.install_directory,
                                                      "Base",
                                                      "GxAdmin.exe")
            self.restart_cv_cmd = "{0} -consoleMode -restartsvcgrp ALL".format(gxadmin_path)

            cvd_log_file = self.machine_obj.join_path(self.client_obj.log_directory, "cvd.log")

            self.log.info("adding additional setting sBindToInterfaces on client")
            self.client_obj.add_additional_setting("~", "sBindToInterface", "STRING", non_existing_interface)

            self.log.info("restarting CV services on client %s", self.tcinputs['FirewallClient1'])
            self.client_obj.restart_services(wait_for_service_restart=False)

            self.log.info("allowing some time for CV service to attempt restarting")
            time.sleep(60)

            expected_pattern = "Failed to pre-bind socket to local interface {0}".format(non_existing_interface)
            self.log.info("reading cvd log file %s", cvd_log_file)
            log_content = self.machine_obj.read_file(cvd_log_file, search_term=expected_pattern)
            if log_content:
                self.log.info("cvd service didn't come up on client with not reachable interface")
            else:
                self.log.error("couldn't find expected string CVD log on client %s",
                               self.tcinputs['FirewallClient1'])

            try:
                self._network.serverbase.check_client_readiness([self.tcinputs['FirewallClient1']])
                raise Exception("check readiness is successful unexpectedly")
            except Exception as excp:
                self.log.info("check readiness failed as expected")

        except Exception as excp:
            self._network.server.fail(excp)
        finally:
            if self.machine_obj.check_registry_exists("", "sBindToInterface"):
                self.log.info("removing sBindToInterface from reg")
                self.machine_obj.remove_registry("", "sBindToInterface")

                if self.machine_obj.check_file_exists(self.additional_setting_cache_file):
                    self.machine_obj.delete_file(self.additional_setting_cache_file)

                self.log.info("running command %s", self.restart_cv_cmd)
                self.machine_obj.execute_command(self.restart_cv_cmd)
            self._network.cleanup_network()
