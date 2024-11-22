# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                              --  initialize TestCase class

    setup()                                 --  setup function of this test case

    run()                                   --  run function of this test case

    tear_down()                             --  tear down function of this test case

    init_tc()                               --  Initial configuration of activate for test case

    check_snap_install_content_analyzer()   --  Reverts the snap and installs CA package on vm client

    create_plan()                           --  Creates the data classification plan for SDG

"""

from AutomationUtils import constants
from AutomationUtils.config import get_config
from AutomationUtils.cvtestcase import CVTestCase
from dynamicindex.content_analyzer_helper import ContentAnalyzerHelper
from dynamicindex.utils import constants as dynamic_constants
from dynamicindex.vm_manager import VmManager
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.Helper.GDPRHelper import GDPR
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import handle_testcase_exception, TestStep

_CONFIG_DATA = get_config().DynamicIndex.LinuxHyperV


class TestCase(CVTestCase):
    """Class for executing this test case"""

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Verify TPPM creation & deletion for Unix content extractor service via DC Plan"
        self.tcinputs = {
            "IndexServerName": None
        }
        self.ca_helper_obj = None
        self.ca_cloud_name = None
        self.browser = None
        self.admin_console = None
        self.gdpr_obj = None
        self.plan_name = None
        self.plan_name_second = None
        self.vm_name = None
        self.vm_manager = None
        self.commcell_password = None
        self.hyperv_name = None
        self.hyperv_username = None
        self.hyperv_password = None
        self.vm_name = None
        self.vm_username = None
        self.vm_password = None
        self.snap_name = None

    def check_snap_install_content_analyzer(self):
        """Reverts the snap and installs CA package on this vm client"""
        self.vm_manager.check_client_revert_snap(
            hyperv_name=self.hyperv_name,
            hyperv_user_name=self.hyperv_username,
            hyperv_user_password=self.hyperv_password,
            snap_name=self.snap_name,
            vm_name=self.vm_name
        )
        self.log.info("Revert is successful")
        index_server_obj = self.commcell.index_servers.get(self.tcinputs['IndexServerName'])
        client_list = index_server_obj.client_name
        client_list.append(self.commcell.commserv_name)
        self.vm_manager.populate_vm_ips_on_client(config_data=_CONFIG_DATA, clients=client_list)

        self.log.info("*************** Install content Analyzer client starts ****************")
        self.ca_helper_obj.install_content_analyzer(
            machine_name=self.vm_name,
            user_name=self.vm_username,
            password=self.vm_password,
            platform="Unix")
        self.log.info(f"Check whether python process is up and running on CA machine : {self.vm_name}")
        self.log.info("Refreshing client list as we installed new client with CA package")
        self.commcell.clients.refresh()
        client_obj = self.commcell.clients.get(self.vm_name)
        self.ca_helper_obj.check_all_python_process(client_obj=client_obj)
        self.log.info("*************** Install content Analyzer client ends *****************")

    def setup(self):
        """Setup function of this test case"""
        self.hyperv_name = _CONFIG_DATA.HyperVName
        self.hyperv_username = _CONFIG_DATA.HyperVUsername
        self.hyperv_password = _CONFIG_DATA.HyperVPassword
        self.vm_name = _CONFIG_DATA.VmName
        self.vm_username = _CONFIG_DATA.VmUsername
        self.vm_password = _CONFIG_DATA.VmPassword
        self.snap_name = _CONFIG_DATA.SnapName
        self.commcell_password = self.inputJSONnode['commcell']['commcellPassword']
        self.ca_helper_obj = ContentAnalyzerHelper(self)
        self.vm_manager = VmManager(self)
        self.ca_cloud_name = "%s_ContentAnalyzer" % self.vm_name
        self.plan_name = "TestPlan_1_%s" % self.id
        self.plan_name_second = "TestPlan_2_%s" % self.id
        self.check_snap_install_content_analyzer()

    def init_tc(self):
        """ Initial configuration of activate for the test case. """
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname,
                                          username=self.commcell.commcell_username,
                                          password=self.commcell_password)
        self.admin_console.login(username=self.commcell.commcell_username,
                                 password=self.commcell_password)
        self.log.info('Logged in through web automation')
        self.gdpr_obj = GDPR(self.admin_console, self.commcell, self.csdb)

    @test_step
    def create_plan(self, plan_name):
        """creates a data classification plan

                Args:

                    plan_name       (str)       --  Name of the plan

                Returns:

                    None
        """
        self.admin_console.navigator.navigate_to_plan()
        self.gdpr_obj.plans_obj.create_data_classification_plan(
            plan_name, self.tcinputs['IndexServerName'],
            self.ca_cloud_name, [dynamic_constants.ENTITY_EMAIL])

    def run(self):
        """Run function of this test case"""
        try:
            self.init_tc()

            # create DC plan
            self.create_plan(plan_name=self.plan_name)

            # Verify tppm entry
            self.ca_helper_obj.validate_tppm_setup(index_server=self.tcinputs['IndexServerName'],
                                                   content_analyzer=self.ca_cloud_name)

            # create second DC plan
            self.log.info(f"Going to create Second DC plan : {self.plan_name_second}")
            self.create_plan(plan_name=self.plan_name_second)

            # Verify no duplicate tppm entry
            self.ca_helper_obj.validate_tppm_setup(index_server=self.tcinputs['IndexServerName'],
                                                   content_analyzer=self.ca_cloud_name)

            # Delete first DC plan
            self.log.info(f"Going to delete First DC plan : {self.plan_name}")
            self.gdpr_obj.cleanup(plan_name=self.plan_name)

            # Verify tppm entry
            self.ca_helper_obj.validate_tppm_setup(index_server=self.tcinputs['IndexServerName'],
                                                   content_analyzer=self.ca_cloud_name)

            # Delete second DC plan
            self.log.info(f"Going to delete Second DC plan : {self.plan_name_second}")
            self.gdpr_obj.cleanup(plan_name=self.plan_name_second)

            # Verify No tppm entry exists now as we deleted all plans
            self.ca_helper_obj.validate_tppm_setup(index_server=self.tcinputs['IndexServerName'],
                                                   content_analyzer=self.ca_cloud_name, exists=False)

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status != constants.FAILED:
            self.log.info("Going to delete CA cloud pseudoclient")
            self.commcell.clients.delete(self.ca_cloud_name)
            self.log.info(f"CA Cloud pseudoclient deleted successfully : {self.ca_cloud_name}")
            self.log.info("Going to delete CA client")
            self.commcell.clients.delete(self.vm_name)
            self.log.info(f"CA client deleted successfully : {self.vm_name}")
            self.vm_manager.vm_shutdown(hyperv_name=self.hyperv_name,
                                        hyperv_user_name=self.hyperv_username,
                                        hyperv_user_password=self.hyperv_password,
                                        vm_name=self.vm_name)
            self.log.info("Power off vm successfull")
