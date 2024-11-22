# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for [Laptop Install]-[Plans]- [Laptop Repurpose] - Reinstall client with admin user with
    reg key set dAllowLaptopRepurposeByAdmin

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelper
from Laptop import laptopconstants as LC
from Server.Security.securityhelper import OrganizationHelper

class TestCase(CVTestCase):
    """Test case class for [Laptop Install]-[Plans]- [Laptop Repurpose] - Reinstall client with admin user
        with reg key set dAllowLaptopRepurposeByAdmin"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """[Laptop Install] [Plans] [Laptop Repurpose] - Reinstall client with admin user and reg key
                            set dAllowLaptopRepurposeByAdmin"""
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.install_kwargs = {}
        self.config_kwargs = {}

        # PRE-REQUISITES OF THE TESTCASE
        # - Company should be created on commcell
        # - A Plan should be created on commcell which could be associated to the company as default plan.

    def run(self):
        """ Main function for test case execution."""
        try:
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Commcell', ["User_admin", "Password_admin"]))
            self.tcinputs['Skip_RDP_Users'] = [self.tcinputs['User_admin']]
            laptop_helper = LaptopHelper(self)

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                            REINSTALL WITH ADMIN USER - OLD CLIENT RENAME - REPURPOSE
                1. Set default plan for commcell and install custom package
                2. Execute SimCallWrapper and register the client with user [user1]
                3. Wait for osc backup, change subclient content and execute backup/restore
                4. Do client validation.
                5. Uninstall client locally and set the registry key dAllowLaptopRepurposeByAdmin
                6. Install custom package again on the client and register with the admin user [admin],
                    and blacklist old owner as he was repurposed and left the company.
                7. Old Laptop should get repurposed and get renamed to oldclient_repurposed
                8. New client also should get created after reinstall with admin user as owner.
            """, 200)
            #-------------------------------------------------------------------------------------

            # Install laptop client and validate laptop installation
            orghelper = OrganizationHelper(self.commcell)
            orghelper.commcell_default_plan = self.tcinputs['Default_Plan']
            self.refresh()
            laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)

            # Install laptop client [Skip hard delete from commcell post uninstallation) and validate post install
            self.install_kwargs['delete_client'] = False
            self.install_kwargs['blacklist_user'] = self.tcinputs['Activation_User']
            user1 = self.tcinputs['Activation_User']
            self.tcinputs['Activation_User'] = self.tcinputs['User_admin']
            self.tcinputs['Activation_Password'] = self.tcinputs['Password_admin']
            laptop_helper.utils.modify_additional_settings('dAllowLaptopRepurposeByAdmin', "1", 'CommServe', 'INTEGER')
            laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)

            # Make sure laptop was repurposed
            repurposed_client = self.tcinputs['Machine_client_name'] + LC.REPURPOSED_CLIENT
            assert self.commcell.clients.has_client(repurposed_client), "Failed to repurpose laptop"
            rep_client_obj = self.commcell.clients.get(repurposed_client)
            assert rep_client_obj.client_name == repurposed_client, "Repurpose laptop's client name failed"
            assert rep_client_obj.client_hostname == repurposed_client, "Repurpose laptop's client hostname failed"
            self.log.info("Repurposed client name on CS: [{0}]".format(rep_client_obj.client_name))
            self.log.info("Repurposed client hostname on CS: [{0}]".format(rep_client_obj.client_hostname))
            self.log.info("Repurposed laptop [{0}] successfully.".format(repurposed_client))

            # Validate repurposed laptop owner. Should not change.
            laptop_helper.organization.validate_client_owners(repurposed_client, [user1])

            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(excp))
            laptop_helper.cleanup(self.tcinputs)
        finally:
            laptop_helper.utils.delete_additional_settings('dAllowLaptopRepurposeByAdmin', 'CommServe')

    def refresh(self):
        """ Refresh the dicts """
        self.config_kwargs.clear()
        self.install_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': False,
            'org_set_default_plan': False
        }

        self.install_kwargs = {
            'install_with_authcode': False,
            'execute_simcallwrapper': True,
            'check_num_of_devices': False
        }
