# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  initialize TestCase class

    setup()             --  setup function of this test case

    run()               --  run function of this test case
"""

import time
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from MediaAgents import scaleouthelper


class TestCase(CVTestCase):
    """Class for validating hyper-scale reference architecture"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = """HyperScale Automation: Reference Architecture end
         to end using KVM virtualization"""
        self.show_to_user = True
        self.csuser = None
        self.cspassword = None
        self.tcinputs = {
            "kvmserver": None,
            "kvmuser": None,
            "kvmpassword": None,
            "vmnames": None,
            "dvdpath": None,
            "csname": None,
            "csuser": None,
            "cspassword": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.csuser = self.tcinputs['csuser']
        self.cspassword = self.tcinputs['cspassword']

    def run(self):
        """Execution method for this test case"""
        try:
            vmnames = self.tcinputs['vmnames'].split(",")
            if len(vmnames) <= 2:
                raise Exception("We need 3 IP values, but less values are provided")
            csname = self.tcinputs['csname']
            kvmserver = self.tcinputs['kvmserver']
            kvmuser = self.tcinputs['kvmuser']
            kvmpassword = self.tcinputs['kvmpassword']
            commcell_user = self.inputJSONnode['commcell']['commcellUsername']
            commcell_password = self.inputJSONnode['commcell']['commcellPassword']
            kvmserver_machine = Machine(kvmserver, None, kvmuser, kvmpassword)
            vmadminobj = scaleouthelper.KvmAdmin(kvmserver_machine, self.log)
            
            for i in range(0, 3):
                ret = vmadminobj.getvm_list(vmnames[i])
                if ret:
                    vmadminobj.delete_vm(vmnames[i])
            vmadminobj.create_vm(vmnames[0], self.tcinputs['dvdpath'])
            vmadminobj.restart_vm(vmnames[0])
            vmadminobj.stopvm(vmnames[0])
            vmadminobj.guest_mount(vmnames[0])
            vmadminobj.ifcfgfileedit()
            vmadminobj.editrcscript()
            vmadminobj.guest_unmount()
            for i in range(1, 3):
                vmadminobj.clone_vm(vmnames[0], vmnames[i])
                if vmadminobj.getvm_list(vmnames[2]) == 0:
                    vmadminobj.delete_vm(vmnames[0])
                    vmadminobj.clone_vm(vmnames[1], vmnames[0])
            vmadminobj.vmip = []
            for i in range(0, 3):
                ret = vmadminobj.restart_vm(vmnames[i])
                if ret:
                    ipadd = vmadminobj.find_vm_ip_addr(vmnames[i])
                    if ipadd == "":
                        vmadminobj.restart_vm(vmnames[i])
                        vmadminobj.vmip.append(vmadminobj.find_vm_ip_addr(vmnames[i]))
                    else:
                        vmadminobj.vmip.append(ipadd)
            value = vmadminobj.vmip + vmnames
            vmadminobj.addhostentry(value)
            vmadminobj.copyreg_to_csscript(vmadminobj.vmip)

            for i in range(0, 3):
                vmadminobj.addhostentrycs(vmnames[i], vmadminobj.vmip[i], csname, self.csuser, self.cspassword)
                vmadminobj.executereg_tocs(vmadminobj.vmip[i], vmnames[i], csname,
                                           commcell_user, commcell_password)
                time.sleep(30)
                vmadminobj.commvault_restart(vmadminobj.vmip[i])
            self.log.info("Testcase execution completed")
        except Exception as exp:
            self.log.error('Failed with error:%s ' % str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
