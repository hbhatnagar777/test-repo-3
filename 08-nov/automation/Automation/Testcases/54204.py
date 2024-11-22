# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2016 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case
"""

import sys
from time import sleep
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.unix_machine import UnixMachine


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "Imaging"
        self.show_to_user = True
        self.unix_machine = None
        self.vm_name = None
        self.command = None
        self.ncommand = None
        self.tcinputs = {
            "ClientIP": None,
            "ClientUserName": None,
            "ClientPassword": None,
            "UserName": None,
            "Password": None,
            "VM1_IP": None,
            "VM2_IP": None,
            "VM3_IP": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.command = "ipmitool -I lanplus -U " + self.tcinputs['UserName'] + " -P " \
                       + self.tcinputs['Password'] + " -H "
        self._log = logger.get_log()
        self._log.info("********* UnixMachine Object ***********")
        self.unix_machine = UnixMachine(
            self.tcinputs['ClientIP'],
            self.commcell,
            self.tcinputs['ClientUserName'],
            self.tcinputs['ClientPassword'])

    def set_command(self, node, stat):
        """set the command"""
        self.ncommand = self.command + self.tcinputs[node] + " chassis power " + stat
        return self.ncommand

    def chassis_power_control(self, node, value=None):
        """Checking chassis power"""

        self._log.info(str("iRMC for " + self.tcinputs[node] + ' Chassis Powered ' + value))
        output = self.unix_machine.execute_command(self.set_command(node, value))
        if output.exception_message:
            raise Exception(output.exception_message)

        return "".join(output.formatted_output)

    def chassis_power_control_pxe(self, node):
        """Checking chassis power"""

        self._log.info(str("iRMC for " + self.tcinputs[node] + ' Chassis boot device set to pxe'))
        output = self.unix_machine.execute_command(self.command + self.tcinputs[node] + " chassis bootdev pxe")
        if output.exception_message:
            raise Exception(output.exception_message)

        return "".join(output.formatted_output)

    def chassis_power_control_disk(self, node):
        """Checking chassis power"""

        self._log.info(str("iRMC for " + self.tcinputs[node] + ' Chassis boot device set to Disk'))
        output = self.unix_machine.execute_command(self.command + self.tcinputs[node] + " chassis bootdev disk")
        if output.exception_message:
            raise Exception(output.exception_code, output.exception_message)

        return "".join(output.formatted_output)

    def status_change(self, type_mode):
        """Checking status"""

        if type_mode is 'disk':
            ret = self.chassis_power_control_disk(self.vm_name)
        else:
            ret = self.chassis_power_control_pxe(self.vm_name)
        self._log.info(str('status: ' + ret))
        if ret == 'Set Boot Device to ' + type_mode:
            sleep(30)
            ret = self.chassis_power_control(self.vm_name, value='on')
            self._log.info(str('status: ' + ret))


    def set_mode(self, type_mode):
        """Set boot mode"""

        try:
            for i in range(1, 4):
                self.vm_name = 'VM' + str(i) + '_IP'
                ret = self.chassis_power_control(self.vm_name, value='status')
                self._log.info(str('status: ' + ret))
                if ret in 'Chassis Power is on' or 'Chassis Power Control: Up/On':
                    ret = self.chassis_power_control(self.vm_name, value='off')
                    self._log.info(str('status: ' + ret))
                    if ret in 'Chassis Power is off' or 'Chassis Power Control: Down/Off':
                        sleep(30)
                        self.status_change(type_mode)
                else:
                    self._log.info('status Off')
                    sleep(30)
                    self.status_change(type_mode)

        except Exception as exp:
            self.log.exception(exp)

    def run(self):
        """Run function of this test case"""
        try:
            self._log.info(str("Started executing %s testcase" % self.id))
            self.set_mode('pxe')
            sleep(2700)
            self.set_mode('disk')
            self.result_string = "Run of test case completed"

        except Exception as exp:
            self.log.error("Detailed Exception : %s", sys.exc_info())
            self.result_string = str(exp)

