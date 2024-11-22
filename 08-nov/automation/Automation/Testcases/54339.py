# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for [Laptop Install] - [ MSP- User Centric ] - Install with /authcode
                when Domain is Not already configured- [Auto Activation]

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelperUserCentric

class TestCase(CVTestCase):
    """Test case class for [Laptop Install] - [ MSP- User Centric ] - Install with /authcode
                            when Domain is Not already configured - [Auto Activation]"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """[Laptop Install] - [MSP- User Centric] - Install with /authcode when
                        Domain is Not already configured - [Auto Activation]"""
        self.product = self.products_list.LAPTOP
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.install_kwargs = {}
        self.config_kwargs = {}

        # PRE-REQUISITES OF THE TESTCASE
        # - Tenant_company and Default_Plan should be created on commcell

        # The DOMAIN for the activating domain user should not be created already or exist on the commcell
        # e.g Domain for the 'Activation_User' should not already exist on the commcell.

    def setup(self):
        """ Setup test case inputs from config template """
        test_inputs = LaptopHelperUserCentric.set_inputs(self, 'CustomDomainCompany')

        # Generate User map
        test_inputs['user_map'] = LaptopHelperUserCentric.create_pseudo_map(test_inputs)
        self.log.info("User map: [{0}]".format(test_inputs['user_map']))
        self.tcinputs.update(test_inputs)

    def run(self):
        """ Main function for test case execution."""
        try:
            laptop_helper = LaptopHelperUserCentric(self, company=self.tcinputs['Tenant_company'])
            user = self.tcinputs['Activation_User']
            laptop_helper.organization.is_domain_user(user)
            domain = user.split('\\')[0]
            commcell = self.commcell
            assert not commcell.domains.has_domain(domain), "Domain [{0}] already exists on commcell".format(domain)
            assert not commcell.users.has_user(user), "User [{0}] already exists on commcell".format(user)
            # Don't delete domain here. User might need it. Let user delete it

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                a. Enable shared laptop, auth code and set Default plan for Tenant company.
                b. [######] Domain should *NOT be created/configured for the Tenant already
                c. Create a custom package from cloud workflow **WITHOUT auth code and download all the packages
                        from cloud.
                d. Login on client with a domain user (e.g ######) .
                e. Install custom package on client [[ WinX64.exe /silent /install /silent /authcode ##### ]]
                    with authcode
                f. Once the client is registered a backup job should get triggered automatically from OSC schedule.
                    Wait for job to complete.
                g. Modify subclient content and add new content. Automatic incremental backup should be triggered
                    for new content added.
                h. Execute out of place restore for the content backed by backup job
                i. Do post install validation

                Expectations:
                    As part of auto activation, domain should get created for the MSP Tenant automatically,
                    for activating user and also the activating user should get created.
                    Client should auto activate and backups should run automatically.
            """, 200)

            self.refresh()
            laptop_helper.install_laptop(self.tcinputs, self.config_kwargs, self.install_kwargs)

            # Validate domain and user got created
            assert commcell.domains.has_domain(domain), "Custom Domain not created automatically."
            assert commcell.users.has_user(user), "Custom domain user not created post client installation."
            user_id = commcell.users.get(user).user_id
        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
        finally:
            laptop_helper.cleanup_user_centric(self.tcinputs)
            laptop_helper.organization.delete_domain(domain)
            laptop_helper.utility.update_commserve_db("delete from umusers where id="+str(user_id))

    def refresh(self):
        """ Refresh the dicts """

        self.config_kwargs.clear()
        self.install_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': True,
            'org_set_default_plan': True
        }

        self.install_kwargs = {
            'install_with_authcode': True,
            'execute_simcallwrapper': False
        }
