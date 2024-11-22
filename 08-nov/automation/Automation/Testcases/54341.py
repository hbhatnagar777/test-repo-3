# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for validating Laptop client upgrade cases

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""

from cvpysdk.deployment.deploymentconstants import DownloadPackages

from AutomationUtils.cvtestcase import CVTestCase
from Laptop.laptophelper import LaptopHelperUserCentric
from Server.JobManager.jobmanager_helper import JobManager

class TestCase(CVTestCase):
    """Test case class for validating Laptop client upgrade cases"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """[Laptop Upgrades] - [MSP- User Centric] - Upgrade laptop from a given service pack to Commserve's SP"""
        self.product = self.products_list.LAPTOP
        self.show_to_user = False
        self.install_kwargs = {}
        self.config_kwargs = {}
        self.custompackage_kwargs = {}
        self.job_list = []

        # PRE-REQUISITES OF THE TESTCASE
        # - Company should be created on commcell
        # - A Plan should be created on commcell which could be associated to the company as default plan.

    def setup(self):
        """ Setup test case inputs from config template """
        common_inputs = [
            "Activation_User1",
            "Activation_Password1",
            "Activation_User2",
            "Activation_Password2"
        ]
        test_inputs = LaptopHelperUserCentric.set_inputs(self, 'Company2', common_inputs)

        # Generate User map
        test_inputs['user_map'] = LaptopHelperUserCentric.create_pseudo_map(test_inputs)
        self.log.info("User map: [{0}]".format(test_inputs['user_map']))
        self.tcinputs.update(test_inputs)
        self.tcinputs['Activation_User'] = self.tcinputs['Activation_User1']
        self.tcinputs['Activation_Password'] = self.tcinputs['Activation_Password1']

    def run(self):
        """ Main function for test case execution."""
        try:
            laptop_helper = LaptopHelperUserCentric(self, company=self.tcinputs['Tenant_company'])

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                            Upgrade laptop from a given service pack to Commserve's SP
                Pre Requirements:
                    a. Check if Commcell Service Pack is higher than Client_SP_Level

                1. Enable shared laptop,Set default plan for Tenant Company and install custom package [Should be at lower SP level
                    than Commserver]
                        <InstallationPackage>.exe /silent /install /silent
                        Run Simcalwrapper to register and activate

                    - Wait for laptop full backup job to start from osc schedule.
                        Change subclient content, wait for incremental backup to trigger.
                        Execute out of place restore and validate.

                    - Validation
                        - Check client readiness succeeds
                        - Verify Session->nchatterflag is off in registry for clients
                        - Verify FileSystem->nLaptopAgent flag is set to 1 in registry for the client
                        - Verify Plan and company's client group associations for activated client
                        - Client is visible in Company's devices
                        - Validate client ownership is set to the activating user

                2. Do push upgrade on the client and upgrade to Commserver's Service pack level

                3. Post Upgrade-
                                a. Create test data on the client
                                b. Add content in the default subclient
                                c. Make sure OSC triggered backup is run 
                                d. After backup completes, execute out of place restore and validate
                                checksum/metadata for the backed up content.

                4. Complete laptop validation.

            """, 200)
            #-------------------------------------------------------------------------------------

            # Install laptop client and validate laptop installation
            self.refresh()
            self.custompackage_kwargs['servicePack'] = laptop_helper.laptop_config.Client_SP_Level
            self.custompackage_kwargs['SP_revision'] = laptop_helper.laptop_config.Client_SP_Revision

            laptop_helper.install_laptop(
                self.tcinputs, self.config_kwargs, self.install_kwargs, self.custompackage_kwargs
            )

            # Execute Download Software job for latest hotfixes for installed service pack.
            download_job = laptop_helper.installer.download_software(
                os_list=[DownloadPackages.UNIX_MAC.value, DownloadPackages.WINDOWS_64.value]
            )
            self.job_list.append(download_job)

            # Execute push install upgrade for the client
            install_job = laptop_helper.installer.push_servicepack_and_hotfix()
            self.job_list.append(install_job)

            # Post upgrade backup validation
            for key in self.tcinputs['user_map']:
                laptop_helper.utils.osc_backup_and_restore(
                    self.tcinputs['Machine_client_name'],
                    validate=True,
                    postbackup=self.install_kwargs.get('post_osc_backup', laptop_helper.skip_postosc_backup),
                    skip_osc=self.install_kwargs.get('skip_osc', laptop_helper.skip_osc_job_wait),
                    options=self.tcinputs['osc_options'],
                    validate_user=self.install_kwargs.get('validate_user', False),
                    registering_user=self.tcinputs['Activation_User'],
                    client_name=self.tcinputs['user_map'][key]['pseudo_client'],
                    current_state=['completed', 'running', 'waiting'],
                    incr_current_state=['running', 'waiting', 'pending']
                )

            #---------------------------------------------------------------------------------
            # Install validation
            # 1: For Physical clients no Owner should be set
            # 2: For Pseudo clients
            #       - For each pseudo client and make sure it's owner is set
            #       - Validate the pseudo client count after installation.
            #---------------------------------------------------------------------------------

            laptop_helper.tc.log_step("""
                -  [{0}] Validation phase""".format(self.tcinputs['Machine_host_name']))

            # Physical client does not get associated to Plan client groups.
            laptop_helper.organization.validate_client(
                self.tcinputs['Machine_object'],
                expected_owners=[],
                client_groups=['Laptop Clients', laptop_helper.organization.company_name],
                clients_joined=True,
                increment_client_count_by=0,
                nLaptopAgent=1,
                client_name=self.tcinputs['Machine_client_name']
            )

            # Validation for User Centric pseudo clients
            for each_user in self.tcinputs.get('user_map', []):
                laptop_helper.organization.validate_usercentric_client(
                    self.tcinputs['user_map'][each_user]['pseudo_client'],
                    expected_owners=[each_user],
                    client_groups=self.install_kwargs.get(
                        'pseudo_client_groups',
                        self.install_kwargs.get('client_groups')
                    )
                )

        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
            for _job in self.job_list:
                if not _job.is_finished:
                    JobManager(_job, self.commcell).modify_job('kill')
        finally:
            laptop_helper.cleanup_user_centric(self.tcinputs)

    def refresh(self):
        """ Refresh the dicts """
        self.config_kwargs.clear()
        self.install_kwargs.clear()
        self.custompackage_kwargs.clear()

        self.config_kwargs = {
            'org_enable_auth_code': False,
            'org_set_default_plan': True
        }

        self.install_kwargs = {
            'install_with_authcode': False,
            'execute_simcallwrapper': True,
        }
