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
from Laptop.laptophelper import LaptopHelper
from Server.JobManager.jobmanager_helper import JobManager

class TestCase(CVTestCase):
    """Test case class for validating Laptop client upgrade cases"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """[Laptop Upgrades] - [MSP] - Upgrade laptop from a given service pack to Commserve's SP"""
        self.product = self.products_list.LAPTOP
        self.show_to_user = False
        self.install_kwargs = {}
        self.config_kwargs = {}
        self.custompackage_kwargs = {}
        self.job_list = []

        # PRE-REQUISITES OF THE TESTCASE
        # - Company should be created on commcell
        # - A Plan should be created on commcell which could be associated to the company as default plan.

    def run(self):
        """ Main function for test case execution."""
        try:
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Company1'))
            laptop_helper = LaptopHelper(self, company=self.tcinputs['Tenant_company'])

            #-------------------------------------------------------------------------------------
            laptop_helper.tc.log_step("""
                            Upgrade laptop from a given service pack to Commserve's SP
                Pre Requirements:
                    a. Check if Commcell Service Pack is higher than Client_SP_Level

                1. Set default plan for Tenant Company and install custom package [Should be at lower SP level
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
            laptop_helper.organization.validate_client(
                self.tcinputs['Machine_object'],
                expected_owners=[self.tcinputs['Activation_User']],
                client_groups=None,
                clients_joined=False,
                nLaptopAgent=1
            )

            # Validate automatic (osc) backups and restores
            _os = self.tcinputs['Machine_object'].os_info
            laptop_helper.utils.osc_backup_and_restore(
                self.tcinputs['Machine_object'],
                validate=True,
                postbackup=True,
                skip_osc=True,
                options='-testuser root -testgroup admin' if _os != 'WINDOWS' else None
            )

            laptop_helper.cleanup(self.tcinputs)

        except Exception as excp:
            laptop_helper.tc.fail(str(excp))
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
            laptop_helper.cleanup(self.tcinputs)
            for _job in self.job_list:
                if not _job.is_finished:
                    JobManager(_job, self.commcell).modify_job('kill')

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
