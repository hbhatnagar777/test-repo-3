# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case"""

from AutomationUtils.cvtestcase import CVTestCase

from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Helper.LaptopHelper import LaptopMain
from Laptop.laptophelper import LaptopHelper
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from Server.JobManager.jobmanager_helper import JobManager


from Reports.utils import TestCaseUtils


class TestCase(CVTestCase):
    """ [Laptop] [AdminConsole]: Add Laptop (Install and activate)"""

    def __init__(self):
        """
         Initializing the Test case file
        """
        super(TestCase, self).__init__()
        self.name = "[Laptop] [AdminConsole]: Add Laptop (Install and activate)"
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ADMINCONSOLE
        self.show_to_user = False
        self.browser = None
        self.admin_console = None
        self.laptop_obj = None
        self.utils = TestCaseUtils(self)
        self.laptop_helper = None
        self.client_obj = None
        self.job_manager = None
        self.ida_utils = None
        self.utility = None


    def run(self):

        try:
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Commcell'))
            self.laptop_helper = LaptopHelper(self)
            self.utility = OptionsSelector(self._commcell)
            self.ida_utils = CommonUtils(self._commcell)
            self.job_manager = JobManager(commcell=self._commcell)

            #-------------------------------------------------------------------------------------
            self.laptop_helper.tc.log_step("""
                1. Go to Solutions->Laptop page and click on "Add laptop" option
                2. Make sure job completes and successfull.
                3. Activate the laptop by user
                4. Validation
                        - Check client readiness succeeds
                        - Verify Session->nchatterflag is off in registry for clients
                        - Verify FileSystem->nLaptopAgent flag is set to 1 in registry for the client
                        - The client should be a part of the default plan that was set for the commcell.
                        - Validate client ownership is set to the activating user

            """, 200)
            #-------------------------------------------------------------------------------------

            self.log.info("Started executing %s testcase", self.id)

            machine_obj = self.utility.get_machine_object(self.tcinputs['Machine_host_name'],
                                                          self.tcinputs['Machine_user_name'],
                                                          self.tcinputs['Machine_password'])

            self.laptop_helper.tc.log_step(""" Initialize browser objects """)

            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)

            self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                     self.inputJSONnode['commcell']['commcellPassword'])

            self.laptop_obj = LaptopMain(self.admin_console, self.commcell)
            self.laptop_obj.host_name = self.tcinputs["Machine_fqdn_name"]
            self.laptop_obj.user_name = self.tcinputs['Machine_user_name']
            self.laptop_obj.password = self.tcinputs['Machine_password']
            self.laptop_obj.confirm_password = self.tcinputs['Machine_password']
            self.laptop_obj.client_name = self.tcinputs['Machine_host_name']
            self.laptop_obj.activation_plan = self.tcinputs['Default_Plan']
            if self.tcinputs['os_type'] == 'Mac':
                self.laptop_obj.add_new_mac_laptop()
            else:
                self.laptop_obj.add_new_windows_laptop()

            #Activate the laptop by default plan
            self.laptop_helper.tc.log_step(""" Started activating laptop by plan """)
            self.laptop_obj.activate_laptop_byplan(self.tcinputs['Default_Plan'])

            self.commcell.clients.refresh()
            self.client_obj = self.commcell.clients.get(self.tcinputs['Machine_host_name'])

            self.laptop_helper.tc.log_step("Wait for auto triggered backup job to be competed after Laptop added")
            _jobs = self.job_manager.get_filtered_jobs(
                self.tcinputs['Machine_host_name'],
                time_limit=5,
                retry_interval=5,
                backup_level='Full',
                current_state='Running'
                )

            self.laptop_helper.tc.log_step(""" Validating laptop after activation """)
            # validate """activated client""" from adminconsole
            self.laptop_obj.validate_client_from_adminconsole(actvation=True)
            #validate installed laptop client
            self.laptop_helper.organization.validate_client(
                machine_obj,
                client_groups=None,
                clients_joined=False
                )

            self.laptop_helper.tc.log_step(""" Started triggering backup job from adminconsole """)

            self.laptop_obj.perform_backup_now() # to perform backup job
            self.log.info("*****Add Laptop (Install and activate) completed successfully*****")


        except Exception as exp:
            self.utils.handle_testcase_exception(exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
            try:
                self.laptop_helper.uninstall_laptop(self.tcinputs)
            except Exception as err:
                self.log.info("Failed to cleanup")

