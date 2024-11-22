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

import multiprocessing
import time
from Server.Network.networkhelper import NetworkHelper
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """
    This test case to verify if CS can handle multiple qlogin operation.
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.tcinputs = {
            "NetworkClient": None,
            "NetworkMediaAgent": None,
        }
        self.name = "[Network & Firewall]: Performing multiple Qlogin operation"
        self.machine = None
        self.cs_obj = None
        self.user = None
        self.passwd = None
        self.cs = None
        self.cmd = None
        self.network_helper = None

    def setup(self):
        self.user = self.inputJSONnode['commcell']['commcellUsername']
        self.passwd = self.inputJSONnode['commcell']['commcellPassword']
        self.cs = self.inputJSONnode['commcell']['webconsoleHostname']
        self.log.info("Creating Machine object")
        self.cs_obj = self.commcell.clients.get(self.commcell.commserv_name)
        self.network_helper = NetworkHelper(self)

    def run(self):
        for i in range(25):
            self.qlogin(i)

        self.log.info("[+] >>> SUCCESSFUL <<< [+]")

    def qlogin(self, idx):
        loop = 20
        self.cmd = f"for (($i = 0); $i -lt {loop}; $i++){{qlogin -u {self.user} -clp {self.passwd} -cs {self.cs}}}"
        self.machine = Machine(self.cs_obj)
        op = self.machine.execute_command(self.cmd)
        if '\r' in op.output:
            op_split = op.output.split('\r\n')
        else:
            op_split = op.output.split('\n')
        count = op_split.count("User logged in successfully.")
        if count != loop:
            raise Exception(f"Unable to perform 50 operations.\n{count} Successful attempts")

    def backup(self):
        self.network_helper.validate(
            [self.tcinputs["NetworkClient"]], self.tcinputs["NetworkMediaAgent"],
            test_data_size=500
        )
