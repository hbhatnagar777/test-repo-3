# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for [Laptop Install] :Enable/Disable laptop backup for a particular client with qscript enableLaptopBackup

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelper

class TestCase(CVTestCase):
    """Test case class for [Laptop Install] : Enable/Disable laptop backup for a particular client
        with qscript enableLaptopBackup"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Laptop Install] : Enable/Disable laptop backup for a client with qscript enableLaptopBackup"
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.install_kwargs = {}
        self.config_kwargs = {}

        # PRE-REQUISITES OF THE TESTCASE
        # - Tenant_company and Default_Plan should be created on commcell

    def run(self):
        """ Main function for test case execution."""
        try:
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Company1'))
            laptop_helper = LaptopHelper(self, company=self.tcinputs['Tenant_company'])

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                - Install a laptop client and verify its registry and db values
                - Run qscript: qoperation execscript -sn enableLaptopBackup -si "OFF" -si "<clientname>"
                    Validate DB and Registry
                - Run qscript: qoperation execscript -sn enableLaptopBackup -si "ON" -si "<clientname>"
                    Validate DB and Registry,  Restart services on the client, Verify DB and Registry.
                - Manually modify DB value
                update app_clientprop set attrval = 0 where attrname = 'Personal Workstation' and componentNameId = ?
                    Run qscript: qoperation execscript -sn enableLaptopBackup -si "ON" -si "<clientname>"
                    Verify DB and Reg key

            """, 200)

            self.refresh()
            laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)
            clientobject = self.commcell.clients.get(self.tcinputs['Machine_client_name'])
            clientname = self.tcinputs['Machine_client_name']
            clientid = clientobject.client_id
            macobj = self.tcinputs['Machine_object']
            laptop_helper.laptop_status(macobj, clientobject, client_status=4096, workstation=1, nlaptopagent=1)

            # -----------------------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                Run qscript: qoperation execscript -sn enableLaptopBackup -si "OFF" -si "<clientname>
                Validate DB and Registry
                """)
            laptop_helper.set_laptop_backup(clientname, 'OFF')
            laptop_helper.laptop_status(macobj, clientobject, client_status=0, workstation=0, nlaptopagent=1)
            laptop_helper.utils.restart_services([clientname])
            laptop_helper.laptop_status(macobj, clientobject, client_status=0, workstation=0, nlaptopagent=0)

            # -----------------------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                Run qscript: qoperation execscript -sn enableLaptopBackup -si "ON" -si "<clientname>"
                Validate DB and Registry""")
            laptop_helper.set_laptop_backup(clientname, 'ON')
            laptop_helper.laptop_status(macobj, clientobject, client_status=4096, workstation=1, nlaptopagent=0)
            laptop_helper.utils.restart_services([clientname])
            laptop_helper.laptop_status(macobj, clientobject, client_status=4096, workstation=1, nlaptopagent=1)

            # -----------------------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                - Manually modify DB value
                update app_clientprop set attrval = 0 where attrname = 'Personal Workstation' and componentNameId = ?
                    Run qscript: qoperation execscript -sn enableLaptopBackup -si "ON" -si "<clientname>"
                    Verify DB and Reg key""")
            laptop_helper.utility.update_commserve_db(
                "update app_clientprop set attrval = 0 where attrname = 'Personal Workstation' and componentNameId = {0}"
                .format(clientid))
            laptop_helper.laptop_status(macobj, clientobject, client_status=4096, workstation=0, nlaptopagent=1)
            laptop_helper.set_laptop_backup(clientname, 'ON')
            laptop_helper.utils.restart_services([clientname])
            laptop_helper.laptop_status(macobj, clientobject, client_status=4096, workstation=1, nlaptopagent=1)

            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
            laptop_helper.cleanup(self.tcinputs)

    def refresh(self):
        """ Refresh the dicts """
        self.config_kwargs.clear()
        self.install_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': False,
            'org_set_default_plan': True,
        }

        self.install_kwargs = {
            'install_with_authcode': False,
            'execute_simcallwrapper': True,
            'post_osc_backup': False
        }
